# Title: *How to Call an External LLM API at Scale — Reliably and at Maximum Throughput*

---

## Opening: SCQA Hook

- Situation: Teams increasingly want to enrich large datasets with LLM-generated content
- Complication: Naive row-by-row API calls are slow, fragile, and collapse under real data volumes
- Question: How do you call an external LLM API at maximum throughput without losing a single row to transience?
- Answer (Governing Thought): Combine PySpark Structured Streaming with three design principles — provider flexibility, parallelised throughput, and layered resilience — and you get a pipeline that is fast, fault-tolerant, and trivially portable across any LLM provider

---

## Key Line — the three arguments that prove the answer

---

## Pillar 1: Decouple your pipeline from any single LLM provider

*Any OpenAI-compatible endpoint drops in with a one-line change*

- The `PROVIDERS` dict as a portability pattern (Mistral, OpenAI, Anthropic, OpenRouter)
- Why OpenAI-compatible APIs are now the de facto standard
- Securing credentials with Databricks Secret Scopes — never hardcode keys

---

## Pillar 2: Maximise throughput at every layer of the stack

*Three nested mechanisms work together to saturate your API quota*

- Streaming reads: `readStream` + checkpointing means only new data is processed each run — no wasted calls
- Pandas UDFs + `ThreadPoolExecutor`: vectorised row processing with concurrent in-partition fan-out
- Connection pooling + `coalesce()`: HTTP session reuse reduces TCP overhead; coalesce caps cluster-wide concurrency to respect rate limits
- Tuning the levers together: `MAX_WORKERS`, `maxFilesPerTrigger`, partition count

---

## Pillar 3: Build resilience in at every layer, not as an afterthought

*A single point of failure anywhere kills the whole enrichment run*

- Tenacity retry logic: exponential backoff handles transient network errors and 5xx responses
- Custom `RateLimitError`: targeted retry behaviour for 429s, separate from generic HTTP errors
- `safe_call` wrapper: exceptions become error strings — one bad row never crashes a partition
- Idempotent Delta writes: `txnAppId` + `txnVersion` deduplicate retried batches, so reruns are safe
- Post-run verification: a simple `startswith("ERROR:")` filter surfaces failures without manual log-trawling

---

Conclusion — restate the governing thought, not a summary

- The three pillars are not independent features — they are a single, composable design decision
- When to use this pattern vs. a managed inference service
- The natural extension path: structured outputs, async clients, cost tracking per batch
