"""Command-line access to native benchmark datasets and student evaluation."""
import sys


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in {"export", "evaluate"}:
        raise SystemExit("usage: python -m steerdistill.benchmarks {export|evaluate} [options]")
    if sys.argv.pop(1) == "export":
        from .prepare_sdar_tasks import main as run
    else:
        from .evaluate_sdar import main as run
    run()


if __name__ == "__main__":
    main()
