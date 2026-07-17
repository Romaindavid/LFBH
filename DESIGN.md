---
name: Aéro-Transparence
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#434655'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#747686'
  outline-variant: '#c4c5d7'
  surface-tint: '#2151da'
  primary: '#0037b0'
  on-primary: '#ffffff'
  primary-container: '#1d4ed8'
  on-primary-container: '#cad3ff'
  inverse-primary: '#b7c4ff'
  secondary: '#a73a00'
  on-secondary: '#ffffff'
  secondary-container: '#fd651e'
  on-secondary-container: '#571a00'
  tertiary: '#005022'
  on-tertiary: '#ffffff'
  tertiary-container: '#006b2f'
  on-tertiary-container: '#88ea9a'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dce1ff'
  primary-fixed-dim: '#b7c4ff'
  on-primary-fixed: '#001551'
  on-primary-fixed-variant: '#0039b5'
  secondary-fixed: '#ffdbce'
  secondary-fixed-dim: '#ffb599'
  on-secondary-fixed: '#370e00'
  on-secondary-fixed-variant: '#7f2b00'
  tertiary-fixed: '#95f8a7'
  tertiary-fixed-dim: '#79db8d'
  on-tertiary-fixed: '#00210a'
  on-tertiary-fixed-variant: '#005323'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  data-display:
    fontFamily: JetBrains Mono
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: -0.01em
  data-label:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  helper-text:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin-desktop: 48px
  margin-mobile: 16px
  stack-sm: 8px
  stack-md: 16px
---

## Brand & Style
The design system is engineered for public accountability and civic transparency. It serves as a data-driven interface for monitoring airport traffic with a focus on environmental impact and operational clarity. The brand personality is authoritative yet accessible, functioning as a professional utility for citizens, researchers, and policymakers.

The aesthetic follows a **Modern Corporate** approach with a **Technical/Data-Driven** edge. It prioritizes information density and legibility over decorative elements. By utilizing a "clean-room" environment—characterized by vast white space, crisp borders, and a rigorous typographic grid—the system fosters an atmosphere of scientific credibility and neutrality.

## Colors
The palette is functional and semantic, designed to categorize complex data sets at a glance without ambiguity.

- **Background & Neutrals:** A base of `#FFFFFF` for primary surfaces and `#F8FAFC` (Slate 50) for background fills ensures a "public utility" feel. Borders use a subtle Slate 200 for definition.
- **Ligne régulière (Primary):** Professional Blue (#1D4ED8) represents stable, scheduled infrastructure.
- **Jets privés (Highlight):** Warning Orange/Red (#EA580C) is used purposefully to draw attention to high-impact travel and CO2 intensity.
- **Tourisme (Tertiary):** Fresh Green (#15803D) identifies recreational and general aviation.
- **Feedback:** Use standard semantic reds and ambers only for system errors; all category-specific coloring must adhere strictly to the flight type tokens.

## Typography
The typographic strategy employs a dual-font system to separate narrative from data.

- **Inter** is used for all UI labels, body text, and headings. Its high x-height and neutral character ensure readability across various screen densities.
- **JetBrains Mono** is reserved for tabular data, flight numbers, timestamps, and KPI metrics. The monospaced nature ensures that columns of numbers remain perfectly aligned, facilitating rapid visual comparison of CO2 values or flight durations.
- **Scientific Credibility:** All estimated CO2 data must be styled using the `helper-text` role (italicized) or accompanied by a small asterisk to indicate a calculated estimate rather than a direct sensor reading.

## Layout & Spacing
This design system utilizes a **12-column fluid grid** for desktop and a **4-column grid** for mobile devices. 

- **Grid Logic:** Content is organized into "Data Modules." On desktop, main dashboards span 8 or 12 columns, while secondary filters and sidebars occupy 3 or 4 columns.
- **Rhythm:** An 8px base unit drives the spacing system, ensuring consistent vertical rhythm between data rows and card elements. 
- **Density:** To maintain a professional feel, padding within data tables is kept compact (8px-12px), while the margins between major sections remain large (48px) to provide visual breathing room and prevent information overload.

## Elevation & Depth
To maintain a "flat" and factual aesthetic, the design system avoids heavy shadows or complex gradients. 

- **Low-Contrast Outlines:** Primary containers use a 1px solid border (`#E2E8F0`). 
- **Subtle Elevation:** Only active or interactive elements (like a selected flight card) use a very soft, ambient shadow: `0px 4px 12px rgba(0, 0, 0, 0.05)`. 
- **Tonal Layers:** Use background shifts to indicate depth. The main canvas is white, while interactive sidebar menus or header bars use the neutral Slate 50 background to create a clear structural hierarchy without relying on shadows.

## Shapes
The shape language is conservative and geometric. 

- **Standard Radius:** A 4px (`0.25rem`) radius is applied to buttons, input fields, and small UI components. This "Soft" setting maintains a modern feel without the playfulness of highly rounded corners.
- **Large Components:** Dashboard cards and map containers may use up to 8px (`0.5rem`) for a slightly more polished, distinct look.
- **Interactive States:** Buttons remain rectangular with minimal rounding to reinforce the serious, institutional nature of the dashboard.

## Components
- **Data Cards:** Use flat white backgrounds with a 1px border. The top edge of the card features a 4px color-coded accent bar corresponding to the flight category (Blue, Orange, or Green).
- **KPI Widgets:** Prominent display of monospaced numbers. The title of the KPI uses the `data-label` style in Slate 500.
- **Flight List Items:** Tight vertical padding. Each row includes a minimalist outline icon of the aircraft type. Private jet rows should feature a subtle hover state that highlights the CO2 metric in `secondary_color`.
- **Buttons:** Primary buttons use a solid fill of the Primary Blue. Secondary buttons use an outline style. Text is always uppercase or semi-bold Inter.
- **Input Fields:** Search and filter bars use a Slate 50 fill with a bottom-only border or a light 1px stroke, appearing integrated into the dashboard header.
- **Status Badges:** Small, rectangular chips with low-opacity background tints (e.g., 10% opacity of the category color) and high-contrast text for high legibility.
- **CO2 Markers:** Any metric involving carbon impact should be paired with a "source" icon—a small, interactive information glyph that reveals the calculation methodology on hover.