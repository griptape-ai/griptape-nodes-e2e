# CreateColorBars

**Library:** Griptape Nodes Library **Class:** `CreateColorBars` **Base class:** `BaseNode`
**Category:** image **Display name:** Create Color Bars

## Description

Generates standard color bar test patterns (SMPTE, EBU, ARIB, full-field solids, etc.) as a PIL
image. Pure local generation with no external dependencies. Ideal as a deterministic image fixture
for test workflows — the "Full Field" variants produce uniform solid-color images suitable for
pixel-exact assertions.

## Parameters

| Name                | Type               | Modes           | Default                | Description                                                      |
| ------------------- | ------------------ | --------------- | ---------------------- | ---------------------------------------------------------------- |
| `bar_type`          | `str` (Options)    | INPUT, PROPERTY | `"SMPTE 219-100 Bars"` | Pattern type. 40 choices — see Options below.                    |
| `width`             | `int`              | INPUT, PROPERTY | `1920`                 | Image width in pixels.                                           |
| `height`            | `int`              | INPUT, PROPERTY | `1080`                 | Image height in pixels.                                          |
| `pluge_ire_setup`   | `str` (Options)    | INPUT, PROPERTY | `"NTSC 7.5 IRE"`       | IRE setup type. Hidden unless `bar_type == "Pluge"`.             |
| `pluge_bar_count`   | `int`              | INPUT, PROPERTY | `3`                    | Number of PLUGE bars (2–5). Hidden unless `bar_type == "Pluge"`. |
| `pluge_orientation` | `str` (Options)    | INPUT, PROPERTY | `"vertical"`           | Bar orientation. Hidden unless `bar_type == "Pluge"`.            |
| `image`             | `ImageUrlArtifact` | OUTPUT          | `None`                 | Generated image.                                                 |
| `output_file`       | `str`              | INPUT, PROPERTY | `"color_bars.png"`     | Output filename.                                                 |

### `bar_type` options

SMPTE 219-100 Bars, SMPTE 75% Bars, SMPTE Bars, SMPTE 219+i Bars, 100% Full Field Bars, 75% Full
Field Bars, 75% Bars Over Red, EBU Bars, ARIB 28-100, ARIB 28-75, ARIB 28+i, HD Color Bars, Full
Field White, Full Field Blue, Full Field Cyan, Full Field Green, Full Field Magenta, Full Field
Red, Full Field Yellow, Zone Plate, Tartan Bars, Stair 5 Step, Stair 5 Step Vert, Stair 10 Step,
Stair 10 Step Vert, Y Ramp Up, Y Ramp Down, Vertical Ramp, Legal Chroma Ramp, Full Chroma Ramp,
Chroma Ramp, Multi Burst, Pluge, Bowtie, Pathological EG, Pathological PLL, Pathological EG/PLL, AV
Delay Pattern 1, AV Delay Pattern 2, Bouncing Box.

### `pluge_ire_setup` options

NTSC 7.5 IRE, PAL 0 IRE, RGB Full Range.

### `pluge_orientation` options

vertical, horizontal.

## Use When

- You need an `ImageUrlArtifact` input for the node under test without external services.
- Use `"Full Field White"` or another solid-color variant for simple, predictable image data.
- Wire `CreateColorBars.image` → `NodeUnderTest.<image_input>`.

## Example Wiring

```
(set CreateColorBars.bar_type = "Full Field White", width = 100, height = 100)
CreateColorBars.image  →  CropImage.input_image
```
