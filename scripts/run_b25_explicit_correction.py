"""Separate human-assisted B25 recognition revision; standard library only."""
import argparse
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DECLARATION = 'config/b25_explicit_correction_v1.json'
spec = importlib.util.spec_from_file_location('pilot_runner', ROOT / 'scripts/run_in_context_pilot.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
runner.OVERRIDE = DECLARATION
SOURCE = 'output/in_context_events/two_corner_examples_v1/b25_exploratory_v1/with_examples/response.txt'
CORRECTION = 'input_prompts/in_context_events/b25_explicit_correction_v1/human_correction.txt'
BASELINE = 'input_prompts/in_context_events/comparison_v1/baseline_prompt.v1.txt'


def save_once(path, value):
    data = (json.dumps(value, indent=2) + '\n').encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f'Existing freeze differs: {path}')
    if not path.exists():
        path.write_bytes(data)


def prepare():
    parent_path = ROOT / 'config/freezes/two_corner_examples_v1_b25.json'
    parent = json.loads(parent_path.read_bytes())
    sidecar = parent_path.with_suffix('.sha256').read_text().split()[0]
    if runner.sha(parent_path) != sidecar:
        raise ValueError('Two-corner freeze checksum differs')
    for frame in parent['query']['frames']:
        if runner.sha(ROOT / frame['path']) != frame['sha256']:
            raise ValueError('Original B25 image changed')
    previous = (ROOT / SOURCE).read_text(encoding='utf-8')
    if not previous.strip():
        raise ValueError('Previous failed answer is empty')
    names = [SOURCE, CORRECTION, BASELINE, 'scripts/run_in_context_pilot.py',
             'scripts/run_b25_explicit_correction.py', parent_path.relative_to(ROOT).as_posix()]
    freeze = dict(experiment_id='b25_explicit_correction_v1', execution_allowed=False,
        approval='Researcher requested explicit correction that B25 is a corner kick in chat on 2026-10-11.',
        model=parent['model'], expected_model_digest=parent['expected_model_digest'], generation=parent['generation'],
        query=parent['query'], examples=[],
        frozen_files={name: runner.sha(ROOT / name) for name in names},
        prompt_files={'explicit_revision': CORRECTION},
        classification='Human-assisted recognition revision, not independent recognition or in-context comparison.',
        request_policy='Original query instruction and 30 B25 JPEGs, previous failed answer, then explicit researcher correction. No demonstration images, no other-run answers, no coaching.',
        source_answer=SOURCE, correction=CORRECTION,
        limitations=['Context retention not independently verified', 'Prior GSR source-match overlap unresolved',
                     'Researcher supplies event identity; any success is human-assisted'])
    path = ROOT / 'config/freezes/b25_explicit_correction_v1.json'
    save_once(path, freeze)
    checksum = runner.sha(path) + '  ' + path.name + '\n'
    checksum_path = path.with_suffix('.sha256')
    if checksum_path.exists() and checksum_path.read_text() != checksum:
        raise ValueError('Existing checksum differs')
    if not checksum_path.exists():
        checksum_path.write_text(checksum)
    declaration = dict(variant='b25_explicit_correction_v1', approval=freeze['approval'],
        parent_freeze=path.relative_to(ROOT).as_posix(), parent_freeze_sha256=runner.sha(path),
        execution_allowed_for_this_variant_only=True, coaching_allowed=False, image_count=30,
        run_arms=['explicit_revision'], keep_alive='10m', timeout_seconds=14400, retries=0,
        output_root='output/in_context_events/b25_explicit_correction_v1/recognition_revision',
        bundle_path='artifacts/transfer/b25_explicit_correction_v1.tar.gz',
        results_archive='b25_explicit_correction_v1_results.tar.gz',
        waived_gates=freeze['limitations'])
    save_once(ROOT / DECLARATION, declaration)


def corrected_payload(frozen, override, arm):
    import base64
    messages = [
        dict(role='user', content=(ROOT / BASELINE).read_text(encoding='utf-8'),
             images=[base64.b64encode((ROOT / f['path']).read_bytes()).decode('ascii') for f in frozen['query']['frames']]),
        dict(role='assistant', content=(ROOT / SOURCE).read_text(encoding='utf-8')),
        dict(role='user', content=(ROOT / CORRECTION).read_text(encoding='utf-8'))]
    return dict(model=frozen['model'], messages=messages, options=frozen['generation']['options'],
                think=frozen['generation']['think'], stream=False, keep_alive=override['keep_alive'])


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
        runner.run(override, frozen)
