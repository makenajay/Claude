# Build sources

These files regenerate `ANOVA_from_First_Principles_2nd_edition.pdf`.

- `compute.py`: recomputes every statistic and draws all figures (SVG)
- `content1-4.html`, `cover.html`: chapter text; `[[...]]` placeholders are filled from the computed results
- `build.py`, `render.js`, `merge.py`: fill placeholders, typeset maths with KaTeX, print to PDF with Chromium
- `make.sh`: runs the whole pipeline

Requirements: Python (numpy, scipy, matplotlib, pymupdf), Node (`npm i katex @fontsource/inter @fontsource/source-serif-4 @fontsource/jetbrains-mono @fontsource/fraunces`, plus Playwright), and the Inter font installed system-wide.
