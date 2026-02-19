# Blog Post Outline: Logging on Databricks

## Introduction (SCQ → Answer)
*   **Situation**: Databricks developers constantly switch between two modes: **Interactive** (notebooks for development) and **Non-Interactive** (workflows/jobs for production). Both modes need proper logging for debugging and observability.
*   **Complication**: The standard Python `logging` module — the obvious choice — behaves erratically on Databricks. Logs are swallowed in notebooks, formatting is hijacked, and developers fall back to `print()` everywhere, sacrificing structure and observability in production.
*   **Question**: How do we get Python's `logging` module to behave like a standard Python process on Databricks, regardless of compute mode?
*   **Answer**: Use `force=True` in `logging.basicConfig`. This single argument reclaims control of the root logger from Databricks, making logging work identically in both Interactive notebooks and automated Jobs.

## Key Arguments

### 1. WHY You Need It: Databricks Overrides Your Logger
*   In a standard Python process, `logging.basicConfig` configures the root logger on first call.
*   Databricks attaches its own handlers to the root logger at startup to capture output for its UI.
*   Because handlers already exist, your `basicConfig` call is **silently ignored** — your format, level, and handlers never take effect.
*   This is why `logger.info()` produces nothing in a notebook cell, while `print()` works fine.

### 1b. But WHY Does Databricks Do This?
*   Databricks notebooks are **not a terminal**. They are a web UI backed by an IPython kernel on a remote driver process. The platform needs to route Python output from that remote process back into a specific notebook cell in a browser.
*   The handlers Databricks attaches serve three purposes:
    1.  **Notebook cell routing**: Intercept log output and display it in the correct cell via the IPython display system.
    2.  **Noise filtering**: The root logger level is set to `WARNING` by default — intentionally preventing noisy libraries (Spark internals, Py4J, urllib3) from flooding cell output.
    3.  **Log4j bridging**: Bridging Python logging into the JVM-side Log4j infrastructure so driver logs from Python and Scala appear in the same place.
*   **"But won't `force=True` break something?"** — In practice, no. `StreamHandler(sys.stderr)` still writes to `stderr`, which is the same underlying stream Databricks captures. You are taking control of the *format* and *level*, not bypassing the platform's output capture. Library-specific loggers (e.g., MLflow) use their own named loggers and are unaffected.
*   **One caveat**: By lowering the level from `WARNING` to `INFO`, you will see more output from third-party libraries. This is why the `py4j` suppression line exists — and you may need similar lines for other noisy loggers (`urllib3`, `azure`, etc.).

### 2. HOW It Works: The `force=True` Fix

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
    force=True,  # CRITICAL: Removes existing handlers attached by Databricks
)

# Suppress internal Spark noise (Py4J is very chatty)
logging.getLogger("py4j").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)
```

*   **`force=True`** (Python 3.8+): Removes all existing handlers on the root logger *before* applying your configuration. This is the key that makes your setup take precedence over Databricks' defaults.
*   **`StreamHandler()`**: Directs logs to `stderr`. Databricks captures this stream and displays it in **both** the notebook cell output (Interactive) and the driver logs (Jobs).
*   **`py4j` suppression**: PySpark uses Py4J to communicate with the JVM. It is extremely verbose. Suppressing it to `ERROR` keeps your application logs readable.
*   **Result**: One configuration, consistent behavior. Write it once in a shared module, import it everywhere.

### 3. WHERE Your Logs End Up: Interactive vs. Jobs Compute
*   **All-Purpose Compute (Interactive)**:
    *   `StreamHandler` forces logs into the notebook cell output — visible immediately during development.
    *   Logs are ephemeral: they disappear when the cluster terminates or restarts.
*   **Jobs Compute (Automated)**:
    *   The Databricks Jobs Service automatically captures `stdout`/`stderr` and persists them in the Job "Output" tab (~60-day retention).
    *   Because our `StreamHandler` writes to `stderr`, logs are automatically captured — no extra configuration needed.
*   **Cluster Log Delivery (Safety Net)**:
    *   For long-term retention beyond 60 days (compliance, auditing), enable **Cluster Log Delivery** in the Compute settings to route logs to DBFS/S3/ADLS.
    *   For All-Purpose clusters, this is the *only* way to persist logs after termination.

## Bonus: The Future is Structured
*   PySpark 4.0 (Databricks Runtime 17.0+) introduces `pyspark.logger.PySparkLogger`, a built-in structured JSON logger that extends Python's standard `logging.Logger` class.
*   It outputs logs in JSON format out of the box — no custom formatting needed. This makes logs machine-parseable for downstream ingestion and analysis.
*   It supports passing **keyword arguments as structured context**, which are included in the JSON output alongside the message.

```python
from pyspark.logger import PySparkLogger

# Drop-in replacement for logging.getLogger()
logger = PySparkLogger.getLogger("MyApp")

# Standard logging calls — but output is structured JSON
logger.info("Pipeline started", stage="ingestion", source="s3://my-bucket")
logger.warning("Rows dropped due to nulls", count=42, table="orders")

# Example output:
# {"ts": "2026-02-11 10:30:01,123", "level": "INFO", "logger": "MyApp",
#  "msg": "Pipeline started", "context": {"stage": "ingestion", "source": "s3://my-bucket"}}
```

*   **Key advantage over the `force=True` approach**: You get structured context fields (key-value pairs) attached to each log entry without building a custom JSON formatter. This is invaluable for querying logs at scale (e.g., "show me all errors where `stage=transformation`").
*   **Compatibility**: `PySparkLogger` extends `logging.Logger`, so it works with standard Python logging handlers, filters, and existing `getLogger()` patterns. You can add a `FileHandler` or route it to any destination just like a normal logger.
*   The `force=True` pattern remains the foundation for older runtimes, but `PySparkLogger` is where Databricks logging is heading.
