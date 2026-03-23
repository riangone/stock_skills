# Stock Skills API 設定ガイド

## 必要な API 設定

このプロジェクトでは、以下の外部 API サービスをオプションで設定できます。**すべての API が必須ではなく、基本機能は API なしでも動作します。**

### 1. Yahoo Finance（必須・自動）

- **用途**: 株価データ、財務データ
- **設定**: 不要（yfinance ライブラリが自動で利用）
- **ステータス**: ✅ 常に利用可能

---

### 2. Grok API (xAI)（オプション）

- **用途**: 
  - X (Twitter) の感情分析
  - トレンド銘柄の検索
  - ニュース検索
- **設定方法**:
  1. https://console.x.ai/ でアカウント作成
  2. API キーを発行
  3. WebUI の設定ページまたは `.env` ファイルに設定
- **環境変数**: `XAI_API_KEY=xai-xxxxxxxxxxxxx`
- **料金**: 使用量ベース（要確認）

---

### 3. Neo4j（オプション）

- **用途**: 
  - 知識グラフの保存
  - 投資メモの管理
  - 関連性分析
- **設定方法**:
  1. Neo4j Desktop または Neo4j Aura をインストール
  2. データベースを作成
  3. 接続情報を設定
- **環境変数**:
  ```
  NEO4J_URI=bolt://localhost:7688
  NEO4J_USER=neo4j
  NEO4J_PASSWORD=password
  NEO4J_MODE=full  # off / summary / full
  ```
- **Docker で起動**:
  ```bash
  docker compose up -d
  ```

---

### 4. TEI (Text Embeddings Inference)（オプション）

- **用途**: 
  - ベクトル埋め込み生成
  - 類似銘柄検索
  - 知識グラフのベクトル検索
- **設定方法**:
  1. Hugging Face TEI を Docker で起動
  2. 接続 URL を設定
- **環境変数**: `TEI_URL=http://localhost:8081`
- **Docker で起動**:
  ```bash
  docker compose up -d
  ```

---

### 5. Perplexity API（オプション）

- **用途**: 
  - 高度な Web 検索
  - 業界リサーチ
  - 競合分析
- **設定方法**:
  1. https://www.perplexity.ai/ でアカウント作成
  2. API キーを発行
- **環境変数**: `PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxx`

---

### 6. Linear（オプション）

- **用途**: 
  - Issue トラッカー連携
  - アクションアイテムの自動作成
- **設定方法**:
  1. https://linear.app/ でアカウント作成
  2. Settings > API から API キーを発行
  3. Team ID と Project ID を取得
- **環境変数**:
  ```
  LINEAR_ENABLED=on
  LINEAR_API_KEY=lin_api_xxxxxxxxxxxxx
  LINEAR_TEAM_ID=team_xxxxx
  LINEAR_PROJECT_ID=proj_xxxxx
  ```

---

### 7. Anthropic API（オプション）

- **用途**: 
  - AI によるグラフ分析
  - 自然言語処理
- **設定方法**:
  1. https://www.anthropic.com/ でアカウント作成
  2. API キーを発行
- **環境変数**: `ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx`

---

## WebUI での設定方法

### 1. WebUI で設定（推奨）

1. WebUI にアクセス（http://localhost:9000）
2. 上部メニューの「⚙️ 設定」をクリック
3. 各 API の情報を入力
4. 「💾 設定を保存」をクリック
5. サーバーを再起動

### 2. 直接 `.env` ファイルを編集

```bash
# .env ファイルをコピー
cp .env.example .env

# エディタで編集
nano .env
# または
code .env
```

`.env` ファイルの例:

```env
# Neo4j
NEO4J_URI=bolt://localhost:7688
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
NEO4J_MODE=full

# Grok API
XAI_API_KEY=xai-xxxxxxxxxxxxx

# TEI
TEI_URL=http://localhost:8081

# Perplexity API
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxx

# Linear
LINEAR_ENABLED=off
LINEAR_API_KEY=

# Context
CONTEXT_FRESH_HOURS=24
CONTEXT_RECENT_HOURS=168
```

---

## 接続テスト

WebUI の設定ページで「🔌 接続テスト」ボタンをクリックすると、各 API の接続状態を確認できます。

またはコマンドラインで:

```bash
curl -X POST http://localhost:9000/api/config/test
```

---

## 推奨構成

### 最小構成（初心者向け）

- ✅ Yahoo Finance（自動）
- ❌ その他は未設定

**できること**:
- 株式スクリーニング
- 個別銘柄分析
- ポートフォリオ管理
- ウォッチリスト

---

### 標準構成（中級者向け）

- ✅ Yahoo Finance
- ✅ Grok API（X 分析）
- ✅ Neo4j（知識グラフ）

**追加できること**:
- X 感情分析
- トレンド銘柄検出
- 投資メモの蓄積
- 関連銘柄分析

---

### 完全構成（上級者向け）

- ✅ Yahoo Finance
- ✅ Grok API
- ✅ Neo4j
- ✅ TEI（ベクトル検索）
- ✅ Perplexity API
- ✅ Linear

**追加できること**:
- ベクトル類似検索
- 高度なリサーチ
- Issue 自動作成
- 完全な知識グラフ

---

## トラブルシューティング

### API キーが機能しない

1. キーのコピー＆ペーストを確認（余白がないか）
2. 有効期限を確認
3. 使用制限を確認

### Neo4j に接続できない

1. Neo4j が起動しているか確認:
   ```bash
   docker ps | grep neo4j
   ```
2. 接続情報を確認:
   ```bash
   docker logs neo4j
   ```
3. 認証情報を再設定

### 設定が反映されない

1. サーバーの再起動を確認
2. `.env` ファイルのパーミッションを確認
3. WebUI の設定ページから再保存

---

## セキュリティ注意事項

1. **API キーの管理**:
   - `.env` ファイルを Git にコミットしない
   - `.gitignore` に `.env` を追加
   - 共有しない

2. **アクセス制限**:
   - 本番環境では認証を有効化
   - HTTPS を使用
   - ファイアウォールでポートを制限

3. **使用量の監視**:
   - 各 API のダッシュボードで使用量を確認
   - 予算アラートを設定

---

## サポート

問題が発生した場合は:

1. ログを確認: `docker logs <container>`
2. ドキュメントを参照: `docs/` ディレクトリ
3. Issue を作成

---

**最終更新**: 2026-03-23
