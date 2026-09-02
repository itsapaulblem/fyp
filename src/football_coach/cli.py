from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import typer
from dotenv import load_dotenv

from .annotations import initialize_annotations, validate_annotation
from .dataset import index_archives, read_manifest, select_records, sha256_file, write_manifest
from .media import extract_sampled_frames, make_contact_sheet, make_review_video
from .ollama_client import OllamaClient

app = typer.Typer(no_args_is_help=True)
ROOT = Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@app.command("index")
def index_command(
    config_path: Path = typer.Option(ROOT / "config/dataset_v0.1.0.json"),
    output: Path = typer.Option(ROOT / "data/manifests/soccernet_v1.3.csv"),
) -> None:
    """Build and validate a manifest directly from the official ZIPs."""
    config = _load_json(config_path)
    records = index_archives(config, ROOT)
    write_manifest(records, output)
    typer.echo(f"Wrote {len(records)} verified clips to {output}")
    typer.echo(f"manifest_sha256={sha256_file(output)}")


@app.command("select")
def select_command(
    config_path: Path = typer.Option(ROOT / "config/dataset_v0.1.0.json"),
    manifest: Path = typer.Option(ROOT / "data/manifests/soccernet_v1.3.csv"),
    output: Path = typer.Option(ROOT / "data/manifests/coaching_120_v0.1.0.csv"),
) -> None:
    """Create the deterministic 40/40/40 action-stratified cohort."""
    config = _load_json(config_path)
    records = read_manifest(manifest)
    selection = config["selection"]
    targets = {split: int(selection[split]) for split in ("train", "valid", "test")}
    selected, allocations = select_records(records, targets, int(config["seed"]))
    write_manifest(selected, output)
    summary_path = output.with_suffix(".summary.json")
    summary = {
        "protocol_id": config["protocol_id"],
        "seed": config["seed"],
        "source_manifest_sha256": sha256_file(manifest),
        "selection_manifest_sha256": sha256_file(output),
        "counts": targets,
        "action_allocations": allocations,
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    typer.echo(f"Wrote {len(selected)} selected clips to {output}")


@app.command("sample")
def sample_command(
    clip_id: str,
    count: int = typer.Option(8, min=2, max=32),
    manifest: Path = typer.Option(ROOT / "data/manifests/coaching_120_v0.1.0.csv"),
) -> None:
    """Extract deterministic uniform frames and a labelled contact sheet."""
    matches = [record for record in read_manifest(manifest) if record.clip_id == clip_id]
    if len(matches) != 1:
        raise typer.BadParameter(
            f"Expected one selected record for {clip_id}, found {len(matches)}"
        )
    output_root = ROOT / "artifacts/model_inputs"
    frames = extract_sampled_frames(matches[0], ROOT, output_root, count)
    sheet = make_contact_sheet(frames, frames[0].parent / "contact_sheet.jpg")
    typer.echo(f"Wrote {len(frames)} frames and {sheet}")


@app.command("review-video")
def review_video_command(
    clip_id: str,
    manifest: Path = typer.Option(ROOT / "data/manifests/coaching_120_v0.1.0.csv"),
) -> None:
    """Create a full 30-second MP4 for private human annotation only."""
    matches = [record for record in read_manifest(manifest) if record.clip_id == clip_id]
    if len(matches) != 1:
        raise typer.BadParameter(
            f"Expected one selected record for {clip_id}, found {len(matches)}"
        )
    record = matches[0]
    destination = ROOT / "data/review" / record.split / f"{record.clip_id}.mp4"
    typer.echo(f"Wrote {make_review_video(record, ROOT, destination)}")


@app.command("annotations-init")
def annotations_init_command(
    manifest: Path = typer.Option(ROOT / "data/manifests/coaching_120_v0.1.0.csv"),
) -> None:
    """Create non-overwriting private annotation work items for selected clips."""
    count = initialize_annotations(read_manifest(manifest), ROOT / "annotations/private")
    typer.echo(f"Created {count} annotation work items")


@app.command("annotations-validate")
def annotations_validate_command(
    annotation_root: Path = typer.Option(ROOT / "annotations/private"),
    schema_path: Path = typer.Option(ROOT / "schemas/coaching_annotation.schema.json"),
) -> None:
    """Validate all human reference files and fail on incomplete drafts."""
    schema = _load_json(schema_path)
    files = sorted(annotation_root.glob("*/*.json"))
    failures = 0
    for path in files:
        errors = validate_annotation(path, schema)
        if errors:
            failures += 1
            typer.echo(f"{path}: {len(errors)} error(s)")
            for error in errors:
                typer.echo(f"  - {error}")
    typer.echo(f"Validated {len(files)} files; {failures} invalid")
    if failures:
        raise typer.Exit(code=1)


@app.command("smoke-run")
def smoke_run_command(
    clip_id: str,
    model: str = typer.Option(..., help="Exact Ollama model tag"),
    count: int = typer.Option(8, min=2, max=16),
    manifest: Path = typer.Option(ROOT / "data/manifests/coaching_120_v0.1.0.csv"),
) -> None:
    """Run one non-test visual request and preserve raw response provenance."""
    load_dotenv(ROOT / ".env")
    matches = [record for record in read_manifest(manifest) if record.clip_id == clip_id]
    if len(matches) != 1:
        raise typer.BadParameter(
            f"Expected one selected record for {clip_id}, found {len(matches)}"
        )
    record = matches[0]
    if record.split == "test":
        raise typer.BadParameter("smoke-run refuses test clips while the protocol is draft")
    frames = extract_sampled_frames(
        record, ROOT, ROOT / "artifacts/model_inputs", count
    )
    prompt_path = ROOT / "input_prompts/recognition_and_coaching_v0.1.0.txt"
    schema_path = ROOT / "schemas/model_response.schema.json"
    experiment_path = ROOT / "config/experiment_v0.1.0.json"
    experiment = _load_json(experiment_path)
    options = dict(experiment["generation"])
    think = bool(options.pop("think"))
    options.pop("stream", None)
    client = OllamaClient()
    raw_response = client.chat(
        model=model,
        prompt=prompt_path.read_text(encoding="utf-8"),
        image_paths=frames,
        schema=_load_json(schema_path),
        options=options,
        think=think,
    )
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    run_dir = ROOT / "output" / model.replace(":", "_") / record.clip_id / timestamp
    run_dir.mkdir(parents=True, exist_ok=False)
    model_text = str(raw_response.get("message", {}).get("content", ""))
    (run_dir / "response.txt").write_text(model_text, encoding="utf-8")
    metadata_lines = [
        f"clip_id: {record.clip_id}",
        f"split: {record.split}",
        f"model: {model}",
        f"created_at_utc: {timestamp}",
        f"frame_count: {count}",
        f"prompt_file: {prompt_path.relative_to(ROOT).as_posix()}",
        f"prompt_sha256: {sha256_file(prompt_path)}",
        f"schema_sha256: {sha256_file(schema_path)}",
        f"experiment_sha256: {sha256_file(experiment_path)}",
        f"done_reason: {raw_response.get('done_reason', '')}",
        f"prompt_eval_count: {raw_response.get('prompt_eval_count', '')}",
        f"eval_count: {raw_response.get('eval_count', '')}",
        f"total_duration_ns: {raw_response.get('total_duration', '')}",
        "",
        "Frames:",
    ]
    metadata_lines.extend(
        f"- {path.relative_to(ROOT).as_posix()} | sha256={sha256_file(path)}"
        for path in frames
    )
    (run_dir / "metadata.txt").write_text(
        "\n".join(metadata_lines) + "\n", encoding="utf-8"
    )
    envelope = {
        "clip_id": record.clip_id,
        "split": record.split,
        "model": model,
        "created_at": timestamp,
        "frame_count": count,
        "frame_paths": [
            str(path.relative_to(ROOT)).replace("\\", "/") for path in frames
        ],
        "frame_sha256": [sha256_file(path) for path in frames],
        "prompt_sha256": sha256_file(prompt_path),
        "schema_sha256": sha256_file(schema_path),
        "experiment_sha256": sha256_file(experiment_path),
        "raw_response": raw_response,
    }
    (run_dir / "raw_api_response.json").write_text(
        json.dumps(envelope, indent=2) + "\n", encoding="utf-8"
    )
    typer.echo(f"Preserved raw smoke response in {run_dir}")


@app.command("ollama-check")
def ollama_check(model: str = typer.Option(..., help="Exact Ollama model tag")) -> None:
    """Check remote connectivity and print installed model metadata."""
    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    tags = client.tags().get("models", [])
    installed = [item for item in tags if item.get("name") == model or item.get("model") == model]
    if not installed:
        raise typer.BadParameter(f"Model {model!r} was not returned by /api/tags")
    detail = client.show(model)
    typer.echo(json.dumps({"tag": installed[0], "details": detail.get("details", {})}, indent=2))


if __name__ == "__main__":
    app()
