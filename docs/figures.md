# Experiment Figures

Code lives on `main`; organized experiment tables, rendered figures, and the
existing case collection live on `gh-pages`. The case files are reused in place
under `data/cases/`, not copied into the code branch or the experiment directory.

## Generate figures

From the `main` checkout, create a separate checkout of the published data:

```bash
git fetch origin gh-pages
git worktree add --detach ../bitdistill-pages origin/gh-pages
python -m pip install -r requirements/figures.txt
python scripts/figures/plot_results.py \
  --data ../bitdistill-pages/experiments/data \
  --output ../bitdistill-pages/experiments/figures
```

If that checkout already exists, use its path instead of adding another one.
Both paths are explicit so generated artifacts do not enter the code branch.
The command produces eight PDF/PNG figure pairs and an input-hash manifest.
No model inference or teacher API is required.

## Check the collection

```bash
STEER_PAGES_ROOT=../bitdistill-pages \
  python -B -m unittest discover -s tests -p test_experiment_data.py -v
```

Checks cover table dimensions, numeric bounds, averages, figure coordinates,
and the existing 40-by-7 case layout. These data-dependent tests are skipped
when `STEER_PAGES_ROOT` is unset; an explicitly configured missing or invalid
checkout fails the tests.

## Extract paper coordinates

The collection's `experiments/manifest.json` identifies the paper snapshot,
units, and table/figure correspondence. To repeat the vector-coordinate
extraction using the matching PDF:

```bash
python scripts/figures/extract_paper_coordinates.py \
  --pdf /path/to/10718_SteerDistill_Quantizing_.pdf \
  --output ../bitdistill-pages/experiments/data
```

The extractor checks the PDF SHA256 before applying its coordinate map. The
collection contains displayed summary values, not reconstructed seed outcomes.
See the [collection documentation](https://github.com/ustccuigm/bitdistill/blob/gh-pages/experiments/README.md)
for figure labels and source details.
