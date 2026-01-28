from dataclasses import dataclass


@dataclass(frozen=True)
class StrategyDetail:
    """Strategy detail fields derived from cleaned_data for allocation tabs."""

    strategy: str
    suite: str
    subtype: str
    type: str
    portfolio: float
    expense_ratio: float
    yield_val: float
    minimum: float
