import pandas as pd
import requests
from databricks.sdk import WorkspaceClient
from pyspark.sql import functions as F  # noqa:N812
from pyspark.sql import types as T  # noqa:N812
from tenacity import (
    retry,
    retry_if_exception_type,  # noqa: F401
    stop_after_attempt,
    wait_exponential,
)

# ---------------------------------------------------------------------------
# Secret Scope Configuration — run once to provision, then skip this cell
# ---------------------------------------------------------------------------

w = WorkspaceClient()
w.secrets.create_scope(scope="api-keys")
w.secrets.put_secret(
    scope="api-keys", key="service-name", string_value="your-secret-value-here"
)
print("Secret scope created and secret added successfully!")


# ---------------------------------------------------------------------------
# Configuration — swap these for any OpenAI-compatible endpoint
# ---------------------------------------------------------------------------
PROVIDERS = {
    "mistral": "https://api.mistral.ai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "openai": "https://api.openai.com/v1",
    "claude": "https://api.anthropic.com/v1",
}

API_BASE_URL = PROVIDERS["mistral"]
SECRET_SCOPE = "your-secret-scope"
SECRET_KEY = "api-key"
API_KEY = dbutils.secrets.get(scope=SECRET_SCOPE, key=SECRET_KEY)  # noqa: F821
MODEL = "ministral-3b-2512"
MAX_WORKERS = 8
INPUT_COLUMN = "review"  # column containing the text to send to the API
INSTRUCTIONS = "Summarize the following review in one sentence."

APP_ID = "streaming_api_call"  # unique identifier for idempotent Delta writes
SOURCE_TABLE = "catalog.schema.source_table"  # three-level Unity Catalog namespace
TARGET_TABLE = "catalog.schema.target_table"  # three-level Unity Catalog namespace
CHECKPOINT_PATH = "/path/to/checkpoint/streaming_api_call"

# ---------------------------------------------------------------------------
# Step 1: Prepare source data as a streaming-compatible table
# ---------------------------------------------------------------------------
df_stream = spark.readStream.table(SOURCE_TABLE)  # noqa: F821


# ---------------------------------------------------------------------------
# Step 3: foreachBatch — enrich + idempotent write
# ---------------------------------------------------------------------------
def process_batch(batch_df, batch_id):
    # Local PySpark imports — keeps them out of the module-level pickle graph.
    # cloudpickle serialises process_batch + every nested code object; any
    # module-level pyspark reference (F, T, DataFrame) can carry Spark Connect
    # session state and trigger STREAMING_CONNECT_SERIALIZATION_ERROR.
    from pyspark.sql import functions as F  # noqa: N812

    if batch_df.isEmpty():
        return

    @F.pandas_udf(T.StringType())
    def call_api(prompts: pd.Series) -> pd.Series:
        """Pandas UDF that calls the API concurrently within each partition."""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        class RateLimitError(Exception):
            pass

        # Session is created once per partition — reuses TCP connections
        session = requests.Session()

        @retry(
            stop=stop_after_attempt(5),
            wait=wait_exponential(multiplier=2, min=2, max=60),
            retry=retry_if_exception_type(
                (
                    requests.ConnectionError,
                    requests.Timeout,
                    RateLimitError,
                )
            ),
            reraise=True,
        )
        def _call_api(prompt: str) -> str:
            """Call any OpenAI-compatible chat/completions endpoint with tenacity retry."""
            resp = session.post(
                f"{API_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "user", "content": f"{INSTRUCTIONS}\n\n{prompt}"},
                    ],
                    "max_tokens": 512,
                    "temperature": 0.3,
                },
                timeout=600,  # timeout of 10 minutes
            )
            if resp.status_code == 429:
                raise RateLimitError(f"Rate limited (429): {resp.text}")
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

        def safe_call(prompt: str) -> str:
            try:
                return _call_api(prompt)
            except Exception as e:
                return f"ERROR: {e}"

        results = [None] * len(prompts)  # allocation of memory space
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_idx = {
                executor.submit(safe_call, prompt): idx
                for idx, prompt in enumerate(prompts)
            }
            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                results[idx] = future.result()

        return pd.Series(results)

    enriched_df = batch_df.coalesce(4).withColumn(
        "response", call_api(F.col(INPUT_COLUMN))
    )

    (
        enriched_df.write.format("delta")
        .mode("append")
        .option("txnVersion", batch_id)
        .option("txnAppId", APP_ID)
        .saveAsTable(TARGET_TABLE)
    )

    print(f"Batch {batch_id}: wrote {enriched_df.count()} rows")


# ---------------------------------------------------------------------------
# Step 4: Start the streaming query
# ---------------------------------------------------------------------------
query = (
    df_stream.writeStream.foreachBatch(process_batch)
    .option("checkpointLocation", CHECKPOINT_PATH)
    .option("maxFilesPerTrigger", 10)
    .trigger(availableNow=True)  # runs all available files, and then stops
    .start()
)

query.awaitTermination()

# ---------------------------------------------------------------------------
# Step 5: Read consolidated results and show amount of errors
# ---------------------------------------------------------------------------
df_result = spark.read.table(TARGET_TABLE)  # noqa: F821
print(f"Total enriched rows: {df_result.count()}")
df_result.show(5, truncate=False)

df_errors = df_result.filter(F.col("response").startswith("ERROR:"))
error_count = df_errors.count()
if error_count > 0:
    print(f"⚠️  {error_count} rows with errors")
