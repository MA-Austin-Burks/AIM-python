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
    """Get the first matching key from a row dict.
    
    DEPRECATED: After column name normalization, this helper is no longer needed.
    Use direct dictionary access with column name strings instead.
    Kept for backward compatibility during migration.
    """
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
        """Create a StrategySummary from a strategy_list row dict.
        
        Column names are normalized to lowercase at load time, so we use
        direct dictionary access with constants.
        """
        return cls(
            strategy=str(row.get("strategy", "")),
            recommended=_normalize_bool(row.get("ic_recommend", False)),
            equity_pct=float(row.get("equity_allo", 0) or 0),
            yield_decimal=row.get("yield", None),
            expense_ratio_decimal=float(row.get("fee", 0) or 0),
            minimum=float(row.get("minimum", 0) or 0),
            subtype=_normalize_subtype(row.get("series", [])),  # SERIES maps to ss_subtype
            type=str(row.get("ss_subtype", "")),  # TYPE maps to ss_subtype
            category=row.get("ss_type", None),  # CATEGORY maps to ss_type
            tax_managed=_normalize_bool(row.get("has_tm", False)),  # TAX_MANAGED maps to has_tm
            private_markets=_normalize_bool(row.get("has_private_market", False)),  # PRIVATE_MARKETS maps to has_private_market
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
        """Create a StrategyDetail from a cleaned_data row dict.
        
        Column names are normalized to lowercase at load time, so we use
        direct dictionary access with constants.
        """
        return cls(
            strategy=str(row.get("strategy", "")),
            model=str(row.get("ss_suite", "")),  # MODEL maps to ss_suite
            type=str(row.get("ss_subtype", "")),  # TYPE maps to ss_subtype
            category=row.get("ss_type", None),  # CATEGORY maps to ss_type
            portfolio=row.get("portfolio", None),
            expense_ratio=row.get("fee", None),
            yield_val=row.get("yield", None),
            minimum=row.get("minimum", None),
        )
