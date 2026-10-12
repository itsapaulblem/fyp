"""Labelled retry of the pre-request images-field failure; no silent reruns."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('explicit_correction', ROOT / 'scripts/run_b25_explicit_correction.py')
correction = importlib.util.module_from_spec(spec)
spec.loader.exec_module(correction)
runner = correction.runner
DECLARATION = 'config/b25_explicit_correction_retry_v1.json'
runner.OVERRIDE = DECLARATION


def corrected_payload(frozen, override, arm):
    request = correction.corrected_payload(frozen, override, arm)
    # Text-only assistant/feedback messages legitimately have zero images.
    # This preserves the frozen original runner while repairing its assumption.
    for message in request['messages']:
        message.setdefault('images', [])
    if sum(len(m['images']) for m in request['messages']) != 30:
        raise ValueError('Retry must retain exactly the same 30 query images')
    return request


def prepare():
    parent_declaration = json.loads((ROOT / 'config/b25_explicit_correction_v1.json').read_bytes())
    parent_path = ROOT / parent_declaration['parent_freeze']
    if runner.sha(parent_path) != parent_declaration['parent_freeze_sha256']:
        raise ValueError('Original correction freeze changed')
    frozen = json.loads(parent_path.read_bytes())
    for name, expected in frozen['frozen_files'].items():
        if runner.sha(ROOT / name) != expected:
            raise ValueError(f'Original frozen input changed: {name}')
    frozen['experiment_id'] = 'b25_explicit_correction_retry_v1'
    frozen['retry_provenance'] = {
        'parent_variant': 'b25_explicit_correction_v1',
        'reason': "Researcher supplied remote traceback: KeyError 'images' while counting text-only messages, before /api/chat.",
        'fix': 'Add empty images arrays to text-only messages; query images, previous answer, correction and settings unchanged.',
        'failed_attempt_policy': 'Keep original remote output and its error archive intact; new output path only.'}
    frozen['frozen_files'][parent_path.relative_to(ROOT).as_posix()] = runner.sha(parent_path)
    frozen['frozen_files']['config/b25_explicit_correction_v1.json'] = runner.sha(ROOT / 'config/b25_explicit_correction_v1.json')
    frozen['frozen_files']['scripts/run_b25_explicit_correction_retry.py'] = runner.sha(Path(__file__))
    freeze_path = ROOT / 'config/freezes/b25_explicit_correction_retry_v1.json'
    correction.save_once(freeze_path, frozen)
    checksum = runner.sha(freeze_path) + '  ' + freeze_path.name + '\n'
    sidecar = freeze_path.with_suffix('.sha256')
    if sidecar.exists() and sidecar.read_text() != checksum:
        raise ValueError('Retry checksum changed')
    if not sidecar.exists():
        sidecar.write_text(checksum)
    declaration = dict(parent_declaration)
    declaration.update(variant='b25_explicit_correction_retry_v1',
        parent_freeze=freeze_path.relative_to(ROOT).as_posix(), parent_freeze_sha256=runner.sha(freeze_path),
        output_root='output/in_context_events/b25_explicit_correction_v1/recognition_revision_retry_v1',
        bundle_path='artifacts/transfer/b25_explicit_correction_retry_v1.tar.gz',
        results_archive='b25_explicit_correction_retry_v1_results.tar.gz')
    correction.save_once(ROOT / DECLARATION, declaration)
    # Offline regression check; no Ollama endpoint is contacted.
    request = corrected_payload(frozen, declaration, 'explicit_revision')
    assert [m['role'] for m in request['messages']] == ['user', 'assistant', 'user']
    assert [len(m['images']) for m in request['messages']] == [30, 0, 0]
    print('Offline images-field regression check passed; no model calls.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--bundle', action='store_true')
    mode.add_argument('--validate-only', action='store_true')
    mode.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.bundle:
        prepare()
    override, frozen, files = runner.validate()
    runner.payload = corrected_payload
    if args.bundle:
        runner.bundle(files, override)
    elif args.run:
        run_check = corrected_payload(frozen, override, 'explicit_revision')
        assert [len(m['images']) for m in run_check['messages']] == [30, 0, 0]
        runner.run(override, frozen)
