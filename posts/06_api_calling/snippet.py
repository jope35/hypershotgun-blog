import pandas as pd
import requests
from pyspark.sql import functions as F  # noqa: N812
from requests.adapters import HTTPAdapter
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# ---------------------------------------------------------------------------
# Configuration — swap these for any OpenAI-compatible endpoint
# ---------------------------------------------------------------------------

API_BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "ministral-3b-2512"
API_KEY = "your-api-key"
MAX_WORKERS = 8
INPUT_COLUMN = "review"
INSTRUCTIONS = "Summarize the following review in one sentence."

# APP_ID + batch_id together form an idempotency key — if a batch is reprocessed
# after a failure, Delta skips the duplicate write instead of creating duplicates
APP_ID = "streaming_api_call"
SOURCE_TABLE = "catalog.schema.source_table"
TARGET_TABLE = "catalog.schema.target_table"
CHECKPOINT_PATH = "/path/to/checkpoint/streaming_api_call"

# ---------------------------------------------------------------------------
# Step 1: Open a streaming read — Structured Streaming tracks progress via
# checkpoints, so only new files are processed on each run
# ---------------------------------------------------------------------------
df_stream = spark.readStream.table(SOURCE_TABLE)  # noqa: F821


# ---------------------------------------------------------------------------
# Step 2: foreachBatch — process each micro-batch as a static DataFrame so we
# can use Pandas UDFs and idempotent Delta writes
# ---------------------------------------------------------------------------
def process_batch(batch_df, batch_id):
    # Local PySpark imports — keeps them out of the module-level pickle graph.
    # cloudpickle serialises process_batch + every nested code object; any
    # module-level pyspark reference (F, T, DataFrame) can carry Spark Connect
    # session state and trigger STREAMING_CONNECT_SERIALIZATION_ERROR.
    from pyspark.sql import functions as F  # noqa: N812
    from pyspark.sql import types as T  # noqa:N812

    # Structured Streaming can dispatch empty micro-batches; bail early to
    # avoid unnecessary API session setup
    if batch_df.isEmpty():
        return

    @F.pandas_udf(T.StringType())
    def call_api(prompts: pd.Series) -> pd.Series:
        """Pandas UDF — vectorised interface lets us batch rows per partition
        and fan out with threads, avoiding the overhead of one API call per row."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Defined inside the UDF so it lives in the serialised closure sent to workers
        class RateLimitError(Exception):
            pass

        # Session is created once per partition — reuses TCP connections
        session = requests.Session()
        # Match pool size to thread count so no thread blocks waiting for a connection
        adapter = HTTPAdapter(pool_connections=MAX_WORKERS, pool_maxsize=MAX_WORKERS)
        session.mount("https://", adapter)

        # Nested inside call_api so it closes over `session` and gets serialised
        # into the same closure Spark sends to workers — no globals needed
        @retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=2, min=2, max=60),
            retry=retry_if_exception_type(
                (
                    requests.ConnectionError,
                    requests.Timeout,
                    requests.HTTPError,
                    RateLimitError,
                )
            ),
            reraise=True,
        )
        def _call_api(prompt: str) -> str:
            resp = session.post(
                f"{API_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "user", "content": f"{INSTRUCTIONS}\n\n{prompt}"},
                    ],
                    "max_tokens": 512,
                    "temperature": 0.3,
                },
                timeout=600,
            )
            # 429 gets a custom exception for targeted retry; 5xx errors bubble
            # up as HTTPError, also retried by tenacity
            if resp.status_code == 429:
                raise RateLimitError(f"Rate limited (429): {resp.text}")
            resp.raise_for_status()
            data = resp.json()
            try:
                return data["choices"][0]["message"]["content"]
            except (KeyError, IndexError) as e:
                raise ValueError(f"Unexpected response structure: {data}") from e

        # Catch-all wrapper: converts exceptions to error strings so one failed
        # row doesn't crash the entire partition
        def safe_call(prompt: str) -> str:
            try:
                return _call_api(prompt)
            except Exception as e:
                return f"ERROR: {e}"

        # Pre-allocate to preserve input ordering — as_completed returns
        # futures in arbitrary finish order
        results = [None] * len(prompts)
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_idx = {
                executor.submit(safe_call, prompt): idx
                for idx, prompt in enumerate(prompts)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                results[idx] = future.result()

        return pd.Series(results)

    # Reduce partitions to limit concurrent API connections across the cluster
    # — tune this to stay within rate limits
    enriched_df = batch_df.coalesce(4).withColumn(
        "response", call_api(F.col(INPUT_COLUMN))
    )

    (
        enriched_df.write.format("delta")
        .mode("append")
        # Idempotent write — Delta uses (txnAppId, txnVersion) to deduplicate
        # if a batch is retried
        .option("txnVersion", batch_id)
        .option("txnAppId", APP_ID)
        .saveAsTable(TARGET_TABLE)
    )

    print(f"Batch {batch_id}: complete")


# ---------------------------------------------------------------------------
# Step 3: Start the streaming query
# ---------------------------------------------------------------------------
query = (
    df_stream.writeStream.foreachBatch(process_batch)
    .option("checkpointLocation", CHECKPOINT_PATH)
    # Cap micro-batch size — soft max on bytes read per micro-batch.
    # Tune this to control how many rows hit the API at once:
    #   target_rows × avg_row_size ≈ byte limit
    #   e.g. 50 000 rows × ~1 KB each ≈ 50 MB
    .option("maxBytesPerTrigger", "50mb")
    .trigger(availableNow=True)  # runs all available files, and then stops
    .start()
)

query.awaitTermination()

# ---------------------------------------------------------------------------
# Step 4: Verify results — read back the target table after the stream finishes
# to confirm row counts and surface any API failures
# ---------------------------------------------------------------------------
df_result = spark.read.table(TARGET_TABLE)  # noqa: F821
print(f"Total enriched rows: {df_result.count()}")
df_result.show(5, truncate=False)

df_errors = df_result.filter(F.col("response").startswith("ERROR:"))
error_count = df_errors.count()
if error_count > 0:
    print(f"WARNING: {error_count} rows with errors")
