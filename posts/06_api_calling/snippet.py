import pandas as pd
import requests
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import Types as T
from pyspark.sql import functions as F
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

# by default databricks has the sparksession initialized under spark
spark = SparkSession.builder.appName("APICalling").getOrCreate()

# ---------------------------------------------------------------------------
# Configuration — swap these for any OpenAI-compatible endpoint
# ---------------------------------------------------------------------------
# Mistral:   https://api.mistral.ai/v1
# Openrouter:https://openrouter.ai/api/v1
# OpenAI:    https://api.openai.com/v1
# Claude:    https://api.anthropic.com/v1

API_BASE_URL = "https://api.mistral.ai/v1"
API_KEY = "your-api-key"  # pull from env vars or secret scope
MODEL = "ministral-3b-2512"

OUTPUT_TABLE = "catalog.schema.enriched_data"  # three-level Unity Catalog namespace
CHECKPOINT_PATH = "/path/to/checkpoint/llm_enrichment"

# ---------------------------------------------------------------------------
# Step 1: Prepare source data as a streaming-compatible table
# ---------------------------------------------------------------------------
INPUT = "catalog.schema.source_table"  # three-level Unity Catalog namespace

df_stream = spark.readStream.table(INPUT)


# ---------------------------------------------------------------------------
# Step 2: Define the API call logic with retries
# ---------------------------------------------------------------------------
class RateLimitError(Exception):
    pass


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
def _call_api(session: requests.Session, prompt: str) -> str:
    """Call any OpenAI-compatible chat/completions endpoint with tenacity retry."""
    resp = session.post(
        f"{API_BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0.3,
        },
        timeout=600,  # timeout of 10 minutes
    )
    if resp.status_code == 429:
        raise RateLimitError(f"Rate limited (429): {resp.text}")
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


@F.pandas_udf(T.StringType())
def call_api(prompts: pd.Series) -> pd.Series:
    """Pandas UDF that calls the API concurrently within each partition."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    MAX_WORKERS = 8

    # Session is created once per partition — reuses TCP connections
    session = requests.Session()

    def safe_call(prompt: str) -> str:
        try:
            return _call_api(session, prompt)
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


# ---------------------------------------------------------------------------
# Step 3: foreachBatch — enrich + idempotent write
# ---------------------------------------------------------------------------
def process_batch(batch_df: DataFrame, batch_id: int) -> None:
    if batch_df.isEmpty():
        return

    enriched_df = (
        batch_df.coalesce(4)
        .withColumn("response", call_api(F.col("prompt")))
        .withColumn("batch_id", F.lit(batch_id))
    )

    (
        enriched_df.write.format("delta")
        .mode("overwrite")
        .option("partitionOverwriteMode", "dynamic")
        .partitionBy("batch_id")
        .saveAsTable(OUTPUT_TABLE)
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
df_result = spark.read.table(OUTPUT_TABLE)
print(f"Total enriched rows: {df_result.count()}")
df_result.show(5, truncate=False)

df_errors = df_result.filter(F.col("response").startswith("ERROR:"))
if df_errors.count() > 0:
    print(f"⚠️  {df_errors.count()} rows with errors")
