# Dataset card: SoccerNet coaching evaluation corpus

## Status

Verified local dataset built from all public clips in the official SoccerNet
Game State Reconstruction v1.3 train, validation, and test archives.

| Split | Clips | Frames | Duration |
|---|---:|---:|---:|
| Train | 57 | 42,750 | 28.5 min |
| Validation | 58 | 43,500 | 29 min |
| Test | 49 | 36,750 | 24.5 min |
| **Total** | **164** | **123,000** | **82 min** |

Every clip is a 30-second, 25-fps sequence of 750 JPEG frames with one
`Labels-GameState.json` file. All labels report version 1.3. The labels combine
the SoccerNet-Tracking object layer (including the ball) with GSR athlete,
team, role, jersey, pitch-position, and calibration information.

## Verified action distribution

| Official anchor action | Clips |
|---|---:|
| Clearance | 18 |
| Corner | 17 |
| Direct free-kick | 16 |
| Foul | 16 |
| Goal | 15 |
| Kick-off | 15 |
| Offside | 12 |
| Penalty | 1 |
| Shots off target | 17 |
| Shots on target | 15 |
| Substitution | 8 |
| Yellow card | 14 |

The corpus is reasonably distributed across its 11 intended common anchor
classes, except that only one penalty occurs in the public clips. There is no
indirect-free-kick anchor clip.

## Requested scenario coverage

| Requested scenario | Verified status |
|---|---|
| Corner | 17 official anchor clips |
| Direct free kick | 16 official anchor clips |
| Indirect free kick | Not present as an anchor class |
| Penalty | 1 official anchor clip; insufficient for category-level claims |
| Shots | 32 official anchor clips |
| Goals | 15 official anchor clips |
| Fouls | 16 official anchor clips |
| Clearance | 18 official anchor clips |

No oversampling is performed. Repeating the single penalty clip would not add
independent evidence and would make evaluation results misleading.

## Published-count discrepancy

The SoccerNet task page advertises 57 train, 59 validation, and 50 test clips
(166 public clips). The downloaded v1.3 archives contain 57, 58, and 49 label
files respectively. Their bundled official `sequences_info.json` independently
lists the same 57/58/49 counts. The project therefore reports the 164 clips
that actually exist rather than creating placeholder records.

## Intended use

This corpus supports objective evaluation of whether an MLLM can ground its
analysis in visible football state:

- player, goalkeeper, referee, and ball localization;
- temporal object identity and movement;
- team, role, and visible jersey identification;
- player locations on the pitch;
- recognition and explanation of the official anchor event.

It does not contain ground-truth coaching advice. Tactical recommendation
quality will require a separate expert-authored rubric in a later project
phase.

## Storage and access

The three official archives remain compressed under `data/raw` and are
excluded from Git because the source data is subject to SoccerNet access
terms. The canonical dataset manifest is `data/processed/manifest.csv`.
Archive SHA-256 hashes and aggregate statistics are in
`data/processed/summary.json`.

## Project-derived reference analytics

All 164 clips have a hidden, project-derived analytics layer under
`data/processed/reference_analytics/`. The canonical entry point is
`data/processed/reference_analytics/all_clips_index.csv`; its validation report
is `all_clips_index_validation.json` and its aggregate description is
`all_splits_summary.json`.

The index links each official clip to its per-frame object positions, direct
spatial metrics, coordinate-check aid, and three event-relative window rows.
It also records structural validity, coverage, missing-coordinate warnings,
and one of four availability tiers:

- `fully_eligible`: shape and ball metric families are eligible in all windows;
- `partially_eligible`: at least one metric family is eligible in a window;
- `tracking_only`: official tracking exists but no window metric family passes;
- `invalid`: structural validation failed.

The validated index contains 33 `fully_eligible`, 127 `partially_eligible`,
four `tracking_only`, and zero `invalid` clips. These tiers describe metric
availability, not football quality or MLLM performance.

The implemented derived metrics are visible-team width, depth, centroid and
compactness, nearest left/right team athlete to the ball, players from each
team within 10 metres of the ball, and eligible changes across the `before`,
`around`, and `after` windows. Missing measurements remain blank, never zero.

These analytics are private reference evidence. The MLLM input condition must
not read the master index, label JSON, per-frame metric tables, window tables,
coordinate checks, quality-control fields, or official event labels.
