---
name: figma-to-code
description: Protocol for translating Figma designs into production-ready code (CSS/Tailwind/Flutter). Covers asset export, token extraction, and responsive layout mapping.
---

# Figma to Code Handoff Protocol

Bridging the gap between Design (Pixel) and Development (Logic).

## 1. Inspect & Analysis
*   **Box Model First:** Don't look at pixels yet. Look at groupings.
    *   Is this a Row or Column (Flexbox/Grid)?
    *   What is the Padding vs. Margin?
*   **Responsive Behavior:** Check constraints (Left/Right, Top/Bottom, Scale). How does it behave on resize?

## 2. Token Extraction (Design System)
*   **Colors:** Do not hardcode HEX. Use the semantic name (e.g., `primary-500` -> `var(--color-primary-500)`).
*   **Typography:** Map Figma Text Styles to CSS Classes (e.g., `H1/Bold` -> `.text-4xl.font-bold`).
*   **Spacing:** Round pixel values to the nearest 4px grid steps (e.g., 17px -> `1rem` / 16px).

## 3. Asset Export
*   **Vectors (Icons/Logos):** Always SVG. Ensure paths are flattened.
*   **Photos:** JPG for opaque, PNG/WebP for transparent.
*   **Naming:** Use kebab-case for filenames (`hero-background.webp`) before export.

## 4. Layout Implementation Strategy
1.  **Structure (HTML):** Write the semantic HTML skeleton first. No styles.
2.  **Layout (CSS Layout):** Apply Flexbox/Grid to parent containers.
3.  **Spacing & Sizing:** Apply Width, Height, Margin, Padding.
4.  **Appearance:** Apply Color, Border, Shadow, Typography.
5.  **Interactive:** Add Hover/Focus states (often missing in static design).

## 5. Flutter Specifics
*   `Auto Layout` (Figma) -> `Column` or `Row` with `MainAxisAlignment`.
*   `Constraints` -> `Expanded`, `Flexible`, or `SizedBox`.
*   `Shadows` -> `BoxShadow` (watch out for performance cost).
