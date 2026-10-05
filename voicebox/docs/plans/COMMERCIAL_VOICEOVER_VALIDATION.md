---
type: plan
plan_state: PROPOSED
owner: Allen
project_id: voicebox
planning_baseline: main@26ca6677aae0842c4bf714c987dd35935f22d6f6
plan_date: 2026-10-06
implementation_authorization: none
---

# Voicebox — AI Voiceover Commercial Validation Plan R0

> This Plan turns the Business Inbox commercial-validation signal into durable
> Voicebox planning. It does not authorize product changes, paid infrastructure,
> public launch, pricing changes, or external publishing.

## 1. Why this Plan exists

Voicebox already has substantial TTS capability: multiple engines, voice cloning,
preset voices, history, Stories, transcription, packaging, and platform support.
The unresolved question is commercial, not "can we build another TTS engine?"

Source Inbox:
`Allen930311/allen-business/planning/inbox/2026-09-11-voicebox-ai-voiceover-commercial-validation.md`.

## 2. Validation question

Determine whether Voicebox can support one repeatable, rights-safe voiceover
workflow that creates enough user/business value to justify a productized
commercial offer.

Do not validate "AI voice" in the abstract. Validate one explicit customer job.

Candidate jobs:
- creator narration / shorts voiceover;
- multilingual localization voiceover;
- internal VideoEdit narration production;
- bounded voice-cloning workflow where the user owns or has permission for the voice.

A later Owner decision must select the first job before implementation.

## 3. Evidence required

For the selected job, capture:

1. target user and current alternative;
2. input/output contract;
3. minimum quality bar and representative test script;
4. latency / hardware / model-download burden;
5. reproducibility and failure modes;
6. language/voice coverage;
7. rights / consent / provenance requirements;
8. operational cost and support burden;
9. willingness-to-pay or concrete internal efficiency evidence;
10. whether current Voicebox already satisfies the job without code changes.

## 4. Rights and safety gate

Commercial validation must not normalize unauthorized voice impersonation.

A viable workflow must preserve:
- source/voice consent or ownership;
- reference-audio provenance;
- disclosure requirements where applicable;
- no claims that the system guarantees identity-perfect cloning;
- no use of third-party voices merely because a model technically permits it.

## 5. Search-before-build gate

Before proposing engineering:
- use current `voicebox/docs/PROJECT_STATUS.md` and live repo capability;
- prefer an existing engine / profile / Stories / export path;
- do not add another TTS backend unless the selected workload proves a capability gap;
- do not conflate model novelty with commercial value.

## 6. R0 decision outcomes

The validation must end in one of:

- `GO_EXISTING_CAPABILITY` — current product can support the offer with packaging/process only;
- `GO_BOUNDED_GAP` — one precise engineering gap blocks the offer;
- `HOLD_EVIDENCE` — value or willingness-to-pay remains unproven;
- `REJECT` — rights, economics, quality, or support burden make the offer unattractive.

## 7. Issue gate

No implementation Issue until all are true:

- one customer job is selected;
- a real test workload is defined;
- current capability was exercised first;
- a bounded gap remains;
- acceptance criteria and non-goals are explicit.

If current Voicebox already satisfies the job, the next durable artifact should
be a commercial-validation result, not an engineering Issue.

## 8. Explicit non-goals

- no generic "best TTS" benchmarking project;
- no new engine marketplace;
- no autonomous public publishing;
- no pricing or payment implementation;
- no model training;
- no voice-rights bypass;
- no rewrite of Voicebox architecture.
