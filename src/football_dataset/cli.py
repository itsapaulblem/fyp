from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

from football_dataset.manifest import build_manifest, validate_manifest
from football_dataset.analytics_index import (
    build_reference_analytics_index,
    validate_reference_analytics_index,
)
from football_dataset.pilot import compare_pilot, prepare_pilot_inputs, run_pilot
from football_dataset.recognition import (
    RECOGNITION_CONDITIONS,
    prepare_recognition_inputs,
    run_recognition_gate,
    summarize_recognition_gate,
)
from football_dataset.reference_analytics import (
    run_reference_analytics_pilot,
    run_reference_analytics_test,
    run_reference_analytics_train,
    run_reference_analytics_valid,
    validate_reference_analytics_pilot,
    validate_reference_analytics_test,
    validate_reference_analytics_train,
    validate_reference_analytics_valid,
)
from football_dataset.review_video import build_review_videos
from football_dataset.claim_thresholds import (
    generate_train_metric_thresholds,
    validate_train_metric_thresholds,
)
from football_dataset.temporal_analytics import (
    generate_test_window_metrics,
    generate_train_window_metrics,
    generate_valid_window_metrics,
    validate_test_window_metrics,
    validate_train_window_metrics,
    validate_valid_window_metrics,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"
CONFIG_PATH = PROJECT_ROOT / "config" / "dataset.json"


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def download_gamestate() -> None:
    from SoccerNet.Downloader import SoccerNetDownloader

    config = load_config()["sources"]["gamestate"]
    destination = RAW_ROOT / "gamestate"
    destination.mkdir(parents=True, exist_ok=True)
    downloader = SoccerNetDownloader(LocalDirectory=str(destination))
    downloader.downloadDataTask(task=config["task"], split=config["splits"])


def download_tracking() -> None:
    from SoccerNet.Downloader import SoccerNetDownloader

    config = load_config()["sources"]["tracking"]
    destination = RAW_ROOT / "tracking"
    destination.mkdir(parents=True, exist_ok=True)
    password = os.environ.get("SOCCERNET_PASSWORD")
    errors: list[str] = []

    for task in config["tasks"]:
        try:
            downloader = SoccerNetDownloader(LocalDirectory=str(destination))
            if password:
                downloader.password = password
            downloader.downloadDataTask(task=task, split=config["splits"])
            return
        except Exception as exc:  # Official SDK errors vary by backend/version.
            errors.append(f"{task}: {exc}")

    details = "\n".join(errors)
    raise RuntimeError(f"All official Tracking download variants failed:\n{details}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare the official SoccerNet coaching-evaluation sources."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    download = subparsers.add_parser("download", help="Download an official source")
    download.add_argument(
        "--source", choices=("gamestate", "tracking", "all"), required=True
    )
    subparsers.add_parser("manifest", help="Build metadata directly from the ZIPs")
    subparsers.add_parser("validate", help="Validate the generated dataset manifest")
    subparsers.add_parser(
        "pilot-prepare", help="Build the audited 16-frame pilot sampling manifest"
    )
    pilot_run = subparsers.add_parser(
        "pilot-run", help="Run Qwen on prepared pilot frame strategies"
    )
    pilot_run.add_argument(
        "--strategy",
        choices=("uniform", "event_centered", "both"),
        default="both",
    )
    pilot_run.add_argument("--limit", type=int)
    pilot_run.add_argument("--overwrite", action="store_true")
    pilot_run.add_argument("--timeout", type=int, default=900)
    subparsers.add_parser(
        "pilot-compare", help="Create a technical comparison of completed pilot runs"
    )
    recognition_prepare = subparsers.add_parser(
        "recognition-prepare", help="Prepare an isolated recognition input condition"
    )
    recognition_prepare.add_argument(
        "--condition", choices=RECOGNITION_CONDITIONS, required=True
    )
    recognition_run = subparsers.add_parser(
        "recognition-run", help="Run a configured recognition-only condition"
    )
    recognition_run.add_argument(
        "--condition", choices=RECOGNITION_CONDITIONS, default="uniform16"
    )
    recognition_run.add_argument("--limit", type=int)
    recognition_run.add_argument("--overwrite", action="store_true")
    recognition_run.add_argument("--timeout", type=int, default=900)
    recognition_summarize = subparsers.add_parser(
        "recognition-summarize",
        help="Summarize recognition runs without replacing human review",
    )
    recognition_summarize.add_argument(
        "--condition", choices=RECOGNITION_CONDITIONS, default="uniform16"
    )
    review_videos = subparsers.add_parser(
        "review-videos", help="Convert selected SoccerNet JPEG sequences to local MP4s"
    )
    review_videos.add_argument("--limit", type=int)
    review_videos.add_argument("--overwrite", action="store_true")
    subparsers.add_parser(
        "analytics-pilot",
        help="Build direct spatial reference analytics for the configured train clips",
    )
    subparsers.add_parser(
        "analytics-validate",
        help="Validate the generated direct-spatial analytics pilot",
    )
    subparsers.add_parser(
        "analytics-train",
        help="Build direct spatial reference analytics for all 57 train clips",
    )
    subparsers.add_parser(
        "analytics-train-validate",
        help="Run train-wide structural and coverage quality control",
    )
    subparsers.add_parser(
        "analytics-train-windows",
        help="Aggregate train frame metrics into fixed event-relative windows",
    )
    subparsers.add_parser(
        "analytics-train-windows-validate",
        help="Validate train event-relative window summaries",
    )
    for split, count in (("valid", 58), ("test", 49)):
        subparsers.add_parser(
            f"analytics-{split}",
            help=f"Build hidden reference analytics for all {count} {split} clips",
        )
        subparsers.add_parser(
            f"analytics-{split}-validate",
            help=f"Run structural and coverage quality control for {split}",
        )
        subparsers.add_parser(
            f"analytics-{split}-windows",
            help=f"Aggregate {split} frame metrics into fixed event-relative windows",
        )
        subparsers.add_parser(
            f"analytics-{split}-windows-validate",
            help=f"Validate {split} event-relative window summaries",
        )
    subparsers.add_parser(
        "analytics-train-thresholds",
        help="Derive train-only claim-verification metric thresholds",
    )
    subparsers.add_parser(
        "analytics-train-thresholds-validate",
        help="Validate train-only claim-verification thresholds",
    )
    subparsers.add_parser(
        "analytics-index",
        help="Build the hidden 164-clip reference-analytics master index",
    )
    subparsers.add_parser(
        "analytics-index-validate",
        help="Validate the master index, linked files, and quality tiers",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "download":
        if args.source in {"gamestate", "all"}:
            download_gamestate()
        if args.source in {"tracking", "all"}:
            download_tracking()
    elif args.command == "manifest":
        print(json.dumps(build_manifest(PROJECT_ROOT), indent=2))
    elif args.command == "validate":
        print(json.dumps(validate_manifest(PROJECT_ROOT), indent=2))
    elif args.command == "pilot-prepare":
        print(json.dumps(prepare_pilot_inputs(PROJECT_ROOT), indent=2))
    elif args.command == "pilot-run":
        strategies = (
            ("uniform", "event_centered")
            if args.strategy == "both"
            else (args.strategy,)
        )
        written = run_pilot(
            PROJECT_ROOT,
            strategies,
            overwrite=args.overwrite,
            limit=args.limit,
            timeout=args.timeout,
        )
        print(json.dumps({"written": [str(path) for path in written]}, indent=2))
    elif args.command == "pilot-compare":
        print(json.dumps(compare_pilot(PROJECT_ROOT), indent=2))
    elif args.command == "recognition-prepare":
        print(
            json.dumps(
                prepare_recognition_inputs(PROJECT_ROOT, args.condition), indent=2
            )
        )
    elif args.command == "recognition-run":
        written = run_recognition_gate(
            PROJECT_ROOT,
            condition=args.condition,
            overwrite=args.overwrite,
            limit=args.limit,
            timeout=args.timeout,
        )
        print(json.dumps({"written": [str(path) for path in written]}, indent=2))
    elif args.command == "recognition-summarize":
        print(
            json.dumps(
                summarize_recognition_gate(PROJECT_ROOT, args.condition), indent=2
            )
        )
    elif args.command == "review-videos":
        print(
            json.dumps(
                build_review_videos(
                    PROJECT_ROOT,
                    overwrite=args.overwrite,
                    limit=args.limit,
                ),
                indent=2,
            )
        )
    elif args.command == "analytics-pilot":
        print(json.dumps(run_reference_analytics_pilot(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-validate":
        print(json.dumps(validate_reference_analytics_pilot(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-train":
        print(json.dumps(run_reference_analytics_train(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-train-validate":
        print(json.dumps(validate_reference_analytics_train(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-train-windows":
        print(json.dumps(generate_train_window_metrics(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-train-windows-validate":
        print(json.dumps(validate_train_window_metrics(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-valid":
        print(json.dumps(run_reference_analytics_valid(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-valid-validate":
        print(json.dumps(validate_reference_analytics_valid(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-valid-windows":
        print(json.dumps(generate_valid_window_metrics(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-valid-windows-validate":
        print(json.dumps(validate_valid_window_metrics(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-test":
        print(json.dumps(run_reference_analytics_test(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-test-validate":
        print(json.dumps(validate_reference_analytics_test(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-test-windows":
        print(json.dumps(generate_test_window_metrics(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-test-windows-validate":
        print(json.dumps(validate_test_window_metrics(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-train-thresholds":
        print(json.dumps(generate_train_metric_thresholds(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-train-thresholds-validate":
        print(json.dumps(validate_train_metric_thresholds(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-index":
        print(json.dumps(build_reference_analytics_index(PROJECT_ROOT), indent=2))
    elif args.command == "analytics-index-validate":
        print(json.dumps(validate_reference_analytics_index(PROJECT_ROOT), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
