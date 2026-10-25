# Experiment data and figures

[Project overview](../../README.md)

Run the commands below from the repository root.

The result tables cover three model families and five benchmarks. Metric
definitions and evaluation settings are listed with the [evaluation guide](../evaluation/README.md).

Organized [experiment data and figures](https://github.com/ustccuigm/bitdistill/tree/gh-pages/experiments)
and the existing [40-case collection](https://github.com/ustccuigm/bitdistill/tree/gh-pages/data/cases)
are maintained on `gh-pages`. The `main` branch contains the implementation,
plotting scripts, and documentation, without duplicating these datasets.
Plot the quantitative results without running model inference:

```bash
python -m pip install -r requirements/figures.txt
git fetch origin gh-pages
git worktree add --detach ../bitdistill-pages origin/gh-pages
python scripts/figures/plot_results.py \
  --data ../bitdistill-pages/experiments/data \
  --output ../bitdistill-pages/experiments/figures
```

See [figure generation](../../docs/figures.md) for data checks and PDF-coordinate extraction.
