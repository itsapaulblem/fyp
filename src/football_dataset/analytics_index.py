from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from football_dataset.reference_analytics import (
    _csv_bool,
    _read_csv,
    _write_csv,
    _write_json,
)


INDEX_FIELDS = (
    "protocol_id",
    "clip_id",
    "split",
    "action_class",
    "scenario_group",
    "game_id",
    "game_time_start",
    "game_time_stop",
    "frame_rate",
    "frame_count",
    "duration_seconds",
    "annotation_version",
    "archive_path",
    "label_member",
    "frame_member_pattern",
    "video_representation",
    "object_positions_path",
    "frame_metrics_path",
    "coordinate_check_path",
    "window_metrics_path",
    "window_row_key",
    "reference_protocol_id",
    "window_protocol_id",
    "structural_pass",
    "both_team_shape_coverage",
    "shape_coverage_pass",
    "ball_metric_coverage",
    "ball_coverage_pass",
    "ambiguous_ball_frames",
    "missing_pitch_coordinate_annotations",
    "off_pitch_athlete_annotations",
    "implausible_coordinate_annotations",
    "total_window_count",
    "temporally_complete_window_count",
    "both_team_shape_eligible_window_count",
    "both_team_ball_eligible_window_count",
    "all_direct_eligible_window_count",
    "all_windows_temporally_complete",
    "all_windows_shape_eligible",
    "all_windows_ball_eligible",
    "fully_eligible",
    "quality_tier",
    "warnings",
)


def _quality_tier(
    *,
    structural_pass: bool,
    expected_windows: int,
    complete_windows: int,
    shape_windows: int,
    ball_windows: int,
) -> str:
    if not structural_pass:
        return "invalid"
    if (
        complete_windows == expected_windows
        and shape_windows == expected_windows
        and ball_windows == expected_windows
    ):
        return "fully_eligible"
    if shape_windows > 0 or ball_windows > 0:
        return "partially_eligible"
    return "tracking_only"


def _load_config(project_root: Path) -> dict:
    return json.loads(
        (project_root / "config" / "reference_analytics_index.json").read_text(
            encoding="utf-8"
        )
    )


def build_reference_analytics_index(project_root: Path) -> dict:
    config = _load_config(project_root)
    manifest_rows = _read_csv(project_root / "data" / "processed" / "manifest.csv")
    manifest_by_clip = {row["clip_id"]: row for row in manifest_rows}
    expected_windows = int(config["expected_windows_per_clip"])
    output_rows: list[dict] = []

    for split, split_config in config["splits"].items():
        root = Path(split_config["root"])
        qc_rows = _read_csv(project_root / root / split_config["quality_control"])
        window_path = root / split_config["window_metrics"]
        window_rows = _read_csv(project_root / window_path)
        windows_by_clip: dict[str, list[dict[str, str]]] = {}
        for row in window_rows:
            windows_by_clip.setdefault(row["clip_id"], []).append(row)

        for qc in qc_rows:
            clip_id = qc["clip_id"]
            source = manifest_by_clip[clip_id]
            if source["split"] != split or qc["split"] != split:
                raise ValueError(f"{clip_id} split mismatch while building index")
            clip_windows = windows_by_clip.get(clip_id, [])
            complete = sum(_csv_bool(row["temporally_complete"]) for row in clip_windows)
            shape = sum(
                _csv_bool(row["left_shape_summary_eligible"])
                and _csv_bool(row["right_shape_summary_eligible"])
                for row in clip_windows
            )
            ball = sum(
                _csv_bool(row["left_ball_summary_eligible"])
                and _csv_bool(row["right_ball_summary_eligible"])
                for row in clip_windows
            )
            direct = sum(
                _csv_bool(row["left_shape_summary_eligible"])
                and _csv_bool(row["right_shape_summary_eligible"])
                and _csv_bool(row["left_ball_summary_eligible"])
                and _csv_bool(row["right_ball_summary_eligible"])
                for row in clip_windows
            )
            structural = _csv_bool(qc["structural_pass"])
            tier = _quality_tier(
                structural_pass=structural,
                expected_windows=expected_windows,
                complete_windows=complete,
                shape_windows=shape,
                ball_windows=ball,
            )
            output_rows.append(
                {
                    "protocol_id": config["protocol_id"],
                    "clip_id": clip_id,
                    "split": split,
                    "action_class": source["action_class"],
                    "scenario_group": source["scenario_group"],
                    "game_id": source["game_id"],
                    "game_time_start": source["game_time_start"],
                    "game_time_stop": source["game_time_stop"],
                    "frame_rate": source["frame_rate"],
                    "frame_count": source["frame_count"],
                    "duration_seconds": source["duration_seconds"],
                    "annotation_version": source["annotation_version"],
                    "archive_path": source["archive_path"],
                    "label_member": source["label_member"],
                    "frame_member_pattern": source["frame_member_pattern"],
                    "video_representation": source["video_representation"],
                    "object_positions_path": str(root / "object_positions" / f"{clip_id}.csv").replace("\\", "/"),
                    "frame_metrics_path": str(root / "frame_metrics" / f"{clip_id}.csv").replace("\\", "/"),
                    "coordinate_check_path": str(root / "coordinate_checks" / f"{clip_id}.png").replace("\\", "/"),
                    "window_metrics_path": str(window_path).replace("\\", "/"),
                    "window_row_key": clip_id,
                    "reference_protocol_id": split_config["reference_protocol_id"],
                    "window_protocol_id": split_config["window_protocol_id"],
                    "structural_pass": structural,
                    "both_team_shape_coverage": qc["both_team_shape_coverage"],
                    "shape_coverage_pass": _csv_bool(qc["shape_coverage_pass"]),
                    "ball_metric_coverage": qc["ball_metric_coverage"],
                    "ball_coverage_pass": _csv_bool(qc["ball_coverage_pass"]),
                    "ambiguous_ball_frames": qc["ambiguous_ball_frames"],
                    "missing_pitch_coordinate_annotations": qc["missing_pitch_coordinate_annotations"],
                    "off_pitch_athlete_annotations": qc["off_pitch_athlete_annotations"],
                    "implausible_coordinate_annotations": qc["implausible_coordinate_annotations"],
                    "total_window_count": len(clip_windows),
                    "temporally_complete_window_count": complete,
                    "both_team_shape_eligible_window_count": shape,
                    "both_team_ball_eligible_window_count": ball,
                    "all_direct_eligible_window_count": direct,
                    "all_windows_temporally_complete": complete == expected_windows,
                    "all_windows_shape_eligible": shape == expected_windows,
                    "all_windows_ball_eligible": ball == expected_windows,
                    "fully_eligible": tier == "fully_eligible",
                    "quality_tier": tier,
                    "warnings": qc["warnings"],
                }
            )

    split_order = {name: index for index, name in enumerate(config["splits"])}
    output_rows.sort(key=lambda row: (split_order[row["split"]], row["clip_id"]))
    _write_csv(project_root / config["outputs"]["index"], INDEX_FIELDS, output_rows)

    split_summaries = {}
    for split in config["splits"]:
        rows = [row for row in output_rows if row["split"] == split]
        split_summaries[split] = {
            "clip_count": len(rows),
            "frame_count": sum(int(row["frame_count"]) for row in rows),
            "quality_tiers": dict(sorted(Counter(row["quality_tier"] for row in rows).items())),
            "structurally_valid_clips": sum(row["structural_pass"] is True for row in rows),
            "clips_passing_whole_clip_shape_coverage": sum(row["shape_coverage_pass"] is True for row in rows),
            "clips_passing_whole_clip_ball_coverage": sum(row["ball_coverage_pass"] is True for row in rows),
        }
    summary = {
        "protocol_id": config["protocol_id"],
        "status": "complete-pending-validation",
        "provenance": "project-derived index joining the official manifest with hidden reference analytics",
        "evidence_layer": config["evidence_layer"],
        "model_access": config["model_access"],
        "clip_count": len(output_rows),
        "frame_count": sum(int(row["frame_count"]) for row in output_rows),
        "duration_minutes": round(sum(float(row["duration_seconds"]) for row in output_rows) / 60, 3),
        "split_summaries": split_summaries,
        "quality_tiers": dict(sorted(Counter(row["quality_tier"] for row in output_rows).items())),
        "action_distribution": dict(sorted(Counter(row["action_class"] for row in output_rows).items())),
        "implemented_metrics": [
            "team width",
            "team depth",
            "team centroid",
            "team compactness",
            "nearest left/right team athlete to ball",
            "left/right team athletes within 10 metres of ball",
            "event-relative window changes for eligible metrics",
        ],
        "limitations": [
            "Metrics describe visible annotated players and may omit off-screen players.",
            "Team labels remain left/right; possession, attacking direction, and shirt colour are not inferred.",
            "Unavailable measurements remain blank and must not be interpreted as zero.",
            "The index and all linked reference analytics are hidden from the MLLM.",
        ],
    }
    _write_json(project_root / config["outputs"]["summary"], summary)
    return summary


def validate_reference_analytics_index(project_root: Path) -> dict:
    config = _load_config(project_root)
    rows = _read_csv(project_root / config["outputs"]["index"])
    manifest = _read_csv(project_root / "data" / "processed" / "manifest.csv")
    manifest_ids = {row["clip_id"] for row in manifest}
    errors: list[str] = []
    expected_windows = int(config["expected_windows_per_clip"])

    if len(rows) != config["expected_clip_count"]:
        errors.append(f"found {len(rows)} rows instead of {config['expected_clip_count']}")
    clip_ids = [row["clip_id"] for row in rows]
    if len(clip_ids) != len(set(clip_ids)):
        errors.append("index contains duplicate clip IDs")
    if set(clip_ids) != manifest_ids:
        errors.append("index clip IDs do not exactly match the official manifest")

    split_counts = Counter(row["split"] for row in rows)
    if dict(split_counts) != config["expected_split_counts"]:
        errors.append(f"split counts do not match config: {dict(split_counts)}")

    for row in rows:
        clip_id = row["clip_id"]
        if row["protocol_id"] != config["protocol_id"]:
            errors.append(f"{clip_id}: wrong index protocol")
        split_config = config["splits"].get(row["split"])
        if split_config is None:
            errors.append(f"{clip_id}: unknown split")
            continue
        if row["reference_protocol_id"] != split_config["reference_protocol_id"]:
            errors.append(f"{clip_id}: wrong reference protocol")
        if row["window_protocol_id"] != split_config["window_protocol_id"]:
            errors.append(f"{clip_id}: wrong window protocol")
        for field in ("archive_path", "object_positions_path", "frame_metrics_path", "coordinate_check_path", "window_metrics_path"):
            if not (project_root / row[field]).is_file():
                errors.append(f"{clip_id}: missing {field} {row[field]}")
        if int(row["total_window_count"]) != expected_windows:
            errors.append(f"{clip_id}: wrong number of window rows")
        structural = _csv_bool(row["structural_pass"])
        complete = int(row["temporally_complete_window_count"])
        shape = int(row["both_team_shape_eligible_window_count"])
        ball = int(row["both_team_ball_eligible_window_count"])
        expected_tier = _quality_tier(
            structural_pass=structural,
            expected_windows=expected_windows,
            complete_windows=complete,
            shape_windows=shape,
            ball_windows=ball,
        )
        if row["quality_tier"] != expected_tier:
            errors.append(f"{clip_id}: inconsistent quality tier")
        if _csv_bool(row["fully_eligible"]) != (expected_tier == "fully_eligible"):
            errors.append(f"{clip_id}: inconsistent fully eligible flag")

    summary_path = project_root / config["outputs"]["summary"]
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("model_access") != "forbidden":
        errors.append("summary does not preserve the model-access boundary")
    if summary.get("clip_count") != len(rows):
        errors.append("summary clip count does not match index")

    report = {
        "protocol_id": config["protocol_id"],
        "status": "pass" if not errors else "fail",
        "verified_clip_count": len(rows),
        "verified_split_counts": dict(split_counts),
        "quality_tiers": dict(sorted(Counter(row["quality_tier"] for row in rows).items())),
        "missing_linked_files": sum(error.startswith(tuple(f"{clip_id}: missing" for clip_id in clip_ids)) for error in errors),
        "model_access": config["model_access"],
        "errors": errors,
    }
    if not errors:
        summary["status"] = "complete-validated"
        _write_json(summary_path, summary)
    _write_json(project_root / config["outputs"]["validation_report"], report)
    return report
