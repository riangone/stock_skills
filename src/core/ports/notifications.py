"""Notification port for external alerts (KIK-582).

Supports Discord and Telegram webhooks for proactive monitoring.
"""

import os
import requests
from typing import Optional


def send_notification(message: str, provider: str = "discord") -> bool:
    """Send a notification to an external service.

    Parameters
    ----------
    message : str
        The message content.
    provider : str
        Service provider ("discord" or "telegram").

    Returns
    -------
    bool
        True if successful.
    """
    if provider == "discord":
        webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
        if not webhook_url:
            return False
        try:
            resp = requests.post(webhook_url, json={"content": message}, timeout=5)
            return resp.status_code < 400
        except Exception:
            return False
            
    elif provider == "telegram":
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        if not token or not chat_id:
            return False
        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=5)
            return resp.status_code < 400
        except Exception:
            return False
            
    return False


def alert_critical_health(symbol: str, alert_level: str, reason: str):
    """Specific alert for critical stock health (EXIT/CAUTION)."""
    emoji = "🚨" if alert_level == "exit" else "⚠️"
    msg = f"{emoji} **[{alert_level.upper()}] {symbol}**\n原因: {reason}\nすぐに対応を検討してください。"
    send_notification(msg)
