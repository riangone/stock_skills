"""Dividend management and advisory engine (KIK-580).

Provides dividend forecasting, ex-dividend alerts, and DRIP effect analysis.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


def generate_dividend_calendar(
    positions: List[dict],
    client
) -> List[dict]:
    """Generate a chronological dividend calendar for the portfolio.

    Parameters
    ----------
    positions : list[dict]
        Portfolio positions with symbols and shares.
    client
        yahoo_client module.

    Returns
    -------
    list[dict]
        List of dividend events sorted by ex-dividend date.
    """
    events = []
    for pos in positions:
        symbol = pos["symbol"]
        shares = pos["shares"]
        info = client.get_stock_info(symbol)
        
        if not info:
            continue
            
        ex_date_raw = info.get("ex_dividend_date")
        div_rate = info.get("dividend_rate")
        
        if ex_date_raw and div_rate:
            try:
                # Yahoo often returns timestamp or ISO string
                if isinstance(ex_date_raw, (int, float)):
                    ex_date = datetime.fromtimestamp(ex_date_raw)
                else:
                    ex_date = datetime.fromisoformat(str(ex_date_raw))
                
                events.append({
                    "symbol": symbol,
                    "name": info.get("name", symbol),
                    "ex_dividend_date": ex_date.strftime("%Y-%m-%d"),
                    "dividend_per_share": div_rate,
                    "total_dividend": div_rate * shares,
                    "currency": info.get("currency", "USD"),
                    "days_to_ex": (ex_date - datetime.now()).days
                })
            except Exception:
                continue
                
    return sorted(events, key=lambda x: x["ex_dividend_date"])


def get_dividend_alerts(calendar: List[dict], days_threshold: int = 14) -> List[dict]:
    """Identify upcoming ex-dividend dates within the threshold."""
    return [e for e in calendar if 0 <= e["days_to_ex"] <= days_threshold]


def calculate_drip_impact(
    total_value: float,
    dividend_yield: float,
    years: int = 10,
    reinvest: bool = True
) -> Dict[str, float]:
    """Calculate the projected impact of Dividend Reinvestment Plan (DRIP)."""
    if not reinvest:
        return {"total_dividends": total_value * dividend_yield * years, "drip_bonus": 0.0}
        
    # Simplified DRIP calculation (annual compounding)
    val_with = total_value * ((1 + dividend_yield) ** years)
    val_without = total_value + (total_value * dividend_yield * years)
    
    return {
        "final_value_with_drip": val_with,
        "final_value_cash_div": val_without,
        "drip_bonus": val_with - val_without,
        "drip_bonus_pct": (val_with / val_without - 1) * 100 if val_without > 0 else 0
    }
