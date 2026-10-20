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
The case comparison shows selected evidence rather than full trajectories.

`cases.js` and `cases.css` implement the viewer. `data/case-slides.json` maps
display numbers 1-40 to stable task IDs and identical `source_case` numbers.
The existing 40 articles in `stories/` and their records under `data/cases/`
remain unchanged. No-call comparisons identify the user turn, show the BF16
comparison action and the model's actual reply, and distinguish omitted calls
from appropriate clarification or refusal to use an unsuitable tool.

## Digital-world demonstrations

The homepage Demo section presents two interactive recorded trajectories:
updating a phone number and copying a redemption code. `demo-player.js` and
`demo-player.css` provide step selection, previous/next navigation, automatic
playback, recorded thinking, teacher guidance, and before/after screenshots.
`demos/player/trajectories.json` contains 70 steps across the original attempts,
guided retries, and independent runs. Screenshot frames are deduplicated under
`demos/player/frames/`.

Animated tap markers use recorded executed coordinates. They are visual
overlays, not a live application or newly generated model actions. A final step
without a following screenshot retains the last frame and displays the
environment result separately. Existing videos and background articles remain
available. Serve over HTTP so the browser can load the trajectory JSON.

Both tasks passed three same-initial-state unguided repetitions; they are
training-task demonstrations, not held-out evaluation. The player shows one
recorded independent run for each task.
