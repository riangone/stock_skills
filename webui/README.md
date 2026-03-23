# Stock Skills WebUI

価値股スクリーニングシステムの Web インターフェース。

## 技術スタック

- **バックエンド**: FastAPI
- **フロントエンド**: HTMX + DaisyUI (Tailwind CSS)
- **テンプレート**: Jinja2
- **データベース**: SQLite (ポートフォリオ・ウォッチリスト管理)

## クイックスタート

### 1. 依存関係のインストール

```bash
# 仮想環境の有効化
source venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt
```

### 2. WebUI サーバーの起動

```bash
# 通常モード
python scripts/run_webui.py

# 開発モード (自動リロード)
python scripts/run_webui.py --reload

# ポート変更
python scripts/run_webui.py --port 8080
```

### 3. ブラウザでアクセス

```
http://localhost:8000
```

## 機能

### 🔍 株式スクリーニング

- **15 の戦略**: バリュー・高配当・成長・モメンタムなど
- **60+ 地域**: 日本・米国・ASEAN・欧州・新興国
- **テーマ指定**: AI・EV・半導体など
- **詳細条件**: PER/PBR/配当利回り/時価総額
- **URL パラメータ**: `?region=japan&strategy=value` で条件を指定可能
- **結果ソート**: 各カラムで昇順/降順ソート
- **CSV エクスポート**: 結果を CSV ファイルで出力
- **ウォッチリスト追加**: 結果をワンクリックでウォッチリストに追加

### 📊 個別銘柄レポート

- **バリュエーション**: PER, PBR, ROE, 配当利回り，利益成長率
- **割安度判定**: 0-100 スコアで視覚的に表示
- **株主還元**: 配当 + 自社株買いの総還元率
- **推定利回り**: 楽観・ベース・悲観シナリオ
- **バリュートラップ**: 割安の罠を検出
- **URL パラメータ**: `?ticker=7203.T` で自動分析

### 💼 ポートフォリオ管理

- **損益表示**: 現在の保有銘柄と損益をリアルタイム表示
- **売買記録**: 買い/売り注文の記録
- **集中度分析**: HHI によるリスク測定
- **ヘルスチェック**: ポートフォリオの健全性診断
- **タブナビゲーション**: 損益・売買・分析・ヘルスチェックをタブで切り替え

### ⭐ ウォッチリスト

- **リスト管理**: 複数リストの作成・削除
- **銘柄追加**: ティッカーの一括追加（カンマ区切り）
- **銘柄削除**: 個別・一括削除
- **分析連携**: ウォッチリストから直接分析ページへ
- **データベース保存**: SQLite で永続化

## API エンドポイント

### スクリーニング

```bash
POST /api/screening
Content-Type: application/json

{
  "region": "japan",
  "strategy": "value",
  "theme": "ai",
  "max_pe": 15,
  "min_dividend_yield": 3,
  "top": 20
}
```

### 個別銘柄レポート

```bash
POST /api/report
Content-Type: application/json

{
  "ticker": "7203.T"
}
```

### ポートフォリオ

```bash
POST /api/portfolio
Content-Type: application/json

{
  "action": "snapshot"
}
```

アクション一覧:
- `snapshot`: ポートフォリオ状況取得
- `buy`: 買い注文
- `sell`: 売り注文
- `analyze`: 集中度分析
- `health`: ヘルスチェック

### ウォッチリスト

```bash
POST /api/watchlist
Content-Type: application/json

{
  "action": "add",
  "list_name": "注目銘柄",
  "tickers": ["7203.T", "AAPL"]
}
```

アクション一覧:
- `list`: 全リスト取得
- `add`: リストに銘柄追加
- `show`: リストの銘柄取得
- `remove`: リストから銘柄削除
- `delete_list`: リスト削除

## HTMX パーシャル

### スクリーニング結果

```bash
POST /partials/screening-results
Content-Type: application/x-www-form-urlencoded

region=japan&strategy=value&max_pe=15
```

### 銘柄レポート

```bash
POST /partials/stock-report
Content-Type: application/x-www-form-urlencoded

ticker=7203.T
```

## 開発

### ディレクトリ構造

```
webui/
├── app.py                 # FastAPI アプリケーション
├── database.py            # SQLite データベースモジュール
├── templates/
│   ├── base.html         # ベースレイアウト
│   ├── index.html        # ダッシュボード
│   ├── screening.html    # スクリーニングページ
│   ├── report.html       # 銘柄レポートページ
│   ├── portfolio.html    # ポートフォリオページ
│   ├── watchlist.html    # ウォッチリストページ
│   └── partials/
│       ├── screening_results.html  # スクリーニング結果 (HTMX)
│       ├── stock_report.html       # 銘柄レポート (HTMX)
│       └── error.html              # エラー表示 (HTMX)
└── static/
    ├── styles.css        # カスタムスタイル
    └── utils.js          # 共通ユーティリティ関数
```

### データベーススキーマ

```sql
-- ポートフォリオ
CREATE TABLE portfolio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL UNIQUE,
    shares INTEGER NOT NULL,
    cost_price REAL NOT NULL,
    currency TEXT DEFAULT 'JPY',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 取引履歴
CREATE TABLE trade_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT NOT NULL,
    action TEXT NOT NULL,
    shares INTEGER NOT NULL,
    price REAL NOT NULL,
    currency TEXT DEFAULT 'JPY',
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ウォッチリスト
CREATE TABLE watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ウォッチリスト銘柄
CREATE TABLE watchlist_tickers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watchlist_id INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watchlist_id) REFERENCES watchlist(id),
    UNIQUE(watchlist_id, ticker)
);
```

### HTMX 使用例

```html
<!-- フォーム送信で結果を更新 -->
<form
    hx-post="/partials/screening-results"
    hx-target="#results"
    hx-indicator="#loading"
>
    <select name="region">
        <option value="japan">日本</option>
    </select>
    <button type="submit">実行</button>
</form>

<div id="results">
    <!-- ここに結果がロードされる -->
</div>

<!-- ローディング表示 -->
<div id="loading" class="htmx-indicator">
    読み込み中...
</div>
```

### DaisyUI コンポーネント

```html
<!-- ボタン -->
<button class="btn btn-primary">Primary</button>

<!-- カード -->
<div class="card bg-base-100 shadow-xl">
  <div class="card-body">...</div>
</div>

<!-- テーブル -->
<table class="table table-zebra">...</table>

<!-- アラート -->
<div class="alert alert-info">...</div>

<!-- 統計 -->
<div class="stats">
  <div class="stat">
    <div class="stat-title">タイトル</div>
    <div class="stat-value">値</div>
  </div>
</div>
```

### 共通ユーティリティ (utils.js)

```javascript
// 数値フォーマット
formatNumber(12345.67, 2)  // "12,345.67"

// 通貨フォーマット
formatCurrency(10000, 'JPY')  // "¥10,000"

// パーセントフォーマット
formatPercent(0.15, 2)  // "15.00%"

// API リクエスト
await apiRequest('/api/screening', 'POST', { region: 'japan' })

// トースト通知
showToast('完了しました', 'success')

// CSV エクスポート
exportToCSV(data, 'export.csv')
```

## 環境変数

任意の設定（`.env` または環境変数）:

```bash
# WebUI サーバー設定
WEBUI_HOST=0.0.0.0
WEBUI_PORT=8000

# Grok API (X センチメント分析)
XAI_API_KEY=xai-xxxxxxxxxxxxx

# Neo4j 設定
NEO4J_MODE=full
```

## 制限事項

- ポートフォリオ機能は SQLite データベースを使用
- リアルタイム株価更新には対応していません（ページリロードで更新）
- 一部の高度な分析機能はバックエンドの実装に依存

## トラブルシューティング

### サーバーが起動しない

```bash
# ポートの確認
lsof -i :8000

# 依存関係の再インストール
pip install -r requirements.txt --upgrade

# データベースの再初期化
rm data/webui.db
python scripts/run_webui.py
```

### スクリーニング結果が表示されない

- Yahoo Finance API のレート制限を確認
- ネットワーク接続を確認
- ログ出力を確認（`--reload` で詳細ログ）

### データベースエラー

```bash
# データベースファイルの削除（データは消去されます）
rm data/webui.db

# 再起動で再作成されます
python scripts/run_webui.py
```

## ライセンス

本プロジェクトは stock_skills と同じライセンス（フリー）に従います。

## 貢献

Issue または Pull Request をお送りください。

---

**Stock Skills WebUI** - 価値股投資を、もっとスマートに。
