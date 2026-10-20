# Experiment Data and Figures

整理的数据和实验图片保存在 `gh-pages`；绘图代码保存在 `main`。

```text
experiments/
  data/            Experiment tables and figure coordinates in CSV format
  figures/         PDF and PNG figures
  manifest.json    Paper version, units, and table/figure correspondence
data/cases/        Existing 40-case collection, shared with the website
```

## Case collection

All case files remain under [data/cases/](../data/cases/).
[case_index.json](../data/case_index.json)
maps case numbers to task IDs; [results.csv](../data/results.csv) lists the
selected outcomes. Each case contains the task, ground truth, analysis, and
seven method directories with actions, trajectories, readable transcripts,
scores, and sampling metadata.

These 40 cases were selected for their outcome pattern: BF16 and Ours pass,
while the five comparison methods fail in the selected trajectories. They
are a qualitative collection, not a benchmark success-rate estimate. Some
failures concern exact string matching; each case's explanation retains that
distinction. Case numbering belongs to this collection, not to the paper's
figure numbering. Existing collection records and content hashes remain under
[data/](../data/); no second case collection is created here.
Benchmark attribution and component terms are listed in
[third-party notices](https://github.com/ustccuigm/bitdistill/blob/main/docs/third_party_notices.md).

## Experiment tables

| File | Paper location | Contents |
| --- | --- | --- |
| [benchmark_results.csv](data/benchmark_results.csv) | Table 1 | Three models, five benchmarks, and the reported precision settings |
| [ablations.csv](data/ablations.csv) | Table 2 | BFCL V4 overall and category scores |
| [training_settings.csv](data/training_settings.csv) | Table 4 | Training settings stated in this paper version |
| [additional_metrics.csv](data/additional_metrics.csv) | Table 5 | tau2 Pass@4, WebShop Task Score, and seven Search QA datasets |
| [inference_statistics.csv](data/inference_statistics.csv) | Table 6 | Tokens, interaction steps, and tool calls per successful task |
| [training_efficiency.csv](data/training_efficiency.csv) | Figure 3a | GPU hours, mean score, and the displayed uncertainty band |
| [inference_efficiency.csv](data/inference_efficiency.csv) | Figures 3b and 4 | Output tokens and the displayed performance coordinates |
| [reasoning_prefix.csv](data/reasoning_prefix.csv) | Figure 8 | Two reasoning-prefix intervention matrices |

Tables retain the paper's displayed numerical precision. Token counts in
Table 6 convert `K` to thousands without adding precision. Figures 3 and 4
are decoded from PDF vector coordinates; the extraction script checks the PDF
SHA256 before using its coordinate map. Their CSVs contain plotted summary
values, not separate seed outcomes. Figure 8 retains the labels printed in the
paper. Figure 1's quantitative comparisons reuse the same result tables and
efficiency data; Figure 2 is a method illustration.

Figure 4's axes say `Pass@1`, whereas its caption says `Pass@4`. The CSV and
plot follow the axes; this discrepancy is recorded in the manifest. Table 4
describes the pinned paper version, not a live configuration dump.

## Plot figures

Run the plotting code from a `main` checkout, with a separate `gh-pages`
checkout at `../bitdistill-pages`:

```bash
python -m pip install -r requirements/figures.txt
python scripts/figures/plot_results.py \
  --data ../bitdistill-pages/experiments/data \
  --output ../bitdistill-pages/experiments/figures
```

The command creates eight PDF/PNG figure pairs under `experiments/figures/`:
model and benchmark comparisons, ablations, additional metrics, training and
inference efficiency, reasoning-prefix matrices, and inference statistics.
The layouts are generated from the CSVs; no training or teacher API is needed.

Choose another `--output` directory to keep the published figures unchanged.
Checkout instructions and the plotting code are documented in
[figure generation](https://github.com/ustccuigm/bitdistill/blob/main/docs/figures.md).

To repeat the coordinate extraction using the matching paper PDF:

```bash
python scripts/figures/extract_paper_coordinates.py \
  --pdf /path/to/10718_SteerDistill_Quantizing_.pdf \
  --output ../bitdistill-pages/experiments/data
```

## Check the data

```bash
STEER_PAGES_ROOT=../bitdistill-pages \
  python -B -m unittest discover -s tests -p test_experiment_data.py -v
```

Checks cover table shapes, numeric bounds, reported averages, plotted ranges,
and the 40-by-7 case layout. Figure generation also records input hashes and
the Matplotlib version in `figures/manifest.json`.
