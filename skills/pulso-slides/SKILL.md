---
name: pulso-slides
description: Create clean, minimal PowerPoint presentations from Markdown. Use when the user asks to create slides, a presentation, or a deck. Produces white-background, black-text PPTX files with Open Sans typography and proper bullet formatting.
---

# pulso-slides

Create minimal, professional PowerPoint presentations from Markdown input. White background, Open Sans font, no clutter.

## Markdown Format

Write slide content using this format:

```markdown
# Slide Title
## Subtitle (title slides only)
- Bullet point
- Another bullet
Plain text becomes a paragraph.
---
(three dashes on their own line separate slides)
```

### Rules

- `# ` = slide title
- `## ` = subtitle (only on title slides)
- `- ` = bullet item (rendered with `·` dot)
- Plain text = paragraph
- `---` = slide separator
- A slide with `##` or a `#` with no body becomes a **title slide** (centered)
- All other slides are **content slides** (title top-left, body below)

## Design

| Element | Font | Size | Weight | Color |
|---------|------|------|--------|-------|
| Title slide title | Open Sans | 36pt | SemiBold | black |
| Title slide subtitle | Open Sans | 20pt | Regular | #444444 |
| Content title | Open Sans | 28pt | SemiBold | black |
| Content body | Open Sans | 18pt | Regular | #1A1A1A |

- Slide size: 13.333 x 7.5 in (widescreen 16:9)
- Background: white (default)
- Bullets: middle dot (`·`) via proper OOXML, editable in PowerPoint
- Title slides are vertically centered

## Usage

```bash
python scripts/create_slides.py <input.md> [output.pptx]
```

If `output.pptx` is omitted, the output file uses the input filename with a `.pptx` extension. Supports `-` to read from stdin.

## Example

Given a file `quarterly.md`:

```markdown
# Q4 Results
## Company Update

---

# Revenue Growth
- Total revenue up 23% YoY
- SaaS ARR crossed $10M milestone
- Net retention rate at 118%

---

# Next Steps
- Expand into European markets
- Launch self-serve tier in Q1
- Hire 12 additional engineers

Targeting full profitability by Q3 next year.
```

Run:

```bash
python scripts/create_slides.py quarterly.md
```

Produces `quarterly.pptx` with 3 slides: a centered title slide, and two content slides with bullets.

## Font Note

Open Sans must be installed on the machine viewing the presentation. If not available, PowerPoint will substitute a fallback font. Open Sans can be downloaded from Google Fonts.
