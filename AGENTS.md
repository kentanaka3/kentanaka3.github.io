# Agent Guide

## Project

This repository is a dependency-free GitHub Pages site (https://kentanaka3.github.io/) for Ken Tanaka Hernandez (健 田中). It combines:

- A static portfolio and CV page in `index.html`.
- Canvas flock simulation behavior in `web/js/index.js`.
- Site styling in `web/css/index.css`.
- Editable CV source in `doc/cv.tex`.
- The published CV artifact at the repository root: `cv.pdf`.

The flock observer is deterministic and browser-only.

## Local development

No package installation is required. Preview the site with:

```sh
python3 -m http.server 8000
```

Then open `http://localhost:8000/`.

## CV workflow

Edit `doc/cv.tex`, then regenerate and publish the root PDF:

```sh
./doc/latex.sh --compile
```

Compile and remove LaTeX intermediates together:

```sh
./doc/latex.sh --compile --clean
```

Clean only generated files under `doc/`:

```sh
./doc/latex.sh --clean
```

The script preserves `doc/cv.tex` and the public root `cv.pdf`. Run the compile command after CV edits and check that the generated PDF is updated.

## Editing guidance

- Keep the site readable without JavaScript; the narrative and CV are ordinary HTML.
- Preserve existing section IDs, navigation anchors, accessibility labels, and external-link `rel` attributes.
- Keep CV links and important achievements synchronized between `index.html` and `doc/cv.tex` when both versions contain the same information.
- Keep edits focused; do not add a framework, package manager, external fonts, or server-side behavior for small changes.
- Use the existing visual and typographic conventions. Avoid unrelated reformatting.

## Deployment

GitHub Pages deploys from `main`. The public deployment includes only:

- `index.html`
- `web/css/index.css`
- `web/js/index.js`
- `web/img/fish.png`
- `cv.pdf`

Before finishing a change, run the narrowest relevant check: compile the CV for LaTeX edits, or preview the static site for HTML/CSS/JavaScript edits.
