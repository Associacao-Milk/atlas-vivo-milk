# MILK IA — ORCHESTRATION CONTRACT

**Canonical Runtime:** `C:\Users\Utilizador\MILK_AI_STATE_CANONICO`
**Created:** 2026-09-08
**Orchestrator:** Mistral Vibe (glm-5-2)

## Rules

- Never use old versions as runtime. Old versions preserved as history.
- Minimise token usage. Inspect files, grep, AST, tests — not reprints.
- Output ~20 lines max per checkpoint unless failure/loss/human-decision.
- Before any change: Git check, snapshot check, identify files, preserve rollback.
- Forbidden: `git add .`, `git clean`, `git reset --hard`, destructive restore/checkout,
  silent overwrites, corpus/model/snapshot deletion, settings.json changes, auto-push.
- Commits: LOCAL only until human authorises push.
- Never rewrite existing components. Search for equivalent before creating.
- Never reprocess 10.538 docs unless NEW/CHANGED/INVALIDATED/REQUESTED.
- LLM only when deterministic tools insufficient.
- continuous_learning.py = event-based scheduler, not infinite clock.
- Training only on NEW_VALIDATED_DATA / HUMAN_CORRECTIONS / NEW_LABELS / DATASET_VERSION_CHANGE / EXPLICIT_EXPERIMENT.
- Never auto-modify canonical code without test. Never promote model without benchmark.
- Never convert hypothesis to fact. Never invent sources.
- Self-improvement: PROPOSTA → PATCH → UNIT TEST → INTEGRATION → REGRESSION → BENCHMARK → BEFORE/AFTER → PROMOTE/REJECT.

## Priority Order

A — Neural math certification (BCE, gradient, sigmoid, Adam, BatchNorm, Dropout, save/load, params, gradient check, NaN/Inf)
B — Real evaluation (TRAIN/VAL/TEST split, per-class metrics, baselines)
C — Controlled training (early stopping, best checkpoint, rollback, versioned)
D — Semantic retrieval (sparse + dense → fusion → top-k → rerank → evidence)
E — Ontological knowledge graph (entity, relation, source, confidence, epistemic_status)
F — Hermeneutic engine (observation → context → interpretations → contra → evidence → synthesis)
G — Scientific engine (FACT/DOCUMENTED/EMPIRICAL/CONSENSUS/STATISTICAL/CORRELATION/INFERENCE/INTERPRETATION/HYPOTHESIS/SPECULATION/UNKNOWN)
H — Multimodality (text, PDF, image, table, geospatial, temporal, audio, code, metadata)
I — Hypercontextualisation (fragment → doc → related → entity → theme → territory → period → corpus → external)
J — Hypotheses (anomaly/gap/contradiction/correlation → hypothesis with falsification)
K — Solutions (evidence → application with pilot criteria, abandonment criteria, reversibility)

## Memory Types

document_memory, semantic_memory, episodic_analysis_memory, hypothesis_memory,
evidence_memory, contradiction_memory, solution_memory, model_memory.

## Stop Conditions

1. Risk of data loss
2. Credential needed
3. Irreversible decision
4. Private data to external service
5. Structural change to validated architecture
6. Real human decision needed
