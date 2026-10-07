# AGENT_CONTEXT — Voicebox

> Fresh-agent entrypoint for `Allen930311/voice`.
> Reconciled 2026-10-08. The old auto-generated tree snapshot is retired as an
> onboarding authority.

## What this repo is

Voicebox is Allen's local-first voice / TTS workspace: the Voicebox desktop
application, MCP integration and automation utilities.

## Where truth lives

| Question | Source |
|---|---|
| Current product / operating direction | `README.md` |
| Voice IDs and profile metadata | `VOICE_PROFILES.md` |
| Current commercial-validation proposal | `voicebox/docs/plans/COMMERCIAL_VOICEOVER_VALIDATION.md` |
| Detailed engineering inventory | `voicebox/docs/PROJECT_STATUS.md` — dated snapshot; useful evidence, not a live queue |

The commercial-validation Plan is `PROPOSED` with
`implementation_authorization: none`. It does not authorize a new backend,
product change, pricing, public launch or publishing.

## Current gate

The next product decision is to select one concrete customer job / workload for
commercial validation and exercise existing Voicebox capability first.

Until a bounded capability gap is proven:

- prefer existing engines / profiles / Stories / export paths;
- do not add another TTS backend for novelty;
- do not treat old issue/PR counts in `voicebox/docs/PROJECT_STATUS.md` as
  current queue truth;
- do not start implementation from the commercial Plan.

## Authority and write boundary

For voice/profile identity, `VOICE_PROFILES.md` is authoritative.
For repository-level current direction, this entry routes to `README.md`.
A dated engineering snapshot or merged planning document cannot silently
override either.

Voice cloning / commercial validation must preserve voice ownership, consent and
provenance boundaries documented by the applicable Plan/workflow.

## Remote vs local truth

The remote default branch `main` is shared repository truth. Local model
downloads, generated audio, running services, GPU state, secrets, unpushed
commits and machine-specific paths are local/runtime facts and must be checked
at execution time.

If remote does not contain something, report
`not found in main@<sha>; local state unknown` rather than guessing.

## Planning-only agents

Planning/research is allowed. Do not claim a model, GPU, service, generated
sample or test is available/running unless current execution evidence proves it.
A proposal is not implementation authority.

## Safe start

1. Read `README.md`.
2. Read `VOICE_PROFILES.md` only if the task needs voice identity.
3. Read the exact Plan/workflow relevant to the requested task.
4. Exercise existing capability before proposing a new backend.
5. Stop before behavior-changing implementation unless an exact authorized
   implementation task exists.
