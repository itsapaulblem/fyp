from __future__ import annotations

import csv
import io
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from zipfile import ZipFile

from PIL import Image, ImageDraw, ImageFont


OBJECT_FIELDS = (
    "protocol_id",
    "clip_id",
    "split",
    "frame",
    "time_seconds",
    "image_id",
    "source_file_name",
    "annotation_id",
    "track_id",
    "role",
    "team",
    "jersey",
    "pitch_x",
    "pitch_y",
    "pitch_coordinate_present",
    "plausible_coordinate",
    "on_pitch",
)

FRAME_FIELDS = (
    "protocol_id",
    "clip_id",
    "split",
    "official_anchor_action",
    "frame",
    "time_seconds",
    "image_id",
    "source_file_name",
    "ball_annotation_count",
    "plausible_ball_count",
    "ball_metric_eligible_count",
    "ball_available",
    "ball_x",
    "ball_y",
    "left_visible_outfield_on_pitch",
    "right_visible_outfield_on_pitch",
    "left_visible_goalkeepers_on_pitch",
    "right_visible_goalkeepers_on_pitch",
    "left_visible_athletes_off_pitch",
    "right_visible_athletes_off_pitch",
    "left_shape_eligible",
    "right_shape_eligible",
    "left_width_m",
    "right_width_m",
    "left_depth_m",
    "right_depth_m",
    "left_centroid_x",
    "left_centroid_y",
    "right_centroid_x",
    "right_centroid_y",
    "left_compactness_m",
    "right_compactness_m",
    "left_ball_distance_eligible",
    "right_ball_distance_eligible",
    "nearest_left_athlete_to_ball_m",
    "nearest_right_athlete_to_ball_m",
    "left_athletes_within_10m_of_ball",
    "right_athletes_within_10m_of_ball",
    "exclusion_reasons",
)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("Cannot calculate a percentile of an empty sequence")
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def _shape_metrics(points: list[tuple[float, float]], minimum_players: int) -> dict:
    if len(points) < minimum_players:
        return {
            "eligible": False,
            "width": None,
            "depth": None,
            "centroid_x": None,
            "centroid_y": None,
            "compactness": None,
        }
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    centroid_x = mean(xs)
    centroid_y = mean(ys)
    compactness = mean(
        math.hypot(x - centroid_x, y - centroid_y) for x, y in points
    )
    return {
        "eligible": True,
        "width": _percentile(ys, 0.95) - _percentile(ys, 0.05),
        "depth": _percentile(xs, 0.95) - _percentile(xs, 0.05),
        "centroid_x": centroid_x,
        "centroid_y": centroid_y,
        "compactness": compactness,
    }


def _round(value: float | None) -> float | str:
    return "" if value is None else round(value, 6)


def _coordinate(annotation: dict) -> tuple[float, float] | None:
    pitch = annotation.get("bbox_pitch") or {}
    x = pitch.get("x_bottom_middle")
    y = pitch.get("y_bottom_middle")
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        return None
    if not math.isfinite(x) or not math.isfinite(y):
        return None
    return float(x), float(y)


def _inside(point: tuple[float, float], bounds: dict) -> bool:
    x, y = point
    return (
        bounds["x_min"] <= x <= bounds["x_max"]
        and bounds["y_min"] <= y <= bounds["y_max"]
    )


def _plausible(point: tuple[float, float], bounds: dict) -> bool:
    x, y = point
    return (
        abs(x) <= bounds["absolute_x_max"]
        and abs(y) <= bounds["absolute_y_max"]
    )


def _frame_number(file_name: str) -> int:
    return int(Path(file_name).stem)


def _distance(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
    return math.hypot(point_a[0] - point_b[0], point_a[1] - point_b[1])


def _frame_metrics(
    *,
    protocol_id: str,
    clip_id: str,
    split: str,
    anchor: str,
    image: dict,
    annotations: list[dict],
    frame_rate: int,
    pitch_bounds: dict,
    plausible_bounds: dict,
    ball_metric_bounds: dict,
    minimum_players: int,
    local_radius: float,
) -> dict:
    frame = _frame_number(image["file_name"])
    outfield = {"left": [], "right": []}
    goalkeepers = {"left": [], "right": []}
    athletes = {"left": [], "right": []}
    off_pitch = {"left": 0, "right": 0}
    ball_annotations = [
        annotation
        for annotation in annotations
        if annotation.get("attributes", {}).get("role") == "ball"
    ]
    plausible_balls = []
    metric_eligible_balls = []

    for annotation in annotations:
        attributes = annotation.get("attributes", {})
        role = attributes.get("role")
        team = attributes.get("team")
        point = _coordinate(annotation)
        if point is None or not _plausible(point, plausible_bounds):
            continue
        if role == "ball":
            plausible_balls.append(point)
            if (
                abs(point[0]) <= ball_metric_bounds["absolute_x_max"]
                and abs(point[1]) <= ball_metric_bounds["absolute_y_max"]
            ):
                metric_eligible_balls.append(point)
            continue
        if role not in {"player", "goalkeeper"} or team not in athletes:
            continue
        if not _inside(point, pitch_bounds):
            off_pitch[team] += 1
            continue
        athletes[team].append(point)
        if role == "player":
            outfield[team].append(point)
        else:
            goalkeepers[team].append(point)

    ball = metric_eligible_balls[0] if len(metric_eligible_balls) == 1 else None
    shapes = {
        team: _shape_metrics(outfield[team], minimum_players)
        for team in ("left", "right")
    }
    nearest: dict[str, float | None] = {"left": None, "right": None}
    local_counts: dict[str, int | None] = {"left": None, "right": None}
    for team in ("left", "right"):
        if ball is not None and athletes[team]:
            distances = [_distance(point, ball) for point in athletes[team]]
            nearest[team] = min(distances)
            local_counts[team] = sum(distance <= local_radius for distance in distances)

    exclusions = []
    if ball is None:
        exclusions.append("ball_missing_or_ambiguous")
    for team in ("left", "right"):
        if not shapes[team]["eligible"]:
            exclusions.append(f"{team}_shape_insufficient_visible_players")
        if ball is not None and not athletes[team]:
            exclusions.append(f"{team}_no_visible_on_pitch_athlete")

    return {
        "protocol_id": protocol_id,
        "clip_id": clip_id,
        "split": split,
        "official_anchor_action": anchor,
        "frame": frame,
        "time_seconds": round((frame - 1) / frame_rate, 3),
        "image_id": image["image_id"],
        "source_file_name": image["file_name"],
        "ball_annotation_count": len(ball_annotations),
        "plausible_ball_count": len(plausible_balls),
        "ball_metric_eligible_count": len(metric_eligible_balls),
        "ball_available": ball is not None,
        "ball_x": _round(ball[0] if ball else None),
        "ball_y": _round(ball[1] if ball else None),
        "left_visible_outfield_on_pitch": len(outfield["left"]),
        "right_visible_outfield_on_pitch": len(outfield["right"]),
        "left_visible_goalkeepers_on_pitch": len(goalkeepers["left"]),
        "right_visible_goalkeepers_on_pitch": len(goalkeepers["right"]),
        "left_visible_athletes_off_pitch": off_pitch["left"],
        "right_visible_athletes_off_pitch": off_pitch["right"],
        "left_shape_eligible": shapes["left"]["eligible"],
        "right_shape_eligible": shapes["right"]["eligible"],
        "left_width_m": _round(shapes["left"]["width"]),
        "right_width_m": _round(shapes["right"]["width"]),
        "left_depth_m": _round(shapes["left"]["depth"]),
        "right_depth_m": _round(shapes["right"]["depth"]),
        "left_centroid_x": _round(shapes["left"]["centroid_x"]),
        "left_centroid_y": _round(shapes["left"]["centroid_y"]),
        "right_centroid_x": _round(shapes["right"]["centroid_x"]),
        "right_centroid_y": _round(shapes["right"]["centroid_y"]),
        "left_compactness_m": _round(shapes["left"]["compactness"]),
        "right_compactness_m": _round(shapes["right"]["compactness"]),
        "left_ball_distance_eligible": nearest["left"] is not None,
        "right_ball_distance_eligible": nearest["right"] is not None,
        "nearest_left_athlete_to_ball_m": _round(nearest["left"]),
        "nearest_right_athlete_to_ball_m": _round(nearest["right"]),
        "left_athletes_within_10m_of_ball": (
            "" if local_counts["left"] is None else local_counts["left"]
        ),
        "right_athletes_within_10m_of_ball": (
            "" if local_counts["right"] is None else local_counts["right"]
        ),
        "exclusion_reasons": ";".join(exclusions),
    }


def _object_rows(
    *,
    protocol_id: str,
    clip_id: str,
    split: str,
    images_by_id: dict[str, dict],
    annotations: list[dict],
    frame_rate: int,
    pitch_bounds: dict,
    plausible_bounds: dict,
) -> list[dict]:
    rows = []
    for annotation in annotations:
        attributes = annotation.get("attributes", {})
        role = attributes.get("role")
        if role is None:
            continue
        image = images_by_id[annotation["image_id"]]
        frame = _frame_number(image["file_name"])
        point = _coordinate(annotation)
        plausible = point is not None and _plausible(point, plausible_bounds)
        rows.append(
            {
                "protocol_id": protocol_id,
                "clip_id": clip_id,
                "split": split,
                "frame": frame,
                "time_seconds": round((frame - 1) / frame_rate, 3),
                "image_id": annotation["image_id"],
                "source_file_name": image["file_name"],
                "annotation_id": annotation.get("id"),
                "track_id": annotation.get("track_id"),
                "role": role,
                "team": attributes.get("team") or "",
                "jersey": attributes.get("jersey") or "",
                "pitch_x": _round(point[0] if point else None),
                "pitch_y": _round(point[1] if point else None),
                "pitch_coordinate_present": point is not None,
                "plausible_coordinate": plausible,
                "on_pitch": plausible and _inside(point, pitch_bounds),
            }
        )
    return rows


def _draw_coordinate_check(
    *,
    archive: ZipFile,
    member_pattern: str,
    clip_id: str,
    images_by_frame: dict[int, dict],
    annotations_by_image: dict[str, list[dict]],
    frames: list[int],
    pitch_bounds: dict,
    plausible_bounds: dict,
    output_path: Path,
) -> None:
    row_height = 360
    source_width = 620
    pitch_width = 620
    canvas = Image.new("RGB", (source_width + pitch_width, row_height * len(frames)), "white")
    font = ImageFont.load_default()
    colours = {"left": (40, 110, 240), "right": (225, 55, 55)}

    for row_index, frame in enumerate(frames):
        image_info = images_by_frame[frame]
        annotations = annotations_by_image.get(image_info["image_id"], [])
        source = Image.open(io.BytesIO(archive.read(member_pattern % frame))).convert("RGB")
        source.thumbnail((source_width, row_height - 25), Image.Resampling.LANCZOS)
        source_draw = ImageDraw.Draw(source)
        scale_x = source.width / image_info["width"]
        scale_y = source.height / image_info["height"]
        for annotation in annotations:
            role = annotation.get("attributes", {}).get("role")
            team = annotation.get("attributes", {}).get("team")
            bbox = annotation.get("bbox_image") or {}
            if role not in {"player", "goalkeeper", "ball"} or not bbox:
                continue
            colour = (245, 205, 35) if role == "ball" else colours.get(team, (120, 120, 120))
            x0 = bbox.get("x", 0) * scale_x
            y0 = bbox.get("y", 0) * scale_y
            x1 = (bbox.get("x", 0) + bbox.get("w", 0)) * scale_x
            y1 = (bbox.get("y", 0) + bbox.get("h", 0)) * scale_y
            source_draw.rectangle((x0, y0, x1, y1), outline=colour, width=2)

        row_top = row_index * row_height
        canvas.paste(source, (0, row_top + 20))
        draw = ImageDraw.Draw(canvas)
        draw.text((5, row_top + 4), f"{clip_id} frame {frame}", fill="black", font=font)

        margin_x = 55
        margin_y = 35
        left = source_width + margin_x
        top = row_top + margin_y
        right = source_width + pitch_width - margin_x
        bottom = row_top + row_height - margin_y
        draw.rectangle((left, top, right, bottom), outline=(25, 120, 55), width=3)
        middle_x = (left + right) / 2
        draw.line((middle_x, top, middle_x, bottom), fill=(25, 120, 55), width=2)
        centre_y = (top + bottom) / 2
        draw.ellipse(
            (middle_x - 35, centre_y - 35, middle_x + 35, centre_y + 35),
            outline=(25, 120, 55),
            width=2,
        )

        def project(point: tuple[float, float]) -> tuple[float, float]:
            x, y = point
            px = left + (x - pitch_bounds["x_min"]) / (
                pitch_bounds["x_max"] - pitch_bounds["x_min"]
            ) * (right - left)
            py = bottom - (y - pitch_bounds["y_min"]) / (
                pitch_bounds["y_max"] - pitch_bounds["y_min"]
            ) * (bottom - top)
            return px, py

        for annotation in annotations:
            attributes = annotation.get("attributes", {})
            role = attributes.get("role")
            team = attributes.get("team")
            point = _coordinate(annotation)
            if role not in {"player", "goalkeeper", "ball"} or point is None:
                continue
            if not _plausible(point, plausible_bounds):
                continue
            px, py = project(point)
            colour = (245, 180, 0) if role == "ball" else colours.get(team, (100, 100, 100))
            radius = 5 if role == "ball" else 7
            if role == "goalkeeper":
                draw.rectangle((px - radius, py - radius, px + radius, py + radius), fill=colour, outline="black")
            else:
                draw.ellipse((px - radius, py - radius, px + radius, py + radius), fill=colour, outline="black")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, format="PNG")


def _clip_summary(
    clip_id: str,
    frame_rows: list[dict],
    object_rows: list[dict],
) -> dict:
    def count_true(field: str) -> int:
        return sum(row[field] is True for row in frame_rows)

    both_shapes = sum(
        row["left_shape_eligible"] is True and row["right_shape_eligible"] is True
        for row in frame_rows
    )
    off_pitch_rows = [
        row
        for row in object_rows
        if row["role"] in {"player", "goalkeeper"}
        and row["plausible_coordinate"] is True
        and row["on_pitch"] is False
    ]
    missing_pitch_rows = [
        row for row in object_rows if row["pitch_coordinate_present"] is False
    ]
    implausible_rows = [
        row
        for row in object_rows
        if row["pitch_coordinate_present"] is True
        and row["plausible_coordinate"] is False
    ]
    return {
        "clip_id": clip_id,
        "frames": len(frame_rows),
        "object_rows": len(object_rows),
        "ball_available_frames": count_true("ball_available"),
        "ball_available_fraction": round(count_true("ball_available") / len(frame_rows), 6),
        "frames_with_multiple_plausible_balls": sum(
            row["plausible_ball_count"] > 1 for row in frame_rows
        ),
        "frames_with_plausible_but_ineligible_ball": sum(
            row["plausible_ball_count"] > 0
            and row["ball_metric_eligible_count"] == 0
            for row in frame_rows
        ),
        "left_shape_eligible_frames": count_true("left_shape_eligible"),
        "right_shape_eligible_frames": count_true("right_shape_eligible"),
        "both_shapes_eligible_frames": both_shapes,
        "both_shapes_eligible_fraction": round(both_shapes / len(frame_rows), 6),
        "left_ball_distance_eligible_frames": count_true("left_ball_distance_eligible"),
        "right_ball_distance_eligible_frames": count_true("right_ball_distance_eligible"),
        "off_pitch_athlete_annotations": len(off_pitch_rows),
        "tracks_with_off_pitch_annotations": sorted(
            {row["track_id"] for row in off_pitch_rows}
        ),
        "object_rows_missing_pitch_coordinates": len(missing_pitch_rows),
        "implausible_coordinate_annotations": len(implausible_rows),
        "implausible_coordinate_roles": {
            role: sum(row["role"] == role for row in implausible_rows)
            for role in sorted({row["role"] for row in implausible_rows})
        },
    }


def _configured_clip_ids(config: dict, manifest_rows: list[dict[str, str]]) -> list[str]:
    if "clip_ids" in config:
        clip_ids = list(config["clip_ids"])
    elif config.get("selection") == "all_manifest_clips_in_split":
        clip_ids = sorted(
            row["clip_id"] for row in manifest_rows if row["split"] == config["split"]
        )
    else:
        raise ValueError("Analytics config must provide clip_ids or a supported selection")

    if len(clip_ids) != len(set(clip_ids)):
        raise ValueError("Analytics config selects duplicate clip IDs")
    expected = config.get("expected_clip_count")
    if expected is not None and len(clip_ids) != expected:
        raise ValueError(f"Selected {len(clip_ids)} clips instead of expected {expected}")
    return clip_ids


def _run_reference_analytics(
    project_root: Path,
    config_filename: str,
    progress_label: str,
) -> dict:
    config_path = project_root / "config" / config_filename
    config = json.loads(config_path.read_text(encoding="utf-8"))
    manifest_rows = _read_csv(project_root / "data" / "processed" / "manifest.csv")
    manifest = {row["clip_id"]: row for row in manifest_rows}
    clip_ids = _configured_clip_ids(config, manifest_rows)
    output_root = project_root / config["outputs"]["root"]
    summaries = []

    for clip_id in clip_ids:
        if clip_id not in manifest:
            raise ValueError(f"Configured clip {clip_id} is missing from the manifest")
        source = manifest[clip_id]
        if source["split"] != config["split"]:
            raise ValueError(f"{clip_id} is not in configured split {config['split']}")
        print(f"{progress_label}: load {clip_id}", flush=True)
        with ZipFile(project_root / source["archive_path"]) as archive:
            label = json.loads(archive.read(source["label_member"]))
            if label["info"].get("version") != "1.3":
                raise ValueError(f"{clip_id} is not SoccerNet-GSR v1.3")
            images = sorted(label["images"], key=lambda image: _frame_number(image["file_name"]))
            if len(images) != 750:
                raise ValueError(f"{clip_id} has {len(images)} images instead of 750")
            images_by_id = {image["image_id"]: image for image in images}
            images_by_frame = {_frame_number(image["file_name"]): image for image in images}
            annotations_by_image: dict[str, list[dict]] = defaultdict(list)
            for annotation in label["annotations"]:
                annotations_by_image[annotation["image_id"]].append(annotation)

            object_rows = _object_rows(
                protocol_id=config["protocol_id"],
                clip_id=clip_id,
                split=source["split"],
                images_by_id=images_by_id,
                annotations=label["annotations"],
                frame_rate=int(label["info"]["frame_rate"]),
                pitch_bounds=config["pitch_metres"],
                plausible_bounds=config["plausible_coordinate_bounds_metres"],
            )
            frame_rows = [
                _frame_metrics(
                    protocol_id=config["protocol_id"],
                    clip_id=clip_id,
                    split=source["split"],
                    anchor=label["info"]["action_class"],
                    image=image,
                    annotations=annotations_by_image.get(image["image_id"], []),
                    frame_rate=int(label["info"]["frame_rate"]),
                    pitch_bounds=config["pitch_metres"],
                    plausible_bounds=config["plausible_coordinate_bounds_metres"],
                    ball_metric_bounds=config["ball_metric_bounds_metres"],
                    minimum_players=config["eligibility"][
                        "minimum_visible_on_pitch_outfield_players_per_team"
                    ],
                    local_radius=config["eligibility"]["local_ball_radius_metres"],
                )
                for image in images
            ]

            _write_csv(
                output_root / config["outputs"]["object_positions"] / f"{clip_id}.csv",
                OBJECT_FIELDS,
                object_rows,
            )
            _write_csv(
                output_root / config["outputs"]["frame_metrics"] / f"{clip_id}.csv",
                FRAME_FIELDS,
                frame_rows,
            )
            _draw_coordinate_check(
                archive=archive,
                member_pattern=source["frame_member_pattern"],
                clip_id=clip_id,
                images_by_frame=images_by_frame,
                annotations_by_image=annotations_by_image,
                frames=config["coordinate_check_frames"],
                pitch_bounds=config["pitch_metres"],
                plausible_bounds=config["plausible_coordinate_bounds_metres"],
                output_path=(
                    output_root
                    / config["outputs"]["coordinate_checks"]
                    / f"{clip_id}.png"
                ),
            )
            summaries.append(_clip_summary(clip_id, frame_rows, object_rows))
        print(f"{progress_label}: wrote {clip_id}", flush=True)

    summary = {
        "protocol_id": config["protocol_id"],
        "status": "complete-awaiting-coordinate-visual-review",
        "provenance": "derived from hidden official SoccerNet-GSR v1.3 annotations",
        "split": config["split"],
        "clip_count": len(summaries),
        "frame_count": sum(summary["frames"] for summary in summaries),
        "clips": summaries,
        "limitations": [
            "Metrics describe visible pitch-located players, not complete team shapes.",
            "Team labels remain left/right; possession and attacking direction are not inferred.",
            "Off-pitch athletes are retained in object tables but excluded from metrics.",
            "Coordinate-check images are human-review aids and are not MLLM inputs.",
        ],
    }
    _write_json(output_root / config["outputs"]["summary"], summary)
    return summary


def run_reference_analytics_pilot(project_root: Path) -> dict:
    return _run_reference_analytics(
        project_root,
        "reference_analytics_pilot.json",
        "analytics pilot",
    )


def run_reference_analytics_train(project_root: Path) -> dict:
    return _run_reference_analytics(
        project_root,
        "reference_analytics_train.json",
        "analytics train",
    )


def run_reference_analytics_valid(project_root: Path) -> dict:
    return _run_reference_analytics(
        project_root,
        "reference_analytics_valid.json",
        "analytics valid",
    )


def run_reference_analytics_test(project_root: Path) -> dict:
    return _run_reference_analytics(
        project_root,
        "reference_analytics_test.json",
        "analytics test",
    )


def _csv_bool(value: str) -> bool:
    if value == "True":
        return True
    if value == "False":
        return False
    raise ValueError(f"Invalid CSV boolean {value!r}")


def _validate_reference_analytics(project_root: Path, config_filename: str) -> dict:
    config = json.loads(
        (project_root / "config" / config_filename).read_text(encoding="utf-8")
    )
    manifest_rows = _read_csv(project_root / "data" / "processed" / "manifest.csv")
    manifest_by_clip = {row["clip_id"]: row for row in manifest_rows}
    clip_ids = _configured_clip_ids(config, manifest_rows)
    output_root = project_root / config["outputs"]["root"]
    summary = json.loads(
        (output_root / config["outputs"]["summary"]).read_text(encoding="utf-8")
    )
    summary_by_clip = {row["clip_id"]: row for row in summary["clips"]}
    clip_reports = []
    all_errors: list[str] = []
    shape_threshold = config.get("quality_control", {}).get(
        "minimum_both_team_shape_coverage", 0.8
    )
    ball_threshold = config.get("quality_control", {}).get(
        "minimum_ball_metric_coverage", 0.9
    )

    if summary.get("clip_count") != len(clip_ids):
        all_errors.append("summary clip count does not match configured selection")
    if set(summary_by_clip) != set(clip_ids):
        all_errors.append("summary clip IDs do not match configured selection")

    shape_fields = (
        "width_m",
        "depth_m",
        "centroid_x",
        "centroid_y",
        "compactness_m",
    )
    for clip_id in clip_ids:
        errors: list[str] = []
        warnings: list[str] = []
        clip_summary = summary_by_clip.get(clip_id)
        if clip_summary is None:
            all_errors.append(f"{clip_id}: missing from summary")
            clip_reports.append(
                {
                    "clip_id": clip_id,
                    "status": "fail",
                    "frame_rows": 0,
                    "object_rows": 0,
                    "coordinate_check_dimensions": None,
                    "errors": ["missing from summary"],
                    "warnings": [],
                }
            )
            continue
        frame_path = (
            output_root / config["outputs"]["frame_metrics"] / f"{clip_id}.csv"
        )
        object_path = (
            output_root / config["outputs"]["object_positions"] / f"{clip_id}.csv"
        )
        check_path = (
            output_root / config["outputs"]["coordinate_checks"] / f"{clip_id}.png"
        )
        frame_rows = _read_csv(frame_path)
        object_rows = _read_csv(object_path)

        frames = [int(row["frame"]) for row in frame_rows]
        if frames != list(range(1, 751)):
            errors.append("frame rows are not exactly the ordered range 1..750")
        if len(object_rows) != summary_by_clip[clip_id]["object_rows"]:
            errors.append("object-row count does not match summary")
        if any(row["protocol_id"] != config["protocol_id"] for row in frame_rows):
            errors.append("frame table contains another protocol ID")
        if any(row["clip_id"] != clip_id for row in frame_rows):
            errors.append("frame table contains another clip ID")

        for row in frame_rows:
            for team in ("left", "right"):
                eligible = _csv_bool(row[f"{team}_shape_eligible"])
                values = [row[f"{team}_{suffix}"] for suffix in shape_fields]
                if eligible and any(value == "" for value in values):
                    errors.append(f"frame {row['frame']} has incomplete eligible {team} shape")
                if not eligible and any(value != "" for value in values):
                    errors.append(f"frame {row['frame']} has ineligible {team} shape values")
                if eligible:
                    width = float(row[f"{team}_width_m"])
                    depth = float(row[f"{team}_depth_m"])
                    compactness = float(row[f"{team}_compactness_m"])
                    if not 0 <= width <= 68:
                        errors.append(f"frame {row['frame']} has invalid {team} width")
                    if not 0 <= depth <= 105:
                        errors.append(f"frame {row['frame']} has invalid {team} depth")
                    if compactness < 0:
                        errors.append(f"frame {row['frame']} has negative {team} compactness")

                ball_eligible = _csv_bool(row[f"{team}_ball_distance_eligible"])
                ball_values = (
                    row[f"nearest_{team}_athlete_to_ball_m"],
                    row[f"{team}_athletes_within_10m_of_ball"],
                )
                if ball_eligible and any(value == "" for value in ball_values):
                    errors.append(f"frame {row['frame']} has incomplete {team} ball metrics")
                if not ball_eligible and any(value != "" for value in ball_values):
                    errors.append(f"frame {row['frame']} has ineligible {team} ball values")
                if ball_eligible and float(ball_values[0]) < 0:
                    errors.append(f"frame {row['frame']} has negative ball distance")

        if not check_path.exists():
            errors.append("coordinate-check image is missing")
            check_dimensions = None
        else:
            with Image.open(check_path) as image:
                check_dimensions = list(image.size)
            if check_dimensions != [1240, 1800]:
                errors.append(f"unexpected coordinate-check dimensions {check_dimensions}")

        if clip_summary["both_shapes_eligible_fraction"] < shape_threshold:
            warnings.append("both-team shape coverage is below 80%")
        if clip_summary["ball_available_fraction"] < ball_threshold:
            warnings.append("ball-distance coverage is below 90%")
        if clip_summary["off_pitch_athlete_annotations"]:
            warnings.append("off-pitch athletes were retained but excluded from metrics")
        if clip_summary["implausible_coordinate_annotations"]:
            warnings.append("implausible ground-plane projections were excluded")
        if clip_summary["frames_with_multiple_plausible_balls"]:
            warnings.append("frames with multiple ball annotations were excluded as ambiguous")
        if clip_summary["object_rows_missing_pitch_coordinates"]:
            warnings.append("object annotations with missing pitch coordinates were retained")

        all_errors.extend(f"{clip_id}: {error}" for error in errors)
        clip_reports.append(
            {
                "clip_id": clip_id,
                "status": "pass_with_warnings" if warnings and not errors else (
                    "pass" if not errors else "fail"
                ),
                "frame_rows": len(frame_rows),
                "object_rows": len(object_rows),
                "coordinate_check_dimensions": check_dimensions,
                "errors": errors,
                "warnings": warnings,
            }
        )

    shape_coverages = [row["both_shapes_eligible_fraction"] for row in summary["clips"]]
    ball_coverages = [row["ball_available_fraction"] for row in summary["clips"]]
    shape_below = [
        row["clip_id"]
        for row in summary["clips"]
        if row["both_shapes_eligible_fraction"] < shape_threshold
    ]
    ball_below = [
        row["clip_id"]
        for row in summary["clips"]
        if row["ball_available_fraction"] < ball_threshold
    ]
    clips_with_warnings = sum(bool(row["warnings"]) for row in clip_reports)
    clips_meeting_both = [
        row["clip_id"]
        for row in summary["clips"]
        if row["both_shapes_eligible_fraction"] >= shape_threshold
        and row["ball_available_fraction"] >= ball_threshold
    ]
    ambiguous_ball_clips = [
        {
            "clip_id": row["clip_id"],
            "ambiguous_frames": row["frames_with_multiple_plausible_balls"],
        }
        for row in summary["clips"]
        if row["frames_with_multiple_plausible_balls"]
    ]
    missing_coordinate_clips = [
        {
            "clip_id": row["clip_id"],
            "missing_annotations": row["object_rows_missing_pitch_coordinates"],
        }
        for row in summary["clips"]
        if row["object_rows_missing_pitch_coordinates"]
    ]
    qc_status = (
        "fail"
        if all_errors
        else "pass_with_data_quality_warnings" if clips_with_warnings else "pass"
    )
    report = {
        "protocol_id": config["protocol_id"],
        "status": qc_status,
        "verified_clip_count": len(clip_reports),
        "verified_frame_count": sum(row["frame_rows"] for row in clip_reports),
        "errors": all_errors,
        "quality_control": {
            "structural_validation_passed": not all_errors,
            "clips_with_warnings": clips_with_warnings,
            "shape_coverage_threshold": shape_threshold,
            "clips_below_shape_coverage_threshold": shape_below,
            "clips_meeting_shape_coverage_threshold": len(clip_ids) - len(shape_below),
            "minimum_both_team_shape_coverage": min(shape_coverages),
            "mean_both_team_shape_coverage": round(mean(shape_coverages), 6),
            "ball_coverage_threshold": ball_threshold,
            "clips_below_ball_coverage_threshold": ball_below,
            "clips_meeting_ball_coverage_threshold": len(clip_ids) - len(ball_below),
            "clips_meeting_both_coverage_thresholds": clips_meeting_both,
            "minimum_ball_metric_coverage": min(ball_coverages),
            "mean_ball_metric_coverage": round(mean(ball_coverages), 6),
            "total_object_rows": sum(row["object_rows"] for row in summary["clips"]),
            "total_off_pitch_athlete_annotations": sum(
                row["off_pitch_athlete_annotations"] for row in summary["clips"]
            ),
            "total_implausible_coordinate_annotations": sum(
                row["implausible_coordinate_annotations"] for row in summary["clips"]
            ),
            "clips_with_ambiguous_ball_frames": ambiguous_ball_clips,
            "clips_with_missing_pitch_coordinates": missing_coordinate_clips,
        },
        "clips": clip_reports,
        "coordinate_checks": {
            "status": config.get("coordinate_review", {}).get(
                "status", "generated-not-human-reviewed"
            ),
            "frames_per_clip": config["coordinate_check_frames"],
            "result": config.get("coordinate_review", {}).get(
                "result",
                "Coordinate-check artifacts passed automated existence and dimension checks.",
            ),
        },
    }
    clip_report_by_id = {row["clip_id"]: row for row in clip_reports}
    qc_rows = []
    for clip_summary in summary["clips"]:
        clip_id = clip_summary["clip_id"]
        clip_report = clip_report_by_id[clip_id]
        qc_rows.append(
            {
                "protocol_id": config["protocol_id"],
                "clip_id": clip_id,
                "split": config["split"],
                "official_anchor_action": manifest_by_clip[clip_id]["action_class"],
                "frame_rows": clip_report["frame_rows"],
                "object_rows": clip_report["object_rows"],
                "structural_pass": not clip_report["errors"],
                "both_team_shape_coverage": clip_summary["both_shapes_eligible_fraction"],
                "shape_coverage_pass": (
                    clip_summary["both_shapes_eligible_fraction"] >= shape_threshold
                ),
                "ball_metric_coverage": clip_summary["ball_available_fraction"],
                "ball_coverage_pass": (
                    clip_summary["ball_available_fraction"] >= ball_threshold
                ),
                "ambiguous_ball_frames": clip_summary[
                    "frames_with_multiple_plausible_balls"
                ],
                "missing_pitch_coordinate_annotations": clip_summary[
                    "object_rows_missing_pitch_coordinates"
                ],
                "off_pitch_athlete_annotations": clip_summary[
                    "off_pitch_athlete_annotations"
                ],
                "implausible_coordinate_annotations": clip_summary[
                    "implausible_coordinate_annotations"
                ],
                "warnings": ";".join(clip_report["warnings"]),
            }
        )
    _write_csv(
        output_root / config["outputs"]["quality_control_table"],
        (
            "protocol_id",
            "clip_id",
            "split",
            "official_anchor_action",
            "frame_rows",
            "object_rows",
            "structural_pass",
            "both_team_shape_coverage",
            "shape_coverage_pass",
            "ball_metric_coverage",
            "ball_coverage_pass",
            "ambiguous_ball_frames",
            "missing_pitch_coordinate_annotations",
            "off_pitch_athlete_annotations",
            "implausible_coordinate_annotations",
            "warnings",
        ),
        qc_rows,
    )
    _write_json(output_root / config["outputs"]["validation_report"], report)
    return report


def validate_reference_analytics_pilot(project_root: Path) -> dict:
    return _validate_reference_analytics(project_root, "reference_analytics_pilot.json")


def validate_reference_analytics_train(project_root: Path) -> dict:
    return _validate_reference_analytics(project_root, "reference_analytics_train.json")


def validate_reference_analytics_valid(project_root: Path) -> dict:
    return _validate_reference_analytics(project_root, "reference_analytics_valid.json")


def validate_reference_analytics_test(project_root: Path) -> dict:
    return _validate_reference_analytics(project_root, "reference_analytics_test.json")
