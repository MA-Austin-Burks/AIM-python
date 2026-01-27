export default function(component) {
  // Grab the host element, data payload, key, and state/trigger callbacks
  const { parentElement, data, key, setTriggerValue, setStateValue } = component;
  const m = data || {};
  
  // Use frontend key for unique DOM IDs (avoids collisions across component instances)
  const cardId = `mc-card-${key}`;
  
  // Ensure recommended is a boolean
  const isRecommended = Boolean(m.recommended);

  // Base colors
  const color = m.color || "#3B82F6";
  const pastel = color + "26";

  // Hardcoded styling values (all cards have the same look)
  const cardRadius = "12px";
  const cardShadow = "0 1px 2px rgba(0,0,0,.04)";
  const cardHoverShadow = "0 8px 28px rgba(0,0,0,.12)";
  const headerHeight = "64px";
  const headerPadding = "12px 16px";
  const bodyPadding = "10px 16px";
  const rowPadding = "6px 0";
  const titleSize = "18px";
  const titleWeight = "700";
  const titleFontFamily = "\"Merriweather\", serif";
  const bodyFontFamily = "\"IBM Plex Sans\", system-ui, sans-serif";
  const labelSize = ".875rem";
  const valueSize = "1rem";
  const valueWeight = "400";
  const labelColor = "#374151";
  const valueColor = "#111827";
  const starBadgeColor = "#facc15";

  // Metric formatting function
  const formatMetricValue = (value, format) => {
    const numValue = Number(value ?? 0);
    
    switch (format) {
      case "STRING":
        return String(value ?? "");
      case "PERCENT":
        if (numValue === 0) return "";
        return numValue.toFixed(2) + "%";
      case "DECIMAL":
        return numValue.toFixed(2);
      case "DOLLAR":
        if (numValue === 0) return "$0.0";
        const absValue = Math.abs(numValue);
        if (absValue >= 1_000_000) return `$${(numValue / 1_000_000).toFixed(1)}M`;
        if (absValue >= 1_000) return `$${(numValue / 1_000).toFixed(1)}K`;
        return `$${numValue.toFixed(1)}`;
      default:
        return String(value ?? "");
    }
  };

  // Build metric rows HTML
  const metrics = m.metrics || [];
  let metricRowsHtml = "";
  metrics.forEach((metric, index) => {
    const isLast = index === metrics.length - 1;
    const borderClass = isLast ? "mc-row-last" : "";
    const borderStyle = isLast ? "border-bottom:none;" : "border-bottom:1px solid rgba(0,0,0,.08);";
    const formattedValue = formatMetricValue(metric.value, metric.format);
    
    metricRowsHtml += `
      <div class="${borderClass}" style="display:flex;justify-content:space-between;align-items:center;
                                        padding:${rowPadding};${borderStyle}">
        <span style="font-size:${labelSize};color:${labelColor};">${metric.label || ""}</span>
        <span style="font-size:${valueSize};font-weight:${valueWeight};color:${valueColor};">
          ${formattedValue}
        </span>
      </div>
    `;
  });

  // Build the HTML with inline styles for reliable rendering
  // Note: CSS variable is set via JavaScript after mount for better compatibility
  // Uses unique cardId from frontend key to avoid DOM collisions
  const html = `
    <div id="${cardId}" class="mc-card" role="button" tabindex="0"
         style="border-radius:${cardRadius};box-shadow:${cardShadow};background:#fff;">
      <div style="background:${color};padding:${headerPadding};height:${headerHeight};
                  display:flex;align-items:center;">
        <div style="display:flex;align-items:center;justify-content:space-between;width:100%;gap:12px;">
          <h3 style="color:#fff;font-weight:${titleWeight};font-size:${titleSize};
                     font-family:${titleFontFamily};margin:0;line-height:1.2;
                     display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
                     overflow:hidden;">
            ${m.name ?? ""}
          </h3>
          <span style="color:${isRecommended ? starBadgeColor : 'rgba(255,255,255,0.5)'};font-size:25px;line-height:1;
                            display:flex;align-items:center;justify-content:center;min-width:25px;">${isRecommended ? '★' : '☆'}</span>
        </div>
      </div>

      <div style="background:${pastel};padding:${bodyPadding};font-family:${bodyFontFamily};">
        ${metricRowsHtml}
      </div>
    </div>
  `;

  // Mount in the Streamlit container
  const node = document.createElement("div");
  node.innerHTML = html;
  parentElement.appendChild(node);

  // Get the card element by unique ID and ensure styles are applied
  const cardElement = node.querySelector(`#${cardId}`);
  if (cardElement) {
    // Set CSS variable for hover shadow effect (must be set on element for :hover to work)
    cardElement.style.setProperty("--mc-card-hover-shadow", cardHoverShadow);
    // Ensure border-radius is applied with !important via inline style
    cardElement.style.setProperty("border-radius", cardRadius, "important");
    // Ensure initial box-shadow is set
    cardElement.style.setProperty("box-shadow", cardShadow);
    
    // Handler to notify Python of selection
    const handleSelect = () => {
      const cardId = m.id || m.name || null;
      setStateValue("selected", cardId);    // Persistent state (survives reruns)
      setTriggerValue("clicked", cardId);   // One-time trigger (resets after rerun)
    };
    
    // Click handler -> notify Python
    cardElement.onclick = handleSelect;
    
    // Keyboard accessibility: Enter or Space triggers selection
    cardElement.onkeydown = (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleSelect();
      }
    };
  }

  // Cleanup on unmount
  return () => {
    parentElement.removeChild(node);
  };
}
