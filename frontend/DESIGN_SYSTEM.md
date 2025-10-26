# AI Legal Tender - Design System Update

## Logo-Inspired Color Palette

Based on your hexagonal emblem with scales of justice and circuit patterns:

### Color Palette

**Gold (Hexagonal Border & Scale)**
- `gold-50` to `gold-900`: Mustard-gold tones from #fffbeb to #78350f
- Primary accent color for borders, highlights, and metallic elements

**Bronze (Circuit Pattern)**
- `bronze-50` to `bronze-900`: Rich bronze-brown from #fdf8f6 to #43302b
- Used for circuit traces and secondary accents

**Marble (Background Texture)**
- `marble-50` to `marble-900`: White marble with grey veining from #fafaf9 to #1c1917
- Base colors for cards and backgrounds

**Circuit Colors**
- `circuit-bronze`: #8B6F47 (circuit traces)
- `circuit-gold`: #C9A961 (circuit highlights)
- `circuit-node`: #6B5840 (connection points)

### Design Elements

**Hexagonal Motifs**
- Hexagon patterns in background textures
- Hexagonal clip-path borders available via `hexagon-border` class

**Metallic Effects**
- `.metallic-text` - Gold gradient text with shimmer effect
- `.scale-icon` - Drop shadow effect for justice scale icons
- Gradient backgrounds from gold to bronze

**Marble Textures**
- `.marble-bg` - Marble background with subtle veining
- Card backgrounds use gradients from `#fafaf9` to `#f5f5f4`
- Circuit-like grid overlay patterns

**Circuit Patterns**
- `.circuit-pattern` - Adds bronze/gold circuit line decoration
- SVG circuit traces in sidebar and dashboard components

### Component Updates

**Header**
- Gold-to-bronze gradient background
- White scale icon with glow effect
- Gold border accent line with circuit pattern

**Sidebar**
- Dark marble background (marble-900 to marble-800)
- Gold accent borders and active states
- Tech stack badges with AMD (red) and Google (blue) colors
- Scale icon logo in gold gradient

**Dashboard**
- Marble textured background
- Stat cards with gold borders and gradients
- Tech stack banner with marble-dark background and gold border
- Metallic gold headings

**Cards & Badges**
- Gold/bronze borders instead of grey
- Marble white backgrounds with subtle grid texture
- Status badges use gold (awaiting), bronze (processing), green (approved)

**Buttons**
- `.btn-primary` - Gold gradient with shadow
- `.btn-secondary` - Bronze solid color
- Enhanced shadows with gold tint

### Typography

**Headings**
- Use `.metallic-text` for gold gradient effect
- Bold weights (700) for authority
- Scale emoji (⚖️) for legal context

**Body Text**
- `text-marble-900` for dark text
- `text-marble-600` for secondary text
- `text-gold-600` for highlights

### Logo Component

Created SVG hexagonal logo combining:
- Hexagonal gold border
- Marble white center
- Circuit traces (bronze) on left
- Scale of justice (gold) on right
- Circuit nodes at connection points
- Metallic filter effects

### Usage

The design merges:
1. **Law** - Scales of justice, professional typography, authority
2. **Technology** - Circuit patterns, modern gradients, digital aesthetic
3. **Sophistication** - Marble textures, metallic finishes, refined geometry

All elements are integrated to suggest "ethical technology, AI governance, and digital justice" as described in the logo.
