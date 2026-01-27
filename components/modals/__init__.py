"""Modal components for displaying strategy details."""

from components.modals.cais_modal import render_cais_modal
from components.modals.registry import (
    register_modal,
    render_modal_by_type,
)
from components.modals.strategy_modal import render_strategy_modal

# Register the modals
register_modal("strategy", render_strategy_modal)
register_modal("cais", render_cais_modal)

__all__ = [
    "render_modal_by_type",
]
