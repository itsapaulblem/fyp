"""Standalone remote B25 exploratory runner/bundler. Standard library only."""
import argparse
import base64
import hashlib
import json
import tarfile
import time
import traceback
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OVERRIDE = 'config/in_context_b25_exploratory_override_v1.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads((ROOT / path).read_bytes())


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def validate():
    override = read(OVERRIDE)
    if override['coaching_allowed'] or not override['execution_allowed_for_this_variant_only']:
        raise ValueError('Exploratory recognition override required')
    frozen_path = ROOT / override['parent_freeze']
    if sha(frozen_path) != override['parent_freeze_sha256']:
        raise ValueError('Parent freeze changed')
    frozen = read(override['parent_freeze'])
    if frozen['execution_allowed']:
        raise ValueError('Expected original freeze to remain gated')
    files = set(frozen['frozen_files']) | {OVERRIDE, override['parent_freeze'],
            str(frozen_path.with_suffix('.sha256').relative_to(ROOT)).replace('\\', '/'),
            'scripts/run_in_context_pilot.py'}
    for name, expected in frozen['frozen_files'].items():
        if sha(ROOT / name) != expected:
            raise ValueError(f'Frozen input changed: {name}')
    frames = [f for example in frozen['examples'] for f in example['frames']] + frozen['query']['frames']
    if len(frames) != override.get('image_count', 120) or len(frozen['query']['frames']) != 30:
        raise ValueError('Image count differs from variant declaration')
    for frame in frames:
        if sha(ROOT / frame['path']) != frame['sha256']:
            raise ValueError(f'Image changed: {frame["path"]}')
        files.add(frame['path'])
    print(f'Validated override and all {len(frames)} frozen images; no model calls yet.', flush=True)
    return override, frozen, files


def payload(frozen, override, arm):
    messages = []
    if arm == 'with_examples':
        for index, example in enumerate(frozen['examples'], 1):
            content = example.get('message_content', f'DEMONSTRATION {index}\nImages 1-30 belong to this demonstration.\n{example["approved_description"]}\n')
            messages.append({'role': 'user', 'content': content,
                             'images': [base64.b64encode((ROOT / f['path']).read_bytes()).decode('ascii') for f in example['frames']]})
    baseline = frozen.get('query_message_content')
    if baseline is None:
        baseline = (ROOT / 'input_prompts/in_context_events/comparison_v1/baseline_prompt.v1.txt').read_text(encoding='utf-8')
    messages.append({'role': 'user', 'content': baseline,
                     'images': [base64.b64encode((ROOT / f['path']).read_bytes()).decode('ascii') for f in frozen['query']['frames']]})
    return dict(model=frozen['model'], messages=messages, options=frozen['generation']['options'],
                think=frozen['generation']['think'], stream=False, keep_alive=override['keep_alive'])


def api(route, body=None, timeout=60):
    # Local Ollama on the remote workstation; no laptop tunnel dependency.
    encoded = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request('http://127.0.0.1:11434' + route, data=encoded,
                                     headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def bundle(files, override):
    destination = ROOT / override.get('bundle_path', 'artifacts/transfer/in_context_b25_exploratory_override_v1.tar.gz')
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open('xb') as stream:
        with tarfile.open(fileobj=stream, mode='w:gz') as archive:
            for name in sorted(files):
                archive.add(ROOT / name, arcname=name, recursive=False)
    destination.with_suffix(destination.suffix + '.sha256').write_text(sha(destination) + '  ' + destination.name + '\n')
    print(f'Bundle: {destination}\nSHA-256: {sha(destination)}', flush=True)


def run(override, frozen):
    output = ROOT / override['output_root']
    # An attempted arm, including a failed one, prevents an unlabelled retry.
    output.mkdir(parents=True, exist_ok=False)
    save(output / 'approval_and_limitations.json', override)
    save(output / 'frozen_inputs.json', frozen)
    failures = []
    try:
        runtime = {name: json.loads(api(route)) for name, route in [('version', '/api/version'), ('tags', '/api/tags'), ('ps_before', '/api/ps')]}
        save(output / 'runtime_before.json', runtime)
        installed = next(m for m in runtime['tags']['models'] if m.get('name', m.get('model')) == frozen['model'])
        if installed['digest'] != frozen['expected_model_digest']:
            raise ValueError('Model digest differs from frozen input')
        for model in runtime['ps_before'].get('models', []):
            if model.get('name', model.get('model')) == frozen['model'] and model.get('size_vram', 0) != 0:
                raise ValueError('Model already GPU-resident; do not change another running request')
        (output / 'model_show.json').write_bytes(api('/api/show', {'model': frozen['model']}))
        for arm in override.get('run_arms', ['baseline', 'with_examples']):
            directory = output / arm
            directory.mkdir()
            request = payload(frozen, override, arm)
            # Exact payload retained privately; filenames and source labels are not sent.
            save(directory / 'request.json', request)
            save(directory / 'settings.json', {k: v for k, v in request.items() if k != 'messages'})
            prompt_name = 'baseline_prompt.v1.txt' if arm == 'baseline' else 'with_examples_prompt.v1.txt'
            prompt_path = frozen.get('prompt_files', {}).get(arm, 'input_prompts/in_context_events/comparison_v1/' + prompt_name)
            (directory / 'prompt.txt').write_bytes((ROOT / prompt_path).read_bytes())
            started = time.monotonic()
            status = dict(arm=arm, started_at_utc=datetime.now(timezone.utc).isoformat(),
                          image_count=sum(len(m['images']) for m in request['messages']),
                          request_sha256=sha(directory / 'request.json'), context_retention_verified=False)
            save(directory / 'status.json', dict(status, state='started'))
            print(f'Starting {arm}: {status["image_count"]} images; recognition only.', flush=True)
            try:
                raw = api('/api/chat', request, override['timeout_seconds'])
                (directory / 'raw_api_response.json').write_bytes(raw)
                result = json.loads(raw)
                (directory / 'response.txt').write_text(result['message']['content'], encoding='utf-8')
                residency = json.loads(api('/api/ps'))
                save(directory / 'residency_after.json', residency)
                model = next(m for m in residency['models'] if m.get('name', m.get('model')) == frozen['model'])
                if model.get('size_vram') != 0 or model.get('context_length') != frozen['generation']['options']['num_ctx']:
                    raise ValueError('CPU/context residency check failed; response preserved, not accepted')
                status.update(state='response_received_unverified_retention', prompt_eval_count=result.get('prompt_eval_count'),
                              eval_count=result.get('eval_count'), done_reason=result.get('done_reason'))
                print(f'Preserved {arm}: {directory}', flush=True)
            except Exception as error:
                if isinstance(error, urllib.error.HTTPError):
                    (directory / 'raw_http_error.bin').write_bytes(error.read())
                save(directory / 'error.json', dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()))
                status.update(state='failed')
                failures.append(arm)
                print(f'Failed {arm}; failure preserved; no retry.', flush=True)
            finally:
                status['elapsed_seconds'] = time.monotonic() - started
                save(directory / 'status.json', status)
    except Exception as error:
        save(output / 'batch_error.json', dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()))
        failures.append('preflight_or_batch')
    finally:
        save(output / 'batch_status.json', dict(finished=True, failures=failures, coaching_requested=False,
                                              context_retention_verified=False, results_are_exploratory=True))
        archive_path = ROOT / override.get('results_archive', 'in_context_b25_exploratory_results.tar.gz')
        with archive_path.open('xb') as stream:
            with tarfile.open(fileobj=stream, mode='w:gz') as archive:
                archive.add(output, arcname=output.relative_to(ROOT).as_posix())
        print(f'Batch ended; failures={failures}; no coaching.\nResults: {archive_path}\nSHA-256: {sha(archive_path)}', flush=True)
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--validate-only', action='store_true')
    mode.add_argument('--bundle', action='store_true')
    mode.add_argument('--run', action='store_true')
    parser.add_argument('--declaration', default=OVERRIDE)
    args = parser.parse_args()
    OVERRIDE = args.declaration
    override, frozen, files = validate()
    if args.bundle:
        bundle(files, override)
    elif args.run:
        run(override, frozen)
