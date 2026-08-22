from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import mean, median

from football_dataset.reference_analytics import (
    _csv_bool,
    _percentile,
    _read_csv,
    _write_csv,
    _write_json,
)


THRESHOLD_FIELDS = (
    "protocol_id",
    "source_protocol_id",
    "scope_type",
    "window_or_transition",
    "metric_name",
    "metric_family",
    "observation_count",
    "unique_clip_count",
    "minimum",
    "p10",
    "p25",
    "median",
    "p75",
    "p90",
    "maximum",
    "mean",
    "primary_low_threshold",
    "primary_high_threshold",
    "meaningful_absolute_change_threshold",
)


def classify_absolute(value: float | None, low: float, high: float, mode: str) -> str:
    if value is None:
        return "not_measurable"
    if mode == "absolute_high":
        if value >= high:
            return "supported"
        if value <= low:
            return "contradicted"
    elif mode == "absolute_low":
        if value <= low:
            return "supported"
        if value >= high:
            return "contradicted"
    else:
        raise ValueError(f"Unsupported absolute mode {mode}")
    return "inconclusive"


def classify_change(value: float | None, threshold: float, mode: str) -> str:
    if value is None:
        return "not_measurable"
    if mode == "change_increase":
        if value >= threshold:
            return "supported"
        if value <= -threshold:
            return "contradicted"
    elif mode == "change_decrease":
        if value <= -threshold:
            return "supported"
        if value >= threshold:
            return "contradicted"
    else:
        raise ValueError(f"Unsupported change mode {mode}")
    return "inconclusive"


def combine_component_results(results: list[str], minimum_agreeing: int) -> str:
    measurable = [result for result in results if result != "not_measurable"]
    if len(measurable) < minimum_agreeing:
        return "not_measurable"
    supported = measurable.count("supported")
    contradicted = measurable.count("contradicted")
    if supported >= minimum_agreeing and contradicted < minimum_agreeing:
        return "supported"
    if contradicted >= minimum_agreeing and supported < minimum_agreeing:
        return "contradicted"
    return "inconclusive"


def _distribution(values: list[float]) -> dict[str, float | int]:
    if not values:
        raise ValueError("Cannot describe an empty metric distribution")
    return {
        "observation_count": len(values),
        "minimum": round(min(values), 6),
        "p10": round(_percentile(values, 0.10), 6),
        "p25": round(_percentile(values, 0.25), 6),
        "median": round(median(values), 6),
        "p75": round(_percentile(values, 0.75), 6),
        "p90": round(_percentile(values, 0.90), 6),
        "maximum": round(max(values), 6),
        "mean": round(mean(values), 6),
    }


def _eligible_value(row: dict[str, str], team: str, metric: dict) -> float | None:
    if not _csv_bool(row[f"{team}_{metric['family']}_summary_eligible"]):
        return None
    value = row[f"{team}_{metric['window_field']}"]
    return None if value == "" else float(value)


def _record(
    *,
    config: dict,
    scope_type: str,
    scope_name: str,
    metric: dict,
    values: list[tuple[str, float]],
) -> dict:
    stats = _distribution([value for _, value in values])
    record = {
        "protocol_id": config["protocol_id"],
        "source_protocol_id": config["source_protocol_id"],
        "scope_type": scope_type,
        "window_or_transition": scope_name,
        "metric_name": metric["name"],
        "metric_family": metric["family"],
        "unique_clip_count": len({clip_id for clip_id, _ in values}),
        **stats,
        "primary_low_threshold": "",
        "primary_high_threshold": "",
        "meaningful_absolute_change_threshold": "",
    }
    if scope_type == "absolute_window":
        record["primary_low_threshold"] = stats["p10"]
        record["primary_high_threshold"] = stats["p90"]
    else:
        absolute_values = [abs(value) for _, value in values]
        record["meaningful_absolute_change_threshold"] = round(
            _percentile(absolute_values, config["change_thresholds"]["meaningful_absolute_change_percentile"]),
            6,
        )
    return record


def generate_train_metric_thresholds(project_root: Path) -> dict:
    config = json.loads(
        (project_root / "config" / "claim_verification_train.json").read_text(
            encoding="utf-8"
        )
    )
    rows = _read_csv(project_root / config["outputs"]["source_window_metrics"])
    if any(row["protocol_id"] != config["source_protocol_id"] for row in rows):
        raise ValueError("Window table contains another source protocol")
    rows_by_clip_window = {
        (row["clip_id"], row["window_name"]): row for row in rows
    }
    clip_ids = sorted({row["clip_id"] for row in rows})
    window_names = ("before", "around", "after")
    records = []

    for window_name in window_names:
        for metric in config["metrics"]:
            values = []
            for clip_id in clip_ids:
                row = rows_by_clip_window[(clip_id, window_name)]
                for team in ("left", "right"):
                    value = _eligible_value(row, team, metric)
                    if value is not None:
                        values.append((clip_id, value))
            records.append(
                _record(
                    config=config,
                    scope_type="absolute_window",
                    scope_name=window_name,
                    metric=metric,
                    values=values,
                )
            )

    for transition in config["transitions"]:
        for metric in config["metrics"]:
            values = []
            for clip_id in clip_ids:
                start = _eligible_value(
                    rows_by_clip_window[(clip_id, transition["from_window"])],
                    "left",
                    metric,
                )
                end = _eligible_value(
                    rows_by_clip_window[(clip_id, transition["to_window"])],
                    "left",
                    metric,
                )
                if start is not None and end is not None:
                    values.append((clip_id, end - start))
                start = _eligible_value(
                    rows_by_clip_window[(clip_id, transition["from_window"])],
                    "right",
                    metric,
                )
                end = _eligible_value(
                    rows_by_clip_window[(clip_id, transition["to_window"])],
                    "right",
                    metric,
                )
                if start is not None and end is not None:
                    values.append((clip_id, end - start))
            records.append(
                _record(
                    config=config,
                    scope_type="window_change",
                    scope_name=transition["name"],
                    metric=metric,
                    values=values,
                )
            )

    _write_csv(
        project_root / config["outputs"]["threshold_table"],
        THRESHOLD_FIELDS,
        records,
    )
    result = {
        "protocol_id": config["protocol_id"],
        "status": "complete-pending-validation",
        "provenance": "thresholds derived only from eligible train temporal-window analytics",
        "split": config["split"],
        "absolute_rule": "supported at the expected p10/p90 extreme, contradicted at the opposite extreme, otherwise inconclusive",
        "change_rule": "supported beyond the expected signed p75 absolute-change deadband, contradicted beyond the opposite deadband, otherwise inconclusive",
        "records": records,
        "claim_rules": config["claim_rules"],
        "limitations": [
            "Thresholds are operational train-development choices, not universal football standards.",
            "A visual shirt-colour team must be manually verified as SoccerNet left/right before team-specific evaluation.",
            "Missing team mapping, window, transition, or eligible metric yields not_measurable.",
            "Tracking evidence does not determine overall coaching quality.",
        ],
    }
    _write_json(project_root / config["outputs"]["threshold_json"], result)
    return result


def validate_train_metric_thresholds(project_root: Path) -> dict:
    config = json.loads(
        (project_root / "config" / "claim_verification_train.json").read_text(
            encoding="utf-8"
        )
    )
    rows = _read_csv(project_root / config["outputs"]["threshold_table"])
    expected = len(config["metrics"]) * (3 + len(config["transitions"]))
    errors: list[str] = []
    if config["absolute_thresholds"] != {
        "low_percentile": 0.10,
        "high_percentile": 0.90,
    }:
        errors.append("named p10/p90 output fields require configured 0.10/0.90 thresholds")
    if config["change_thresholds"]["meaningful_absolute_change_percentile"] != 0.75:
        errors.append("the named p75 absolute-change rule requires configured percentile 0.75")
    if len(rows) != expected:
        errors.append(f"found {len(rows)} threshold rows instead of {expected}")
    keys = [(row["scope_type"], row["window_or_transition"], row["metric_name"]) for row in rows]
    if len(keys) != len(set(keys)):
        errors.append("threshold table contains duplicate scope/metric rows")

    for row in rows:
        count = int(row["observation_count"])
        if count < config["minimum_distribution_observations"]:
            errors.append(
                f"{row['window_or_transition']} {row['metric_name']} has only {count} observations"
            )
        quantiles = [
            float(row[field])
            for field in ("minimum", "p10", "p25", "median", "p75", "p90", "maximum")
        ]
        if any(not math.isfinite(value) for value in quantiles):
            errors.append(f"{row['metric_name']} contains a non-finite threshold")
        if quantiles != sorted(quantiles):
            errors.append(f"{row['window_or_transition']} {row['metric_name']} quantiles are not ordered")
        if row["scope_type"] == "absolute_window":
            if row["primary_low_threshold"] != row["p10"] or row["primary_high_threshold"] != row["p90"]:
                errors.append(f"{row['window_or_transition']} {row['metric_name']} absolute thresholds mismatch")
            if row["meaningful_absolute_change_threshold"] != "":
                errors.append(f"{row['window_or_transition']} {row['metric_name']} has an unexpected change threshold")
        elif row["scope_type"] == "window_change":
            threshold = float(row["meaningful_absolute_change_threshold"])
            if threshold < 0:
                errors.append(f"{row['window_or_transition']} {row['metric_name']} has a negative deadband")
            if row["primary_low_threshold"] != "" or row["primary_high_threshold"] != "":
                errors.append(f"{row['window_or_transition']} {row['metric_name']} has unexpected absolute thresholds")
        else:
            errors.append(f"unknown threshold scope {row['scope_type']}")

    result = json.loads(
        (project_root / config["outputs"]["threshold_json"]).read_text(encoding="utf-8")
    )
    report = {
        "protocol_id": config["protocol_id"],
        "status": "pass" if not errors else "fail",
        "verified_threshold_rows": len(rows),
        "errors": errors,
        "minimum_observation_count": min(int(row["observation_count"]) for row in rows),
        "maximum_observation_count": max(int(row["observation_count"]) for row in rows),
    }
    if not errors:
        result["status"] = "complete-validated"
        _write_json(project_root / config["outputs"]["threshold_json"], result)
    _write_json(project_root / config["outputs"]["validation_report"], report)
    return report
