# SteerDistill case stories

This branch contains the static case-study website and its source data.
Training and evaluation code live on the `main` branch.

Serve this directory with any static HTTP server. No build step is required.
GitHub Pages can publish the root of this `gh-pages` branch.

The website presents 40 individually titled articles. Each article follows the
original task, BF16 and Ours, baseline divergence evidence, and interpretation.
Only short reasoning excerpts and selected actions appear on the website;
there is no full-trajectory viewer or raw-data download interface.

`index.html` opens the first case, `contents.html` lists all cases, and
`stories/` contains the individual articles. `story.css` defines the layout.
Original records under `data/` are retained as source material.
