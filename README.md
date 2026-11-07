# AI Review Triage

A local pipeline that takes product reviews, labels them with Llama 3, and shows sales and satisfaction next to the shop's orders.

Reviews arrive at a FastAPI webhook and wait as JSON files. A worker removes emails and French phone numbers, asks Ollama for a category and a sentiment score, and writes a parquet batch. dlt loads those batches and the transaction files into `raw.duckdb` without transforming them. dbt builds the facts, dimensions, and dashboard views in a second file. That file replaces `analytics.duckdb` only after the dbt tests pass. Streamlit reads the published file.

Sales are the value of delivered order lines. Satisfaction is the average sentiment, rescaled from -1..1 to 0..100.

## Start here

Install [uv](https://docs.astral.sh/uv/) and [Ollama](https://ollama.com/), then clone the repo and run:

```bash
uv sync
ollama pull llama3
```

Leave Ollama running. Then, from the repo root:

```bash
make mock-transactions
```

In a second terminal, start the webhook and leave it running:

```bash
make api
```

Back in the first terminal, send 5 reviews, label them, load DuckDB, publish the analytics file, and open the dashboard:

```bash
make mock-reviews ARGS="--count 5 --interval 0"
make worker-once
make load
make dbt
make dashboard
```

The dashboard is at http://127.0.0.1:8501. The webhook is at http://127.0.0.1:8000 and expects the header `X-API-Key: dev-key`.

`make worker` keeps polling for new reviews every few seconds. `make worker-once` handles whatever is waiting and exits. `make dbt` installs the dbt packages, builds `analytics_next.duckdb`, runs the tests, and swaps that file onto `analytics.duckdb` only when the tests pass.

To run the tests: `uv run python -m pytest`.
