"""Separate label-conditioned coaching probe; never approves recognition."""
import argparse
import base64
import importlib.util
import json
import tarfile
import time
import traceback
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pilot_helpers', ROOT / 'scripts/run_in_context_pilot.py')
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
FREEZE = 'config/freezes/b25_corner_conditioned_coaching_v1.json'
PROMPT = 'input_prompts/in_context_events/b25_corner_conditioned_coaching_v1/coaching_prompt.txt'
ANSWER = 'output/in_context_events/b25_explicit_correction_v1/recognition_revision_retry_v1/explicit_revision/response.txt'
BASELINE = 'input_prompts/in_context_events/comparison_v1/baseline_prompt.v1.txt'
OUTPUT = 'output/in_context_events/b25_corner_conditioned_coaching_v1/exploratory_probe_v1'


def save_once(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f'Preserved artifact differs: {path}')
    if not path.exists():
        path.write_bytes(data)


def prepare():
    parent_path = ROOT / 'config/freezes/b25_explicit_correction_retry_v1.json'
    if helpers.sha(parent_path) != parent_path.with_suffix('.sha256').read_text().split()[0]:
        raise ValueError('Recognition retry freeze changed')
    parent = json.loads(parent_path.read_bytes())
    if not (ROOT / ANSWER).read_text(encoding='utf-8').strip():
        raise ValueError('Failed recognition answer is empty')
    names = [PROMPT, ANSWER, BASELINE, parent_path.relative_to(ROOT).as_posix(),
             'scripts/run_in_context_pilot.py', 'scripts/run_b25_corner_coaching_probe.py']
    frozen = dict(variant='b25_corner_conditioned_coaching_v1',
        approval='Researcher requested the corner-conditioned coaching prompt and remote tmux preparation in chat on 2026-10-11.',
        model=parent['model'], expected_model_digest=parent['expected_model_digest'], generation=parent['generation'],
        query=parent['query'], frozen_files={name: helpers.sha(ROOT / name) for name in names},
        recognition_approved=False, coaching_requested=True, exploratory_only=True,
        request_policy='Condensed continuation: original query instruction and 30 B25 JPEGs; failed revised answer; new researcher-supplied corner coaching prompt. No demonstration images or other-run answers.',
        keep_alive='10m', timeout_seconds=14400, retries=0, output_root=OUTPUT,
        limitations=['Event supplied by researcher, not independent recognition', 'Recognition remains unapproved',
                     'Coaching must be reviewed before use', 'Prior match overlap and context retention remain unresolved'])
    path = ROOT / FREEZE
    save_once(path, (json.dumps(frozen, indent=2) + '\n').encode())
    save_once(path.with_suffix('.sha256'), (helpers.sha(path) + '  ' + path.name + '\n').encode())


def validate():
    path = ROOT / FREEZE
    if helpers.sha(path) != path.with_suffix('.sha256').read_text().split()[0]:
        raise ValueError('Coaching freeze checksum differs')
    frozen = json.loads(path.read_bytes())
    if frozen['recognition_approved'] or not frozen['exploratory_only'] or not frozen['coaching_requested']:
        raise ValueError('Expected separate unapproved-recognition coaching probe')
    files = set(frozen['frozen_files']) | {FREEZE, path.with_suffix('.sha256').relative_to(ROOT).as_posix()}
    for name, expected in frozen['frozen_files'].items():
        if helpers.sha(ROOT / name) != expected:
            raise ValueError(f'Frozen input changed: {name}')
    if len(frozen['query']['frames']) != 30:
        raise ValueError('Expected 30 original query images')
    for frame in frozen['query']['frames']:
        if helpers.sha(ROOT / frame['path']) != frame['sha256']:
            raise ValueError(f'Frame changed: {frame["path"]}')
        files.add(frame['path'])
    print('Validated 30 B25 images, failed answer and coaching prompt; no model calls yet.', flush=True)
    return frozen, files


def payload(frozen):
    messages = [dict(role='user', content=(ROOT / BASELINE).read_text(encoding='utf-8'),
        images=[base64.b64encode((ROOT / f['path']).read_bytes()).decode('ascii') for f in frozen['query']['frames']]),
        dict(role='assistant', content=(ROOT / ANSWER).read_text(encoding='utf-8'), images=[]),
        dict(role='user', content=(ROOT / PROMPT).read_text(encoding='utf-8'), images=[])]
    if [len(m['images']) for m in messages] != [30, 0, 0]:
        raise ValueError('Unexpected input layout')
    return dict(model=frozen['model'], messages=messages, options=frozen['generation']['options'],
                think=frozen['generation']['think'], stream=False, keep_alive=frozen['keep_alive'])


def run(frozen):
    output = ROOT / frozen['output_root']
    output.mkdir(parents=True, exist_ok=False)
    helpers.save(output / 'frozen_inputs.json', frozen)
    request = payload(frozen)
    helpers.save(output / 'request.json', request)
    helpers.save(output / 'settings.json', {k:v for k,v in request.items() if k != 'messages'})
    (output / 'prompt.txt').write_bytes((ROOT / PROMPT).read_bytes())
    started = time.monotonic()
    status = dict(started_at_utc=datetime.now(timezone.utc).isoformat(), image_count=30,
                  coaching_requested=True, recognition_approved=False, exploratory_only=True,
                  context_retention_verified=False, request_sha256=helpers.sha(output / 'request.json'), state='preflight')
    helpers.save(output / 'status.json', status)
    failed = False
    try:
        runtime = {key: json.loads(helpers.api(route)) for key,route in [('version','/api/version'),('tags','/api/tags'),('ps_before','/api/ps')]}
        helpers.save(output / 'runtime_before.json', runtime)
        installed = next(m for m in runtime['tags']['models'] if m.get('name',m.get('model')) == frozen['model'])
        if installed['digest'] != frozen['expected_model_digest']:
            raise ValueError('Model digest mismatch')
        for model in runtime['ps_before'].get('models', []):
            if model.get('name',model.get('model')) == frozen['model'] and model.get('size_vram', 0) != 0:
                raise ValueError('Model already GPU-resident; do not interfere with another request')
        print('Starting exploratory coaching probe: 30 images; recognition remains unapproved.', flush=True)
        status['state'] = 'request_started'
        helpers.save(output / 'status.json', status)
        raw = helpers.api('/api/chat', request, frozen['timeout_seconds'])
        (output / 'raw_api_response.json').write_bytes(raw)
        result = json.loads(raw)
        (output / 'response.txt').write_text(result['message']['content'], encoding='utf-8')
        residency = json.loads(helpers.api('/api/ps'))
        helpers.save(output / 'residency_after.json', residency)
        model = next(m for m in residency['models'] if m.get('name',m.get('model')) == frozen['model'])
        if model.get('size_vram') != 0 or model.get('context_length') != frozen['generation']['options']['num_ctx']:
            raise ValueError('CPU/context residency mismatch; answer preserved, not accepted')
        status.update(state='response_received_review_pending', prompt_eval_count=result.get('prompt_eval_count'),
                      eval_count=result.get('eval_count'), done_reason=result.get('done_reason'))
        print(f'Preserved exploratory coaching response: {output}', flush=True)
    except Exception as error:
        failed = True
        if isinstance(error, urllib.error.HTTPError):
            (output / 'raw_http_error.bin').write_bytes(error.read())
        helpers.save(output / 'error.json', dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()))
        status['state'] = 'failed'
    finally:
        status['elapsed_seconds'] = time.monotonic() - started
        helpers.save(output / 'status.json', status)
        archive_path = ROOT / 'b25_corner_conditioned_coaching_v1_results.tar.gz'
        with archive_path.open('xb') as stream:
            with tarfile.open(fileobj=stream, mode='w:gz') as archive:
                archive.add(output, arcname=output.relative_to(ROOT).as_posix())
        print(f'Probe ended; failed={failed}; review before use.\nResults: {archive_path}\nSHA-256: {helpers.sha(archive_path)}', flush=True)
    if failed:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--bundle', action='store_true')
    mode.add_argument('--validate-only', action='store_true')
    mode.add_argument('--run', action='store_true')
    args = parser.parse_args()
    if args.bundle:
        prepare()
    frozen, files = validate()
    payload(frozen)  # Offline regression check; no model endpoint contacted.
    if args.bundle:
        helpers.bundle(files, {'bundle_path':'artifacts/transfer/b25_corner_conditioned_coaching_v1.tar.gz'})
    elif args.run:
        run(frozen)
