# Single-reviewer pilot evaluation

This directory is the project author's human-reference workspace for the 12
train-pilot clips. There is one Markdown form per clip under
`pilot_references/`, plus `pilot_review_index.csv` for progress tracking.

## Why a human reference is required

SoccerNet supplies object tracking and an anchor action, but it does not supply
ground-truth tactical problems or coaching recommendations. A human reference
provides the missing interpretation needed to judge whether Qwen understood
the visible sequence and whether its advice follows from that sequence.

The reference does not make one person's opinion universally correct. Record
visible evidence, uncertainty, and non-measurable claims so the judgement can
be audited.

## Single-reviewer design

The project has one reviewer: the project author. Do not calculate or report
inter-rater agreement. In the final report, state that coaching-quality scores
are single-rater judgements and therefore subject to reviewer bias.

The pilot review is also non-blinded because the reviewer inspected model
outputs and labels before these forms were created. Record that limitation
honestly. For validation and test, review the model input before revealing the
official label or analytics whenever practical.

## Review order

1. Inspect the exact 16 uniform frames.
2. Complete the human-observation and human-coaching sections.
3. Read the original coaching response and score it using the 0–2 rubric.
4. Read the recognition-only response and complete the recognition gate.
5. Reveal/check the official SoccerNet anchor and tracking data.
6. Distinguish verified SoccerNet metadata from human judgement.

Judge Qwen against what was visible in the same 16 frames. If you also inspect
all 750 source frames, record information missing from the sample separately.

## Full review videos

Silent 30-second MP4s for all 12 clips are in
`data/processed/review_videos/`. Every video contains all 750 official JPEG
frames at 25 fps and 1920×1080. The conversion manifest records source paths,
codec, dimensions, file sizes, and SHA-256 checksums.

Use these videos to understand the complete sequence and fill the optional
full-sequence section. Qwen did not receive these MP4s or all 750 frames.
Therefore:

- score visual grounding against the 16 sampled frames Qwen actually received;
- use the MP4 to identify what the sparse sample omitted;
- do not mark Qwen wrong for information visible only outside its 16 frames;
- record sampling omissions as an input limitation.

The MP4s are derived from NDA-controlled SoccerNet footage and remain excluded
from Git under `data/processed`.

## Recognition progression rule

The recognition gate passes at the pilot level only if at least 9 of 12
eligible clips have the attacking team, event, and visible outcome judged
correct. A clip is ineligible only when the required information genuinely
cannot be determined from the 16 frames; explain every exclusion.

Passing the gate permits coaching evaluation to continue. It does not prove
that the later coaching advice is correct.
