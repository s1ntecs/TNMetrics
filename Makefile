.PHONY: lint format typecheck test up down

DC ?= docker compose

lint:
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check . && ruff format --check .; \
	else \
		$(DC) run --rm api sh -lc "ruff check . && ruff format --check ."; \
	fi

format:
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check --fix . && ruff format .; \
	else \
		$(DC) run --rm api sh -lc "ruff check --fix . && ruff format ."; \
	fi

typecheck:
	@if command -v mypy >/dev/null 2>&1; then \
		mypy src; \
	else \
		$(DC) run --rm api sh -lc "mypy src"; \
	fi

test:
	@if command -v pytest >/dev/null 2>&1; then \
		pytest -q; \
	else \
		$(DC) run --rm api sh -lc "pytest -q"; \
	fi

up:
	$(DC) up -d --build

down:
	$(DC) down
