# PaletteFlow Color Extraction Guide

## Phase 1: The Extraction Algorithm (Core Logic)
Since you are using Rust, you can process the full-resolution image quickly
without downscaling.

### Color Space Conversion (Crucial)
Read the image pixels (RGB) and convert them to the LAB color space. LAB mimics
human vision, meaning the mathematical distance between two colors matches how
different they look to the human eye.

### Clustering (Grouping the Colors)
Pass the LAB pixels into a K-Means algorithm.

- Set K = 8 to 10. You want to extract more colors than you need so you can
  filter out the bad ones.
- **Snap to reality**: Once the K centroids are found, find the exact pixel in
  your image closest to each centroid to ensure authenticity.

### Filtering & Refinement
- **Calculate Dominance**: Count how many pixels belong to each of the K
  clusters.
- **Enforce Diversity**: Check the mathematical distance between all K chosen
  colors. If two colors have a distance below a certain threshold (e.g., they
  look too similar), discard the one with the lower pixel count.
- **Calculate Properties**: For the remaining distinct colors, calculate their
  Luminance (brightness) and Saturation (color intensity).
- **Trim**: Keep the top 5–6 best candidates based on highest pixel count and
  distinct saturation.

## Phase 2: The 6-Color UI Structure
You will map the extracted, filtered colors into four functional groups.

### Group 1: Backgrounds & Surfaces
- **Base Background**: The foundation of the UI.
- **Surface / Card**: Used for floating elements, modals, and cards to create
  depth against the background.

### Group 2: Action & Brand
- **Primary**: The main brand color used for primary buttons, active states, and
  important links.
- **Secondary**: Used for outlined buttons, secondary borders, or hover states.

### Group 3: Accent
- **Accent**: The "pop" color used very sparingly for badges, toggles, or
  floating action buttons.

### Group 4: Text
- **Primary Text**: Standard reading text.
- **Secondary Text**: Muted text for dates, captions, or subtitles.

## Phase 3: The Mapping Logic (What goes where?)
Programmatically assign your extracted list of exact image colors to the 6 UI
roles based on their properties (Dominance/Pixel Count, Saturation, and
Luminance).

### Selecting the Base Background
Choose the color with the highest dominance (largest pixel count). This is
usually a sky, a wall, or a dominant shadow.

### Selecting the Surface / Card
Look for the color with the second-highest dominance.
- **Fallback check**: If this second color contrasts too sharply with the Base
  Background (e.g., background is black, second color is bright red), it will
  look terrible as a card. In this case, simply take the Base Background and
  mathematically lighten or darken it slightly (e.g., by 5%) to generate a
  synthetic Surface color.

### Selecting the Primary & Secondary Action Colors
Sort the remaining colors by Saturation.
- The color with the highest balanced saturation and a decent pixel count
  becomes your Primary.
- The next distinct saturated color becomes your Secondary.

### Selecting the Accent
Find the color with the absolute highest Saturation, regardless of how tiny its
pixel count is (it might just be a small red flower in a wide green field).
This is your Accent.

## Phase 4: The Text Logic (Accessibility)
Text colors must be calculated dynamically based on the Base Background to
ensure readability. Use the WCAG Contrast Ratio formula, which requires a
minimum ratio of 4.5:1 for standard text.

1. **Check Background Luminance**: Is the Base Background dark or light?
2. **Pick a Candidate**:
   - If the background is light, find the darkest color extracted from the
     image.
   - If the background is dark, find the lightest color extracted.
3. **Verify Contrast**: Calculate the ratio between the Base Background and
   the Candidate.
   - If Ratio ≥ 4.5:1: Perfect. Use the Candidate exact image color as Primary
     Text.
   - If Ratio < 4.5:1: You cannot use the exact image color. You must
     programmatically darken (if light bg) or lighten (if dark bg) the
     candidate color in a loop until the mathematical ratio hits exactly 4.5:1.
4. **Generate Secondary Text**: Take your finalized Primary Text color and
   apply an alpha channel of 70% opacity, or mathematically mix it with the
   background color by 30% to create a muted text variant.
