.PHONY: mock-transactions mock-reviews mock-reviews-dry api

mock-transactions:
	uv run python -m generators.transactions

mock-reviews:
	uv run python -m generators.reviews $(ARGS)

mock-reviews-dry:
	uv run python -m generators.reviews --dry-run --count 5 --interval 0 $(ARGS)

api:
	uv run uvicorn api.main:app --reload --port 8000
