# Thesis Literature Review Register

## Research question

**Does providing a human-annotated analogous Dataset A case improve an MLLM's recognition and coaching advice for a new Dataset B sequence?**

This is a working research register for an undergraduate thesis. It replaces the immediate need to learn Zotero. It should not be presented as the finished literature-review chapter.

The central comparison is between the same Dataset B frames analysed without a case and with an analogous human-annotated Dataset A case. Retrieval-assisted performance must not be described as independent video understanding.

## How to use this file

For each paper that you actually read:

1. Open the official paper or publisher page.
2. Check the title, authors, year, venue, pages, and DOI.
3. Add a reading note using the template near the end of this file.
4. Separate what the paper directly demonstrates from what you infer for this thesis.
5. Change its reading status from `TO READ` to `READ`.
6. Cite the original paper in the thesis, not an AI-generated summary.

Verification labels in this file mean:

- `READ`: you supplied a human reading review, which was checked and organised in the consolidated reading-notes section.
- `PRIMARY RECORD CHECKED`: core bibliographic details were checked against an official proceedings, publisher, or paper page.
- `CORRECTION CHECKED`: a specific correction was checked against primary records.
- `TO VERIFY`: retained from the consolidated search table but still needs a source-by-source metadata check before citation.
- `NON-ARCHIVAL`: preprint, workshop version without confirmed archival proceedings, or technical report.

Every paper title in the grouped tables below is a clickable reading link. Links point to an official proceedings or publisher page where possible; arXiv or an official project page is used for non-archival work. Most official pages have a **PDF** button for the full article.

## Recommended reading order

Do not try to read all 37 papers from beginning to end immediately.

1. Read the abstract, introduction, method overview, experiment setup, limitations, and conclusion of the core papers.
2. Use the remaining papers to support individual design choices or establish background.
3. Begin writing by claim, not by summarising one paper after another.

The priority papers and their current reading status are listed below.

| Current ID | Paper | Human reading status |
|---|---|---|
| S08 | Revealing Single Frame Bias for Video-and-Language Learning | Completed |
| S11 | Too Many Frames, Not All Useful / LVNet | Completed |
| S16 | MRAG-Bench | Completed |
| S20 | What Makes Good Examples for Visual In-Context Learning? | Completed |
| S22 | CLIP | Completed |
| S28 | SoccerNet Game State Reconstruction | Completed |
| S31 | X-VARS | Completed |
| S33 | ChatGPT-generated running training plans | Completed |
| S35 | POPE: Evaluating Object Hallucination in LVLMs | Completed |
| S36 | VideoHallucer | Completed |

Therefore, all ten priority papers now have human reading notes.

## Group 1: Multimodal video understanding

| ID | Short title | Role in this thesis | Status |
|---|---|---|---|
| S01 | [Video-ChatGPT](https://aclanthology.org/2024.acl-long.679/) | Background on detailed video understanding and video-language evaluation. | TO VERIFY |
| S02 | [MVBench](https://openaccess.thecvf.com/content/CVPR2024/html/Li_MVBench_A_Comprehensive_Multi-modal_Video_Understanding_Benchmark_CVPR_2024_paper.html) | Evidence that temporal video tasks require more than static image recognition. | PRIMARY RECORD CHECKED |
| S03 | [EgoSchema](https://proceedings.neurips.cc/paper_files/paper/2023/hash/90ce332aff156b910b002ce4e6880dec-Abstract-Datasets_and_Benchmarks.html) | Long-form video question-answering benchmark and evidence of a substantial model-human gap. | PRIMARY RECORD CHECKED |
| S04 | [Video-MME](https://openaccess.thecvf.com/content/CVPR2025/html/Fu_Video-MME_The_First-Ever_Comprehensive_Evaluation_Benchmark_of_Multi-modal_LLMs_in_CVPR_2025_paper.html) | Broad evaluation across video durations; useful context for duration and frame-count decisions. | CORRECTION CHECKED: CVPR 2025 |
| S05 | [TemporalBench](https://arxiv.org/abs/2410.10818) | Temporal reasoning benchmark; useful but should be treated as arXiv/workshop work. | NON-ARCHIVAL |
| S06 | [TempCompass](https://aclanthology.org/2024.findings-acl.517/) | Evidence about temporal perception and reasoning weaknesses in video language models. | PRIMARY RECORD CHECKED |
| S07 | [Gemini 1.5 technical report](https://arxiv.org/abs/2403.05530) | Background on long-context multimodal processing, not peer-reviewed evidence. | NON-ARCHIVAL |

## Group 2: Frame sampling and temporal reasoning

| ID | Short title | Role in this thesis | Status |
|---|---|---|---|
| S08 | [Revealing Single Frame Bias for Video-and-Language Learning](https://aclanthology.org/2023.acl-long.29/) | Core justification for testing whether multiple sampled frames add information beyond a single view. | READ; PRIMARY RECORD CHECKED |
| S09 | [Revisiting the “Video” in Video-Language Understanding](https://openaccess.thecvf.com/content/CVPR2022/html/Buch_Revisiting_the_Video_in_Video-Language_Understanding_CVPR_2022_paper.html) | Background on whether video models really use temporal information. | TO VERIFY |
| S10 | [Adaptive Keyframe Sampling for Long Video Understanding](https://openaccess.thecvf.com/content/CVPR2025/html/Tang_Adaptive_Keyframe_Sampling_for_Long_Video_Understanding_CVPR_2025_paper.html) | Alternative sampling approach and evidence that frame selection can matter. | TO VERIFY |
| S11 | [Too Many Frames, Not All Useful / LVNet](https://aclanthology.org/2026.eacl-long.164/) | Core evidence that more frames are not automatically better; relevant to the F10/F20/F30/F60 pilot. | READ; PRIMARY RECORD CHECKED |
| S12 | [VideoAgent](https://videoagent.github.io/) | Example of selecting or retrieving useful visual evidence rather than processing every frame equally. | TO VERIFY |

## Group 3: Retrieval, case-based reasoning, and in-context examples

| ID | Short title | Role in this thesis | Status |
|---|---|---|---|
| S13 | [Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks](https://proceedings.neurips.cc/paper/2020/hash/6b493230-Abstract.html) | Foundational text-RAG background; indirect evidence only. | TO VERIFY |
| S14 | [Retrieval-Augmented Multimodal Language Modeling / RA-CM3](https://proceedings.mlr.press/v202/yasunaga23a.html) | Evidence that retrieved multimodal context can improve generation, but not the same intervention as one football coaching case. | PRIMARY RECORD CHECKED |
| S15 | [Wiki-LLaVA](https://openaccess.thecvf.com/content/CVPR2024W/MMFM/html/Caffagni_Wiki-LLaVA_Hierarchical_Retrieval-Augmented_Generation_for_Multimodal_LLMs_CVPRW_2024_paper.html) | Example of retrieval-augmented multimodal generation. | TO VERIFY |
| S16 | [MRAG-Bench](https://openreview.net/forum?id=Usklli4gMc) | Core benchmark evidence about using retrieved visual context; closest retrieval evaluation paper in this group, but it is not football coaching. | READ; PRIMARY RECORD CHECKED |
| S17 | [Aamodt and Plaza case-based reasoning survey](https://doi.org/10.3233/AIC-1994-7104) | Foundational vocabulary for retrieving and reusing analogous cases. | TO VERIFY |
| S18 | [CBR-RAG](https://doi.org/10.1007/978-3-031-63646-2_29) | Modern connection between case-based reasoning and retrieval-augmented generation. | TO VERIFY |
| S19 | [Flamingo](https://proceedings.neurips.cc/paper_files/paper/2022/hash/960a172bc7fbf0177ccccbb411a7d800-Abstract-Conference.html) | Background on multimodal few-shot and in-context learning. | TO VERIFY |
| S20 | [What Makes Good Examples for Visual In-Context Learning?](https://proceedings.neurips.cc/paper_files/paper/2023/hash/398ae57ed4fda79d0781c65c926d667b-Abstract-Conference.html) | Core evidence that example selection can outperform random examples. | READ; PRIMARY RECORD CHECKED |
| S21 | [Learning to Retrieve Prompts for In-Context Learning](https://aclanthology.org/2022.naacl-main.191/) | Background supporting learned or similarity-based example selection over random selection. | TO VERIFY |

## Group 4: CLIP and embedding retrieval

| ID | Short title | Role in this thesis | Status |
|---|---|---|---|
| S22 | [CLIP](https://proceedings.mlr.press/v139/radford21a.html) | Foundation for pixel-derived visual embeddings and cosine similarity. | READ; PRIMARY RECORD CHECKED |
| S23 | [A Straightforward Framework for Video Retrieval Using CLIP](https://doi.org/10.1007/978-3-030-77004-4_1) | Supports aggregation of frame-level CLIP representations for video retrieval. It is a proceedings book chapter, not a journal article. | CORRECTION CHECKED |
| S24 | [X-CLIP](https://doi.org/10.1145/3503161.3547910) | More advanced video-text retrieval baseline; useful background rather than a required implementation. | PRIMARY RECORD CHECKED |
| S25 | [I3D](https://openaccess.thecvf.com/content_cvpr_2017/html/Carreira_Quo_Vadis_Action_CVPR_2017_paper.html) | Older video representation baseline and historical context. | TO VERIFY |

## Group 5: SoccerNet, football understanding, and coaching

| ID | Short title | Role in this thesis | Status |
|---|---|---|---|
| S26 | [SoccerNet](https://openaccess.thecvf.com/content_cvpr_2018_workshops/w34/html/Giancola_SoccerNet_A_Scalable_CVPR_2018_paper.html) | Original dataset background. | TO VERIFY |
| S27 | [SoccerNet-v2](https://openaccess.thecvf.com/content/CVPR2021W/CVSports/html/Deliege_SoccerNet-v2_A_Dataset_and_Benchmarks_for_Holistic_Understanding_of_Broadcast_CVPRW_2021_paper.html) | Dataset development and football event-understanding background. | TO VERIFY |
| S28 | [SoccerNet Game State Reconstruction](https://openaccess.thecvf.com/content/CVPR2024W/CVsports/html/Somers_SoccerNet_Game_State_Reconstruction_End-to-End_Athlete_Tracking_and_Identification_on_CVPRW_2024_paper.html) | Official provenance and structure for the Dataset B source family. It does not provide coaching ground truth. | READ; PRIMARY RECORD CHECKED |
| S29 | [MatchTime](https://aclanthology.org/2024.emnlp-main.99/) | Football video-language understanding precedent. | PRIMARY RECORD CHECKED |
| S30 | [VARS](https://openaccess.thecvf.com/content/CVPR2023W/CVSports/html/Held_VARS_Video_Assistant_Referee_System_for_Automated_Soccer_Decision_Making_CVPRW_2023_paper.html) | Football refereeing and visual reasoning precedent, not coaching retrieval. | TO VERIFY |
| S31 | [X-VARS](https://openaccess.thecvf.com/content/CVPR2024W/CVsports/html/Held_X-VARS_Introducing_Explainability_in_Football_Refereeing_with_Multi-Modal_Large_Language_CVPRW_2024_paper.html) | One of the closest football MLLM precedents, but it studies referee explanations rather than retrieved coaching cases. | READ; PRIMARY RECORD CHECKED |
| S32 | [SportQA](https://aclanthology.org/2024.naacl-long.283/) | Sports video question-answering background. | PRIMARY RECORD CHECKED |
| S33 | [ChatGPT-generated running training plans](https://doi.org/10.52082/jssm.2024.56) | Indirect evidence about generated coaching/training advice and human evaluation. It is text-based and not football video analysis. | READ; PRIMARY RECORD CHECKED |

## Group 6: Hallucination and human evaluation

| ID | Short title | Role in this thesis | Status |
|---|---|---|---|
| S34 | [CHAIR: Object Hallucination in Image Captioning](https://aclanthology.org/D18-1437/) | Foundational object-hallucination evaluation; useful conceptual background. | TO VERIFY |
| S35 | [POPE: Evaluating Object Hallucination in Large Vision-Language Models](https://aclanthology.org/2023.emnlp-main.20/) | Core inspiration for checking unsupported claims, but its binary object evaluation does not validate this thesis's open-ended coaching rubric. | READ; PRIMARY RECORD CHECKED |
| S36 | [VideoHallucer](https://arxiv.org/abs/2406.16338) | Directly relevant video-hallucination benchmark. The abstract reports eleven evaluated LVLMs, while the setup and body describe twelve model families; report the source inconsistency rather than relying on one number. | READ; NON-ARCHIVAL; PRIMARY RECORD CHECKED |
| S37 | [MT-Bench and Chatbot Arena](https://proceedings.neurips.cc/paper_files/paper/2023/hash/91f18a1287b398d378ef22505bf41832-Abstract-Datasets_and_Benchmarks.html) | Relevant only if an LLM judge is used. Human scoring remains preferable for the main thesis evaluation. | TO VERIFY |

## Human reading notes

These are the reviews you wrote after reading the papers. They are collected here in current numerical order. Accuracy checks and thesis-specific cautions have been incorporated, but the notes remain a record of your reading rather than evidence that every source in the full register has been read.

Completed reviews: **S08, S11, S16, S20, S22, S28, S31, S33, S35, and S36.** All priority reviews are now complete.

### Reading note - S08

**Citation:** Lei, J., Berg, T., and Bansal, M. (2023). “Revealing Single Frame Bias for Video-and-Language Learning.” *Proceedings of the 61st Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pp. 487–507.

**DOI:** [10.18653/v1/2023.acl-long.29](https://doi.org/10.18653/v1/2023.acl-long.29)

**Official paper:** [ACL Anthology](https://aclanthology.org/2023.acl-long.29/)

**Date read:** 2026-09-07

**Research problem:** Whether single-frame training, instead of standard multi-frame or dense-frame training, is sufficient for strong video-language performance, and what this reveals about static-appearance bias in existing datasets.

**Datasets:** Pre-training uses either a 5M corpus consisting of CC3M and WebVid or a 17M corpus that additionally includes COCO, Visual Genome, SBU, and CC12M. Downstream retrieval datasets are MSRVTT, DiDeMo, and ActivityNet Captions. Question-answering datasets are MSRVTT-QA, ActivityNet-QA, and MSRVTT-MC. The new SSv2-Template and SSv2-Label retrieval tasks are constructed from Something-Something v2.

**Model:** SINGULARITY uses a ViT/BEiT-base vision encoder, the first nine layers of BERT-base as its language encoder, and the final three BERT layers with randomly initialised cross-attention as its multimodal encoder. SINGULARITY-temporal adds a two-layer temporal transformer after the vision encoder for four-frame inputs.

**Input representation:** During training, the model receives one randomly sampled frame from each video. At inference, multiple uniformly sampled frames are encoded separately and their representations are concatenated before the multimodal cross-attention stage.

**Retrieval or sampling method:** Random single-frame sampling is used during training. At inference, the study compares an early-fusion strategy, which concatenates frame representations before cross-attention, with late-fusion strategies such as mean pooling, max pooling, and LogSumExp over predictions.

**Experimental baselines:** Retrieval baselines include ClipBERT, HERO, VideoCLIP, Frozen-in-Time, AlignPrompt, All-in-one, and ECLIPSE. Question-answering baselines include ClipBERT, AlignPrompt, JustAsk, MERLOT, VideoCLIP, and All-in-one.

**Evaluation metrics:** Recall@K, including R1, R5, and R10, and average recall are used for retrieval. Accuracy is used for open-ended and multiple-choice question answering.

**Main finding in my own words:** On the evaluated retrieval and question-answering benchmarks, single-frame training combined with a multi-frame ensemble at inference was competitive with or better than several multi-frame systems. This indicates substantial static-appearance bias in those particular benchmarks. The comparison does not isolate frame count as the only cause because systems also differ in architecture, pre-training data, and scale.

**Evidence from the paper:**

- Table 1 (p. 491): the 17M-pretrained single-frame SINGULARITY results are competitive with or exceed several retrieval baselines on MSRVTT, DiDeMo, and ActivityNet Captions.
- Table 2 (p. 491): SINGULARITY is competitive with or exceeds several reported question-answering baselines.
- Table 3 (p. 493): on SSv2-Template and SSv2-Label, which place greater demands on temporal modelling, single-frame SINGULARITY trails four-frame temporal models substantially.
- Figure 6: the reported gap between one-frame and four-frame models reduces as pre-training data increases.
- Figure 3 and the “Frames Ensemble Strategy” section: early fusion outperforms the evaluated late-fusion strategies, particularly as more inference frames are added.

**Limitations stated by the authors:** The single-frame approach performs poorly on genuinely temporal SSv2 tasks and requires more pre-training data than multi-frame models. This is paraphrased rather than reproduced as a long quotation.

**Additional limitations I noticed:**

- The paper studies single-frame versus multi-frame **training**, whereas this thesis varies the number of frames supplied at inference to an already-trained Qwen MLLM. The results motivate a sampling pilot but cannot determine the best Qwen frame count.
- Comparisons with other systems also vary architecture, training corpus, pre-training scale, and optimisation, so they are not a controlled causal test of frame count alone.
- The paper does not test ordered football broadcast sequences or open-ended coaching advice.
- A possible concern is that WebVid's composition may encourage static visual shortcuts, but this requires support from the WebVid dataset paper before being stated as fact.

**Relevance to my thesis:** The paper is directly relevant to the risk that video-language benchmarks can reward static visual shortcuts. It motivates testing whether additional frames reveal event order and outcomes that isolated frames miss. It is indirectly relevant to the thesis's inference-time F10/F20/F30/F60 comparison because its principal intervention occurs during training.

**Evidence classification:**

- Direct evidence that static-appearance bias exists in the video-language benchmarks evaluated by the paper.
- Direct evidence that frame use and inference-time frame-combination strategies affect the studied models.
- Indirect support for running this thesis's frame-count pilot.
- Background only for CLIP retrieval.
- No direct evidence for football coaching, case-based prompting, cosine k-NN case retrieval, or hallucination scoring.

**Thesis design choice supported:** Run the preregistered F10/F20/F30/F60 sampling pilot rather than assuming that more frames always improve performance. Evaluate temporal event order separately from static scene recognition, report the exact sampling method, and document examples where lower frame counts omit outcome-changing evidence. B-TRAIN-0040 is locally relevant because lower-count human review suggested a save while F60 revealed a goal.

**What the paper does not establish:** It does not determine this thesis's final frame count, validate Qwen's ordered multi-image processing, justify mean-pooling CLIP embeddings for B4, establish the value of analogous football cases, or provide a hallucination-evaluation method.

**Where I may cite it:** In the literature review and methodology rationale concerning static-appearance bias, the need for a controlled frame-count pilot, the distinction between static recognition and temporal event understanding, and the limitation that sampled-frame evaluation may not demonstrate complete video understanding. It should not be cited as direct evidence for football coaching, B4 retrieval, or hallucination metrics.

### Reading note - S11

**Citation:** Park, J., Ranasinghe, K., Kahatapitiya, K., Ryu, W., Kim, D., and Ryoo, M. S. (2026). “Too Many Frames, Not All Useful: Efficient Strategies for Long-Form Video QA.” *Proceedings of the 19th Conference of the European Chapter of the Association for Computational Linguistics (Volume 1: Long Papers)*, pp. 3569–3588.

**DOI:** [10.18653/v1/2026.eacl-long.164](https://doi.org/10.18653/v1/2026.eacl-long.164)

**Official paper:** [ACL Anthology](https://aclanthology.org/2026.eacl-long.164/)

**Date read:** 2026-09-07

**Research problem:** How to identify a small, question-relevant set of informative frames for long-form video question answering without captioning a large number of redundant uniformly sampled frames.

**Datasets:** The evaluation uses EgoSchema, with 5,031 multiple-choice questions over approximately three-minute videos; the NExT-QA validation set, with 4,996 questions over 570 videos and causal, temporal, and descriptive categories; IntentQA, with approximately 16,000 multiple-choice questions based on NExT-QA videos; and the VideoMME long split, containing videos of up to approximately one hour. These datasets are used for evaluation rather than task-specific video training.

**Training status:** LVNet performs no task-specific or video-level training. It is described as training-free or zero-shot at the framework level. However, its ResNet, CLIP, VLM, and LLM components were previously pretrained.

**Model:** LVNet is a modular three-stage pipeline:

1. a Hierarchical Keyframe Selector;
2. a VLM that captions the selected frames; and
3. an LLM, such as GPT-4o or DeepSeek-V3, that answers the question from those captions.

The selector contains Temporal Scene Clustering using ResNet-18, a Coarse Keyframe Detector using a spatially aware CLIP-B/16 dual encoder, and a Fine Keyframe Detector using a VLM with collage-style visual templates.

**Input representation:** LVNet begins with 900, or up to 1,800, uniformly sampled candidate frames depending on the evaluation setting. It progressively filters these to a small set, commonly 12 frames for the shorter benchmarks and 24 for VideoMME-Long. A VLM converts the selected frames into natural-language captions, and the final answering LLM receives the captions rather than the original pixels.

**Frame-selection method:**

- Temporal Scene Clustering groups visually similar frames into temporally non-overlapping sets and samples within them.
- The Coarse Keyframe Detector generates keywords from the question and, where available, answer options. It uses CLIP-based similarity to score frame relevance.
- The Fine Keyframe Detector arranges candidate frames into eight-frame visual grids and asks a VLM to choose frames associated with the keywords.

This is question-conditioned frame selection within one video, not retrieval of an analogous case from another dataset.

**Experimental baselines:** The paper compares with systems including VideoAgent, VideoTree, TraveLER, LangRepo, LLoVi, MVU, MoReVQA, VFC, ProViQ, IG-VLM, SeViLA, VideoChat-T, Frame-Voyager, VideoLLaMA2, InternVideo2, Tarsier, Qwen-VL, Qwen2-VL, InternVL, LLaVA-Video, and LLaVA-OneVision. Not every comparison uses the same model, caption budget, architecture, hardware, or training history.

**Evaluation metrics:** Multiple-choice accuracy is the principal task metric. Efficiency measurements include inference latency, frames per second, GPU memory, API cost, and the number of frames or captions processed.

**Main finding in my own words:** On the evaluated long-video QA benchmarks, LVNet selects a small question-relevant frame subset and achieves strong accuracy relative to similarly configured systems. Under matched GPT-4o and caption budgets, its selection pipeline outperforms VideoAgent and VideoTree. The results show that selection quality matters, but they do not show that frame count is unimportant: the paper also reports improved VideoMME-Long accuracy when the LVNet budget increases from 12 to 24 frames.

**Evidence from the paper:**

- Table 2 (p. 3574): with 12 captions, LVNet reports 61.1% on EgoSchema, 72.9% on NExT-QA, and 71.7% on IntentQA. These results are strong relative to systems using similar caption budgets, although the broader table is not a completely controlled comparison.
- Table 4a (p. 3575): with GPT-4o used consistently, LVNet outperforms VideoAgent and VideoTree at caption budgets of 8, 12, and 16. At 12 captions, LVNet reports 68.2%, while both comparison systems report 63.6%.
- Table 4c (p. 3575): accuracy on the 500-video EgoSchema subset rises from 62.6% with uniform sampling to 64.5% with temporal scene clustering, 65.8% after adding the coarse detector, and 68.2% with the complete selector.
- Tables 7 and 8 (pp. 3575–3576): the selector accounts for 36% of LVNet's reported runtime. In the matched 180-frame runtime comparison, LVNet takes 25.6 seconds, compared with 87.3 for VideoAgent and 64.2 for VideoTree.
- Table 6 (p. 3575): on VideoMME-Long, direct GPT-4o processing reports 65.3% accuracy at approximately $2.88 per video, whereas LVNet reports 53.9% at approximately $0.19 per video. The reported totals are approximately $2,592 and $171. This is a substantial cost reduction accompanied by an 11.4-point accuracy reduction.
- Table 10 (p. 3576): on VideoMME-Long, increasing the selected-frame budget from 12 to 24 improves accuracy from 50.1% to 53.9%.
- Figure A.4 (p. 3582): LVNet selects evidence related to phone use, while VideoAgent focuses on hand use and answers incorrectly.
- Figure A.5 (p. 3586): LVNet's selected frames capture more of the relevant tools than a uniform-sampling example.

**Limitations stated by the authors:**

- Computational cost prevented evaluation with every available VLM and LLM.
- The selector contains three separate components rather than one unified module.
- Results remain sensitive to prompting.
- Biases and limitations of the pretrained components may persist in LVNet.

**Additional limitations I noticed:**

- Many headline comparisons combine different models, frame or caption budgets, hardware, architectures, and training histories. The matched comparisons are stronger evidence than the full baseline table.
- The paper reports single evaluation runs, so there are no variance estimates or confidence intervals. Small reported gains should be interpreted cautiously.
- The effect of errors in question-to-keyword generation is not isolated independently from the other selector stages.
- Much of the evaluation is multiple choice, and answer options may help generate selection keywords. This thesis asks for open-ended football analysis and supplies no candidate answers.
- The videos are much longer than the 30-second Dataset B clips. The amount of redundancy and the efficiency trade-off may therefore differ.

**Relevance to my thesis:** The paper is highly relevant to the frame-selection literature and shows that selected visual evidence and computational cost should be evaluated together. It highlights a limitation of uniform sampling: redundant frames may be retained while brief important events are missed. It complements S08 by showing that, in the studied long-video setting, carefully selected multiple frames can outperform less targeted selection.

**Evidence classification:**

- Direct evidence for the effectiveness and efficiency of LVNet's question-conditioned frame-selection pipeline on the evaluated benchmarks.
- Direct evidence that its full selector outperforms the compared selection methods under the paper's matched GPT-4o caption-budget experiment.
- Indirect support for the importance of capturing temporally relevant evidence.
- Indirect support for this thesis's F10/F20/F30/F60 pilot because the thesis uses short football clips, fixed uniform sampling, raw images supplied to Qwen, and open-ended answers.
- Background only for CLIP/cosine retrieval because CLIP is one internal frame-scoring component.
- No direct evidence for analogous-case retrieval, football coaching, or hallucination evaluation.

**Thesis design choice supported:** Evaluate recognition, frame count, capacity, latency, and failure behaviour together rather than assuming that denser sampling is always better. Record the limitation that uniform sampling can miss brief events and retain redundant frames. LVNet-style hierarchical, question-conditioned selection is a possible future comparison, not part of the current frozen F10/F20/F30/F60 uniform-sampling pilot.

**What the paper does not establish:** It does not show that single-frame input is sufficient, that frame count does not matter, that LVNet is preferable for 30-second football clips, or that CLIP cosine similarity alone is a retrieval-based answer mechanism. It does not evaluate analogous football cases, open-ended coaching, blind copying, or hallucination.

**Where I may cite it:** In the literature review on long-video frame selection and in the methodology discussion of sampling accuracy, latency, memory, and capacity. It can also support the limitation that uniform endpoint sampling is simpler and reproducible but may miss short events. It should not be cited as direct evidence for B4 case retrieval, football-domain effectiveness, or hallucination scoring.

### Reading note - S16

**Citation:** Hu, W., Gu, J.-C., Dou, Z.-Y., Fayyaz, M., Lu, P., Chang, K.-W., and Peng, N. (2025). "MRAG-Bench: Vision-Centric Evaluation for Retrieval-Augmented Multimodal Models." *The Thirteenth International Conference on Learning Representations (ICLR 2025)*.

**Persistent arXiv DOI:** [10.48550/arXiv.2410.08182](https://doi.org/10.48550/arXiv.2410.08182)

**Official conference paper:** [OpenReview](https://openreview.net/forum?id=Usklli4gMc)

**Accessible copy:** [arXiv](https://arxiv.org/abs/2410.08182)

**Date read:** 2026-09-07

**Research problem:** Existing multimodal RAG benchmarks mainly test retrieval and use of external textual knowledge. MRAG-Bench asks whether large vision-language models can instead use retrieved visual knowledge in situations where additional images are more useful than text.

**Dataset:** MRAG-Bench contains 16,130 images and 1,353 human-annotated multiple-choice questions across nine scenarios. Four scenarios concern changes in perspective: Angle, Partial, Scope, and Occlusion. Four concern transformations: Temporal, Deformation, Incomplete, and Biological. An Others category covers geographic knowledge. The benchmark includes 9,673 human-selected images as its ground-truth image-knowledge corpus. Images come from ImageNet, Oxford Flowers102, StanfordCars, GeoDE, and manually collected and filtered web images.

**Training status:** The paper proposes a benchmark rather than a new model. It evaluates 14 existing LVLMs, 10 open-source and four proprietary, in zero-shot settings. "Training-free" here means that the authors do not train the evaluated models for MRAG-Bench; the models and retrievers still use pretrained components.

**Input representation:** A query contains a query image and a textual multiple-choice question. A multimodal retriever returns additional images, which are placed with the query image in a structured multi-image prompt. The LVLM then selects an answer. The main setting supplies five retrieved or ground-truth images, except for the Incomplete scenario, where one image is used.

**Retrieval method:** CLIP is the common retriever used in the main model comparison. A separate retriever analysis compares CLIP, MagicLens, E5-V, and VISTA using Recall@5, with LLaVA-NeXT-Interleave as the downstream LVLM. This is retrieval of external reference images from a corpus, not temporal frame sampling within a video and not retrieval of a complete coaching case.

**Experimental conditions and baselines:** The 14 LVLMs are compared under no-RAG, retrieved-image RAG, and ground-truth-image RAG conditions. Random-chance and human results provide reference points. The paper also compares text-based and image-based augmentation for two representative models and analyses the effects of changing the retriever and the number of ground-truth images.

**Evaluation metrics:** Multiple-choice accuracy is reported overall and by scenario. The paper reports changes in accuracy after augmentation, Recall@5 for retrieval, and correlation between Recall@5 and downstream accuracy.

**Main finding in my own words:** Relevant visual context can help, but current models do not necessarily use retrieved images reliably. Humans benefit substantially from retrieved and ground-truth images. GPT-4o benefits only slightly from realistically retrieved images and more from clean ground-truth images. Almost all evaluated open-source models decline on average with noisy retrieved images. Retrieving something visually similar is therefore not enough: both retrieval quality and the model's ability to ignore misleading context matter.

**Evidence from the paper:**

- Table 3: GPT-4o scores 68.68% without RAG and 74.50% with ground-truth image RAG, a gain of 5.82 percentage points. With retrieved images, its gain is 0.28 points. Human participants gain 33.16 points with ground-truth images and 22.91 points with retrieved images.
- Table 3: almost all evaluated open-source models decline on average when supplied with realistically retrieved images, even though all models improve with ground-truth images. For example, VILA1.5-13B falls from 43.68% without RAG to 35.48% with retrieved-image RAG, a decrease of 8.20 points.
- Table 4: ground-truth images improve LLaVA-NeXT-Interleave by 11.90 points more than ground-truth text, while the corresponding advantage for GPT-4-Turbo is 3.87 points. Under realistic retrieval, the image-over-text advantages are smaller: 2.36 and 2.34 points respectively.
- Figure 4: a qualitative example contains two useful and three incorrect retrieved car images. Gemini Pro answers correctly, whereas LLaVA-NeXT-Interleave is misled. This illustrates a possible failure mechanism but is not causal proof of a general proprietary-versus-open-source difference.
- Figure 5 and Section 4.2: across four retrievers, LLaVA-NeXT-Interleave's accuracy has a reported 0.95 correlation with retriever Recall@5. This result is based on one downstream model.
- Figure 5 and Section 4.3: on 892 questions, performance generally rises as the number of sampled ground-truth images increases from one to ten and is slightly lower at 20. These results are averaged over three random seeds.

The paper labels several arithmetic changes in accuracy as percentages. Because, for example, 74.50 minus 68.68 equals 5.82, this review describes them as **percentage-point changes** to avoid confusing them with relative percentage increases.

**Limitations noted or implied by the authors:**

- The impact of the order of retrieved images remains unexplored; position bias may affect visual RAG.
- A fixed number of images may not suit every question, motivating adaptive selection of the image count.
- Open-source-model results may reflect both weaker stored knowledge and weaker ability to distinguish useful from poor retrieved images.

**Additional limitations I noticed:**

- Many transformative examples are derived from manually filtered web searches using constructed keyword templates. Human curation is necessary, but it may favour visually clear transformations and introduce selection subjectivity.
- The human reference results come from three domain annotators, so they should not be treated as a population-wide estimate of human performance.
- The main retriever setting uses a fixed top five, or top one for Incomplete, rather than selecting the amount of evidence per query.
- The reported 0.95 retrieval-accuracy correlation is measured with only LLaVA-NeXT-Interleave and four retrievers. It is useful evidence in that setting, not a general law for all MLLMs.
- The benchmark is multiple choice and image-based. It does not test open-ended coaching, football video, ordered frames, or reuse of text advice from an analogous case.

**Relevance to my thesis:** This is one of the closest papers for understanding the risks and potential value of retrieved visual context. It directly supports testing retrieved cases against both no-case and random-case controls. It also helps explain why B4 retrieval quality must be evaluated separately from the quality of the model's final recognition and coaching answer. However, the intervention differs from this thesis: MRAG-Bench supplies retrieved reference images, whereas B4 supplies a complete human-annotated Dataset A case, including its frames and text, to assist analysis of a Dataset B sequence.

**Evidence classification:**

- Direct evidence that clean, relevant image context can improve accuracy on MRAG-Bench.
- Direct evidence that realistically retrieved, noisy images can reduce accuracy for many evaluated models.
- Direct evidence, for LLaVA-NeXT-Interleave in this experiment, that retrieval Recall@5 and answer accuracy are strongly associated.
- Indirect support for the thesis's B0, B1, B3, and B4 comparisons because the task, modality structure, output format, and domain differ.
- Indirect support for evaluating whether models copy or are misled by retrieved information; the paper does not formally measure hallucination or blind copying.
- Background only for temporal frame sampling and no direct evidence for football coaching.

**Thesis design choices supported:**

- Compare no case, random case, human-selected case, and automatically retrieved case instead of reporting B4 alone.
- Score retrieval relevance separately from recognition and coaching quality.
- Preserve the same retrieval method when comparing downstream models so retriever changes do not confound model comparisons.
- Report failures where retrieved context misleads the model, rather than assuming retrieval always helps.
- Treat B3 human selection and B4 automatic selection as different conditions: clean human selection and realistic automatic retrieval answer different questions.

**What the paper does not establish:** It does not validate this thesis's exact CLIP frame-aggregation or cosine k-nearest-neighbour implementation. It does not establish that image retrieval will find tactically analogous football cases, that retrieved human advice will improve coaching, or that more retrieved items are always better. It does not measure temporal video understanding, formal hallucination rates, blind copying, or calibrated uncertainty.

**Where I may cite it:** In related work and motivation for multimodal retrieval, when explaining that relevance and noise can determine whether retrieved context helps or harms a model. It can also motivate separate retrieval and answer evaluation and the use of no-case, random, human-selected, and automatically retrieved controls. It should not be cited as direct evidence for football coaching, temporal frame sampling, the exact B4 retrieval implementation, or hallucination measurement.

### Reading note - S20

**Citation:** Zhang, Y., Zhou, K., and Liu, Z. (2023). "What Makes Good Examples for Visual In-Context Learning?" *Advances in Neural Information Processing Systems 36 (NeurIPS 2023)*.

**DOI:** [10.52202/075280-0780](https://doi.org/10.52202/075280-0780)

**Official paper:** [NeurIPS Proceedings](https://proceedings.neurips.cc/paper_files/paper/2023/hash/398ae57ed4fda79d0781c65c926d667b-Abstract-Conference.html)

**Date read:** 2026-09-07

**Research problem:** Visual in-context learning with a frozen large vision model is highly sensitive to which input-output image examples are supplied. The paper asks how suitable examples can be selected automatically instead of relying on random choice.

**Datasets and tasks:** Foreground segmentation uses the four Pascal-5i splits. Single-object detection uses Pascal VOC. Colorization uses the 50,000-image ImageNet-2012 validation set for testing, while 50,000 sampled ImageNet training images train the supervised retriever. A Pascal-to-MSCOCO protocol, called MSCOCO-5i, evaluates foreground-segmentation retrieval under distribution shift.

**Base model:** The frozen visual in-context learner is the image-inpainting model introduced by Bar et al. It was pretrained to fill missing regions in grid-like academic figures and is repurposed without parameter updates for segmentation, detection, and colorization. The paper contributes retrieval methods around this base model rather than a new general-purpose MLLM.

**Input representation:** An in-context image and its output annotation are arranged with the query in a grid. The bottom-right output region is masked, and the frozen inpainting model predicts that region. This differs substantially from this thesis, where Qwen receives ordered football frames plus natural-language information about an analogous case.

**Retrieval methods:**

- Unsupervised Prompt Retrieval (UnsupPR) performs nearest-example search using a fixed off-the-shelf feature extractor. The main experiments use the CLIP vision encoder.
- Supervised Prompt Retrieval (SupPR) fine-tunes the feature extractor using contrastive learning. For each training query, the five candidate examples producing the best in-context performance form the positive set and the five producing the worst performance form the negative set.
- Both methods rank candidates using feature similarity based on the paper's cosine-distance score function and select the top candidate or candidates.
- The principal baseline is within-class random example selection, following the earlier visual-prompting protocol.

**Other comparisons:** The authors compare CLIP, EVA, and ViT feature backbones; cosine, Euclidean, and Manhattan distance; different retrieval-pool sizes; different numbers and orders of in-context examples; and a fine-tuned Masked Autoencoder feature extractor.

**Evaluation metrics:** Mean Intersection-over-Union (mIoU) is used for foreground segmentation and detection, where higher is better. Mean squared error (MSE) is used for colorization, where lower is better. The order experiment reports means and standard deviations.

**Main finding in my own words:** In this visual in-context system, example identity matters greatly. Both automatic retrieval methods outperform random selection, and the task-trained SupPR retriever performs best. Useful examples tend to resemble the query in semantic content and visual context such as pose, viewpoint, background, and appearance. The benefit is much smaller under a Pascal-to-MSCOCO distribution shift, so similarity learned in one domain does not transfer perfectly.

**Evidence from the paper:**

- Figure 1: across 30 Pascal-5i queries and 50 randomly selected prompts per query, the gap between the best and worst examples can exceed 70 mIoU points. This illustrates sensitivity; it is not an average improvement achieved by the proposed method.
- Table 1: on foreground segmentation, average mIoU is 27.56 for Random, 33.56 for UnsupPR, and 35.56 for SupPR. Detection follows the same ordering at 25.45, 26.84, and 28.22. Colorization MSE is 0.67, 0.63, and 0.63, so the colorization improvement is small and SupPR does not improve on UnsupPR there.
- Table 2: under the Pascal-to-MSCOCO shift, average segmentation mIoU is 16.78 for Random, 18.02 for UnsupPR, and 19.95 for SupPR. SupPR remains best, but its advantage over Random falls from 8.00 points in-domain to 3.17 points under the shift.
- Figure 3 and supplementary Figures 6-15: selected examples illustrate similarities in semantics, background, pose, appearance, viewpoint, and style. These qualitative examples help explain the results but do not independently prove which feature causes an improvement.
- Table 4: with three in-context examples, performance varies little across their possible orders. SupPR averages 24.06 mIoU with a standard deviation of 0.40. This finding is specific to this model, task, and three-example prompt.
- Figure 5: retrieval performance improves as the candidate pool grows and later plateaus. The three evaluated distance functions produce similar results.
- Table 5: the task-trained SupPR representation scores 35.56 average mIoU, compared with 31.27 for the fine-tuned MAE representation.

**Limitations stated by the authors:**

- The retrieval methods are not strong enough to handle distribution shifts; their advantage over random selection becomes much smaller.
- Colorization gains are marginal, possibly because the frozen inpainting model is weak at colorization.
- SupPR is presented as a simple implementation rather than a final solution to supervised prompt retrieval.

**Additional limitations I noticed:**

- SupPR requires a separately trained supervised retriever for each task. The frozen inpainting model remains unchanged, but the full method is not training-free.
- The positive and negative training sets are defined using the frozen model's own measured performance. Weaknesses in that model can therefore affect what the retriever learns.
- The experiments use one inpainting-based visual in-context learner, so the ordering SupPR over UnsupPR over Random is not established for general MLLMs.
- Random selection is within class and therefore already uses the query class label. It is not identical to this thesis's B1 rule, which must remain independent of hidden Dataset B labels.
- The tasks use static images and structured output annotations, not videos, open-ended language, tactical analogies, or coaching advice.

**Relevance to my thesis:** This paper strongly motivates comparing a visually similar retrieved example with a random example instead of assuming that all demonstrations are equally useful. It also supports using a simple off-the-shelf visual retriever as a reproducible baseline and treating a learned retriever as a possible later extension. However, it does not directly validate B4: Dataset A and Dataset B differ in source and purpose, each case contains a football sequence plus human text, and Qwen must generate open-ended recognition and coaching language.

**Evidence classification:**

- Direct evidence that UnsupPR and SupPR outperform within-class random selection in the paper's evaluated visual in-context system.
- Direct evidence that the benefit shrinks under the evaluated domain shift.
- Direct evidence that CLIP features and the paper's cosine-based score provide a workable unsupervised retrieval baseline in this setting.
- Indirect support for B1 versus B4 because this thesis uses cross-dataset football cases, an MLLM, and open-ended outputs.
- Background only for temporal frame sampling; no evidence for football coaching or hallucination measurement.

**Thesis design choices supported:**

- Keep B1 random-case and B4 embedding-kNN as separate conditions.
- Use a transparent pretrained visual embedding baseline before considering task-specific retriever training.
- Fit or tune any learned retrieval component on Dataset B train only and test transfer on validation, because the paper shows weaker gains under domain shift.
- Record retrieval-pool size, distance function, and selected case provenance.
- Score retrieval relevance separately from downstream recognition and coaching so a poor answer is not automatically blamed on retrieval.

The paper's ordering ablation does **not** justify ignoring order in this thesis. B4 currently supplies one analogous Dataset A case, so there is no ordering among multiple cases. The order of frames and prompt sections remains part of this thesis's frozen input construction.

**What the paper does not establish:** It does not show that retrieved examples improve video understanding, football recognition, coaching quality, or factual reliability. It does not validate mean aggregation of frame embeddings, cross-dataset tactical similarity, this thesis's value of k, or Qwen's use of retrieved cases. It does not measure hallucination, blind copying, or calibrated uncertainty.

**Where I may cite it:** In related work and methodology when motivating relevant-versus-random case selection, pretrained visual embeddings, and the need to test retrieval under distribution shift. It may support B1 versus B4 as a design motivation, but the thesis's own experiments must establish whether the effect transfers to football case retrieval. It should not be cited for temporal sampling, football coaching effectiveness, or hallucination evaluation.

### Reading note - S22

**Citation:** Radford, A., Kim, J. W., Hallacy, C., Ramesh, A., Goh, G., Agarwal, S., Sastry, G., Askell, A., Mishkin, P., Clark, J., Krueger, G., and Sutskever, I. (2021). "Learning Transferable Visual Models From Natural Language Supervision." *Proceedings of the 38th International Conference on Machine Learning*, PMLR 139, pp. 8748-8763.

**DOI:** No DOI is listed in the official PMLR record. Use the stable PMLR paper URL below rather than assigning an unofficial identifier.

**Official paper:** [PMLR](https://proceedings.mlr.press/v139/radford21a.html)

**Date read:** 2026-09-07

**Research problem:** The paper asks whether contrastive pretraining on web-scale image-text pairs can learn general-purpose visual representations that transfer to new datasets and tasks through natural-language prompts, without dataset-specific training.

**Pretraining dataset:** WebImageText (WIT) contains 400 million image-text pairs collected from publicly available internet sources. The authors constructed a query list of 500,000 terms and retained up to 20,000 pairs per query to approximately balance coverage. This WIT dataset is different from the later Wikipedia-based WIT dataset.

**Model:** CLIP is a dual encoder with an image encoder and a Transformer text encoder. It learns a shared embedding space by increasing cosine similarity for the true image-text pairs in a batch and decreasing it for incorrect pairings using a symmetric cross-entropy loss.

The authors trained five ResNet variants: RN50, RN101, RN50x4, RN50x16, and RN50x64. They trained three distinct Vision Transformer backbones: ViT-B/32, ViT-B/16, and ViT-L/14. ViT-L/14 was additionally trained for one epoch at 336-pixel resolution, producing the reported ViT-L/14@336px checkpoint. The higher-resolution checkpoint is not a fourth independently pretrained ViT architecture.

**Input representation:** Training uses a random square crop from a resized image as the only image augmentation. Text is represented using lower-cased byte-pair encoding with start- and end-of-sequence tokens. The final-layer end-of-sequence activation is normalized and linearly projected into the shared embedding space.

**Zero-shot use:** For classification, class names or natural-language templates such as "a photo of a {class}" are embedded by the text encoder. The normalized image embedding is compared with the normalized text embeddings using scaled cosine similarity. Prompt templates can be ensembled. This is zero-shot image-text matching, not nearest-neighbour retrieval of another image or a coaching case.

**Experimental comparisons:** The paper compares CLIP with Visual N-Grams, a supervised linear classifier on ResNet50 features, few-shot classifiers using several representations, and linear probes on more than 50 existing visual systems. Its evaluation covers more than 30 datasets, including classification, OCR, geolocation, and action-recognition datasets.

**Evaluation metrics:** Metrics vary by dataset and include top-1 accuracy, top-5 accuracy, mean per-class accuracy, mAP, and ROC AUC. The paper also reports averaged linear-probe scores, compute scaling, and effective and relative robustness under natural distribution shift.

**Main finding in my own words:** Web-scale natural-language supervision produces a broadly transferable visual representation. Zero-shot CLIP performs competitively with a supervised ResNet50 linear-probe baseline on many evaluated datasets and is substantially stronger on some tasks, but it is not uniformly best and remains weak on several specialised, abstract, and counting tasks. Its shared visual-semantic embedding is the foundational reason CLIP can be considered as an encoder for retrieval, not proof that any particular downstream retrieval design will work.

**Evidence from the paper:**

- Figure 2: replacing a Transformer caption-prediction objective with bag-of-words prediction improves learning efficiency by about three times, and replacing that predictive objective with CLIP's contrastive objective provides a further four-times improvement in the measured zero-shot ImageNet learning rate.
- Table 1: CLIP reports 98.4 on aYahoo, 76.2 on ImageNet, and 58.5 on SUN, compared with 72.4, 11.5, and 23.0 for Visual N-Grams. The authors caution that this comparison includes many uncontrolled differences.
- Figure 4: zero-shot CLIP outperforms a supervised linear classifier on ResNet50 features on 16 of 27 datasets. Differences include +28.9 points on Stanford Cars, +23.2 on Country211, and +22.5 on Food101, but -37.1 on EuroSAT, -34.0 on KITTI Distance, and -19.5 on PatchCamelyon.
- Figure 7: zero-shot CLIP reduces the fitted ImageNet-to-natural-distribution-shift robustness gap by up to 75%. In the illustrative banana comparison, ImageNet-A accuracy is 77.1% for zero-shot CLIP and 2.7% for a ResNet101 with matched ImageNet accuracy, a difference of 74.4 points. This example should not be confused with the separate fitted-gap statistic.
- Section 6: the authors estimate that scaling their existing approach to overall state-of-the-art zero-shot performance would require roughly 1,000 times more compute, which they describe as infeasible on the hardware available at the time.

**Important video nuance:** The evaluation includes UCF101 and Kinetics700, and Figure 4 reports advantages of 7.7 and 14.5 points over the ResNet50-feature baseline. However, the supplementary methods state that only the **middle frame of each video clip** is used as the input image. These results demonstrate static visual action cues, not temporal modelling, ordered-frame understanding, or video retrieval.

**Limitations stated by the authors:**

- Zero-shot CLIP is often only competitive with a ResNet50 linear-probe baseline that is itself below contemporary state of the art.
- Scaling alone would be extremely computationally expensive.
- Validation-set performance was repeatedly consulted during development, which is not a pure zero-shot development process.
- The 27-dataset suite is described as somewhat haphazard and co-adapted to CLIP's capabilities.
- Natural-language task specification can be difficult for complex or unfamiliar tasks, and actual training examples remain useful.
- CLIP performs poorly on several specialised, abstract, counting, medical, satellite, traffic-sign, and distance-estimation tasks.
- The paper identifies bias and surveillance risks, including sensitivity to chosen class labels and nontrivial person-identification capability.

**Additional limitations for this thesis:**

- CLIP was trained on web data whose complete contents are not released for inspection, limiting full analysis of domain coverage and bias.
- The main paper evaluates image-text alignment and classification, not image-to-image nearest-neighbour retrieval.
- Using the middle frame for video datasets discards event order and short actions, so those results cannot justify this thesis's temporal sampling design.
- The paper does not test tactical similarity, cross-dataset case matching, advice transfer, or generation by an MLLM.

**Relevance to my thesis:** CLIP is foundational background for converting Dataset A and Dataset B pixels into comparable visual embeddings. Its normalized shared embedding and cosine-similarity formulation motivate a transparent pretrained encoder baseline for B4. The paper does not determine how multiple football frames should be aggregated or whether visual resemblance corresponds to a useful tactical analogy. Those choices require separate literature and train/validation evidence from this project.

**Evidence classification:**

- Direct evidence that CLIP learns transferable image-text representations and supports cosine-based image-text comparison.
- Direct evidence that middle-frame visual features carry useful static cues on UCF101 and Kinetics700 under the paper's evaluation.
- Background support for using a pretrained CLIP image encoder in B4.
- No direct evidence for image-to-image football case retrieval, temporal video understanding, coaching improvement, or hallucination evaluation.

**Thesis design choices supported:**

- Use a documented pretrained visual encoder to derive pixel-only representations without exposing hidden Dataset B labels.
- Normalize embeddings and use an explicit similarity measure whose implementation and model checkpoint can be frozen and recorded.
- Treat encoder selection as a design choice to validate, rather than assuming CLIP is automatically suitable for tactical football similarity.
- Record the exact encoder name, weights, preprocessing, resolution, frame aggregation, embedding dimension, and similarity function in the freeze artifact.

**What the paper does not establish:** It does not establish that CLIP-based retrieval outperforms random cases in this thesis, that mean-pooled frame embeddings preserve event order, that visually similar clips are tactically analogous, or that a retrieved human coaching case improves Qwen's answer. It also does not measure hallucination, blind copying, calibrated uncertainty, or coaching quality.

**Where I may cite it:** In background and methodology as the source of CLIP's contrastive image-text embedding mechanism and cosine-based comparison. It may justify selecting CLIP as a candidate pixel encoder, but S20 and the thesis experiments are needed for relevant-versus-random example claims, while video-specific papers are needed for temporal aggregation claims.

Important limitation: S23 and S24 mainly concern text-to-video retrieval. The thesis's B4 condition is video-to-case retrieval. They justify visual embedding and temporal aggregation ideas, but they do not directly prove that B4 will retrieve a useful coaching analogy.

### Reading note - S28

**Citation:** Somers, V., Joos, V., Cioppa, A., Giancola, S., Ghasemzadeh, S. A., Magera, F., Standaert, B., Mansourian, A. M., Zhou, X., Kasaei, S., Ghanem, B., Alahi, A., Van Droogenbroeck, M., and De Vleeschouwer, C. (2024). "SoccerNet Game State Reconstruction: End-to-End Athlete Tracking and Identification on a Minimap." *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops*, pp. 3293-3305.

**DOI:** [10.1109/CVPRW63382.2024.00334](https://doi.org/10.1109/CVPRW63382.2024.00334)

**Official paper:** [CVF Open Access](https://openaccess.thecvf.com/content/CVPR2024W/CVsports/html/Somers_SoccerNet_Game_State_Reconstruction_End-to-End_Athlete_Tracking_and_Identification_on_CVPRW_2024_paper.html)

**Accessible copy:** [arXiv](https://arxiv.org/abs/2404.11335)

**Official implementation:** [SoccerNet sn-gamestate](https://github.com/SoccerNet/sn-gamestate)

**Date read:** 2026-09-07

**Research problem:** The paper formalizes Game State Reconstruction (GSR): localizing and identifying all athletes over time from a single moving broadcast camera and projecting them onto a two-dimensional pitch minimap. Standard multi-object tracking provides image-space boxes and track identities but does not by itself provide real-world pitch positions, roles, teams, and jersey numbers.

**Dataset:** The paper introduces SoccerNet-GSR and describes 200 fully annotated 30-second broadcast clips, including its challenge material. It reports more than 9.37 million annotated pitch-line points and more than 2.36 million athlete positions. Each athlete detection can include pitch position, role, team, jersey number, and track identity.

**Dataset-version note for this thesis:** The publication-level count of 200 clips must not replace the actual frozen source description used in this project. Dataset B uses the immutable SoccerNet GSR v1.3 release available to the project: 57 train, 58 validation, and 49 test clips, totalling 164 clips. Each contains 750 ordered JPEG frames at 25 fps. The thesis must report these exact working-release counts and explain that challenge material is not part of Dataset B.

**Model and pipeline:** GSR-Baseline is a modular computer-vision pipeline implemented with TrackLab rather than a language model. It combines YOLOv8 person detection, StrongSORT tracking, PRTReID embeddings for re-identification and role/team information, MMOCR for jersey-number recognition, TVCalib for pitch localization and camera calibration, K-means for team grouping, and tracklet-level voting for consistent attributes.

YOLOv8 is used without SoccerNet fine-tuning. Most modules use pretrained models; PRTReID is trained on the SoccerNet-GSR training set, while the baseline uses the standard TVCalib weights. Describing the whole pipeline as entirely off-the-shelf or entirely unfine-tuned would therefore be inaccurate.

**Input and output:** Raw frames from a single broadcast camera are processed to obtain athlete boxes and tracks. Pitch-line segmentation and camera calibration estimate a homography. The bottom centre of each person's bounding box is treated as the point on the ground and projected into the assumed 105 by 68 metre pitch coordinates. The final output is a structured game state, not natural-language recognition or coaching advice.

**Retrieval or sampling method:** The paper does not perform analogous-case retrieval or LLM frame sampling. K-means groups tracklet embeddings to assign team affiliation, while voting aggregates role and jersey-number predictions across detections. Neither operation is equivalent to B4 cosine nearest-neighbour retrieval between Dataset B and Dataset A cases.

**Metric:** GS-HOTA adapts HOTA to game-state reconstruction. Localization similarity depends on Euclidean distance in pitch coordinates, using a five-metre tolerance parameter. Identification similarity is one only when all applicable attributes match. Detection and association accuracy are then incorporated following HOTA. This strict joint score is appropriate for GSR but is not an evaluation metric for this thesis's natural-language outputs.

**Experimental comparisons:** Because GSR is introduced as a new combined task, there is no prior end-to-end GSR system used as a direct baseline. The main paper analyses variants of its own metric and pipeline. Module ablations substitute ground-truth inputs for upstream components to isolate error propagation. The supplementary material separately compares the image-plane tracking component with standard MOT systems.

**Main finding in my own words:** Reconstructing an identity-rich, pitch-grounded game state from one broadcast camera is difficult because detection, tracking, identification, OCR, pitch localization, and calibration errors interact. The released baseline obtains a low full-pipeline score, and calibration failures can destroy an otherwise plausible reconstruction. The result characterizes this first modular baseline, not a fundamental limit on GSR.

**Evidence from the paper:**

- Table 1: the test score is 57.64 when evaluated as standard image-space HOTA without pitch or identity attributes. Successively enforcing pitch and identity information reduces performance, reaching 22.26 GS-HOTA for the complete condition. Full-condition scores are 18.05 on validation and 23.36 on challenge.
- Table 2: when ground truth replaces other upstream modules, the reported GS-HOTA values are 92.00 for Team Side, 87.42 for ReID and its downstream components, 51.39 for Calibration, 49.99 for Pitch, 56.75 for Jersey Number, and 35.28 for Bounding-Box Detection. The full pipeline scores 22.26. Because downstream dependencies remain enabled in several rows, these are diagnostic module experiments rather than pure isolated accuracies.
- Figure 4: performance changes sharply under stricter distance tolerances, and the authors select five metres as a reasonable default given the field scale and camera distance.
- Figure 5: the stronger qualitative example scores 49.69 GS-HOTA. A second example scores 0.23 after poor calibration caused by too few visible pitch elements, illustrating error propagation.
- Table 2 and the inference discussion: pitch localization, calibration, and jersey recognition run at 2.9, 7.6, and 3.8 fps respectively in the authors' A100 measurements. The offline full pipeline takes approximately 11 minutes per 30-second clip.

**Limitations stated or acknowledged by the authors:**

- The modular pipeline contains strongly interdependent subtasks and compounds upstream errors.
- It is an offline system and far from real-time processing.
- The authors propose better individual modules and end-to-end differentiable approaches as future work.
- A person's location is approximated using the bottom of the bounding box on the ground plane, reducing precision during jumps.
- The ball is excluded because it frequently leaves the ground plane.

**Additional limitations I noticed:**

- The strict identity similarity gives zero when any required attribute is wrong. This appropriately penalizes an incorrect identity but does not express how close the failed attribute was; component analyses are needed for diagnosis.
- Left and right team labels are defined relative to the clip's camera view, not as persistent real team identities.
- The reported 22.26 score is for one initial modular baseline and must not be called an upper bound or a performance ceiling. Later methods could and do improve on it.
- The paper evaluates tracking and structured reconstruction, not event recognition, causal understanding, tactical diagnosis, or coaching.

**Relevance to my thesis:** This paper is the primary provenance and task-context source for the SoccerNet-GSR family from which Dataset B clips originate. It establishes that the clips are 30-second football broadcast sequences and explains the private metadata associated with them. It also demonstrates how difficult detailed football perception can be. It is not an MLLM paper and does not answer whether an analogous human case improves recognition or coaching.

**Leakage relevance:** GSR annotations, tracking, pitch coordinates, identities, jersey numbers, team labels, action labels, filenames revealing events, and human references must not be exposed to Qwen in B0, B1, B3, B4, or B5. Automatic B4 retrieval may use only Dataset B pixels or embeddings derived from those pixels. Hidden Dataset B action labels are allowed only for B2 and must be reported as intentional diagnostic leakage.

**Evidence classification:**

- Direct evidence for the original SoccerNet-GSR task, dataset, annotations, metric, baseline, and reported computer-vision results.
- Direct provenance background for the source family used by Dataset B, subject to the project's v1.3 version-specific counts.
- Background for the difficulty of extracting structured football information from broadcast video.
- No direct evidence for MLLM performance, sampled-frame prompting, analogous-case retrieval, natural-language coaching, or hallucination evaluation.

**Thesis design choices supported:**

- Cite and version the exact Dataset B release and preserve its original frame order and resolution metadata.
- Keep SoccerNet metadata private and use it for reference or permitted diagnostics rather than as normal model input.
- Report that the experiment uses sampled RGB frames from GSR clips but does not attempt full game-state reconstruction.
- Avoid interpreting MLLM recognition scores as equivalent to tracking, calibration, or identity reconstruction performance.

This paper does **not** support supplying structured game-state annotations to Qwen in the current experiment. Doing so would change the research question and violate the pixel-only input rule for the automatic visual conditions.

**What the paper does not establish:** It does not evaluate an MLLM, natural-language generation, frame-count selection, CLIP retrieval, analogous examples, coaching advice, blind copying, hallucination, or calibrated uncertainty. It does not provide coaching ground truth, and its tracking annotations are not substitutes for the private human Dataset B recognition references.

**Where I may cite it:** In the Dataset B provenance and football computer-vision background sections; when defining SoccerNet-GSR, its clips, annotations, and the distinction between structured game state and language-based coaching analysis; and when explaining why hidden metadata must remain separate from visual experimental inputs. It should not be cited as evidence that retrieval improves an MLLM or that the system understands tactics.

### Reading note - S31

**Citation:** Held, J., Itani, H., Cioppa, A., Giancola, S., Ghanem, B., and Van Droogenbroeck, M. (2024). "X-VARS: Introducing Explainability in Football Refereeing with Multi-Modal Large Language Models." *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops*, pp. 3267-3279.

**DOI:** [10.1109/CVPRW63382.2024.00332](https://doi.org/10.1109/CVPRW63382.2024.00332)

**Official paper:** [CVF Open Access](https://openaccess.thecvf.com/content/CVPR2024W/CVsports/html/Held_X-VARS_Introducing_Explainability_in_Football_Refereeing_with_Multi-Modal_Large_Language_CVPRW_2024_paper.html)

**Accessible copy:** [arXiv](https://arxiv.org/abs/2404.06332)

**Date read:** 2026-09-07

**Research problem:** The paper asks whether a football-specific multimodal language model can classify foul incidents and generate natural-language explanations that are consistent with the video and the Laws of the Game.

**Dataset:** SoccerNet-XFoul contains more than 10,000 football clips and more than 22,000 video-question-answer triplets. More than 70 experienced referees contributed annotations after officiating between 140 and 2,279 official games, with an average of 655. Four languages were permitted; ChatGPT-3.5 translated non-English answers and another referee reviewed the translations. Due to the subjectivity of foul decisions, the collection has an average of 1.5 answers per question.

**Model:** X-VARS builds on Video-ChatGPT and uses Vicuna-v1.1 as its language component. A fine-tuned CLIP ViT-L/14 encoder produces visual features and auxiliary predictions for foul type and offence severity. A projection layer maps the pooled video representation into the LLM embedding space, while auxiliary class predictions are also inserted into the language prompt as text.

**Input representation:** Each incident is represented by 16 frames at 224-pixel resolution: eight frames before and eight frames after the annotated foul moment. CLIP hidden states are averaged separately over temporal and spatial dimensions and concatenated into a spatio-temporal representation before projection into language-model tokens.

This construction is event-centred because it uses a known foul boundary to choose the before-and-after window. It is not equivalent to this thesis's blind, uniformly sampled 30-second Dataset B input, where the hidden action location or label cannot guide frame selection.

**Training:** In stage one, CLIP and its classification heads are fine-tuned for 14 epochs while the language component is not trained. In stage two, the visual components are frozen and QLoRA is used to tune approximately 1% of the language-model layers for three epochs alongside the projection mechanism. X-VARS is therefore a domain-trained system, not a zero-shot evaluation of a general MLLM.

**Retrieval or sampling method:** X-VARS does not retrieve analogous cases. CLIP is used as a learned visual encoder and classifier, not for cosine nearest-neighbour search. The paper uses one fixed 16-frame event-centred design and does not compare F10, F20, F30, F60, adaptive sampling, or random versus relevant cases.

**Experimental comparisons:** Classification results are compared with ResNet, R(2+1)D, and VARS-MViT variants from the earlier multi-view VARS system. The authors also report a fine-tuned CLIP-L/14 classifier, X-VARS with and without injected classification predictions, and qualitative analyses of generated answers.

**Evaluation metrics:** Foul-type and offence-severity recognition use accuracy and balanced accuracy. Generated explanations are evaluated by referees using a five-point agreement scale. The paper also reports agreement between X-VARS's generated classification and the CLIP classification supplied as text.

**Main finding in my own words:** A football-domain MLLM can produce fluent referee explanations and competitive foul/severity classifications after substantial task-specific training. Its human-study ratings are close to those of human-written explanations on a small selected evaluation. However, it sometimes invents actions, and the experiment does not show that a general model understands football clips without domain training or that retrieved analogies improve its answers.

**Evidence from the paper:**

- Table 3: human-written explanations receive a mean score of 4.0 and X-VARS explanations 3.8. X-VARS is rated higher than the paired human explanation in 46% of evaluated clips. Its rating distribution contains more disagreement responses, so “comparable” should not be rewritten as equivalent or superior human performance.
- Human-study method: 20 referees each evaluate 20 randomly selected five-second clips without being told whether the explanation came from X-VARS or a referee. They judge consistency with the video and alignment with the Laws of the Game.
- Table 4: the fine-tuned single-view CLIP-L/14 obtains 0.51 foul-type accuracy and 0.52 offence/severity accuracy. X-VARS obtains 0.62 offence/severity accuracy. The previous VARS-MViT max-pooling result is 0.43, so X-VARS improves by **19 percentage points**. The paper calls this 19%, but it is an arithmetic point difference rather than a 19% relative increase.
- Section 5.4: the generated X-VARS classification agrees with its injected CLIP classification in 76% of cases. This shows that the LLM does not simply reproduce the injected label every time. It does not by itself isolate whether disagreement is caused by video tokens, language priors, or another component.
- A 40-clip qualitative ablation reports six points higher balanced accuracy when class-prediction text is supplied, especially on rare cases. Its small, selected sample limits the strength of this evidence.
- Figure 4 and Section 5.3: the authors explicitly observe hallucinations in which X-VARS recognizes actions that are not present in the video. This is qualitative evidence; no hallucination rate or dedicated metric is reported.

**Limitations stated or acknowledged by the authors:**

- X-VARS can hallucinate actions not shown in the video.
- The generated explanations often do not state foul type explicitly, preventing direct foul-type evaluation of X-VARS's natural-language answers.
- Referee decisions are subjective, and annotators can reasonably disagree about intensity, cards, and foul interpretation.
- The authors identify the general tendency of LLMs to agree with users, although their examples suggest X-VARS often maintains its original decision.

**Additional limitations I noticed:**

- The human study is small: 20 referees evaluate 20 short clips each, and the paper does not establish broad equivalence with professional referee performance.
- Explanations are assessed for perceived video/rule consistency, not with separate factuality, hallucination, calibration, or causal-reasoning scores.
- Frame selection is aligned to a known foul timestamp and is not ablated. It therefore cannot justify an optimal frame count or blind sampling method.
- ChatGPT-3.5 is used to extract classifications from generated explanations. This adds another model-dependent stage to the reported X-VARS recognition score.
- The system is trained on the same football-refereeing task and labels it evaluates. Its results do not represent zero-shot transfer to general football coaching.
- Auxiliary foul and severity predictions are provided as text. This changes more than visual prompting alone and can propagate classifier mistakes into the explanation.

**Relevance to my thesis:** X-VARS is a close precedent showing that a multimodal language model can process football frames and generate domain-specific natural-language analysis. It supports evaluating recognition separately from explanation quality and retaining a hallucination category. The task nevertheless differs: X-VARS explains officiating decisions after supervised football-domain training, whereas this thesis tests whether a retrieved human-annotated analogous case changes a general MLLM's recognition and coaching advice for a new clip.

**Evidence classification:**

- Direct evidence for X-VARS and its performance on the evaluated foul-recognition and referee-explanation tasks.
- Direct evidence that its human evaluators rated generated explanations close to human-written explanations in the reported small study.
- Direct qualitative evidence that a football MLLM can hallucinate unseen actions.
- Indirect support for sampled-frame football prompting and separate recognition/coaching evaluation.
- No evidence for analogous-case retrieval, cosine kNN, relevant-versus-random case selection, or optimal frame count.

**Thesis design choices supported:**

- Score recognition before coaching quality so a fluent explanation cannot conceal an incorrect event interpretation.
- Use human evaluation for domain-specific free text rather than relying only on lexical overlap.
- Score unsupported visual claims explicitly because a football MLLM can produce plausible explanations containing actions absent from the video.
- Report the exact number, placement, resolution, and construction of input frames.
- Avoid calling fluent or convincing language proof of correct football understanding.

The paper's hybrid classifier-to-text design should **not** be added to the present experiment. Supplying predicted foul or action labels would introduce a second intervention and no longer isolate the effect of the analogous Dataset A case. Likewise, X-VARS's event-centred 16-frame input does not replace the current F10/F20/F30/F60 sampling pilot.

**What the paper does not establish:** It does not test retrieval augmentation, Dataset A analogies, random cases, CLIP cosine search, or advice-only controls. It does not determine the best frame count, quantify hallucination, evaluate calibrated uncertainty, or provide coaching ground truth. Refereeing explanations are not the same outcome as tactical coaching advice.

**Where I may cite it:** In related work as a football-specific MLLM precedent; in methodology when motivating separate recognition and explanation scores and human evaluation; and in limitations as qualitative evidence that sports MLLMs can hallucinate actions. It should not be cited as evidence that B4 retrieval improves coaching or that 16 event-centred frames are optimal for Dataset B.

### Reading note - S33

**Citation:** Düking, P., Sperlich, B., Voigt, L., Van Hooren, B., Zanini, M., and Zinner, C. (2024). "ChatGPT Generated Training Plans for Runners are not Rated Optimal by Coaching Experts, but Increase in Quality with Additional Input Information." *Journal of Sports Science and Medicine*, 23, 56-72.

**DOI:** [10.52082/jssm.2024.56](https://doi.org/10.52082/jssm.2024.56)

**Official paper:** [Journal of Sports Science and Medicine PDF](https://jssm.org/volume23/iss1/cap/jssm-23-56.pdf)

**Accessible full text:** [PubMed Central](https://pmc.ncbi.nlm.nih.gov/articles/PMC10915606/)

**Date read:** 2026-09-07

**Research problem:** The study asks whether the quality of a ChatGPT-generated six-week running plan changes when the user supplies increasingly detailed personal and training information.

**Study material:** The authors created three plans for the same fictional 20-year-old male runner. Plan 1 began with only a general request for a six-week plan. Plans 2 and 3 supplied progressively more information about training history, performance, goals, health, available equipment, and monitoring. The authors also used progressively more follow-up questions, or "check-backs," in the richer conversations. The complete prompts and model responses are reproduced in the paper's appendix.

**Model and date:** The paper reports ChatGPT "Version 3.0.1," used on 23 May 2023 without plugins. This is the authors' label and does not identify a reproducible API model snapshot, decoding configuration, or seed.

**Evaluation:** Ten endurance coaching experts rated each plan against 22 literature-derived criteria on a five-point scale, with zero for not applicable. Eligible raters had at least a Master's degree in sports science and at least five years of relevant coaching experience. The sample had a mean age of 33 plus or minus 5 years, included four PhD and six Master's degree holders, and reported 7 plus or minus 2 years of coaching experience. The analysis used a Friedman test with Bonferroni correction and Fleiss' kappa for inter-rater agreement.

**Main finding in my own words:** More detailed user information and follow-up prompting produced plans that coaches generally rated more highly, but even the most detailed plan was not judged consistently optimal. The result supports the importance of input context and expert checking; it does not show that an LLM can replace a coach.

**Evidence from the paper:**

- Across all 22 criteria, the number of median ratings below 3 was 19 for Plan 1, 11 for Plan 2, and 1 for Plan 3. Median ratings equal to 3 occurred 3, 5, and 8 times, while ratings above 3 occurred 0, 6, and 13 times.
- Plan 1 was rated significantly lower than Plan 2 on 3 criteria and lower than Plan 3 on 15 criteria. Plan 2 was rated lower than Plan 3 on 9 criteria.
- For the single overall-plan item, the medians were 2, 3, and 4. Plan 1 differed significantly from Plan 2 (`p = 0.005`) and Plan 3 (`p = 0.003`), whereas Plan 2 and Plan 3 did not differ on this single item (`p = 1.0`). The lack of significance for that item does not contradict the nine significant criterion-level differences.
- Table 2's summary of 15/7/1 ratings below 3, 3/5/6 ratings equal to 3, and 0/6/11 ratings above 3 covers the 18 **primary** criteria. Adding the four secondary criteria produces the 22-criterion totals reported in the abstract and results. There is therefore no abstract-versus-table contradiction.
- Fleiss' kappa was 0.43 for Plan 1, 0.247 for Plan 2, and 0.00 for Plan 3. Agreement became poorer as the plans became more detailed, illustrating that expert coaching judgments can differ even when raters meet strict experience criteria.
- The discussion says Plan 2 outperformed Plan 1 on 9 of 22 criteria, but the abstract, results paragraph, and Table 2 instead support Plan 2 outperforming Plan 1 on 3 criteria and Plan 3 outperforming Plan 2 on 9. The thesis should use the table-supported result and not repeat the likely discussion wording error.
- The authors identify unsupported or questionable recommendations despite fluent presentation. One example is active recovery after exercise, which the paper says was recommended despite the cited evidence not supporting it as an effective recovery method.

**Limitations stated or acknowledged by the authors:**

- The findings apply only to the ChatGPT version accessed on 23 May 2023; rapidly changing models may behave differently.
- Agreement between raters was weak, especially for Plan 3. The authors link this partly to the lack of a universal evidence-based definition of an optimal plan and differences in coaching style.
- The authors advise against using the generated plans without checking their recommendations and call for future comparison with plans written by certified coaches.

**Additional limitations I noticed:**

- Only three model-generated plans for one fictional runner were evaluated. The study does not report repeated generations, decoding settings, or variation across people, sports, or goals.
- Input detail and number of follow-up turns change together. The experiment therefore cannot isolate whether improvement came from the initial information, the extra interaction, or both.
- There is no human-written training-plan baseline, athlete outcome study, injury analysis, or test of whether following a plan improves performance.
- The 22 criteria concern a multi-week running programme. They cannot be copied directly as a rubric for short, clip-specific football recognition and tactical coaching advice.
- This is a text-only study. It does not evaluate images, video sampling, multimodal recognition, case retrieval, or whether an analogy is relevant.

**Relevance to my thesis:** This is indirect evidence that coaching-related LLM output can change with the information supplied and that fluent advice still needs structured human assessment. It supports freezing the prompt, evaluating intended coaching dimensions separately, preserving exact model answers, and checking unsupported advice. It also shows why reporting only one overall quality score can hide criterion-level weaknesses.

Because this thesis currently has one human reviewer, Fleiss' kappa or any other inter-rater reliability statistic cannot be calculated. A fixed rubric, written scoring anchors, blinded condition labels where practical, and a later repeat-scoring consistency check can improve discipline, but they are not substitutes for independent raters. The one-reviewer design must be reported as a limitation.

**Evidence classification:**

- Direct evidence that the three evaluated ChatGPT conversations produced differently rated running plans as prompt information and follow-up interaction increased.
- Direct evidence of substantial disagreement among the ten raters in this particular evaluation.
- Indirect support for structured human evaluation of generated sports advice and for recording exact prompts and outputs.
- No evidence that a retrieved football case improves recognition or coaching.

**Thesis design choices supported:**

- Keep B frames, prompts, generation settings, and scoring criteria fixed across paired conditions so the case is the intended difference.
- Score coaching with explicit dimensions rather than only an overall impression.
- Check for unsupported recommendations even when the answer sounds confident and useful.
- Preserve the exact prompt and raw output so input context and output quality can be audited.

**What the paper does not establish:** It does not test an MLLM, football sequences, temporal frame sampling, Dataset A cases, similarity retrieval, B0 versus B3 or B4, recognition accuracy, blind copying, calibrated uncertainty, or retrieval-assisted coaching. More information in a prompt is not the same intervention as providing an analogous case.

**Where I may cite it:** In related work on AI-generated sports advice and in methodology when motivating criterion-based human assessment and expert verification. It may also support a limitations discussion about subjective coaching judgments. It should not be cited as evidence that B4 retrieval works or that more frames necessarily improve performance.

### Reading note - S35

**Citation:** Li, Y., Du, Y., Zhou, K., Wang, J., Zhao, W. X., and Wen, J.-R. (2023). "Evaluating Object Hallucination in Large Vision-Language Models." *Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing*, pp. 292-305.

**DOI:** [10.18653/v1/2023.emnlp-main.20](https://doi.org/10.18653/v1/2023.emnlp-main.20)

**Official record and paper:** [ACL Anthology](https://aclanthology.org/2023.emnlp-main.20/)

**Date read:** 2026-09-07

**ID clarification:** This is S35, the POPE paper. S34 is the separate 2018 CHAIR paper by Rohrbach et al. POPE uses CHAIR as an earlier comparison metric, but the two papers must not be combined into one bibliography entry.

**Research problem:** The paper asks whether large vision-language models generate objects that are absent from the supplied image, whether visual-instruction data statistics are associated with those errors, and whether object hallucination can be evaluated more stably than by parsing free-form captions.

**Datasets:** The CHAIR analysis uses 2,000 randomly sampled MSCOCO validation images with object annotations and human captions. The main POPE experiment uses 500 MSCOCO validation images containing more than three annotated objects and constructs six balanced yes/no questions per image. The scalability analysis uses SEEM-generated object annotations for MSCOCO, A-OKVQA, and GQA.

**Models:** The paper evaluates mPLUG-Owl, LLaVA, MultiModal-GPT, MiniGPT-4, and InstructBLIP. It also reports earlier results for OSCAR, VinVL, BLIP, and OFA as smaller vision-language baselines. These systems use different visual encoders, alignment modules, language backbones, and instruction-tuning datasets, so their differences cannot be attributed solely to model size or the presence of an LLM.

**Input representation:** The experiments use individual static images, not video. For CHAIR, the models generate captions using two similar prompts: "Generate a short caption of the image" and "Provide a brief description of the given image." POPE instead asks binary questions of the form "Is there a/an <object> in the image?"

**CHAIR and POPE:** CHAIR-I measures the proportion of mentioned object instances that are hallucinated, while CHAIR-S measures the proportion of captions containing at least one hallucinated object. POPE reformulates object hallucination as balanced binary classification by pairing present objects with nonexistent objects and recording yes/no answers. The reported POPE metrics are accuracy, precision, recall, F1, and the proportion of answers that say yes.

**Negative-object sampling:**

- Random sampling selects objects absent from the image at random.
- Popular sampling selects frequent dataset-level objects that are absent from the image.
- Adversarial sampling selects absent objects that frequently co-occur with objects actually present in the image.

These strategies construct increasingly difficult **evaluation probes**. They are not retrieval strategies, in-context examples, analogous cases, or evidence that relevant cases outperform random cases.

**Main finding in my own words:** Several evaluated LVLMs frequently claimed that absent objects were present, especially when those objects were common in the instruction data or commonly co-occurred with real image objects. POPE exposed this behaviour using controlled yes/no questions and was less sensitive than CHAIR to small changes in prompt wording. A better POPE score nevertheless does not imply better overall multimodal performance.

**Evidence from the paper:**

- Table 1 reports a CHAIR-S value of 32.7 for LLaVA and 13.0 for OSCAR-Base under the short-caption instruction. This supports the paper's finding for those evaluated systems; it should not be generalized to every LVLM or every prompt.
- Table 2 reports appearance-frequency hit ratios at 10 between 0.4152 and 0.5455 and dining-table co-occurrence hit ratios at 10 between 0.5600 and 0.6608 for four LVLMs. Roughly half of the hallucinated objects fall among the ten most frequent or relevant co-occurring COCO objects under these analyses.
- Table 3 shows that mPLUG-Owl, LLaVA, and MultiModal-GPT have very high recall but say yes to approximately 95% to 100% of questions, producing F1 scores below 70. InstructBLIP has the strongest reported F1: 89.29 for random, 83.45 for popular, and 78.45 for adversarial sampling.
- Table 4 evaluates LLaVA with four prompt paraphrases. POPE F1 has a reported standard deviation of 0.78, while CHAIR-I has a standard deviation of 3.22. This is evidence of greater prompt stability in that experiment, not universal proof that POPE is prompt-independent.
- The consistency analysis finds that, among 1,303 and 1,445 objects answered no by InstructBLIP and MiniGPT-4, respectively, 0 and 5 appeared in the models' own captions. It also reports that 664 of 664 and 961 of 1,034 caption-mentioned objects received yes answers.
- Table 6 shows that hallucination and VQA performance need not rank models identically. MiniGPT-4 has higher POPE F1 than LLaVA but lower VQA performance on the reported A-OKVQA and GQA evaluations.

**Limitations stated by the authors:**

- POPE measures coarse object presence, not overall LVLM capability or fine-grained errors involving attributes, counts, and positions.
- Only subsets of the validation datasets are evaluated, so results can depend on the sampled distribution.
- Matching explicit yes/no strings can misclassify answers that do not follow the requested format.
- Automatically generated SEEM labels can differ from human object annotations and change the results.
- Only a small set of contemporary models is compared, without newer or closed-source systems.

**Additional limitations I noticed:**

- The experiments are static-image evaluations and contain no temporal order, action boundary, or video-level hallucination.
- The study evaluates object nouns from dataset label sets. Football errors in this thesis can instead concern actions, possession changes, temporal order, causal claims, outcomes, or tactical interpretation.
- Popular and adversarial negatives depend on corpus statistics and object annotations. Applying them to Dataset B would require a justified football concept vocabulary and private reference annotations that must never be exposed to the model in the main visual conditions.
- POPE changes the output task from normal analysis to a collection of binary questions. It therefore cannot directly score the natural-text B0-B5 answers without adding a separate diagnostic experiment.
- Because the evaluated models differ in architecture and training data, the frequency and co-occurrence analyses show an empirical association; they do not fully establish a single causal mechanism for hallucination.

**Relevance to my thesis:** POPE provides direct methodological background for controlled object-hallucination evaluation and strong evidence that hallucination must be measured separately from general task performance. Its central lesson applies to this thesis: a model can produce plausible visual claims that are unsupported by the input, so recognition and coaching scores alone are insufficient.

The current thesis should retain human scoring of unsupported claims in the normal-text answers. A POPE-style football probe set could be an optional, separately reported diagnostic only if it is designed and frozen before test evaluation. It is not required for answering the main B0-versus-B3 and B0-versus-B4 research comparisons, and it should not be silently added after viewing test outputs.

**Evidence classification:**

- Direct evidence for object hallucination and POPE on the evaluated static-image datasets and models.
- Direct evidence that the evaluated POPE setup is less prompt-sensitive than CHAIR in the reported LLaVA comparison.
- Indirect support for separately measuring unsupported visual claims in football-video answers.
- No evidence for video temporal hallucination, football coaching, analogous cases, or cosine nearest-neighbour retrieval.

**Thesis design choices supported:**

- Score unsupported claims separately from recognition accuracy and coaching quality.
- Do not treat a low hallucination score as proof of strong overall task performance.
- Define exactly what counts as unsupported using the frozen Dataset B human reference and visible sampled frames.
- Preserve raw model text rather than silently correcting or normalizing unsupported claims.
- If a separate binary diagnostic is ever used, freeze its questions, labels, parsing rules, and sampling method before the final test run.

**What the paper does not establish:** It does not validate the thesis's open-ended football hallucination rubric, select a video frame count, test temporal understanding, retrieve Dataset A cases, compare B0 with B3 or B4, or show that relevant analogies improve coaching. POPE random sampling is not the same as B1 random-case selection, and its adversarial sampling is not B4 retrieval.

**Where I may cite it:** In related work and methodology when defining object hallucination, explaining CHAIR-I/CHAIR-S and POPE, and motivating a separate unsupported-claim score. It may also be cited in limitations to explain why an object-only static-image benchmark cannot fully cover action and temporal hallucinations in football video.

### Reading note - S36

**Citation:** Wang, Y., Wang, Y., Zhao, D., Xie, C., and Zheng, Z. (2024). "VideoHallucer: Evaluating Intrinsic and Extrinsic Hallucinations in Large Video-Language Models." *arXiv:2406.16338v1* [cs.CV].

**Persistent identifier:** [10.48550/arXiv.2406.16338](https://doi.org/10.48550/arXiv.2406.16338)

**Paper and record:** [arXiv](https://arxiv.org/abs/2406.16338)

**Status:** Non-archival arXiv preprint; no peer-reviewed venue is claimed in this register.

**Date read:** 2026-09-07

**Research problem:** The paper asks how well large video-language models can distinguish content supported by a video from content that contradicts or cannot be verified from that video. It introduces a video-specific hallucination taxonomy, a paired binary-question benchmark, and a self-explanation mitigation method.

**Hallucination taxonomy:** Intrinsic hallucinations contradict the source video and are divided into object-relation, temporal, and semantic-detail errors. Extrinsic hallucinations cannot be verified from the source video and are divided into factual claims that may agree with outside world knowledge and non-factual claims that conflict with it. The distinction is particularly useful for this thesis because plausible football knowledge may still be unsupported by the sampled Dataset B frames.

**Dataset:** VideoHallucer contains 1,800 unique question-answer pairs across 948 videos. It draws object-relation material from VidOR and VidVRD, temporal material from ActivityNet, semantic-detail material from HawkEye, and extrinsic factual/non-factual material from YouCook, COIN, and EDUVSUM. The paper reports an average question length of 61.4 words and an average video length of 85.6 seconds, with setting-level averages ranging from 7.0 to 187.0 seconds.

Each of the five settings is described as having 200 basic and 200 hallucinated questions. However, the factual and non-factual settings deliberately reuse the same 200 basic questions. Thus, the 1,800 unique total consists of 800 unique basic questions and 1,000 hallucinated questions, not 900 of each.

**Benchmark construction:** Every evaluation item uses a basic question and an intentionally modified hallucinated counterpart. A model receives an overall hit only when it answers both questions correctly. The question order is randomized and yes/no answers are balanced to reduce simple language and answer-distribution biases. The paper also reports basic-question accuracy, hallucinated-question accuracy, overall paired accuracy, yes-percentage difference, and false-positive ratio.

**Models and source inconsistency:** The abstract says the benchmark evaluates eleven LVLMs. Section 4.1 and the main text instead say twelve model families: ten open-source systems plus Gemini-1.5-Pro and GPT-4o. Table 3 additionally reports several 13B and 34B variants, so its number of result rows is larger than the family count. The thesis should state that the preprint is internally inconsistent and avoid using the model count as an important claim.

**Input representation and frame settings:** Models are run according to their original configurations, including their own numbers of frames and generation hyperparameters. The benchmark therefore does not hold visual sampling constant across models. For a separate image-language comparison, LLaVA-1.5 and GPT-4V receive only the middle video frame.

**Use of CLIP:** For semantic-detail data construction, HawkEye segments with a CLIP similarity score above 0.85 are selected as visually similar source pairs before annotators identify semantic differences. This is dataset curation and hard-pair construction. It is not retrieval-augmented generation, video-to-case cosine kNN, or evidence that B4 improves coaching.

**Main finding in my own words:** The evaluated video-language models often answer straightforward questions correctly while failing to reject plausible but unsupported alternatives. The problem is especially difficult when a statement is factually reasonable in the outside world but is not established by the video. Scaling appears helpful for some visual-detail and counterfactual settings but does not solve source-grounded factual hallucination. Self-generated explanation can help some models, but it is not uniformly beneficial.

**Evidence from the paper:**

- Table 3 reports that VideoChatGPT scores 92.8 on basic questions, 10.4 on hallucinated questions, and 6.4 on paired overall accuracy. GPT-4o records 75.1, 74.2, and 53.3 respectively, compared with the reported human results of 90.0, 88.8, and 85.0.
- Most model results on object-relation hallucination are centred around 50%, while extrinsic factual hallucination remains especially difficult. These findings apply to the evaluated benchmark and should not be presented as universal model behaviour.
- Table 4 shows that middle-frame image-language models can outperform several video-language systems on object-relation and semantic-detail subsets. For example, LLaVA-1.5 obtains 61.5 paired accuracy for object-relation questions versus 43.5 for LLaMA-VID. Because architectures, training data, and input processing differ, this does not isolate a causal advantage of one frame.
- Figure 5 reports that most evaluated models are better at checking whether a statement is factually correct than deciding whether the video itself supports that statement. LLaVA-NeXT-Video-DPO is noted as an exception.
- Table 5 reports large Self-PEP gains for some models, including VideoChatGPT from 6.4 to 20.9, VideoChat2 from 7.8 to 23.5, and Gemini-1.5-Pro from 37.8 to 52.0 overall. It also reports decreases for VideoLaVIT, PLLaVA, and LLaVA-NeXT-Video-DPO. The abstract's average "5.38% improvement" should be reported using the authors' wording or described cautiously as an average reported gain, not as a universal guarantee.
- Three English-proficient evaluators with basic computer knowledge produce the human benchmark result. The paper reports a Pearson correlation coefficient of 0.557 among their scores, described as moderate agreement. They are not described as football, video, or subject-matter experts.

**Limitations stated by the authors:**

- Human annotation introduces noise.
- The benchmark's scalability is limited.
- The authors warn that hallucinated questions could be misinterpreted in related research.

**Additional limitations I noticed:**

- The arXiv version is internally inconsistent about whether eleven or twelve LVLMs were evaluated.
- Using each model's original frame count and generation settings confounds architecture, training data, frame sampling, and decoding in cross-model comparisons.
- The human comparison uses only three general evaluators, and Pearson correlation is not a complete measure of agreement for binary labels.
- The paired binary VQA task detects susceptibility to supplied false or unsupported premises. It is different from measuring hallucinations that arise spontaneously in a model's normal free-text description.
- Some source questions and altered videos are constructed specifically for the benchmark. Performance may depend on annotation choices and the difficulty of the selected negative pair.
- Self-PEP changes the prompting procedure and sometimes lowers accuracy. It is therefore not a safe default intervention and cannot be added to the thesis experiment without changing the design.
- The benchmark contains no football-specific tactical coaching and does not test whether a supplied analogy causes blind copying or unsupported transfer.

**Relevance to my thesis:** VideoHallucer is the strongest priority source for explaining why video hallucination includes more than nonexistent objects. Its intrinsic categories map conceptually to incorrect players or relations, incorrect event order, and unsupported visible details. Its extrinsic factual category is also important: generic football knowledge may be true but still unsupported as a diagnosis of the current sequence.

The paper supports keeping hallucination separate from recognition and coaching quality and checking whether every claim is grounded in the sampled frames or the permitted case context. It also supports distinguishing contradiction from unverifiable extra information. The thesis's primary results should still come from the normal-text B0-B5 outputs and the frozen human rubric. Introducing paired yes/no questions would be a separate experiment, not a silent scoring transformation.

**Evidence classification:**

- Direct evidence for VideoHallucer's taxonomy, paired-question benchmark, and results on the evaluated general-domain videos and models.
- Direct evidence that basic-question accuracy can substantially exceed paired hallucination accuracy in this benchmark.
- Indirect support for temporal and source-grounding hallucination categories in the football-video rubric.
- No direct evidence for football coaching, analogous Dataset A cases, cosine kNN retrieval, or B0-versus-B3/B4 improvement.

**Thesis design choices supported:**

- Score hallucination separately from recognition and coaching quality.
- Distinguish claims contradicted by the frames from claims that are merely unsupported or unverifiable.
- Include temporal-order and event-detail errors, not only absent-object errors.
- Do not treat generally correct football knowledge as evidence that the model correctly interpreted the current clip.
- Keep frame sampling and generation settings identical across paired B0-B5 comparisons.
- Preserve raw free-text answers so spontaneous unsupported claims can be reviewed.

**What the paper does not establish:** It does not determine an optimal frame count, isolate native-video processing from sampled frames, evaluate Qwen3.5, use football footage, retrieve analogous coaching cases, validate B4, or show that a larger model will necessarily hallucinate less. Its CLIP threshold is not a case-retrieval experiment, and Self-PEP is not uniformly reliable.

**Where I may cite it:** In related work as the main video-specific hallucination benchmark; in methodology when defining intrinsic, temporal, semantic-detail, and extrinsic unsupported claims; and in limitations when explaining why normal-text football answers require human grounding judgments beyond object-presence metrics such as CHAIR and POPE.

## Literature synthesis

This section turns the individual paper reviews into a claim-based account of the existing evidence, the unresolved question, and the role of this experiment. The concise version is suitable for an initial supervisor explanation. The full draft preserves the longer reasoning for later thesis writing.

### Concise synthesis

#### 1. What existing research establishes

Prior research provides the separate foundations for this project. Video-language studies show that sampled-frame models can rely heavily on static appearance and that more frames are not automatically better. Visual in-context-learning and multimodal retrieval research shows that selecting relevant examples can outperform random examples, although noisy retrieval may also harm performance. CLIP provides a practical way to represent pixels as embeddings for cosine-similarity matching. SoccerNet-GSR and X-VARS establish the football-video context, while the running-plan study shows that generated sports advice requires structured human evaluation. POPE and VideoHallucer demonstrate that fluent multimodal answers can contain unsupported object, event, temporal, and factual claims.

#### 2. What remains uncertain

These studies do not show whether a human-annotated analogous football case improves an MLLM's interpretation of a new football sequence or the coaching advice generated from it. They also do not establish whether an automatically retrieved case works as well as a human-selected case. A visually similar case may be tactically irrelevant, and an imperfect case may cause copying or unsupported transfer. Recognition and coaching quality therefore cannot be treated as one outcome.

#### 3. Research gap

The gap is a controlled evaluation combining sampled football frames, human-annotated prior cases, automatic pixel-only retrieval, normal-text MLLM outputs, and separate recognition and coaching scores. None of the reviewed papers directly compares no case, a human-selected analogous case, and an automatically retrieved analogous case while also checking retrieval relevance, hallucination, copying, unsupported transfer, and uncertainty.

#### 4. How the experiment addresses the gap

The main comparisons are B0 versus B3 and B0 versus B4. B0 versus B3 tests whether a human-selected analogous case can help. B0 versus B4 tests whether a pixel-only cosine k-nearest-neighbour retriever can select a useful human-annotated case automatically. B3 versus B4 measures the remaining gap between human and automatic selection. B1 supplies a random case, B2 is an action-label diagnostic with intentional leakage, and B5 supplies only B4's retrieved advice. Dataset B frames, prompts, model settings, and scoring criteria remain identical across paired conditions except for the intended intervention.

#### 5. Expected contribution

The expected contribution is an initial controlled account of whether analogous human coaching cases improve football-sequence recognition, coaching advice, both, or neither, and whether automatic retrieval approaches human selection. The experiment also contributes a transparent evaluation procedure for normal-text answers that separates recognition, coaching quality, retrieval relevance, hallucination, copying, unsupported transfer, and calibrated uncertainty. Until results are obtained, the thesis should say that it investigates or addresses this gap, not that it solves it.

### Full synthesis draft

1. What existing research already establishes

Prior work establishes several separate pieces relevant to this project, but each in isolation. CLIP (Radford et al., 2021) shows that contrastive image-text pretraining on web-scale data produces embeddings whose cosine similarity can support zero-shot classification and, by extension, similarity-based retrieval between visual items; this underlies the embedding mechanism that any automatic case-retrieval system would rely on. Zhang et al. (2023) build directly on this mechanism for visual in-context learning, showing that automatically retrieving in-context examples via CLIP-cosine similarity (unsupervised) or via a contrastively fine-tuned retriever (supervised) reliably outperforms random example selection on segmentation, detection, and colorization tasks, and that the retrieved examples tend to be both semantically and spatially/stylistically close to the query. This is the clearest existing evidence that relevance-based retrieval of an example beats random selection, but it is tested only on static-image, non-language-generating tasks, with no coaching-style or advice-generation component and no football content.

X-VARS (Held et al., 2024) establishes that a fine-tuned CLIP visual encoder combined with an LLM can perform foul recognition and generate referee-style explanations for football clips. In a small study, those explanations received a mean human rating close to the mean rating for paired human-written explanations. The paper reports qualitative hallucination examples and uses a fixed event-centred frame window rather than comparing sampling methods. Lei et al. (2023) complicate the assumption that more or denser frames are always needed, showing that single-frame-trained models can match multi-frame models on several video-language benchmarks once pretraining is large enough. This reveals a static-appearance bias in popular datasets and cautions that frame quantity is not a reliable proxy for genuine temporal understanding. LVNet (Park et al., 2026) shows that non-uniform, question-relevance-conditioned keyframe selection can outperform uniform sampling for long-form video QA at lower computational cost, reinforcing that frame selection matters. MRAG-Bench (Hu et al., 2025) shows in a general, non-football multimodal retrieval setting that retrieved visual knowledge can help, while noisy or imperfect retrieval can harm many evaluated open-source models. This demonstrates that reference quality, not merely reference presence, matters. Somers et al. (2024) establish a richly annotated football game-state dataset and computer-vision pipeline for tracking and identifying athletes from broadcast video. It provides Dataset B context but does not evaluate MLLM language generation or coaching.

The Düking et al. (2024) ChatGPT training-plan paper establishes, in a related but non-visual sports-coaching context, that the quality of AI-generated sports advice depends heavily on how much relevant input information the model is given, and that expert panels using Likert-scale ratings are a workable way to judge AI-generated coaching content. POPE (Li et al., 2023) establishes a stable, prompt-robust binary-question protocol for detecting object hallucination in image-language models, and shows that negative-sampling strategies (random, popular, adversarial) can reveal systematic biases in a model's answers. VideoHallucer (Wang et al., 2024) extends this to video, establishing a taxonomy of intrinsic and extrinsic hallucination types (including a temporal subtype) and an adversarial paired-question evaluation method, and shows that model scaling helps with some hallucination types but not others, and that models are generally better at detecting plain facts than at detecting whether a claim is actually supported by the video.

Taken together, these papers establish that football-focused video-language systems can produce recognition outputs and plausible domain-specific explanations; that hallucination is a real and measurable problem in both image and video LLMs; that CLIP-style embeddings are a standard mechanism for measuring visual similarity and retrieving relevant examples; that relevance-based retrieval (via CLIP/cosine similarity) reliably beats random selection for static in-context visual examples; that non-uniform, relevance-conditioned frame/keyframe selection beats naive uniform or dense sampling for video tasks; that retrieved visual context can help or actively hurt a model's output depending on its quality and the model's ability to filter noise; and that the amount and relevance of input information given to a language model measurably changes the quality of its generated advice in a coaching context. What none of them establish is examined next.

2. What remains uncertain

It remains uncertain whether giving an MLLM analysing football an additional analogous prior example alongside a new football sequence changes its recognition accuracy or the quality of its coaching advice, and if so, whether the source of that example (a human-selected analogous case versus an automatically retrieved one, for instance via CLIP cosine similarity) matters. X-VARS shows that auxiliary classifier predictions injected as text can shift the model's output, but this is a different mechanism (fed-in labels, not a full analogous case) and was not tested against a no-case baseline in a controlled way that isolates the effect of the example itself. Zhang et al. show that CLIP-based retrieval beats random selection for in-context examples, but only for static image-to-image tasks (segmentation, detection, colorization) with no language generation and no football content; it is unknown whether the same relevance-retrieval advantage transfers to a setting where the "output" is generated coaching text rather than a predicted mask or label. MRAG-Bench shows that retrieved visual knowledge can help or hurt depending on quality and depending on whether the model (open-source vs proprietary) can filter bad examples, which raises the possibility that an automatically retrieved football case, if imperfectly matched, could actively degrade rather than improve a football MLLM's output; but this has never been tested in a coaching-advice context specifically. LVNet's finding that relevance-conditioned selection beats uniform sampling is about which frames within a single video to feed a model, not about supplying an entirely separate analogous case from a different video/instance, so it is uncertain whether the same logic (relevance beats naive selection) extends to cross-instance case retrieval.

The Düking et al. paper shows that more detailed input information improves output quality in a general running-coach context, but this involved progressively more personal detail about the same athlete, not a separate analogous case drawn from a different instance, and it was text-only with no visual component. Neither this paper nor X-VARS isolates recognition performance from advice-quality performance as two separate axes, and neither systematically checks whether the model is hallucinating, copying the provided case verbatim, or transferring conclusions from the case in an unsupported way when such a case is present. It is also uncertain whether an automatically retrieved case (using CLIP-style cosine similarity, as used for filtering in VideoHallucer's dataset construction, for zero-shot classification in the original CLIP paper, or for in-context example retrieval in Zhang et al.) would function as well as a human-selected one when used as an in-context reference for a downstream generation task, since none of the reviewed papers use CLIP retrieval for this specific purpose; supplying a retrieved example to condition a model's coaching output about a new football sequence. Whether retrieval relevance itself needs to be checked, and whether the model's use of a case is transparent or opaque, are open questions none of the papers directly test.

3. The research gap

Existing research separately studies sampled-frame video understanding (Lei et al., LVNet), visual example selection for evaluation purposes and retrieval-based prompting (Zhang et al., MRAG-Bench), embedding-based retrieval (CLIP, Zhang et al.), football-specific video analysis and infrastructure (X-VARS, Somers et al.), generated sports coaching advice (Düking et al.), and hallucination detection in both image and video LLMs (POPE, VideoHallucer). However, no paper reviewed here brings these together to ask whether supplying a human-annotated analogous football case, or an automatically retrieved analogous case, actually improves an MLLM's recognition of what is happening in a new football sequence and the quality of the coaching advice it then generates about that sequence. X-VARS comes closest by combining a football-specific visual encoder with an LLM, but it does not test the effect of supplying a full analogous case (as opposed to a classifier label) as context, nor does it separate recognition quality from advice quality, nor does it compare human-selected against automatically retrieved reference material. Zhang et al. and MRAG-Bench come closest on the retrieval side; one showing relevance-based retrieval beats random selection for static in-context examples, the other showing retrieved visual knowledge can help or hurt LVLM output depending on quality; but neither touches football, coaching advice, or case-based reasoning, and neither generates free text as its output. LVNet shows relevance-conditioned selection beats uniform sampling for frames within a video, but not for cross-instance case retrieval. POPE and VideoHallucer show how to test for hallucination but do so in general-domain image and video settings unrelated to football coaching or case-based reasoning. The Düking et al. paper shows information-granularity effects but in a text-only, non-visual, non-case-based setting. The gap, therefore, is the absence of any controlled comparison of no-case, human-selected-case, and automatically-retrieved-case conditions for a football-video MLLM, evaluated separately on recognition and coaching-advice quality, with accompanying checks for hallucination, copying, unsupported transfer, retrieval relevance, and model uncertainty.

4. How my experiment addresses the gap

The experiment investigates this gap using a controlled comparison across three main comparison conditions applied to the same set of Dataset B football frames under identical model settings. B0 (no case) versus B3 (human-selected analogous case) tests whether providing a human-selected analogous case changes recognition and advice quality compared with the model working from the new sequence alone. B0 versus B4 (automatically retrieved case) tests the same question but for a case obtained through an automatic retrieval mechanism rather than human judgment, addressing whether case-provision helps even without a human curator in the loop; and, drawing on MRAG-Bench's finding that noisy retrieved visual context can hurt rather than help, this comparison also serves as a check for whether an imperfect automatic match could degrade performance relative to no case at all. B3 versus B4 directly measures the gap between human selection and automatic retrieval, which is left unaddressed by any of the papers reviewed here, including Zhang et al.'s otherwise-relevant work on CLIP-based retrieval for static in-context examples.

The remaining conditions provide supporting controls. B1 tests whether any change is caused merely by receiving an unrelated case. B2 uses the hidden Dataset B action label only as a diagnostic matching condition and must be reported as intentional label leakage, not as an automatic system. B5 supplies only the advice from B4's retrieved case to test whether case frames and descriptive context add value beyond advice text alone.

Recognition and coaching-advice quality are evaluated as two separate outcomes rather than a single blended score, following the general principle (visible in X-VARS's separate classification-accuracy and human-study explanation-quality results) that a model's ability to correctly identify what occurred and its ability to generate good advice about it are not necessarily the same capability. In addition, the experiment incorporates checks for hallucination (informed by the POPE and VideoHallucer protocols), copying of the provided case verbatim, unsupported transfer of conclusions from the case to the new sequence, retrieval relevance (informed by CLIP similarity scoring, following the general mechanism used in VideoHallucer's dataset construction and in Zhang et al.'s prompt retrieval framework), and the model's expressed uncertainty. Holding the Dataset B frames and model settings identical across all paired conditions is intended to isolate the effect of the case-provision condition itself from confounds such as different input videos or different model configurations. At this stage, the experiment tests and investigates whether case-provision and its source affect performance; it does not yet establish or confirm a result.

5. My expected contribution

If the experiment shows a measurable difference between the no-case, human-selected-case, and automatically-retrieved-case conditions, the expected contribution is an initial, controlled account of whether and how supplying an analogous football case affects an MLLM's recognition and coaching-advice generation for a new sequence, something not directly tested in any of the papers reviewed here; including the two papers (Zhang et al., MRAG-Bench) that come closest to studying retrieval-based example provision, since neither addresses football, coaching text generation, or case-based reasoning specifically. A secondary expected contribution is a combined evaluation protocol, using a human rubric informed by POPE's and VideoHallucer's hallucination taxonomies together with checks for copying, unsupported transfer, and retrieval relevance, applied to normal-text case-conditioned football coaching outputs rather than copied directly from binary captioning or question-answering benchmarks. This would extend X-VARS's demonstration that a football-specific MLLM can generate referee explanations that received ratings close to human-written explanations in a small study by asking a narrower, more specific question: whether an additional analogous case, and the way that case is obtained, changes the reliability and quality of what the model produces. These are intended as investigative findings from a first controlled test, not as a general or conclusive resolution of the broader question of case-based reasoning in football MLLMs.

## Verified correction ledger

These corrections were checked against primary publication records.

| ID | Correct record or treatment | Primary source |
|---|---|---|
| S04 | CVPR 2025, pp. 24108–24118. DOI `10.1109/CVPR52734.2025.02245`. | [CVF Open Access](https://openaccess.thecvf.com/content/CVPR2025/html/Fu_Video-MME_The_First-Ever_Comprehensive_Evaluation_Benchmark_of_Multi-modal_LLMs_in_CVPR_2025_paper.html) |
| S05 | Treat as arXiv/workshop work, not a confirmed main-track NeurIPS paper. | [Project page](https://temporalbench.github.io/) and [arXiv](https://arxiv.org/abs/2410.10818) |
| S07 | Technical report; do not count as peer-reviewed. | Verify the exact version used before citation. |
| S11 | EACL 2026 main conference, pp. 3569–3588. DOI `10.18653/v1/2026.eacl-long.164`. | [ACL Anthology](https://aclanthology.org/2026.eacl-long.164/) |
| S23 | Springer conference-proceedings book chapter. DOI `10.1007/978-3-030-77004-4_1`. | [Springer proceedings](https://link.springer.com/book/10.1007/978-3-030-77004-4) |
| S28 | CVPR Workshops 2024, pp. 3293–3305. DOI `10.1109/CVPRW63382.2024.00334`. | [CVF Open Access](https://openaccess.thecvf.com/content/CVPR2024W/CVsports/html/Somers_SoccerNet_Game_State_Reconstruction_End-to-End_Athlete_Tracking_and_Identification_on_CVPRW_2024_paper.html) |
| S36 | The abstract says eleven LVLMs, while Section 4.1 and the main text describe twelve model families. Report this internal inconsistency and avoid making the count an important thesis claim. | [arXiv](https://arxiv.org/abs/2406.16338) |

The resulting high-level classification is **34 peer-reviewed publications and 3 non-archival records (S05, S07, and S36)**. This count should be treated as a bibliography-management note, not as a substantive thesis finding.

## What the literature needs to justify

### 1. Why use sampled frames?

Ollama receives images rather than the native video stream. Video-language research also shows that temporal information can matter and that adding frames is not automatically beneficial. Therefore, the thesis uses a documented frame-sampling pilot instead of assuming a frame count. The human pilot observation that B-TRAIN-0040 required F60 to reveal the goal is local experimental evidence and should be reported separately from published literature.

### 2. Why might an analogous human case help?

Case-based reasoning says that a new problem can be approached by retrieving and adapting a similar past case. Multimodal retrieval and visual in-context-learning research suggests that the relevance of supplied examples matters. This motivates the hypothesis; it does not guarantee that football recognition or coaching will improve.

### 3. Why use cosine embedding retrieval?

CLIP and video-retrieval research provide a practical basis for representing visual content with embeddings. Cosine nearest-neighbour retrieval gives a direct and reproducible similarity rule. Dataset B hidden event labels cannot be used by the automatic B4 retriever; it may use only pixels or embeddings derived from pixels.

### 4. Why score recognition and coaching separately?

A model could misunderstand the play but produce generic-sounding advice, or recognise the play correctly while giving poor advice. Separate scoring is therefore required to tell whether a retrieved case improves visual recognition, coaching quality, both, or neither. Hallucination, blind copying, retrieval relevance, unsupported transfer, and calibrated uncertainty also need separate judgments.

## Research gap

The reviewed literature covers video understanding, temporal sampling, multimodal retrieval, case selection, football analysis, generated training advice, and hallucination evaluation. However, these are mostly separate research lines.

The apparent gap is a controlled test of whether a **human-annotated analogous football case** improves both:

1. recognition of a new football sequence; and
2. coaching advice grounded in that sequence.

The experiment addresses this gap through paired conditions using identical Dataset B frames and generation settings, changing only the intended case information.

This gap statement must be revisited after reading the closest papers in full. An absence in the current search results is not proof that no such study exists.

## Per-paper reading-note template

Copy this section under a paper when you read it.

```text
Paper ID and citation:
Date read:

Research problem:
Dataset:
Model:
Input representation:
Retrieval or sampling method:
Experimental baselines:
Evaluation metrics:

Main finding in my own words:
Evidence from the paper (page/table/figure):
Limitations stated by the authors:
Additional limitation I noticed:

Relevance to my thesis:
Direct evidence, indirect support, or background:
Which thesis design choice does it support:
What it does NOT establish:
Where I may cite it in the thesis:
```

## Search log

Record future searches so the literature review is reproducible.

| Search date | Database | Exact query | Inclusion criteria | Exclusion criteria | Papers retained |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

Suggested databases include Google Scholar, Scopus or Web of Science if available through the university, ACL Anthology, IEEE Xplore, ACM Digital Library, CVF Open Access, and arXiv for recent non-peer-reviewed work.

## Thesis-writing outline supported by this register

1. Multimodal video understanding and temporal limitations.
2. Frame sampling as a practical and methodological choice.
3. Retrieval-augmented multimodal generation and visual examples.
4. Case-based reasoning and analogous coaching examples.
5. Pixel-derived embeddings and cosine nearest-neighbour retrieval.
6. SoccerNet and existing football-language systems.
7. Recognition versus coaching evaluation.
8. Hallucination, copying, unsupported transfer, and uncertainty.
9. Research gap and experimental hypotheses.

## Current cautions

- Do not cite the consolidated AI-generated table as a source.
- Do not claim that every bibliographic record has been fully verified; only the entries marked above have received a primary-record check so far.
- Do not claim that retrieval improves independent video understanding.
- Do not use SoccerNet hidden labels as model input or automatic B4 retrieval input.
- Do not treat football event labels as human coaching ground truth.
- Do not present text-to-video retrieval results as direct proof of video-to-case retrieval performance.
- Do not report the sampling-pilot observations as published literature findings.
