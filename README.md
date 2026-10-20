# SteerDistill case stories

This branch contains the static case-study website and its source data.
Training and evaluation code live on the [`main` branch](https://github.com/ustccuigm/bitdistill/tree/main).
See the [project README](https://github.com/ustccuigm/bitdistill/blob/main/README.md)
for the three model families and five benchmark routes, and the
[setup guide](https://github.com/ustccuigm/bitdistill/blob/main/docs/benchmarks.md)
for model checkpoints, data, training, and evaluation commands.

Serve this directory with any static HTTP server. No build step is required.
GitHub Pages can publish the root of this `gh-pages` branch.

The homepage and `contents.html` present all 40 cases as a paginated
comparison. Each case has task, comparison, and conclusion views; readers can
switch between Ours/BF16 and five baselines. Reasons for correct and incorrect
outcomes are highlighted alongside selected actions and reasoning excerpts.
There is no full-trajectory viewer.

`cases.js` and `cases.css` implement the viewer. `data/case-slides.json` maps
display numbers 1-40 to stable task IDs and identical `source_case` numbers.
The existing 40 articles in `stories/` and their records under `data/cases/`
remain unchanged. No-call comparisons identify the user turn, show the BF16
comparison action and the model's actual reply, and distinguish omitted calls
from appropriate clarification or refusal to use an unsuitable tool.

## Digital-world demonstrations

The homepage Demo section introduces two evidence-led stories: updating a phone number and copying a redemption code. Each story includes selected screenshots, the original teacher guidance, a correction video, and independent execution by the step-8 quantized student. All four videos and the pages work offline. Both tasks passed three same-initial-state unguided repetitions; they are training-task demonstrations, not held-out evaluation.
