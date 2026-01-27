"""StrategyDetail model for strategy detail fields."""

from dataclasses import dataclass
from typing import Any


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
