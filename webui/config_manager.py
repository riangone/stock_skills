"""WebUI 設定管理モジュール"""

import os
from pathlib import Path
from typing import Dict, Optional
import yaml

# 設定ファイルパス
ENV_EXAMPLE_PATH = Path(__file__).parent.parent / ".env.example"
ENV_PATH = Path(__file__).parent.parent / ".env"

# 設定項目定義
CONFIG_FIELDS = {
    # Neo4j
    "NEO4J_URI": {
        "label": "Neo4j URI",
        "type": "text",
        "default": "bolt://localhost:7688",
        "required": False,
        "category": "neo4j"
    },
    "NEO4J_USER": {
        "label": "Neo4j ユーザー",
        "type": "text",
        "default": "neo4j",
        "required": False,
        "category": "neo4j"
    },
    "NEO4J_PASSWORD": {
        "label": "Neo4j パスワード",
        "type": "password",
        "default": "",
        "required": False,
        "category": "neo4j"
    },
    "NEO4J_MODE": {
        "label": "Neo4j モード",
        "type": "select",
        "options": ["off", "summary", "full"],
        "default": "full",
        "required": False,
        "category": "neo4j"
    },
    
    # TEI
    "TEI_URL": {
        "label": "TEI URL",
        "type": "text",
        "default": "http://localhost:8081",
        "required": False,
        "category": "tei"
    },
    
    # Grok API
    "XAI_API_KEY": {
        "label": "Grok API キー (xAI)",
        "type": "password",
        "default": "",
        "required": False,
        "category": "grok",
        "help": "https://console.x.ai/ から取得"
    },
    
    # Perplexity API
    "PERPLEXITY_API_KEY": {
        "label": "Perplexity API キー",
        "type": "password",
        "default": "",
        "required": False,
        "category": "perplexity",
        "help": "https://www.perplexity.ai/ から取得"
    },
    
    # Anthropic API
    "ANTHROPIC_API_KEY": {
        "label": "Anthropic API キー",
        "type": "password",
        "default": "",
        "required": False,
        "category": "anthropic",
        "help": "https://www.anthropic.com/ から取得"
    },
    
    # Linear
    "LINEAR_ENABLED": {
        "label": "Linear 統合",
        "type": "select",
        "options": ["on", "off"],
        "default": "off",
        "required": False,
        "category": "linear"
    },
    "LINEAR_API_KEY": {
        "label": "Linear API キー",
        "type": "password",
        "default": "",
        "required": False,
        "category": "linear"
    },
    "LINEAR_TEAM_ID": {
        "label": "Linear Team ID",
        "type": "text",
        "default": "",
        "required": False,
        "category": "linear"
    },
    "LINEAR_PROJECT_ID": {
        "label": "Linear Project ID",
        "type": "text",
        "default": "",
        "required": False,
        "category": "linear"
    },
    
    # Context
    "CONTEXT_FRESH_HOURS": {
        "label": "コンテキスト新鮮度 (時間)",
        "type": "number",
        "default": "24",
        "required": False,
        "category": "context"
    },
    "CONTEXT_RECENT_HOURS": {
        "label": "コンテキスト期間 (時間)",
        "type": "number",
        "default": "168",
        "required": False,
        "category": "context"
    }
}


def load_env() -> Dict[str, str]:
    """環境変数ファイルから設定を読み込み"""
    env_vars = {}
    
    if ENV_PATH.exists():
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    return env_vars


def save_env(env_vars: Dict[str, str]) -> bool:
    """環境変数ファイルに設定を保存"""
    try:
        # 既存の .env.example を読み込んでテンプレートとして使用
        template = {}
        if ENV_EXAMPLE_PATH.exists():
            with open(ENV_EXAMPLE_PATH) as f:
                current_section = None
                for line in f:
                    line_stripped = line.strip()
                    if line_stripped.startswith('# ---'):
                        current_section = line_stripped
                    elif line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
                        key = line_stripped.split('=', 1)[0].strip()
                        template[key] = line
        
        # .env ファイルを生成
        with open(ENV_PATH, 'w') as f:
            f.write("# Stock Skills Environment Variables\n")
            f.write("# WebUI から自動生成\n\n")
            
            # カテゴリごとに整理
            categories = {}
            for key, value in env_vars.items():
                if key in CONFIG_FIELDS:
                    cat = CONFIG_FIELDS[key].get('category', 'other')
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append((key, value))
            
            # 各カテゴリを書き込み
            category_headers = {
                'neo4j': 'Neo4j',
                'tei': 'TEI (Text Embeddings Inference)',
                'grok': 'Grok API (xAI)',
                'perplexity': 'Perplexity API',
                'anthropic': 'Anthropic API',
                'linear': 'Linear Integration',
                'context': 'Context Settings'
            }
            
            for cat, items in categories.items():
                header = category_headers.get(cat, cat.upper())
                f.write(f"# --- {header} ---\n")
                for key, value in items:
                    if value:  # 値がある場合のみ
                        f.write(f"{key}={value}\n")
                f.write("\n")
        
        # 環境変数を更新
        for key, value in env_vars.items():
            if value:
                os.environ[key] = value
        
        return True
    except Exception as e:
        print(f"Error saving .env: {e}")
        return False


def get_config_status() -> Dict[str, Dict]:
    """各 API の設定状態を取得"""
    env_vars = load_env()
    status = {}
    
    # カテゴリごとに状態をチェック
    status['neo4j'] = {
        'configured': all(env_vars.get(k) for k in ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD']),
        'items': {k: bool(env_vars.get(k)) for k in ['NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD', 'NEO4J_MODE']}
    }
    
    status['grok'] = {
        'configured': bool(env_vars.get('XAI_API_KEY')),
        'items': {'XAI_API_KEY': bool(env_vars.get('XAI_API_KEY'))}
    }
    
    status['tei'] = {
        'configured': bool(env_vars.get('TEI_URL')),
        'items': {'TEI_URL': bool(env_vars.get('TEI_URL'))}
    }
    
    status['perplexity'] = {
        'configured': bool(env_vars.get('PERPLEXITY_API_KEY')),
        'items': {'PERPLEXITY_API_KEY': bool(env_vars.get('PERPLEXITY_API_KEY'))}
    }
    
    status['anthropic'] = {
        'configured': bool(env_vars.get('ANTHROPIC_API_KEY')),
        'items': {'ANTHROPIC_API_KEY': bool(env_vars.get('ANTHROPIC_API_KEY'))}
    }
    
    status['linear'] = {
        'configured': env_vars.get('LINEAR_ENABLED') == 'on' and bool(env_vars.get('LINEAR_API_KEY')),
        'items': {
            'LINEAR_ENABLED': env_vars.get('LINEAR_ENABLED', 'off'),
            'LINEAR_API_KEY': bool(env_vars.get('LINEAR_API_KEY')),
            'LINEAR_TEAM_ID': bool(env_vars.get('LINEAR_TEAM_ID')),
            'LINEAR_PROJECT_ID': bool(env_vars.get('LINEAR_PROJECT_ID'))
        }
    }
    
    return status
