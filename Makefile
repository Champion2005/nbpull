.PHONY: install lint format typecheck test all clean help

help: ## 📖 Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## 📦 Install project + dev dependencies
	uv sync --all-groups

lint: ## 🔍 Run ruff linter
	uv run ruff check src/ tests/

format: ## 🎨 Format code with ruff
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

typecheck: ## 🔠 Run mypy type checking
	uv run mypy src/

test: ## 🧪 Run unit tests (no network)
	uv run pytest -v -m "not integration"

test-integration: ## 🌐 Run integration tests (real NetBox API)
	uv run pytest -v -m integration

test-all: ## 🧪🌐 Run all tests (unit + integration)
	uv run pytest -v

all: format lint typecheck test ## ✅ Run all checks

batch-prefixes: ## 📦 Query NetBox for batch prefixes
	uv run nbpull batch-prefixes

clean: ## 🧹 Remove build artifacts
	rm -rf dist/ build/ .mypy_cache/ .pytest_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
