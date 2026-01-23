import streamlit as st

CARD_FIXED_WIDTH = "375px"  # Fixed width for each card

# ======================
# INLINE CSS (scoped)
# ======================
# Minimal CSS to keep hover behavior and shared class rules.
CSS = f"""
.mc-card{{
  overflow:hidden;
  cursor:pointer;
  transition:box-shadow .15s,transform .06s;
  width:100%;
  flex-shrink:0;
}}
.mc-card:hover{{
  box-shadow:var(--mc-card-hover-shadow);
  transform:translateY(-1px)
}}
.mc-row-last{{border-bottom:none}}
"""

# ======================
# INLINE JS (V2 Component)
# ======================
# Uses Streamlit's V2 mounting API: setTriggerValue('clicked', id)
# Docs: https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component
JS = r"""
export default function(component) {
  // Grab the host element, data payload, and trigger callback
  const { parentElement, data, setTriggerValue } = component;
  const m = data || {};
  
  // Ensure featured is a boolean
  const isFeatured = Boolean(m.featured);

  // Base colors
  const color = m.color || "#3B82F6";
  const pastel = color + "26";

  // Styling options (defaults match current look)
  const style = m.style || {};
  const cardRadius = style.cardRadius || "12px";
  const cardShadow = style.cardShadow || "0 1px 2px rgba(0,0,0,.04)";
  const cardHoverShadow = style.cardHoverShadow || "0 8px 28px rgba(0,0,0,.12)";
  const headerHeight = style.headerHeight || "64px";
  const headerPadding = style.headerPadding || "12px 16px";
  const bodyPadding = style.bodyPadding || "10px 16px";
  const rowPadding = style.rowPadding || "6px 0";
  const titleSize = style.titleSize || "18px";
  const titleWeight = style.titleWeight || "700";
  const titleFontFamily = style.titleFontFamily || "\"Merriweather\", serif";
  const bodyFontFamily = style.bodyFontFamily || "\"IBM Plex Sans\", system-ui, sans-serif";
  const labelSize = style.labelSize || ".875rem";
  const valueSize = style.valueSize || "1rem";
  const valueWeight = style.valueWeight || "400";
  const labelColor = style.labelColor || "#374151";
  const valueColor = style.valueColor || "#111827";
  const accentColor = style.accentColor || "#188038";
  const starBadgeBg = style.starBadgeBg || "rgba(255,255,255,.2)";
  const starBadgeColor = style.starBadgeColor || "#facc15";
  const starBadgeRadius = style.starBadgeRadius || "10px";
  const starBadgePadding = style.starBadgePadding || "6px 8px";

  // Format minimum as $x.xK / $x.xM with 1 decimal
  const formatMinimum = () => {
    const value = Number(m.minimum ?? 0);
    if (value === 0) return "$0.0";
    const absValue = Math.abs(value);
    if (absValue >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
    if (absValue >= 1_000) return `$${(value / 1_000).toFixed(1)}K`;
    return `$${value.toFixed(1)}`;
  };

  // Build the HTML with inline styles for reliable rendering
  const html = `
    <div class="mc-card" role="button"
         style="border-radius:${cardRadius};box-shadow:${cardShadow};
                --mc-card-hover-shadow:${cardHoverShadow};background:#fff;">
      <div style="background:${color};padding:${headerPadding};height:${headerHeight};
                  display:flex;align-items:center;">
        <div style="display:flex;align-items:center;justify-content:space-between;width:100%;gap:12px;">
          <h3 style="color:#fff;font-weight:${titleWeight};font-size:${titleSize};
                     font-family:${titleFontFamily};margin:0;line-height:1.2;
                     display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
                     overflow:hidden;">
            ${m.name ?? ""}
          </h3>
          <span style="color:${isFeatured ? starBadgeColor : 'rgba(255,255,255,0.5)'};font-size:25px;line-height:1;
                            display:flex;align-items:center;justify-content:center;min-width:25px;">${isFeatured ? '★' : '☆'}</span>
        </div>
      </div>

      <div style="background:${pastel};padding:${bodyPadding};font-family:${bodyFontFamily};">
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:${rowPadding};border-bottom:1px solid rgba(0,0,0,.08);">
          <span style="font-size:${labelSize};color:${labelColor};">Yield</span>
          <span style="font-size:${valueSize};font-weight:${valueWeight};color:${valueColor};">
            ${Number(m.yield ?? 0).toFixed(2)}%
          </span>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;
                    padding:${rowPadding};border-bottom:1px solid rgba(0,0,0,.08);">
          <span style="font-size:${labelSize};color:${labelColor};">Expense Ratio</span>
          <span style="font-size:${valueSize};font-weight:${valueWeight};color:${valueColor};">
            ${Number(m.expenseRatio ?? 0).toFixed(2)}
          </span>
        </div>
        <div class="mc-row-last" style="display:flex;justify-content:space-between;align-items:center;
                                        padding:${rowPadding};border-bottom:none;">
          <span style="font-size:${labelSize};color:${labelColor};">Minimum</span>
          <span style="font-size:${valueSize};font-weight:${valueWeight};color:${valueColor};">
            ${formatMinimum()}
          </span>
        </div>
      </div>
    </div>
  `;

  // Mount in the Streamlit container
  const node = document.createElement("div");
  node.innerHTML = html;
  parentElement.appendChild(node);

  // Click handler -> notify Python
  node.querySelector(".mc-card").onclick = () =>
      setTriggerValue("clicked", m.id || m.name || null);

  // Cleanup on unmount
  return () => {
    parentElement.removeChild(node);
  };
}
"""

@st.cache_resource
def _get_model_card_component():
    """Register and cache the inline model card component."""
    return st.components.v2.component(
        "model_card_inline",
        js=JS,
        css=CSS,
    )


_model_card = _get_model_card_component()


# ======================
# PYTHON API YOU USE IN YOUR APP
# ======================
def model_card(
    *,
    id: str,
    name: str,
    yield_pct: float,
    expense_ratio: float,
    minimum: float,
    color: str | None = None,
    featured: bool = False,
    card_radius: str = "12px",
    card_shadow: str = "0 1px 2px rgba(0,0,0,.04)",
    card_hover_shadow: str = "0 8px 28px rgba(0,0,0,.12)",
    header_height: str = "60px",
    header_padding: str = "10px 14px",
    body_padding: str = "10px 14px",
    row_padding: str = "3px 0",
    title_size: str = "18px",
    title_weight: str = "700",
    title_font_family: str = "\"Merriweather\", serif",
    body_font_family: str = "\"IBM Plex Sans\", system-ui, sans-serif",
    label_size: str = ".875rem",
    value_size: str = "1rem",
    value_weight: str = "400",
    label_color: str = "#374151",
    value_color: str = "#111827",
    accent_color: str = "#188038",
    star_badge_bg: str = "rgba(255,255,255,.2)",
    star_badge_color: str = "#facc15",
    star_badge_radius: str = "10px",
    star_badge_padding: str = "6px 8px",
    key: str | None = None,
):
    """Render a model card and return the clicked ID (or None)."""
    result = _model_card(
        data={
            "id": id,
            "name": name,
            "yield": yield_pct,
            "expenseRatio": expense_ratio,
            "minimum": minimum,
            "color": color,
            "featured": featured,
            "style": {
                "cardRadius": card_radius,
                "cardShadow": card_shadow,
                "cardHoverShadow": card_hover_shadow,
                "headerHeight": header_height,
                "headerPadding": header_padding,
                "bodyPadding": body_padding,
                "rowPadding": row_padding,
                "titleSize": title_size,
                "titleWeight": title_weight,
                "titleFontFamily": title_font_family,
                "bodyFontFamily": body_font_family,
                "labelSize": label_size,
                "valueSize": value_size,
                "valueWeight": value_weight,
                "labelColor": label_color,
                "valueColor": value_color,
                "accentColor": accent_color,
                "starBadgeBg": star_badge_bg,
                "starBadgeColor": star_badge_color,
                "starBadgeRadius": star_badge_radius,
                "starBadgePadding": star_badge_padding,
            },
        },
        key=key,
        on_clicked_change=lambda: None,  # register the JS -> Python trigger
    )
    return getattr(result, "clicked", None)


# ======================
# Slim readable version (reference)
# ======================
# JS: use `data`, append HTML to `parentElement`, call setTriggerValue on click.
