from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StrategySummary:
    """Strategy summary fields used across cards, filters, and the modal header."""

    strategy: str
    recommended: bool
    equity_pct: float
    yield_decimal: float
    expense_ratio_decimal: float
    minimum: float
    subtype: list[str]
    subtype_primary: str
    type: str
    tax_managed: bool
    private_markets: bool
    sma: bool
    vbi: bool
