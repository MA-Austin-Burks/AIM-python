"""CAISSummary model for CAIS strategy summary fields."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CAISSummary:
    """CAIS strategy summary fields used for CAIS cards."""

    strategy: str
    cais_type: str
    cais_subtype: str
    sub_strategy: str
    client_type: str
    avail_schwab: str
    avail_fidelity: str
    core_niche: str
    ma_rank: int | None
    mercer_rating: str
    mercer_ora: str
    minimum: float
    reporting_type: str
    lockup: str
    notes: str

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "CAISSummary":
        """Create a CAISSummary from a CAIS data row dict."""
        return cls(
            strategy=str(row.get("strategy", "")),
            cais_type=str(row.get("cais_type", "")),
            cais_subtype=str(row.get("cais_subtype", "")),
            sub_strategy=str(row.get("sub_strategy", "")),
            client_type=str(row.get("client_type", "")),
            avail_schwab=str(row.get("avail_schwab", "")),
            avail_fidelity=str(row.get("avail_fidelity", "")),
            core_niche=str(row.get("core_niche", "")),
            ma_rank=row.get("ma_rank", None),
            mercer_rating=str(row.get("mercer_rating", "")),
            mercer_ora=str(row.get("mercer_ora", "")),
            minimum=float(row.get("minimum", 0) or 0),
            reporting_type=str(row.get("reporting_type", "")),
            lockup=str(row.get("lockup", "")),
            notes=str(row.get("notes", "")),
        )
