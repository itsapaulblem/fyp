"""Freeze and audit the B25 pilot inputs. No network or inference calls."""
import csv
import hashlib
import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np

from .event_examples import CONFIG, ROOT, verify

BASE = ROOT / 'artifacts/in_context_events/v1'
PROMPTS = ROOT / 'input_prompts/in_context_events/comparison_v1'
AUDIT = ROOT / 'artifacts/in_context_events/comparison_v1/private_audit.json'
EXAMPLES = ['E-0016', 'E-0009', 'E-0023']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_once(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f'Existing frozen file differs: {path}')
    else:
        path.write_bytes(data)


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def perceptual(path):
    gray = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if gray is None:
        raise ValueError(f'Cannot decode {path}')
    small = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    dct = cv2.dct(cv2.resize(gray, (32, 32), interpolation=cv2.INTER_AREA).astype(np.float32))[:8, :8].flatten()[1:]
    def number(bits):
        return int(''.join('1' if b else '0' for b in bits.flatten()), 2)
    return number(dct > np.median(dct)), number(small[:, 1:] > small[:, :-1])


def prepare():
    verify(CONFIG)
    amendment_path = ROOT / 'config/in_context_event_media_amendment_v1.json'
    rejected = {r['rejected_clip_id'] for r in json.loads(amendment_path.read_bytes())['replacements']}
    records = [json.loads(p.read_bytes()) for p in sorted((BASE / 'media_records/clips').glob('*.json'))]
    records = [r for r in records if r['candidate']['clip_id'] not in rejected]
    if len(records) != 180:
        raise ValueError('Expected 180 active clips')
    inventory, roles = [], defaultdict(set)
    for record in records:
        row = record['candidate']
        roles[row['match_group']].add(row['role'])
        if len(record['frames']) != 30:
            raise ValueError('Wrong frame count')
        for frame in record['frames']:
            if sha(ROOT / frame['path']) != frame['sha256']:
                raise ValueError(f'Frame changed: {frame["path"]}')
            inventory.append(dict(frame, clip_id=row['clip_id'], role=row['role']))
    if any(len(v) > 1 for v in roles.values()):
        raise ValueError('Match crosses roles')
    original = ROOT / 'output/v0.4/prompt_chain/P1_human_guided/B-TRAIN-0025/20260927T104444767548Z/metadata.txt'
    line = next(s for s in original.read_text().splitlines() if s.startswith('frame_sha256:'))
    expected = json.loads(line.split(':', 1)[1])
    query = sorted((ROOT / 'artifacts/model_inputs/dataset_b/B-TRAIN-0025/uniform_30_edge_672').glob('*.jpg'))
    if len(query) != 30 or set(expected) != {p.relative_to(ROOT).as_posix() for p in query}:
        raise ValueError('B25 sampling differs from original P1')
    for index, path in enumerate(query, 1):
        relative = path.relative_to(ROOT).as_posix()
        if sha(path) != expected[relative]:
            raise ValueError(f'B25 frame changed: {path}')
        inventory.append(dict(path=relative, sha256=sha(path), clip_id='B-TRAIN-0025', role='known_b_train_pilot', sample_position_1_based=index))
    print('Verified 5,400 dataset images and 30 original B25 images.', flush=True)
    exact = defaultdict(list)
    for frame in inventory:
        exact[frame['sha256']].append(frame)
    exact_groups = [g for g in exact.values() if len({f['role'] for f in g}) > 1]
    hashes = [perceptual(ROOT / f['path']) for f in inventory]
    near = []
    for i, (ph, dh) in enumerate(hashes):
        for j in range(i):
            if inventory[i]['role'] == inventory[j]['role']:
                continue
            pd = (ph ^ hashes[j][0]).bit_count()
            if pd <= 4:
                dd = (dh ^ hashes[j][1]).bit_count()
                if dd <= 4:
                    near.append(dict(left=inventory[j]['path'], right=inventory[i]['path'], phash_distance=pd, dhash_distance=dd,
                                     left_clip=inventory[j]['clip_id'], right_clip=inventory[i]['clip_id']))
    print(f'Cross-role exact groups: {len(exact_groups)}; perceptual candidates: {len(near)}.', flush=True)
    with (ROOT / 'data/video_b/private/soccernet_gsr_v1.3_reference.csv').open(encoding='utf-8') as stream:
        train = [r for r in csv.DictReader(stream) if r['split'] == 'train']
    with zipfile.ZipFile(ROOT / 'data/raw/gamestate/gamestate-2024/train.zip') as archive:
        gsr_ids = {r['clip_id']: json.loads(archive.read(r['label_member']))['info']['game_id'] for r in train}
    audit = dict(scope='180 active new clips plus B25; train metadata only; no held-out visual review', image_count=len(inventory),
                 match_overlap_across_internal_roles=0, exact_cross_role_groups=exact_groups, near_duplicate_candidates=near,
                 method='SHA-256; 63-bit grayscale DCT pHash and 64-bit dHash, both Hamming distances <=4; full-image only',
                 limitations='Heuristic screen cannot rule out crops, overlays or replays. Candidate pairs require human review.',
                 prior_gsr_match_overlap=dict(status='unresolved', train_game_ids=gsr_ids,
                     reason='Numeric GSR game_id has no locally available authoritative mapping to SoccerNet match paths. Never infer from list order.'),
                 execution_allowed=False)
    save_once(AUDIT, encoded(audit))
    description = PROMPTS / 'example_descriptions.txt'
    save_once(PROMPTS / 'example_descriptions.approved_v1.txt', description.read_bytes())
    chunks = re.split(r'EXAMPLE (E-\d{4})\s*\n', description.read_text(encoding='utf-8'))[1:]
    texts = dict(zip(chunks[0::2], chunks[1::2]))
    examples = []
    for clip_id in EXAMPLES:
        record = next(r for r in records if r['candidate']['clip_id'] == clip_id)
        if record['candidate']['role'] != 'example':
            raise ValueError('Demonstration outside example split')
        examples.append(dict(clip_id=clip_id, approved_description=texts[clip_id].strip(), frames=record['frames']))
    instruction = (ROOT / 'input_prompts/v0.4/p1_recognition.txt').read_bytes()
    save_once(PROMPTS / 'recognition_instruction.v1.txt', instruction)
    baseline = b'QUERY\nImages 1-30 belong to the query sequence.\n\n' + instruction
    packet = ''.join(f'DEMONSTRATION {i}\nImages 1-30 belong to this demonstration.\n{e["approved_description"]}\n\n' for i, e in enumerate(examples, 1))
    save_once(PROMPTS / 'baseline_prompt.v1.txt', baseline)
    save_once(PROMPTS / 'with_examples_prompt.v1.txt', packet.encode() + baseline)
    frozen_files = [PROMPTS / name for name in ['example_descriptions.approved_v1.txt','recognition_instruction.v1.txt','baseline_prompt.v1.txt','with_examples_prompt.v1.txt']]
    frozen_files += [AUDIT, amendment_path, ROOT / 'config/freezes/in_context_event_selection_v1.json', Path(__file__)]
    freeze = dict(experiment_id='in_context_comparison_v1_b25_pilot', status='approved_examples_and_prompts_frozen_execution_gated',
        approval=dict(date='2026-10-11', source='researcher approval in chat', blinded=False, scope=EXAMPLES),
        query=dict(clip_id='B-TRAIN-0025', classification='known development pilot, not unseen evaluation', frames=inventory[-30:]), examples=examples,
        model='qwen3.5:27b', expected_model_digest='193ec05b1e8048df17f7b8d15528671ae40e1a25cf4e0f5416c02b9cac5b990c',
        generation=dict(options=dict(temperature=0, seed=20260903, num_ctx=32768, num_gpu=0), think=False, stream=False),
        device_policy='CPU-only in both arms; verify digest and /api/ps residency before execution',
        request_policy='Separate fresh requests; no prior answers, corrections, query labels or references; no coaching',
        payload_order=dict(baseline=['query:30 ordered JPEGs','recognition instruction'], with_examples=['demo1:30 JPEGs + description','demo2:30 JPEGs + description','demo3:30 JPEGs + description','query:30 JPEGs','same recognition instruction']),
        images_per_request=dict(baseline=30, with_examples=120),
        frozen_files={p.relative_to(ROOT).as_posix():sha(p) for p in frozen_files}, execution_allowed=False,
        outstanding_gates=['Authoritative prior GSR match mapping','Review any cross-role duplicate candidates','Verify 120-image payload/context capacity without silent truncation on development only','Verify current model digest and CPU residency'],
        full_dataset_reference_review='pending; three example approvals do not approve other clips')
    path = ROOT / 'config/freezes/in_context_comparison_v1_b25.json'
    save_once(path, encoded(freeze))
    save_once(path.with_suffix('.sha256'), (sha(path) + '  ' + path.name + '\n').encode())
    print(f'Frozen at {path}; execution remains gated.')


if __name__ == '__main__':
    prepare()
