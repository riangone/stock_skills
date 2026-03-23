"""WebUI SQLite Database Module.

ポートフォリオとウォッチリストを管理する SQLite データベースモジュール。
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime


# データベースパス
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "webui.db"


@contextmanager
def get_db_connection():
    """データベース接続コンテキストマネージャ"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """データベース初期化（テーブル作成）"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # ポートフォリオテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                shares INTEGER NOT NULL,
                cost_price REAL NOT NULL,
                currency TEXT DEFAULT 'JPY',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(ticker)
            )
        """)

        # 取引履歴テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trade_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                action TEXT NOT NULL,
                shares INTEGER NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'JPY',
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        """)

        # ウォッチリストテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ウォッチリスト銘柄テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist_tickers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watchlist_id INTEGER NOT NULL,
                ticker TEXT NOT NULL,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (watchlist_id) REFERENCES watchlist(id),
                UNIQUE(watchlist_id, ticker)
            )
        """)

        # スクリーニング履歴テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS screening_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                region TEXT NOT NULL,
                strategy TEXT NOT NULL,
                parameters TEXT,
                results_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()


# ==============
# ポートフォリオ操作
# ==============

def get_portfolio_positions() -> List[Dict[str, Any]]:
    """ポートフォリオの全ポジション取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM portfolio ORDER BY ticker")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def add_portfolio_position(ticker: str, shares: int, cost_price: float, currency: str = "JPY") -> bool:
    """ポジション追加・更新"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO portfolio (ticker, shares, cost_price, currency)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                shares = shares + excluded.shares,
                cost_price = (portfolio.cost_price * portfolio.shares + excluded.cost_price * excluded.shares) / (portfolio.shares + excluded.shares),
                updated_at = CURRENT_TIMESTAMP
        """, (ticker, shares, cost_price, currency))
        conn.commit()
        return True


def sell_portfolio_position(ticker: str, shares: int, price: float = 0) -> bool:
    """ポジション売却"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 現在のポジション取得
        cursor.execute("SELECT shares FROM portfolio WHERE ticker = ?", (ticker,))
        row = cursor.fetchone()

        if not row:
            return False

        current_shares = row["shares"]

        if shares >= current_shares:
            # 全売却
            cursor.execute("DELETE FROM portfolio WHERE ticker = ?", (ticker,))
        else:
            # 一部売却
            cursor.execute("""
                UPDATE portfolio SET shares = shares - ?, updated_at = CURRENT_TIMESTAMP
                WHERE ticker = ?
            """, (shares, ticker))

        conn.commit()
        return True


def clear_portfolio():
    """ポートフォリオをクリア"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM portfolio")
        conn.commit()


# ==============
# 取引履歴操作
# ==============

def add_trade_history(
    ticker: str,
    action: str,
    shares: int,
    price: float,
    currency: str = "JPY",
    notes: Optional[str] = None
) -> bool:
    """取引履歴を追加"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO trade_history (ticker, action, shares, price, currency, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (ticker, action, shares, price, currency, notes))
        conn.commit()
        return True


def get_trade_history(ticker: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """取引履歴取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if ticker:
            cursor.execute(
                "SELECT * FROM trade_history WHERE ticker = ? ORDER BY executed_at DESC LIMIT ?",
                (ticker, limit)
            )
        else:
            cursor.execute("SELECT * FROM trade_history ORDER BY executed_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ==============
# ウォッチリスト操作
# ==============

def get_watchlists() -> Dict[str, List[str]]:
    """すべてのウォッチリスト取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM watchlist")
        watchlists = {}

        for row in cursor.fetchall():
            watchlist_id = row["id"]
            watchlist_name = row["name"]

            cursor.execute(
                "SELECT ticker FROM watchlist_tickers WHERE watchlist_id = ?",
                (watchlist_id,)
            )
            tickers = [r["ticker"] for r in cursor.fetchall()]
            watchlists[watchlist_name] = tickers

        return watchlists


def create_watchlist(name: str) -> bool:
    """ウォッチリスト作成"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO watchlist (name) VALUES (?)", (name,))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False


def delete_watchlist(name: str) -> bool:
    """ウォッチリスト削除"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM watchlist WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            return False

        watchlist_id = row["id"]
        cursor.execute("DELETE FROM watchlist_tickers WHERE watchlist_id = ?", (watchlist_id,))
        cursor.execute("DELETE FROM watchlist WHERE id = ?", (watchlist_id,))
        conn.commit()
        return True


def add_to_watchlist(name: str, tickers: List[str]) -> bool:
    """ウォッチリストに銘柄追加"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # ウォッチリストが存在するか確認
        cursor.execute("SELECT id FROM watchlist WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            # 存在しない場合は作成
            cursor.execute("INSERT INTO watchlist (name) VALUES (?)", (name,))
            watchlist_id = cursor.lastrowid
        else:
            watchlist_id = row["id"]

        # 銘柄追加
        for ticker in tickers:
            try:
                cursor.execute("""
                    INSERT INTO watchlist_tickers (watchlist_id, ticker)
                    VALUES (?, ?)
                """, (watchlist_id, ticker))
            except sqlite3.IntegrityError:
                pass  # 重複は無視

        conn.commit()
        return True


def remove_from_watchlist(name: str, tickers: List[str]) -> bool:
    """ウォッチリストから銘柄削除"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM watchlist WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            return False

        watchlist_id = row["id"]
        cursor.execute("""
            DELETE FROM watchlist_tickers
            WHERE watchlist_id = ? AND ticker IN ({})
        """.format(",".join("?" * len(tickers))), [watchlist_id] + list(tickers))

        conn.commit()
        return True


def get_watchlist_tickers(name: str) -> List[str]:
    """ウォッチリストの銘柄取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM watchlist WHERE name = ?", (name,))
        row = cursor.fetchone()

        if not row:
            return []

        watchlist_id = row["id"]
        cursor.execute("SELECT ticker FROM watchlist_tickers WHERE watchlist_id = ?", (watchlist_id,))
        return [r["ticker"] for r in cursor.fetchall()]


# ==============
# スクリーニング履歴操作
# ==============

def add_screening_history(
    region: str,
    strategy: str,
    parameters: Dict[str, Any],
    results_count: int
) -> bool:
    """スクリーニング履歴を追加"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO screening_history (region, strategy, parameters, results_count)
            VALUES (?, ?, ?, ?)
        """, (region, strategy, json.dumps(parameters), results_count))
        conn.commit()
        return True


def get_screening_history(limit: int = 20) -> List[Dict[str, Any]]:
    """スクリーニング履歴取得"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM screening_history ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            d = dict(row)
            if d.get("parameters"):
                d["parameters"] = json.loads(d["parameters"])
            result.append(d)
        return result


# JSON インポート
import json

# 初期化
init_db()
