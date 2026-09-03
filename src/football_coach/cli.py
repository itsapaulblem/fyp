from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import numpy as np
import typer
from dotenv import load_dotenv

from .catalog import initialize_case, load_case, load_library, validate_library
from .domain import CaseARecord, Condition, ModelAnswer, SoccerNetClip
from .media import sample_dataset_a, sample_dataset_b
from .ollama_client import OllamaClient
from .pairing import deterministic_control_case, normalize_action
from .prompting import build_messages, readable_transcript
from .provenance import sha256_file, timestamp_utc, write_run
from .retrieval import EmbeddingIndex
from .soccernet import (
    audit_dataset_b,
    index_dataset_b,
    read_manifest,
    write_integrity_report,
    write_private_manifest,
    write_public_manifest,
)

app = typer.Typer(no_args_is_help=True)
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = ROOT / "config/project_v0.2.0.json"
DEFAULT_B_MANIFEST = ROOT / "data/video_b/private/soccernet_gsr_v1.3_reference.csv"
DEFAULT_B_PUBLIC_MANIFEST = ROOT / "data/video_b/manifests/soccernet_gsr_v1.3_public.csv"
DEFAULT_B_INTEGRITY_REPORT = ROOT / "data/video_b/private/integrity_v1.3.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def find_b_clip(manifest: Path, clip_id: str) -> SoccerNetClip:
    matches = [record for record in read_manifest(manifest) if record.clip_id == clip_id]
    if len(matches) != 1:
        raise typer.BadParameter(
            f"Expected one Dataset B record for {clip_id}, found {len(matches)}"
        )
    return matches[0]


def require_allowed_split(config: dict, split: str) -> None:
    status = config["status"]
    allowed = {
        "draft_train_only": {"train"},
        "frozen_validation": {"train", "valid"},
        "frozen_test": {"train", "valid", "test"},
    }
    if status not in allowed:
        raise ValueError(f"Unknown protocol status: {status}")
    if split not in allowed[status]:
        raise typer.BadParameter(
            f"Protocol status {status!r} does not permit Dataset B split {split!r}"
        )


def approved_case(case_id: str) -> CaseARecord:
    path = ROOT / "data/video_a/cases" / f"{case_id}.json"
    if not path.is_file():
        raise typer.BadParameter(f"Dataset A case does not exist: {case_id}")
    case = load_case(path)
    errors = case.approval_errors(ROOT)
    if case.status != "approved" or errors:
        details = "; ".join(errors) if errors else "status is not approved"
        raise typer.BadParameter(f"Dataset A case {case_id} is not usable: {details}")
    return case


@app.command("index-b")
def index_b(
    config_path: Path = typer.Option(DEFAULT_CONFIG),
    public_output: Path = typer.Option(DEFAULT_B_PUBLIC_MANIFEST),
    private_output: Path = typer.Option(DEFAULT_B_MANIFEST),
    report_output: Path = typer.Option(DEFAULT_B_INTEGRITY_REPORT),
) -> None:
    """Index and fully verify immutable SoccerNet Dataset B archives."""
    records = index_dataset_b(load_json(config_path), ROOT)
    write_public_manifest(records, public_output)
    write_private_manifest(records, private_output)
    counts = {
        split: sum(record.split == split for record in records)
        for split in ("train", "valid", "test")
    }
    typer.echo(f"Wrote model-visible manifest to {public_output}")
    typer.echo(f"Wrote private reference crosswalk to {private_output}")
    typer.echo(f"split_counts={json.dumps(counts)}")
    typer.echo(f"public_manifest_sha256={sha256_file(public_output)}")
    typer.echo(f"private_manifest_sha256={sha256_file(private_output)}")
    report = audit_dataset_b(records, ROOT, progress=typer.echo)
    write_integrity_report(report, report_output)
    typer.echo(f"Wrote integrity report to {report_output}")
    typer.echo(
        f"integrity_status={report['status']} "
        f"decoded_frames={report['decoded_frame_count']}/"
        f"{report['expected_frame_count']}"
    )
    if report["status"] != "pass":
        raise typer.Exit(code=1)


@app.command("init-case-a")
def init_case_a(case_id: str) -> None:
    """Create non-overwriting Dataset A metadata and advice templates."""
    case_path, advice_path = initialize_case(
        case_id,
        ROOT,
        ROOT / "templates/case_a.template.json",
        ROOT / "templates/advice.template.txt",
    )
    typer.echo(f"Created {case_path}")
    typer.echo(f"Created {advice_path}")
    typer.echo(f"Add private media at data/video_a/media/{case_id}.mp4")


@app.command("validate-a")
def validate_a() -> None:
    """Validate Dataset A syntax and all requirements for approved cases."""
    reports = validate_library(ROOT / "data/video_a/cases", ROOT)
    invalid = 0
    approved = 0
    for case_id, errors in reports.items():
        case_path = ROOT / "data/video_a/cases" / f"{case_id}.json"
        case = None if errors else load_case(case_path)
        if errors:
            invalid += 1
            typer.echo(f"{case_id}: INVALID")
            for error in errors:
                typer.echo(f"  - {error}")
        elif case is not None:
            approved += case.status == "approved"
            typer.echo(f"{case_id}: {case.status.upper()}")
    typer.echo(f"cases={len(reports)} approved={approved} invalid={invalid}")
    if invalid:
        raise typer.Exit(code=1)


@app.command("sample-a")
def sample_a(
    case_id: str,
    count: int = typer.Option(20, min=1, max=32),
    maximum_edge: int = typer.Option(672, min=224, max=1920),
) -> None:
    """Sample chronological frames from one approved Dataset A case."""
    case = approved_case(case_id)
    media_path = ROOT / cast(str, case.source.local_media_path)
    destination = ROOT / "data/video_a/frames" / case_id / (
        f"uniform_{count}_edge_{maximum_edge}"
    )
    frames = sample_dataset_a(
        media_path,
        destination,
        case.source.clip_start_seconds,
        case.source.clip_end_seconds,
        count,
        maximum_edge,
    )
    typer.echo(f"Wrote {len(frames)} Dataset A frames to {destination}")


@app.command("sample-b")
def sample_b(
    clip_id: str,
    count: int = typer.Option(60, min=1, max=750),
    maximum_edge: int = typer.Option(672, min=224, max=1920),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Sample Dataset B frames without using hidden event timing."""
    record = find_b_clip(manifest, clip_id)
    destination = ROOT / "artifacts/model_inputs/dataset_b" / clip_id / (
        f"uniform_{count}_edge_{maximum_edge}"
    )
    frames = sample_dataset_b(record, ROOT, destination, count, maximum_edge)
    typer.echo(f"Wrote {len(frames)} Dataset B frames to {destination}")


@app.command("retrieve")
def retrieve(
    index_path: Path,
    query_vector_path: Path,
    k: int = typer.Option(3, min=1),
) -> None:
    """Return cosine k-nearest Dataset A cases from precomputed embeddings."""
    index = EmbeddingIndex.load(index_path)
    query = np.load(query_vector_path, allow_pickle=False)
    for hit in index.search(query, k):
        typer.echo(f"{hit.rank}\t{hit.case_id}\t{hit.similarity:.6f}")


@app.command("ollama-check")
def ollama_check(model: str = typer.Option(..., help="Exact Ollama model tag")) -> None:
    """Verify the remote endpoint and return exact installed-model metadata."""
    load_dotenv(ROOT / ".env")
    metadata = OllamaClient().model_metadata(model)
    typer.echo(json.dumps(metadata, indent=2))


@app.command("run-pair")
def run_pair(
    clip_b_id: str,
    condition: str = typer.Option(..., help="B0 through B5 condition ID"),
    model: str = typer.Option(..., help="Exact Ollama model tag"),
    case_a_id: str | None = typer.Option(None),
    pairing_note: str = typer.Option(""),
    retrieval_score: float | None = typer.Option(None),
    retrieval_index_path: Path | None = typer.Option(None),
    frame_count_b: int = typer.Option(60, min=1, max=750, help="Dataset B frames"),
    frame_count_a: int = typer.Option(20, min=1, max=32, help="Dataset A frames"),
    maximum_edge: int = typer.Option(672, min=224, max=1344),
    config_path: Path = typer.Option(DEFAULT_CONFIG),
    manifest: Path = typer.Option(DEFAULT_B_MANIFEST),
) -> None:
    """Run one controlled Dataset A/B comparison and preserve exact artifacts."""
    config = load_json(config_path)
    if condition not in config["conditions"]:
        raise typer.BadParameter(f"Unknown condition: {condition}")
    typed_condition = cast(Condition, condition)
    record_b = find_b_clip(manifest, clip_b_id)
    require_allowed_split(config, record_b.split)

    case = None
    advice = None
    frames_a: list[Path] | None = None
    if typed_condition != "B0_frames_only":
        if typed_condition in {"B1_random_case", "B2_action_oracle"}:
            if case_a_id:
                raise typer.BadParameter(
                    f"{condition} selects Dataset A deterministically; omit --case-a-id"
                )
            library = load_library(ROOT / "data/video_a/cases")
            usable = [
                item
                for item in library.values()
                if item.status == "approved" and not item.approval_errors(ROOT)
            ]
            try:
                case = deterministic_control_case(
                    usable, record_b, typed_condition, int(config["seed"])
                )
            except ValueError as error:
                raise typer.BadParameter(str(error)) from error
        elif not case_a_id:
            raise typer.BadParameter(f"{condition} requires --case-a-id")
        else:
            case = approved_case(case_a_id)
        if (
            typed_condition == "B1_random_case"
            and normalize_action(case.situation.action_family)
            == normalize_action(record_b.action_class)
        ):
            raise typer.BadParameter("B1 requires an unrelated action family")
        if (
            typed_condition == "B2_action_oracle"
            and normalize_action(case.situation.action_family)
            != normalize_action(record_b.action_class)
        ):
            raise typer.BadParameter("B2 requires Dataset A action_family to equal hidden B action")
        if typed_condition == "B3_human_oracle" and not pairing_note.strip():
            raise typer.BadParameter("B3 requires a human pairing rationale in --pairing-note")
        if typed_condition == "B4_embedding_knn" and retrieval_score is None:
            raise typer.BadParameter("B4 requires --retrieval-score provenance")
        if typed_condition == "B4_embedding_knn" and not retrieval_index_path:
            raise typer.BadParameter("B4 requires --retrieval-index-path provenance")
        if retrieval_index_path and not retrieval_index_path.is_file():
            raise typer.BadParameter(f"Retrieval index does not exist: {retrieval_index_path}")
        advice = (ROOT / case.coaching.advice_path).read_text(encoding="utf-8")
        if typed_condition != "B5_advice_only":
            frames_a = sample_dataset_a(
                ROOT / cast(str, case.source.local_media_path),
                ROOT / "artifacts/model_inputs/dataset_a" / case.case_id / (
                    f"uniform_{frame_count_a}_edge_{maximum_edge}"
                ),
                case.source.clip_start_seconds,
                case.source.clip_end_seconds,
                frame_count_a,
                maximum_edge,
            )

    frames_b = sample_dataset_b(
        record_b,
        ROOT,
        ROOT / "artifacts/model_inputs/dataset_b" / record_b.clip_id / (
            f"uniform_{frame_count_b}_edge_{maximum_edge}"
        ),
        frame_count_b,
        maximum_edge,
    )
    case_template_path = ROOT / "input_prompts/dataset_a_case_v0.2.0.txt"
    query_template_path = ROOT / "input_prompts/dataset_b_query_v0.2.0.txt"
    messages = build_messages(
        typed_condition,
        query_template_path.read_text(encoding="utf-8"),
        frames_b,
        case,
        advice,
        case_template_path.read_text(encoding="utf-8"),
        frames_a,
    )

    load_dotenv(ROOT / ".env")
    client = OllamaClient()
    model_metadata = client.model_metadata(model)
    options = dict(config["generation"])
    think = bool(options.pop("think"))
    options.pop("stream", None)
    raw_response = client.chat(
        model=model,
        messages=messages,
        schema=ModelAnswer.model_json_schema(),
        options=options,
        think=think,
    )
    raw_text = str(raw_response.get("message", {}).get("content", ""))
    try:
        ModelAnswer.model_validate_json(raw_text)
        schema_status = "valid"
        schema_error = ""
    except Exception as error:
        schema_status = "invalid"
        schema_error = str(error)

    timestamp = timestamp_utc()
    run_dir = ROOT / "output" / condition / model.replace(":", "_") / clip_b_id / timestamp
    all_frames = (frames_a or []) + frames_b
    metadata = {
        "protocol_id": config["protocol_id"],
        "condition": condition,
        "dataset_a_case_id": case.case_id if case else None,
        "dataset_b_clip_id": record_b.clip_id,
        "dataset_b_split": record_b.split,
        "hidden_b_action_sent_to_model": False,
        "hidden_b_action_used_for_pairing": typed_condition in {
            "B1_random_case",
            "B2_action_oracle",
        },
        "pairing_note": pairing_note,
        "retrieval_score": retrieval_score,
        "retrieval_index_sha256": (
            sha256_file(retrieval_index_path) if retrieval_index_path else None
        ),
        "model": model,
        "model_digest": model_metadata.get("digest"),
        "dataset_b_frame_count": frame_count_b,
        "dataset_a_frame_count": frame_count_a if case else None,
        "maximum_edge": maximum_edge,
        "frame_sha256": {
            path.relative_to(ROOT).as_posix(): sha256_file(path) for path in all_frames
        },
        "config_sha256": sha256_file(config_path),
        "case_prompt_sha256": sha256_file(case_template_path),
        "query_prompt_sha256": sha256_file(query_template_path),
        "schema_status": schema_status,
        "schema_error": schema_error,
        "created_at_utc": timestamp,
    }
    write_run(run_dir, readable_transcript(messages, ROOT), raw_response, metadata)
    typer.echo(f"Preserved run at {run_dir}")


if __name__ == "__main__":
    app()
