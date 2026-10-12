"""Create the researcher-approved two-corner freeze; no model requests."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROMPTS = ROOT / 'input_prompts/in_context_events/two_corner_examples_v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_once(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != data:
        raise ValueError(f'Frozen artifact differs: {path}')
    if not path.exists():
        path.write_bytes(data)


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def main():
    parent_path = ROOT / 'config/freezes/in_context_comparison_v1_b25.json'
    if sha(parent_path) != '50142163fa3cc2545552ce43169a84a53076234960a71a240ee2865067f79a41':
        raise ValueError('Original freeze changed')
    parent = json.loads(parent_path.read_bytes())
    second_path = ROOT / 'artifacts/in_context_events/v1/media_records/clips/E-0017.json'
    second = json.loads(second_path.read_bytes())
    if second['candidate']['role'] != 'example' or len(second['frames']) != 30:
        raise ValueError('Second example must contain 30 example-split images')
    if second['candidate']['match_group'] == json.loads((ROOT / 'artifacts/in_context_events/v1/media_records/clips/E-0016.json').read_bytes())['candidate']['match_group']:
        raise ValueError('Examples must be from different matches')
    for frame in parent['examples'][0]['frames'] + second['frames'] + parent['query']['frames']:
        if sha(ROOT / frame['path']) != frame['sha256']:
            raise ValueError(f'Image changed: {frame["path"]}')
    prompt = (PROMPTS / 'with_examples_prompt.draft.txt').read_text(encoding='utf-8')
    sections = re.findall(r'BEGIN DEMONSTRATION (\d) — 30 ORDERED IMAGES\n(.*?)\nEND DEMONSTRATION \1', prompt, re.S)
    if [i for i, text in sections] != ['1', '2']:
        raise ValueError('Expected two demonstration blocks')
    if sections[0][1].strip() != parent['examples'][0]['approved_description']:
        raise ValueError('Previously approved example wording differs')
    query_content = prompt.split('BEGIN QUERY — 30 ORDERED IMAGES\n', 1)[1].split('\n\nEND QUERY', 1)[0]
    baseline_path = ROOT / 'input_prompts/in_context_events/comparison_v1/baseline_prompt.v1.txt'
    if query_content.strip() != baseline_path.read_text(encoding='utf-8').strip():
        raise ValueError('Query instruction changed')
    approved_prompt = PROMPTS / 'with_examples_prompt.approved_v1.txt'
    approved_descriptions = PROMPTS / 'example_descriptions.approved_v1.txt'
    save_once(approved_prompt, (PROMPTS / 'with_examples_prompt.draft.txt').read_bytes())
    save_once(approved_descriptions, encoded({'approval': 'Researcher approved E-0017 and the two-corner prompt in chat on 2026-10-11; not blinded references.',
                                            'examples': [{'clip_id': clip, 'description': text.strip()} for clip, (_, text) in zip(['E-0016','E-0017'], sections)]}))
    prefix = prompt.split('BEGIN DEMONSTRATION 1', 1)[0]
    examples = []
    for index, (clip, (_, description), frames) in enumerate(zip(['E-0016', 'E-0017'], sections, [parent['examples'][0]['frames'], second['frames']]), 1):
        content = (prefix if index == 1 else '') + f'BEGIN DEMONSTRATION {index} — 30 ORDERED IMAGES\n{description}\nEND DEMONSTRATION {index}\n'
        examples.append(dict(clip_id=clip, approved_description=description.strip(), message_content=content, frames=frames))
    files = [approved_prompt, approved_descriptions, parent_path, parent_path.with_suffix('.sha256'),
             ROOT / 'scripts/run_in_context_pilot.py', Path(__file__), baseline_path,
             ROOT / 'artifacts/in_context_events/comparison_v1/private_audit.json', second_path]
    audit = json.loads(files[-2].read_bytes())
    if any(clip in {p['left_clip'], p['right_clip']} for p in audit['near_duplicate_candidates'] for clip in ['E-0016','E-0017','B-TRAIN-0025']):
        raise ValueError('Selected input has unresolved perceptual duplicate candidate')
    frozen = dict(experiment_id='two_corner_examples_v1_b25_exploratory', execution_allowed=False,
        approval='Researcher approved descriptions, prompt freeze and preparation of separate remote exploratory run on 2026-10-11.',
        model=parent['model'], expected_model_digest=parent['expected_model_digest'], generation=parent['generation'],
        examples=examples, query=parent['query'], query_message_content='BEGIN QUERY — 30 ORDERED IMAGES\n' + query_content + '\n\nEND QUERY\n',
        prompt_files={'with_examples': approved_prompt.relative_to(ROOT).as_posix()},
        frozen_files={p.relative_to(ROOT).as_posix(): sha(p) for p in files},
        image_count=90, prior_baseline_reference='Earlier 30-image B25 baseline preserved; not rerun or treated as paired unseen evaluation.',
        limitations=['Known B25 development pilot', 'Prior GSR source-match overlap unresolved', 'Context retention unverified',
                     'Corner-only demonstrations may bias output', 'Both category balance and boundary wording differ from previous pilot'],
        coaching_allowed=False)
    freeze_path = ROOT / 'config/freezes/two_corner_examples_v1_b25.json'
    save_once(freeze_path, encoded(frozen))
    save_once(freeze_path.with_suffix('.sha256'), (sha(freeze_path) + '  ' + freeze_path.name + '\n').encode())
    declaration = dict(variant='two_corner_examples_v1_b25_exploratory', approval=frozen['approval'],
        parent_freeze=freeze_path.relative_to(ROOT).as_posix(), parent_freeze_sha256=sha(freeze_path),
        execution_allowed_for_this_variant_only=True, coaching_allowed=False, image_count=90, run_arms=['with_examples'],
        keep_alive='10m', timeout_seconds=14400, retries=0, waived_gates=frozen['limitations'],
        output_root='output/in_context_events/two_corner_examples_v1/b25_exploratory_v1',
        bundle_path='artifacts/transfer/two_corner_b25_exploratory_v1.tar.gz',
        results_archive='two_corner_b25_exploratory_v1_results.tar.gz')
    save_once(ROOT / 'config/two_corner_b25_exploratory_v1.json', encoded(declaration))
    print(f'Frozen approved text and all 90 images: {freeze_path}; no model requests.')


if __name__ == '__main__':
    main()
