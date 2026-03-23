#!/usr/bin/env python3
"""Stock Skills WebUI 起動スクリプト.

使用方法:
    python scripts/run_webui.py [--host HOST] [--port PORT] [--reload]

例:
    python scripts/run_webui.py              # http://localhost:9000
    python scripts/run_webui.py --port 8080  # http://localhost:8080
    python scripts/run_webui.py --reload     # 開発モード (自動リロード)
"""

import argparse
import sys
import uvicorn
from pathlib import Path

# プロジェクトルートを Python パスに追加
BASE_DIR = Path(__file__).parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def main():
    parser = argparse.ArgumentParser(description='Stock Skills WebUI サーバー')
    parser.add_argument('--host', default='0.0.0.0', help='ホスト (デフォルト：0.0.0.0)')
    parser.add_argument('--port', type=int, default=9000, help='ポート (デフォルト：9000)')
    parser.add_argument('--reload', action='store_true', help='開発モード (自動リロード)')

    args = parser.parse_args()

    print(f"""
╔═══════════════════════════════════════════════════════════╗
║           Stock Skills WebUI を起動します                  ║
╠═══════════════════════════════════════════════════════════╣
║  ホスト：{args.host:<45} ║
║  ポート：{args.port:<44} ║
║  開発モード：{'はい' if args.reload else 'いいえ':<42} ║
╠═══════════════════════════════════════════════════════════╣
║  アクセス：http://{args.host.replace('0.0.0.0', 'localhost')}:{args.port}/                        ║
╚═══════════════════════════════════════════════════════════╝
    """)

    # アプリケーションを直接インポート
    from webui.app import app

    uvicorn.run(
        'webui.app:app',
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_includes=['*.py', '*.html', '*.css', '*.js'],
        reload_dirs=[str(BASE_DIR / 'webui')]
    )


if __name__ == '__main__':
    main()
