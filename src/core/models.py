"""Core data models for portfolio management (KIK-365 Phase 2).

Pydantic models providing strict type validation and safety for domain objects.
External interfaces remain dict-based for backward compatibility;
these classes provide to_dict() and from_dict() for seamless integration.
"""

from typing import Optional, Union, Any, Dict, List
from pydantic import BaseModel, Field, ConfigDict


class Position(BaseModel):
    """A single portfolio position.

    Attributes
    ----------
    symbol : str
        Ticker symbol (e.g., "7203.T", "AAPL", "JPY.CASH").
    shares : int
        Number of shares held.
    cost_price : float
        Average acquisition price per share (in cost_currency).
    cost_currency : str
        Currency of the cost_price (e.g., "JPY", "USD").
    current_price : float
        Latest market price per share (in market_currency).
    value_jpy : float
        Current position value in JPY.
    sector : str
        GICS sector name (e.g., "Technology").
    country : str
        Country of domicile.
    market_currency : str
        Trading currency on the exchange.
    name : str
        Company/fund display name.
    purchase_date : str
        Date of last purchase (YYYY-MM-DD).
    memo : str
        Free-form note.
    """
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    shares: int
    cost_price: float
    cost_currency: str = "JPY"
    current_price: float = 0.0
    value_jpy: float = 0.0
    sector: str = ""
    country: str = ""
    market_currency: str = ""
    name: str = ""
    purchase_date: str = ""
    memo: str = ""

    @property
    def is_cash(self) -> bool:
        from src.core.common import is_cash
        return is_cash(self.symbol)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, d: dict) -> "Position":
        # Handle legacy field mappings
        data = d.copy()
        if "evaluation_jpy" in data and not data.get("value_jpy"):
            data["value_jpy"] = data.pop("evaluation_jpy")
        return cls(**data)


class ForecastResult(BaseModel):
    """Return estimate for a single stock."""
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    method: str
    base: Optional[float] = None
    optimistic: Optional[float] = None
    pessimistic: Optional[float] = None

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, d: dict) -> "ForecastResult":
        return cls(**d)


class HealthResult(BaseModel):
    """Health check result for a single holding."""
    model_config = ConfigDict(from_attributes=True)

    symbol: str
    trend: str = ""
    quality_label: str = ""
    alert_level: str = ""
    reasons: List[str] = Field(default_factory=list)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, d: dict) -> "HealthResult":
        # Handle complex nesting in legacy dictionary
        alert = d.get("alert", {})
        data = {
            "symbol": d.get("symbol", ""),
            "trend": d.get("trend_health", {}).get("trend", ""),
            "quality_label": d.get("change_quality", {}).get("quality_label", ""),
            "alert_level": alert.get("level", ""),
            "reasons": alert.get("reasons", []),
        }
        return cls(**data)


class RebalanceAction(BaseModel):
    """A single rebalancing action proposal."""
    model_config = ConfigDict(from_attributes=True)

    action: str
    symbol: str
    name: str = ""
    ratio: float = 0.0
    amount_jpy: float = 0.0
    reason: str = ""
    priority: int = 99

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, d: dict) -> "RebalanceAction":
        return cls(**d)


class YearlySnapshot(BaseModel):
    """1年分のシミュレーション結果 (KIK-366)."""
    model_config = ConfigDict(from_attributes=True)

    year: int
    value: float
    cumulative_input: float
    capital_gain: float
    cumulative_dividends: float

    def to_dict(self) -> dict:
        return self.model_dump()


class SimulationResult(BaseModel):
    """複利シミュレーション結果 (KIK-366)."""
    model_config = ConfigDict(from_attributes=True)

    scenarios: Dict[str, List[YearlySnapshot]]
    monte_carlo: Optional[Dict[str, Any]] = None
    target: Optional[float] = None
    target_year_base: Optional[float] = None
    target_year_optimistic: Optional[float] = None
    target_year_pessimistic: Optional[float] = None
    required_monthly: Optional[float] = None
    dividend_effect: float = 0.0
    dividend_effect_pct: float = 0.0

    years: int = 0
    monthly_add: float = 0.0
    reinvest_dividends: bool = True
    current_value: float = 0.0
    portfolio_return_base: Optional[float] = None
    dividend_yield: float = 0.0

    def to_dict(self) -> dict:
        # Use model_dump to get dictionaries for nested structures
        return self.model_dump()

    @classmethod
    def empty(cls) -> "SimulationResult":
        """シミュレーション不可時の空結果。"""
        return cls(
            scenarios={},
            target=None,
            target_year_base=None,
            target_year_optimistic=None,
            target_year_pessimistic=None,
            required_monthly=None,
            dividend_effect=0.0,
            dividend_effect_pct=0.0,
        )
