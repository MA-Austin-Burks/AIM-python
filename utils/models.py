"""Dataclass models for strategy data passed to the UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _normalize_bool(value: Any) -> bool:
    """Normalize mixed truthy values into a bool."""
    if isinstance(value, str):
        return value.strip().upper() in ("TRUE", "YES", "1")
    return bool(value)


def _normalize_subtype(value: Any) -> list[str]:
    """Normalize Subtype field into a list of strings."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return [str(value)]


def _get_row_value(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Get the first matching key from a row dict."""
    for key in keys:
        if key in row:
            return row[key]
    return default


@dataclass(frozen=True, slots=True)
class StrategySummary:
    """Strategy summary fields used across cards, filters, and the modal header."""

    strategy: str
    recommended: bool
    equity_pct: float
    yield_decimal: float | None
    expense_ratio_decimal: float
    minimum: float
    subtype: list[str]
    type: str
    category: str | None
    tax_managed: bool
    private_markets: bool

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "StrategySummary":
        """Create a StrategySummary from a strategy_list row dict."""
        return cls(
            strategy=str(_get_row_value(row, "Strategy", default="")),
            recommended=_normalize_bool(_get_row_value(row, "Recommended", default=False)),
            equity_pct=float(_get_row_value(row, "Equity %", default=0) or 0),
            yield_decimal=_get_row_value(row, "Yield", default=None),
            expense_ratio_decimal=float(_get_row_value(row, "Expense Ratio", default=0) or 0),
            minimum=float(_get_row_value(row, "Minimum", default=0) or 0),
            subtype=_normalize_subtype(_get_row_value(row, "Series", default=[])),
            type=str(_get_row_value(row, "Type", default="")),
            category=_get_row_value(row, "Strategy Type", default=None),
            tax_managed=_normalize_bool(_get_row_value(row, "Tax-Managed", default=False)),
            private_markets=_normalize_bool(_get_row_value(row, "Private Markets", default=False)),
        )

    @property
    def yield_pct_display(self) -> float:
        """Yield % for display (input stored as decimal)."""
        return (self.yield_decimal or 0.0) * 100

    @property
    def expense_ratio_pct_display(self) -> float:
        """Expense ratio % for display (input stored as decimal)."""
        return self.expense_ratio_decimal * 100

    @property
    def subtype_primary(self) -> str | None:
        """First subtype name if available."""
        return self.subtype[0] if self.subtype else None


@dataclass(frozen=True)
class StrategyDetail:
    """Strategy detail fields derived from cleaned_data for allocation tabs."""

    strategy: str
    model: str
    type: str
    category: str | None
    portfolio: float | None
    expense_ratio: float | None
    yield_val: float | None
    minimum: float | None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "StrategyDetail":
        """Create a StrategyDetail from a cleaned_data row dict."""
        return cls(
            strategy=str(_get_row_value(row, "strategy", "Strategy", default="")),
            model=str(_get_row_value(row, "model", "Model", default="")),
            type=str(_get_row_value(row, "type", "Type", default="")),
            category=_get_row_value(row, "strategy_type", "Strategy Type", default=None),
            portfolio=_get_row_value(row, "portfolio", "Portfolio", default=None),
            expense_ratio=_get_row_value(row, "expense_ratio", "Expense Ratio", default=None),
            yield_val=_get_row_value(row, "yield", "Yield", default=None),
            minimum=_get_row_value(row, "minimum", "Minimum", default=None),
        )
