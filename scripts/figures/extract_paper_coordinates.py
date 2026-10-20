"""Recover plotted coordinates from the pinned paper PDF, not from pixel estimates."""
import argparse
import csv
import hashlib
from pathlib import Path


PAPER_SHA256 = "0105ebb9e4df6877c7d97cebade0d4f584ea8dd999c499ec4a1f602482e502bf"
METHODS = ["GPTQ", "EfficientQAT", "BitDistiller", "On-Policy QAD", "QeRL", "Ours", "BF16"]


def vertices(drawing):
    points = []
    for command in drawing["items"]:
        if command[0] != "l":
            raise ValueError("Expected a polyline in the pinned PDF")
        points.extend(command[1:])
    return points


def write_csv(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if hashlib.sha256(args.pdf.read_bytes()).hexdigest() != PAPER_SHA256:
        parser.error("PDF revision differs from the pinned coordinate map")
    import pymupdf
    document = pymupdf.open(args.pdf)
    args.output.mkdir(parents=True, exist_ok=True)
    drawings = document[7].get_drawings()
    # Axis ticks: x=0,16 GPU hours and y=26,27 on Figure 3a.
    x0, x16 = drawings[6]["rect"].x0, drawings[8]["rect"].x0
    y26, y27 = drawings[22]["rect"].y0, drawings[24]["rect"].y0
    score = lambda y: 26 + (y26 - y) / (y26 - y27)
    rows = []
    for method, line, band in (("On-Policy QAD", 45, 3), ("QeRL", 57, 4), ("Ours", 69, 5)):
        means = {round(point.x, 5): point for point in vertices(drawings[line])}
        bounds = vertices(drawings[band])
        if len(means) != 11:
            raise ValueError("Unexpected number of curve points")
        for point in sorted(means.values(), key=lambda value: value.x):
            limits = [score(bound.y) for bound in bounds if abs(bound.x - point.x) < 1e-3]
            rows.append({"method": method, "gpu_hours": round((point.x - x0) / (x16 - x0) * 16),
                         "mean": round(score(point.y), 4), "lower": round(min(limits), 4),
                         "upper": round(max(limits), 4), "evaluation_seeds": 4})
    reference = score(drawings[38]["rect"].y0)
    for hours in (0, 112):
        rows.append({"method": "BF16", "gpu_hours": hours, "mean": round(reference, 4),
                     "lower": "", "upper": "", "evaluation_seeds": ""})
    write_csv(args.output / "training_efficiency.csv", rows)

    # Page, marker indices, and axis-tick drawing indices for Figures 3b and 4.
    panels = [
        (7, "W4A16", "3b", 108, (92, 94), (4000, 5000), (96, 98), (26, 28)),
        (17, "W2A16", "4a", 33, (3, 5), (4000, 5000), (15, 17), (8, 12)),
        (17, "W4A8", "4b", 69, (49, 51), (4000, 5000), (55, 57), (24, 26)),
    ]
    rows = []
    for page, precision, figure, marker, xticks, xvalues, yticks, yvalues in panels:
        paths = document[page].get_drawings()
        x0, x1 = [paths[i]["rect"].x0 for i in xticks]
        y0, y1 = [paths[i]["rect"].y0 for i in yticks]
        for offset, method in enumerate(METHODS):
            path = paths[marker + offset]
            if len(path["items"]) != 8 or path["type"] != "fs":
                raise ValueError("Expected a scatter marker in the pinned PDF")
            rect = path["rect"]
            x, y = (rect.x0 + rect.x1) / 2, (rect.y0 + rect.y1) / 2
            rows.append({"figure": figure, "precision": precision, "method": method,
                         "output_tokens": round(xvalues[0] + (x-x0)/(x1-x0)*(xvalues[1]-xvalues[0])),
                         "pass_at_1": round(yvalues[0] + (y-y0)/(y1-y0)*(yvalues[1]-yvalues[0]), 4)})
    write_csv(args.output / "inference_efficiency.csv", rows)


if __name__ == "__main__":
    main()
