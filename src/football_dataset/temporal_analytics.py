from __future__ import annotations

import json
from pathlib import Path
from statistics import mean, median
from zipfile import ZipFile

from football_dataset.pilot import event_frame_from_info
from football_dataset.reference_analytics import (
    _csv_bool,
    _read_csv,
    _write_csv,
    _write_json,
)


BASE_FIELDS = (
    "protocol_id",
    "source_protocol_id",
    "clip_id",
    "split",
    "official_anchor_action",
    "event_frame",
    "event_second",
    "window_name",
    "start_offset_seconds",
    "end_offset_seconds",
    "planned_frame_count",
    "observed_frame_count",
    "temporal_coverage",
    "temporally_complete",
)

TEAM_FIELDS = (
    "shape_eligible_frames",
    "shape_frame_coverage",
    "shape_summary_eligible",
    "median_width_m",
    "median_depth_m",
    "median_centroid_x",
    "median_centroid_y",
    "median_compactness_m",
    "ball_eligible_frames",
    "ball_frame_coverage",
    "ball_summary_eligible",
    "median_nearest_athlete_to_ball_m",
    "minimum_nearest_athlete_to_ball_m",
    "mean_athletes_within_10m_of_ball",
    "delta_median_width_m_from_previous_window",
    "delta_median_depth_m_from_previous_window",
    "delta_median_compactness_m_from_previous_window",
    "delta_median_nearest_ball_distance_m_from_previous_window",
    "delta_mean_athletes_within_10m_from_previous_window",
)

WINDOW_FIELDS = BASE_FIELDS + tuple(
    f"{team}_{field}" for team in ("left", "right") for field in TEAM_FIELDS
)

SHAPE_INPUTS = {
    "median_width_m": "width_m",
    "median_depth_m": "depth_m",
    "median_centroid_x": "centroid_x",
    "median_centroid_y": "centroid_y",
    "median_compactness_m": "compactness_m",
}

DELTA_INPUTS = {
    "delta_median_width_m_from_previous_window": ("median_width_m", "shape"),
    "delta_median_depth_m_from_previous_window": ("median_depth_m", "shape"),
    "delta_median_compactness_m_from_previous_window": (
        "median_compactness_m",
        "shape",
    ),
    "delta_median_nearest_ball_distance_m_from_previous_window": (
        "median_nearest_athlete_to_ball_m",
        "ball",
    ),
    "delta_mean_athletes_within_10m_from_previous_window": (
        "mean_athletes_within_10m_of_ball",
        "ball",
    ),
}


def _window_for_offset(offset_seconds: float, windows: list[dict]) -> str | None:
    for window in windows:
        if window["start_offset_seconds"] <= offset_seconds < window["end_offset_seconds"]:
            return window["name"]
    return None


def _rounded(value: float) -> float:
    return round(value, 6)


def _coverage(eligible_count: int, observed_count: int) -> float:
    return _rounded(eligible_count / observed_count) if observed_count else 0.0


def _eligible(
    eligible_count: int,
    observed_count: int,
    temporally_complete: bool,
    minimum_coverage: float,
) -> bool:
    return (
        temporally_complete
        and observed_count > 0
        and eligible_count / observed_count >= minimum_coverage
    )


def _median(rows: list[dict[str, str]], field: str) -> float:
    return _rounded(median(float(row[field]) for row in rows))


def _build_window_row(
    *,
    config: dict,
    clip_id: str,
    action: str,
    event_frame: int,
    window: dict,
    frame_rows: list[dict[str, str]],
) -> dict:
    frame_rate = int(config["frame_rate"])
    planned = round(
        (window["end_offset_seconds"] - window["start_offset_seconds"])
        * frame_rate
    )
    observed = len(frame_rows)
    complete = observed == planned
    row: dict = {
        "protocol_id": config["protocol_id"],
        "source_protocol_id": config["source_protocol_id"],
        "clip_id": clip_id,
        "split": config["split"],
        "official_anchor_action": action,
        "event_frame": event_frame,
        "event_second": _rounded((event_frame - 1) / frame_rate),
        "window_name": window["name"],
        "start_offset_seconds": window["start_offset_seconds"],
        "end_offset_seconds": window["end_offset_seconds"],
        "planned_frame_count": planned,
        "observed_frame_count": observed,
        "temporal_coverage": _coverage(observed, planned),
        "temporally_complete": complete,
    }

    minimum_coverage = float(config["minimum_metric_frame_coverage"])
    for team in ("left", "right"):
        shape_rows = [
            frame_row
            for frame_row in frame_rows
            if _csv_bool(frame_row[f"{team}_shape_eligible"])
        ]
        ball_rows = [
            frame_row
            for frame_row in frame_rows
            if _csv_bool(frame_row[f"{team}_ball_distance_eligible"])
        ]
        shape_ok = _eligible(len(shape_rows), observed, complete, minimum_coverage)
        ball_ok = _eligible(len(ball_rows), observed, complete, minimum_coverage)
        row[f"{team}_shape_eligible_frames"] = len(shape_rows)
        row[f"{team}_shape_frame_coverage"] = _coverage(len(shape_rows), observed)
        row[f"{team}_shape_summary_eligible"] = shape_ok
        for output_field, input_suffix in SHAPE_INPUTS.items():
            row[f"{team}_{output_field}"] = (
                _median(shape_rows, f"{team}_{input_suffix}") if shape_ok else ""
            )

        row[f"{team}_ball_eligible_frames"] = len(ball_rows)
        row[f"{team}_ball_frame_coverage"] = _coverage(len(ball_rows), observed)
        row[f"{team}_ball_summary_eligible"] = ball_ok
        if ball_ok:
            distances = [
                float(frame_row[f"nearest_{team}_athlete_to_ball_m"])
                for frame_row in ball_rows
            ]
            local_counts = [
                float(frame_row[f"{team}_athletes_within_10m_of_ball"])
                for frame_row in ball_rows
            ]
            row[f"{team}_median_nearest_athlete_to_ball_m"] = _rounded(
                median(distances)
            )
            row[f"{team}_minimum_nearest_athlete_to_ball_m"] = _rounded(
                min(distances)
            )
            row[f"{team}_mean_athletes_within_10m_of_ball"] = _rounded(
                mean(local_counts)
            )
        else:
            row[f"{team}_median_nearest_athlete_to_ball_m"] = ""
            row[f"{team}_minimum_nearest_athlete_to_ball_m"] = ""
            row[f"{team}_mean_athletes_within_10m_of_ball"] = ""

        for delta_field in DELTA_INPUTS:
            row[f"{team}_{delta_field}"] = ""
    return row


def _add_deltas(rows: list[dict]) -> None:
    previous: dict | None = None
    for row in rows:
        if previous is not None:
            for team in ("left", "right"):
                for delta_field, (metric_field, family) in DELTA_INPUTS.items():
                    current_ok = row[f"{team}_{family}_summary_eligible"] is True
                    previous_ok = previous[f"{team}_{family}_summary_eligible"] is True
                    if current_ok and previous_ok:
                        row[f"{team}_{delta_field}"] = _rounded(
                            float(row[f"{team}_{metric_field}"])
                            - float(previous[f"{team}_{metric_field}"])
                        )
        previous = row


def _generate_window_metrics(project_root: Path, config_filename: str) -> dict:
    config = json.loads(
        (project_root / "config" / config_filename).read_text(
            encoding="utf-8"
        )
    )
    manifest_rows = [
        row
        for row in _read_csv(project_root / "data" / "processed" / "manifest.csv")
        if row["split"] == config["split"]
    ]
    manifest_rows.sort(key=lambda row: row["clip_id"])
    if len(manifest_rows) != config["expected_clip_count"]:
        raise ValueError(
            f"{config['split']} manifest count does not match the window protocol"
        )

    archives: dict[Path, ZipFile] = {}
    output_rows: list[dict] = []
    try:
        for source in manifest_rows:
            clip_id = source["clip_id"]
            archive_path = project_root / source["archive_path"]
            archive = archives.setdefault(archive_path, ZipFile(archive_path))
            info = json.loads(archive.read(source["label_member"]))["info"]
            event_frame = event_frame_from_info(info)
            frame_rows = _read_csv(
                project_root
                / config["outputs"]["source_frame_metrics"]
                / f"{clip_id}.csv"
            )
            if any(row["protocol_id"] != config["source_protocol_id"] for row in frame_rows):
                raise ValueError(f"{clip_id} frame metrics use another protocol")

            rows_for_clip = []
            for window in config["windows"]:
                selected = [
                    row
                    for row in frame_rows
                    if _window_for_offset(
                        (int(row["frame"]) - event_frame) / config["frame_rate"],
                        [window],
                    )
                    is not None
                ]
                rows_for_clip.append(
                    _build_window_row(
                        config=config,
                        clip_id=clip_id,
                        action=source["action_class"],
                        event_frame=event_frame,
                        window=window,
                        frame_rows=selected,
                    )
                )
            _add_deltas(rows_for_clip)
            output_rows.extend(rows_for_clip)
            print(f"analytics windows: wrote {clip_id}", flush=True)
    finally:
        for archive in archives.values():
            archive.close()

    output_path = project_root / config["outputs"]["window_metrics"]
    _write_csv(output_path, WINDOW_FIELDS, output_rows)
    window_summaries = []
    for window in config["windows"]:
        rows = [row for row in output_rows if row["window_name"] == window["name"]]
        window_summaries.append(
            {
                "window_name": window["name"],
                "rows": len(rows),
                "temporally_complete_clips": sum(
                    row["temporally_complete"] is True for row in rows
                ),
                "both_team_shape_eligible_clips": sum(
                    row["left_shape_summary_eligible"] is True
                    and row["right_shape_summary_eligible"] is True
                    for row in rows
                ),
                "both_team_ball_eligible_clips": sum(
                    row["left_ball_summary_eligible"] is True
                    and row["right_ball_summary_eligible"] is True
                    for row in rows
                ),
            }
        )
    rows_by_clip = {
        clip_id: [row for row in output_rows if row["clip_id"] == clip_id]
        for clip_id in sorted({row["clip_id"] for row in output_rows})
    }
    all_shape_clips = [
        clip_id
        for clip_id, rows in rows_by_clip.items()
        if all(
            row["left_shape_summary_eligible"] is True
            and row["right_shape_summary_eligible"] is True
            for row in rows
        )
    ]
    all_ball_clips = [
        clip_id
        for clip_id, rows in rows_by_clip.items()
        if all(
            row["left_ball_summary_eligible"] is True
            and row["right_ball_summary_eligible"] is True
            for row in rows
        )
    ]
    all_metric_clips = sorted(set(all_shape_clips) & set(all_ball_clips))
    summary = {
        "protocol_id": config["protocol_id"],
        "status": "complete-pending-validation",
        "provenance": (
            "derived from hidden SoccerNet-GSR annotations and "
            f"{config['split']} frame metrics"
        ),
        "split": config["split"],
        "clip_count": len(manifest_rows),
        "row_count": len(output_rows),
        "minimum_metric_frame_coverage": config["minimum_metric_frame_coverage"],
        "windows": config["windows"],
        "window_summaries": window_summaries,
        "cross_window_eligibility": {
            "clips_with_both_team_shape_in_all_windows": all_shape_clips,
            "clips_with_both_team_ball_metrics_in_all_windows": all_ball_clips,
            "clips_with_all_direct_metrics_in_all_windows": all_metric_clips,
        },
        "limitations": [
            "Team labels remain left/right; possession and attacking direction are not inferred.",
            "A window aggregate is blank unless its temporal and metric eligibility checks pass.",
            "Window medians describe visible annotated players, not complete off-screen team shapes.",
        ],
    }
    _write_json(project_root / config["outputs"]["summary"], summary)
    return summary


def _validate_window_metrics(project_root: Path, config_filename: str) -> dict:
    config = json.loads(
        (project_root / "config" / config_filename).read_text(
            encoding="utf-8"
        )
    )
    rows = _read_csv(project_root / config["outputs"]["window_metrics"])
    errors: list[str] = []
    expected_rows = config["expected_clip_count"] * len(config["windows"])
    if len(rows) != expected_rows:
        errors.append(f"found {len(rows)} rows instead of {expected_rows}")

    expected_windows = [window["name"] for window in config["windows"]]
    clip_ids = sorted({row["clip_id"] for row in rows})
    if len(clip_ids) != config["expected_clip_count"]:
        errors.append("clip count does not match the protocol")
    for clip_id in clip_ids:
        names = [row["window_name"] for row in rows if row["clip_id"] == clip_id]
        if names != expected_windows:
            errors.append(f"{clip_id} does not have the ordered configured windows")

    aggregate_fields = {
        "shape": tuple(SHAPE_INPUTS),
        "ball": (
            "median_nearest_athlete_to_ball_m",
            "minimum_nearest_athlete_to_ball_m",
            "mean_athletes_within_10m_of_ball",
        ),
    }
    for row in rows:
        if row["protocol_id"] != config["protocol_id"]:
            errors.append(f"{row['clip_id']} contains another window protocol")
        if row["source_protocol_id"] != config["source_protocol_id"]:
            errors.append(f"{row['clip_id']} contains another source protocol")
        observed = int(row["observed_frame_count"])
        planned = int(row["planned_frame_count"])
        complete = _csv_bool(row["temporally_complete"])
        if complete != (observed == planned):
            errors.append(f"{row['clip_id']} {row['window_name']} temporal flag mismatch")
        for team in ("left", "right"):
            for family, fields in aggregate_fields.items():
                eligible = _csv_bool(row[f"{team}_{family}_summary_eligible"])
                values = [row[f"{team}_{field}"] for field in fields]
                if eligible and any(value == "" for value in values):
                    errors.append(
                        f"{row['clip_id']} {row['window_name']} incomplete eligible {team} {family}"
                    )
                if not eligible and any(value != "" for value in values):
                    errors.append(
                        f"{row['clip_id']} {row['window_name']} populated ineligible {team} {family}"
                    )
                coverage = float(row[f"{team}_{family}_frame_coverage"])
                if not 0 <= coverage <= 1:
                    errors.append(
                        f"{row['clip_id']} {row['window_name']} invalid {team} {family} coverage"
                    )

    for clip_id in clip_ids:
        clip_rows = [row for row in rows if row["clip_id"] == clip_id]
        previous: dict[str, str] | None = None
        for row in clip_rows:
            for team in ("left", "right"):
                if _csv_bool(row[f"{team}_shape_summary_eligible"]):
                    width = float(row[f"{team}_median_width_m"])
                    depth = float(row[f"{team}_median_depth_m"])
                    compactness = float(row[f"{team}_median_compactness_m"])
                    if not 0 <= width <= 68 or not 0 <= depth <= 105 or compactness < 0:
                        errors.append(
                            f"{clip_id} {row['window_name']} invalid {team} shape aggregate"
                        )
                if _csv_bool(row[f"{team}_ball_summary_eligible"]):
                    nearest = float(row[f"{team}_median_nearest_athlete_to_ball_m"])
                    minimum = float(row[f"{team}_minimum_nearest_athlete_to_ball_m"])
                    local = float(row[f"{team}_mean_athletes_within_10m_of_ball"])
                    if nearest < 0 or minimum < 0 or local < 0:
                        errors.append(
                            f"{clip_id} {row['window_name']} invalid {team} ball aggregate"
                        )

                for delta_field, (metric_field, family) in DELTA_INPUTS.items():
                    value = row[f"{team}_{delta_field}"]
                    should_exist = (
                        previous is not None
                        and _csv_bool(row[f"{team}_{family}_summary_eligible"])
                        and _csv_bool(previous[f"{team}_{family}_summary_eligible"])
                    )
                    if should_exist:
                        expected = float(row[f"{team}_{metric_field}"]) - float(
                            previous[f"{team}_{metric_field}"]
                        )
                        if value == "" or abs(float(value) - expected) > 0.000002:
                            errors.append(
                                f"{clip_id} {row['window_name']} invalid {team} delta {delta_field}"
                            )
                    elif value != "":
                        errors.append(
                            f"{clip_id} {row['window_name']} unexpected {team} delta {delta_field}"
                        )
            previous = row

    summary = json.loads(
        (project_root / config["outputs"]["summary"]).read_text(encoding="utf-8")
    )
    incomplete = [
        {"clip_id": row["clip_id"], "window_name": row["window_name"]}
        for row in rows
        if not _csv_bool(row["temporally_complete"])
    ]
    report = {
        "protocol_id": config["protocol_id"],
        "status": "pass" if not errors else "fail",
        "verified_clip_count": len(clip_ids),
        "verified_window_rows": len(rows),
        "errors": errors,
        "temporally_incomplete_windows": incomplete,
        "window_summaries": summary["window_summaries"],
        "cross_window_eligibility": summary["cross_window_eligibility"],
    }
    if not errors:
        summary["status"] = "complete-validated"
        _write_json(project_root / config["outputs"]["summary"], summary)
    _write_json(project_root / config["outputs"]["validation_report"], report)
    return report


def generate_train_window_metrics(project_root: Path) -> dict:
    return _generate_window_metrics(project_root, "temporal_windows_train.json")


def validate_train_window_metrics(project_root: Path) -> dict:
    return _validate_window_metrics(project_root, "temporal_windows_train.json")


def generate_valid_window_metrics(project_root: Path) -> dict:
    return _generate_window_metrics(project_root, "temporal_windows_valid.json")


def validate_valid_window_metrics(project_root: Path) -> dict:
    return _validate_window_metrics(project_root, "temporal_windows_valid.json")


def generate_test_window_metrics(project_root: Path) -> dict:
    return _generate_window_metrics(project_root, "temporal_windows_test.json")


def validate_test_window_metrics(project_root: Path) -> dict:
    return _validate_window_metrics(project_root, "temporal_windows_test.json")
