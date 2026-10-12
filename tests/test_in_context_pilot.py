import importlib.util
import json
from pathlib import Path


def load_runner():
    path = Path(__file__).resolve().parents[1] / 'scripts/run_in_context_pilot.py'
    spec = importlib.util.spec_from_file_location('pilot_runner', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fresh_requests_same_query_and_settings(tmp_path):
    module = load_runner()
    module.ROOT = tmp_path
    prompt = tmp_path / 'input_prompts/in_context_events/comparison_v1/baseline_prompt.v1.txt'
    prompt.parent.mkdir(parents=True)
    prompt.write_text('Describe the query; no coaching.', encoding='utf-8')
    (tmp_path / 'image.jpg').write_bytes(b'jpeg-bytes')
    frames = [{'path': 'image.jpg'}] * 30
    frozen = {'model': 'qwen3.5:27b', 'query': {'frames': frames},
              'examples': [{'frames': frames, 'approved_description': 'Example only.'}] * 3,
              'generation': {'options': {'num_ctx': 32768, 'num_gpu': 0}, 'think': False}}
    override = {'keep_alive': '10m'}
    baseline = module.payload(frozen, override, 'baseline')
    examples = module.payload(frozen, override, 'with_examples')
    assert len(baseline['messages']) == 1
    assert len(examples['messages']) == 4
    assert baseline['messages'][-1] == examples['messages'][-1]
    assert sum(len(m['images']) for m in examples['messages']) == 120
    assert all(m['role'] == 'user' for m in examples['messages'])
    assert baseline['options'] == examples['options']
    assert 'image.jpg' not in str(examples['messages'])


def test_two_corner_frozen_payload():
    module = load_runner()
    freeze = module.ROOT / 'config/freezes/two_corner_examples_v1_b25.json'
    if not freeze.exists():
        return  # Private/generated freeze is not required in a clean checkout.
    frozen = json.loads(freeze.read_bytes())
    declaration = json.loads((module.ROOT / 'config/two_corner_b25_exploratory_v1.json').read_bytes())
    request = module.payload(frozen, declaration, 'with_examples')
    assert len(request['messages']) == 3
    assert sum(len(m['images']) for m in request['messages']) == 90
    assert 'BEGIN DEMONSTRATION 1' in request['messages'][0]['content']
    assert 'BEGIN DEMONSTRATION 2' in request['messages'][1]['content']
    assert request['messages'][2]['content'].startswith('BEGIN QUERY')
    assert 'Event: Corner kick.' not in request['messages'][2]['content']
    assert declaration['run_arms'] == ['with_examples']
    assert declaration['coaching_allowed'] is False
