from collections.abc import Callable
from pathlib import Path

import streamlit as st

# Get the directory where this file is located
_MODEL_CARD_DIR = Path(__file__).parent

CARD_FIXED_WIDTH = "375px"  # Fixed width for each card

# Load CSS and JS from files
_CSS_FILE = _MODEL_CARD_DIR / "model_card.css"
_JS_FILE = _MODEL_CARD_DIR / "model_card.js"


@st.cache_resource
def _load_css() -> str:
    """Load CSS from file (cached)."""
    with open(_CSS_FILE, "r", encoding="utf-8") as f:
        return f.read()


@st.cache_resource
def _load_js() -> str:
    """Load JavaScript from file (cached)."""
    with open(_JS_FILE, "r", encoding="utf-8") as f:
        return f.read()


@st.cache_resource
def _get_model_card_component():
    """Register and cache the inline model card component."""
    css = _load_css()
    js = _load_js()
    return st.components.v2.component(  # type: ignore[attr-defined]
        "model_card_inline",
        js=js,
        css=css,
    )


_model_card = _get_model_card_component()


# ======================
# PYTHON API YOU USE IN YOUR APP
# ======================
def model_card(
    *,
    id: str,
    name: str,
    color: str | None = None,
    recommended: bool = False,
    metric_label_1: str,
    metric_value_1: float | str,
    metric_format_1: str,
    metric_label_2: str,
    metric_value_2: float | str,
    metric_format_2: str,
    metric_label_3: str,
    metric_value_3: float | str,
    metric_format_3: str,
    modal_type: str,
    key: str | None = None,
    on_click: Callable[[], None] = lambda: None,
    on_select: Callable[[], None] = lambda: None,
):
    """
    Render a model card with dynamic metrics and return the result object.
    
    Args:
        id: Unique identifier for the card
        name: Strategy/card name displayed in header
        color: Header background color (hex code, e.g., "#3B82F6")
        recommended: Whether to show the recommended star badge
        metric_label_1/2/3: Label text for each metric
        metric_value_1/2/3: Value for each metric (float or string)
        metric_format_1/2/3: Format type - one of "STRING", "PERCENT", "DECIMAL", "DOLLAR"
        modal_type: Identifier for which modal to show when card is clicked
        key: Streamlit component key
        on_click: Callback for click events
        on_select: Callback for selection events
    
    Returns:
        result: Object with two attributes:
            - clicked (str | None): One-time trigger, resets to None after rerun
            - selected (str | None): Persistent state, survives across reruns
    """
    # Build metrics array for JavaScript component
    metrics = [
        {"label": metric_label_1, "value": metric_value_1, "format": metric_format_1},
        {"label": metric_label_2, "value": metric_value_2, "format": metric_format_2},
        {"label": metric_label_3, "value": metric_value_3, "format": metric_format_3},
    ]
    
    result = _model_card(
        data={
            "id": id,
            "name": name,
            "color": color,
            "recommended": recommended,
            "metrics": metrics,
            "modal_type": modal_type,
        },
        default={"selected": None},       # Default state value for persistent selection
        key=key,
        on_clicked_change=on_click,       # One-time trigger callback
        on_selected_change=on_select,     # Persistent state callback
    )
    return result
