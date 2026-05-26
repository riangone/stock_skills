"""Stock Skills WebUI - FastAPI Application.

価値股スクリーニングシステムの WebUI。
FastAPI + HTMX + DaisyUI で構成。
"""

from fastapi import FastAPI, Request, Form, HTTPException, Query, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
from pathlib import Path
import json

from webui.auth import (
    verify_password, set_session_cookie, clear_session_cookie,
    get_current_user, require_auth,
    AUTH_USERNAME, AUTH_PASSWORD_HASH, AUTH_ENABLED
)

from src.core.screening.screener import QueryScreener, build_default_registry
from src.core.portfolio.portfolio_query import get_snapshot, get_portfolio_shareholder_return
from src.core.portfolio.portfolio_io import load_portfolio, save_portfolio, add_position, sell_position
from src.core.portfolio.concentration import analyze_concentration
from src.core.health_check import run_health_check as portfolio_health_check
from src.core.return_estimate import estimate_stock_return
from webui.config_manager import load_env, save_env, get_config_status, CONFIG_FIELDS

# ウォッチリスト用インポート
try:
    from src.core.common import load_watchlist, save_watchlist
    HAS_WATCHLIST = True
except ImportError:
    import yaml
    from pathlib import Path as FilePath

    WATCHLIST_PATH = FilePath(__file__).parent.parent / "data" / "watchlists.yaml"

    def load_watchlist():
        if WATCHLIST_PATH.exists():
            with open(WATCHLIST_PATH) as f:
                return yaml.safe_load(f) or {}
        return {}

    def save_watchlist(data):
        WATCHLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(WATCHLIST_PATH, 'w') as f:
            yaml.safe_dump(data, f, allow_unicode=True, default_flow_style=False)

    HAS_WATCHLIST = False

app = FastAPI(
    title="Stock Skills WebUI",
    description="価値股スクリーニングシステムの Web インターフェース",
    version="1.0.0"
)

# テンプレートと静的ファイルの設定
BASE_DIR = Path(__file__).resolve().parent.parent
templates_dir = BASE_DIR / "webui" / "templates"
static_path = BASE_DIR / "webui" / "static"

# Jinja2 テンプレートの設定
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader(str(templates_dir)),
    autoescape=True,
    cache_size=0,  # 開発モードではキャッシュを無効化
    auto_reload=True
)

class Templates:
    def __init__(self, env):
        self.env = env
    
    def TemplateResponse(self, name, context):
        from fastapi.responses import HTMLResponse
        template = self.env.get_template(name)
        return HTMLResponse(template.render(**context))

templates = Templates(env)
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# 307 リダイレクト HTTPException を実際の RedirectResponse に変換するハンドラー
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code in (307, 302, 301) and exc.headers and "Location" in exc.headers:
        return RedirectResponse(url=exc.headers["Location"], status_code=exc.status_code)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# ==============
# Pydantic モデル
# ==============

class ScreeningRequest(BaseModel):
    """スクリーニングリクエストモデル"""
    region: str = "japan"
    strategy: str = "value"
    theme: Optional[str] = None
    sector: Optional[str] = None
    with_pullback: bool = False
    min_market_cap: Optional[float] = None
    max_pe: Optional[float] = None
    max_pb: Optional[float] = None
    min_dividend_yield: Optional[float] = None
    top: int = 20


class StockReportRequest(BaseModel):
    """個別銘柄レポートリクエストモデル"""
    ticker: str


class PortfolioAction(BaseModel):
    """ポートフォリオアクションモデル"""
    action: str
    ticker: Optional[str] = None
    shares: Optional[int] = None
    price: Optional[float] = None
    currency: str = "JPY"


class WatchlistAction(BaseModel):
    """ウォッチリストアクションモデル"""
    action: str
    list_name: Optional[str] = None
    tickers: Optional[List[str]] = None


# ==============
# ユーティリティ関数
# ==============

def run_screening(region: str, strategy: str, **kwargs) -> Dict[str, Any]:
    """株式スクリーニングを実行"""
    from src.data.yahoo_client.screen import screen_stocks
    from src.core.screening.query_builder import build_query, load_preset
    
    # top パラメータを処理
    top = kwargs.pop('top', 20)
    
    # 戦略から条件を読み込み
    criteria = load_preset(strategy)
    
    # クエリ構築
    query = build_query(
        criteria=criteria,
        region=region,
        sector=kwargs.get('sector'),
        theme=kwargs.get('theme'),
    )
    
    # スクリーニング実行
    results_raw = screen_stocks(query, size=min(top, 250))
    
    # 結果の正規化
    results = []
    for quote in results_raw[:top]:
        symbol = quote.get('symbol', quote.get('ticker', 'N/A'))
        results.append({
            'ticker': symbol,
            'name': quote.get('shortName', quote.get('longName', 'N/A')),
            'price': quote.get('regularMarketPrice', quote.get('price', 0)),
            'pe_ratio': quote.get('trailingPE', quote.get('peRatio')),
            'pb_ratio': quote.get('priceToBook', quote.get('pbRatio')),
            'dividend_yield': quote.get('dividendYield', 0),
            'roe': quote.get('returnOnEquity', 0),
        })

    # サマリー計算
    summary = {
        "total": len(results),
        "avg_pe": None,
        "avg_pb": None,
        "avg_dividend_yield": None
    }

    pe_values = [r.get("pe_ratio") for r in results if r.get("pe_ratio") and isinstance(r.get("pe_ratio"), (int, float))]
    pb_values = [r.get("pb_ratio") for r in results if r.get("pb_ratio") and isinstance(r.get("pb_ratio"), (int, float))]
    dy_values = [r.get("dividend_yield") for r in results if r.get("dividend_yield") and isinstance(r.get("dividend_yield"), (int, float))]

    if pe_values:
        summary["avg_pe"] = sum(pe_values) / len(pe_values)
    if pb_values:
        summary["avg_pb"] = sum(pb_values) / len(pb_values)
    if dy_values:
        summary["avg_dividend_yield"] = sum(dy_values) / len(dy_values)

    return {
        "success": True,
        "results": results,
        "metadata": {},
        "summary": summary
    }


def _normalize_ticker(ticker: str) -> str:
    """ティッカーシンボルを正規化する。

    純粋な数字のみ（例: 9008）→ 日本株として .T を付与（9008.T）
    """
    ticker = ticker.strip().upper()
    if ticker.isdigit():
        ticker = ticker + ".T"
    return ticker


def generate_stock_report(ticker: str) -> Dict[str, Any]:
    """個別銘柄レポートを生成"""
    import yfinance as yf

    ticker = _normalize_ticker(ticker)

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # データが実質的に空の場合（存在しないティッカー）
        if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None and info.get("shortName") is None:
            return {
                "success": False,
                "error": f"銘柄 '{ticker}' のデータが見つかりません。ティッカーシンボルを確認してください。"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"銘柄データの取得に失敗しました：{str(e)}"
        }

    def _to_ratio(value):
        """yfinance が % 形式（>1）で返す場合に比率形式へ変換（例: 3.35 → 0.0335）。"""
        if value is not None and value > 1:
            return value / 100
        return value

    # バリュエーションデータ（配当利回りは比率形式に正規化）
    valuation = {
        "pe_ratio": info.get("trailingPE"),
        "pb_ratio": info.get("priceToBook"),
        "dividend_yield": _to_ratio(info.get("dividendYield")),
        "roe": info.get("returnOnEquity"),
        "earnings_growth": info.get("earningsGrowth"),
        "buyback_yield": None,
    }

    # 割安度判定（簡易版）
    score = 50
    if valuation["pe_ratio"] and valuation["pe_ratio"] < 15:
        score += 20
    if valuation["pb_ratio"] and valuation["pb_ratio"] < 1:
        score += 15
    if valuation["dividend_yield"] and valuation["dividend_yield"] > 0.03:  # 3% 超
        score += 15
    if valuation["roe"] and valuation["roe"] > 0.15:  # ROE 15% 超
        score += 10

    score = min(100, max(0, score))

    if score >= 80:
        label = "非常に割安"
    elif score >= 60:
        label = "やや割安"
    elif score >= 40:
        label = "標準"
    elif score >= 20:
        label = "やや割高"
    else:
        label = "非常に割高"

    health = {"score": score, "label": label}

    # 推定利回り・自社株買い利回り（yahoo_client.get_stock_detail + estimate_stock_return）
    forecast = {"base": None, "optimistic": None, "pessimistic": None}
    try:
        from src.data import yahoo_client as _yc
        stock_detail = _yc.get_stock_detail(ticker)

        # Fallback: get_stock_detail が失敗またはprice_historyなしの場合、
        # 既に取得済みの stock Ticker から直接price_historyを補完する
        if not stock_detail or not stock_detail.get("price_history"):
            try:
                hist = stock.history(period="2y")
                if hist is not None and not hist.empty and "Close" in hist.columns:
                    price_history = [float(v) for v in hist["Close"].tolist()]
                    if stock_detail is None:
                        stock_detail = {}
                    stock_detail.setdefault("price_history", price_history)
                    stock_detail.setdefault(
                        "price",
                        info.get("currentPrice") or info.get("regularMarketPrice")
                    )
                    stock_detail.setdefault(
                        "dividend_yield",
                        _to_ratio(info.get("dividendYield"))
                    )
            except Exception:
                pass

        if stock_detail:
            est = estimate_stock_return(ticker, stock_detail)
            forecast = {
                "base": est.get("base"),
                "optimistic": est.get("optimistic"),
                "pessimistic": est.get("pessimistic"),
            }
            # 推定利回りを % 表示に変換（例: 0.05 → 5.0）
            for key in ("base", "optimistic", "pessimistic"):
                if forecast[key] is not None:
                    forecast[key] = round(forecast[key] * 100, 1)
            buyback = est.get("buyback_yield")
            if buyback is not None:
                valuation["buyback_yield"] = round(buyback * 100, 2)
    except Exception:
        pass

    # バリュートラップ判定（簡易版）
    value_trap = {"is_trap": False, "reason": ""}

    return {
        "success": True,
        "ticker": ticker,
        "name": info.get("shortName", info.get("longName", "")),
        "sector": info.get("sector", ""),
        "industry": info.get("industry", ""),
        "valuation": valuation,
        "health": health,
        "forecast": forecast,
        "value_trap": value_trap,
        "current_price": info.get("currentPrice", info.get("regularMarketPrice"))
    }


# ==============
# 認証ルート
# ==============

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    """ログインページ"""
    if get_current_user(request):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": next,
        "error": None
    })


@app.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/")
):
    """ログイン処理"""
    if username == AUTH_USERNAME and verify_password(password, AUTH_PASSWORD_HASH):
        redirect_url = next if next.startswith("/") else "/"
        response = RedirectResponse(url=redirect_url, status_code=302)
        set_session_cookie(response, username)
        return response
    return templates.TemplateResponse("login.html", {
        "request": request,
        "next": next,
        "error": "ユーザー名またはパスワードが違います"
    })


@app.get("/logout")
async def logout():
    """ログアウト処理"""
    response = RedirectResponse(url="/login", status_code=302)
    clear_session_cookie(response)
    return response


# ==============
# ページルート
# ==============

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, user: str = Depends(require_auth)):
    """ダッシュボードページ"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "Stock Skills WebUI",
        "current_user": user
    })


@app.get("/screening", response_class=HTMLResponse)
async def screening_page(
    request: Request,
    region: Optional[str] = Query(None),
    strategy: Optional[str] = Query(None),
    theme: Optional[str] = Query(None),
    user: str = Depends(require_auth)
):
    """スクリーニングページ"""
    return templates.TemplateResponse("screening.html", {
        "request": request,
        "title": "株式スクリーニング",
        "default_region": region,
        "default_strategy": strategy,
        "default_theme": theme,
        "current_user": user
    })


@app.get("/report", response_class=HTMLResponse)
async def report_page(request: Request, ticker: Optional[str] = Query(None), user: str = Depends(require_auth)):
    """個別銘柄レポートページ"""
    return templates.TemplateResponse("report.html", {
        "request": request,
        "title": "個別銘柄レポート",
        "default_ticker": ticker,
        "current_user": user
    })


@app.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page(request: Request, user: str = Depends(require_auth)):
    """ポートフォリオ管理ページ"""
    return templates.TemplateResponse("portfolio.html", {
        "request": request,
        "title": "ポートフォリオ管理",
        "current_user": user
    })


@app.get("/watchlist", response_class=HTMLResponse)
async def watchlist_page(request: Request, user: str = Depends(require_auth)):
    """ウォッチリストページ"""
    return templates.TemplateResponse("watchlist.html", {
        "request": request,
        "title": "ウォッチリスト",
        "current_user": user
    })


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request, user: str = Depends(require_auth)):
    """API 設定ページ"""
    config = load_env()
    cfg_status = get_config_status()
    return templates.TemplateResponse("config.html", {
        "request": request,
        "title": "API 設定",
        "config": config,
        "status": cfg_status,
        "current_user": user
    })


# ==============
# API エンドポイント
# ==============

@app.post("/api/screening")
async def api_screening(req: ScreeningRequest):
    """株式スクリーニング API"""
    try:
        kwargs = {
            "top": req.top
        }
        if req.theme:
            kwargs["theme"] = req.theme
        if req.sector:
            kwargs["sector"] = req.sector
        if req.with_pullback:
            kwargs["with_pullback"] = True
        if req.min_market_cap:
            kwargs["min_market_cap"] = req.min_market_cap
        if req.max_pe:
            kwargs["max_pe"] = req.max_pe
        if req.max_pb:
            kwargs["max_pb"] = req.max_pb
        if req.min_dividend_yield:
            kwargs["min_dividend_yield"] = req.min_dividend_yield

        result = await asyncio.to_thread(
            run_screening, req.region, req.strategy, **kwargs
        )
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/report")
async def api_report(req: StockReportRequest):
    """個別銘柄レポート API"""
    try:
        result = await asyncio.to_thread(generate_stock_report, req.ticker)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/portfolio")
async def api_portfolio(action: PortfolioAction):
    """ポートフォリオ操作 API"""
    try:
        if action.action == "snapshot":
            result = get_snapshot()
        elif action.action == "buy":
            if not action.ticker or not action.shares or not action.price:
                raise ValueError("ticker, shares, and price are required")
            add_position(action.ticker, action.shares, action.price, action.currency)
            result = {"message": f"Added {action.shares} shares of {action.ticker}"}
        elif action.action == "sell":
            if not action.ticker or not action.shares:
                raise ValueError("ticker and shares are required")
            sell_position(action.ticker, action.shares, action.price if action.price else 0)
            result = {"message": f"Sold {action.shares} shares of {action.ticker}"}
        elif action.action == "analyze":
            result = analyze_concentration()
        elif action.action == "health":
            result = portfolio_health_check()
        elif action.action == "forecast":
            result = {"message": "推定利回り機能は開発中です"}
        else:
            raise ValueError(f"Unknown action: {action.action}")

        return JSONResponse(content={"success": True, "result": result})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/watchlist")
async def api_watchlist(action: WatchlistAction):
    """ウォッチリスト操作 API"""
    try:
        if action.action == "list":
            watchlists = load_watchlist()
            return JSONResponse(content={"success": True, "watchlists": watchlists})
        elif action.action == "add":
            if not action.list_name:
                raise ValueError("list_name is required")
            watchlists = load_watchlist()
            if action.list_name not in watchlists:
                watchlists[action.list_name] = []
            if action.tickers:
                watchlists[action.list_name].extend(action.tickers)
                watchlists[action.list_name] = list(set(watchlists[action.list_name]))
            save_watchlist(watchlists)
            return JSONResponse(content={"success": True, "watchlists": watchlists})
        elif action.action == "show":
            if not action.list_name:
                raise ValueError("list_name is required")
            watchlists = load_watchlist()
            tickers = watchlists.get(action.list_name, [])
            return JSONResponse(content={"success": True, "tickers": tickers})
        elif action.action == "remove":
            if not action.list_name or not action.tickers:
                raise ValueError("list_name and tickers are required")
            watchlists = load_watchlist()
            if action.list_name in watchlists:
                watchlists[action.list_name] = [
                    t for t in watchlists[action.list_name] if t not in action.tickers
                ]
            save_watchlist(watchlists)
            return JSONResponse(content={"success": True, "watchlists": watchlists})
        elif action.action == "delete_list":
            if not action.list_name:
                raise ValueError("list_name is required")
            watchlists = load_watchlist()
            if action.list_name in watchlists:
                del watchlists[action.list_name]
            save_watchlist(watchlists)
            return JSONResponse(content={"success": True, "watchlists": watchlists})
        else:
            raise ValueError(f"Unknown action: {action.action}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============
# HTMX パーシャル
# ==============

@app.post("/partials/screening-results")
async def partial_screening_results(
    request: Request,
    region: str = Form("japan"),
    strategy: str = Form("value"),
    theme: Optional[str] = Form(None),
    sector: Optional[str] = Form(None),
    with_pullback: bool = Form(False),
    min_market_cap: Optional[float] = Form(None),
    max_pe: Optional[float] = Form(None),
    max_pb: Optional[float] = Form(None),
    min_dividend_yield: Optional[float] = Form(None),
    top: int = Form(20)
):
    """スクリーニング結果の HTMX パーシャル"""
    try:
        kwargs = {
            "top": top
        }
        if theme:
            kwargs["theme"] = theme
        if sector:
            kwargs["sector"] = sector
        if with_pullback:
            kwargs["with_pullback"] = True
        if min_market_cap:
            kwargs["min_market_cap"] = min_market_cap
        if max_pe:
            kwargs["max_pe"] = max_pe
        if max_pb:
            kwargs["max_pb"] = max_pb
        if min_dividend_yield:
            kwargs["min_dividend_yield"] = min_dividend_yield

        result = await asyncio.to_thread(run_screening, region, strategy, **kwargs)

        return templates.TemplateResponse("partials/screening_results.html", {
            "request": request,
            "results": result["results"],
            "summary": result["summary"]
        })
    except Exception as e:
        return templates.TemplateResponse("partials/error.html", {
            "request": request,
            "error": str(e)
        })


@app.post("/partials/stock-report")
async def partial_stock_report(request: Request, ticker: str = Form(...)):
    """銘柄レポートの HTMX パーシャル"""
    try:
        result = await asyncio.to_thread(generate_stock_report, ticker)

        return templates.TemplateResponse("partials/stock_report.html", {
            "request": request,
            "report": result
        })
    except Exception as e:
        return templates.TemplateResponse("partials/error.html", {
            "request": request,
            "error": str(e)
        })


# ==============
# 設定 API
# ==============

@app.post("/api/config")
async def api_save_config(request: Request):
    """設定を保存"""
    try:
        data = await request.json()
        
        # 有効な設定項目のみをフィルタリング
        valid_config = {
            k: v for k, v in data.items() 
            if k in CONFIG_FIELDS and v
        }
        
        if save_env(valid_config):
            return JSONResponse(content={"success": True})
        else:
            raise HTTPException(status_code=500, detail="設定の保存に失敗しました")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/test")
async def api_test_connections():
    """接続テストを実行"""
    try:
        import asyncio
        
        results = {}
        
        # Yahoo Finance (常に利用可能)
        results['yahoo'] = {"ok": True, "message": "利用可能"}
        
        # Neo4j テスト
        try:
            env_vars = load_env()
            if env_vars.get('NEO4J_URI'):
                # Neo4j 接続テスト
                from src.data.graph_store._common import _get_driver, _check_connection
                driver = _get_driver()
                if driver:
                    ok = _check_connection()
                    results['neo4j'] = {
                        "ok": ok,
                        "message": "接続成功" if ok else "接続失敗"
                    }
                else:
                    results['neo4j'] = {"ok": False, "message": "ドライバー初期化失敗"}
            else:
                results['neo4j'] = {"ok": False, "message": "未設定"}
        except Exception as e:
            results['neo4j'] = {"ok": False, "message": f"エラー：{str(e)}"}
        
        # Grok API テスト
        try:
            env_vars = load_env()
            if env_vars.get('XAI_API_KEY'):
                # TODO: Grok API 接続テスト
                results['grok'] = {"ok": True, "message": "設定済み"}
            else:
                results['grok'] = {"ok": False, "message": "未設定"}
        except Exception as e:
            results['grok'] = {"ok": False, "message": f"エラー：{str(e)}"}
        
        # TEI テスト
        try:
            env_vars = load_env()
            if env_vars.get('TEI_URL'):
                import requests
                resp = requests.get(f"{env_vars['TEI_URL']}/health", timeout=3)
                results['tei'] = {
                    "ok": resp.status_code == 200,
                    "message": "接続成功" if resp.status_code == 200 else "接続失敗"
                }
            else:
                results['tei'] = {"ok": False, "message": "未設定"}
        except Exception as e:
            results['tei'] = {"ok": False, "message": f"エラー：{str(e)}"}
        
        return JSONResponse(content={
            "success": True,
            "results": results
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
