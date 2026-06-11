.PHONY: help install data data-refresh features train sim quiniela web test lint format clean

help:
	@echo "Available targets:"
	@echo "  install      - sync uv environment with dev extras"
	@echo "  data         - fetch all raw data + build unified match log"
	@echo "  data-refresh - re-fetch volatile sources (Elo, odds, Kalshi, Wikipedia)"
	@echo "  features     - build feature store from raw data"
	@echo "  train        - regenerate OOF predictions + fit the stacker"
	@echo "  sim          - full prediction pipeline + Monte Carlo bracket (50k sims)"
	@echo "  quiniela     - generate pool entries + bracket picks from the latest sim run"
	@echo "  web          - launch Gradio app locally"
	@echo "  test         - run pytest"
	@echo "  lint         - ruff check + mypy"
	@echo "  format       - ruff format"
	@echo "  clean        - remove caches and build artifacts"

install:
	uv sync --extra dev

data:
	uv run python -m src.data.fetch_kaggle_martj42
	uv run python -m src.data.fetch_elo
	uv run python -m src.data.fetch_statsbomb
	uv run python -m src.data.fetch_transfermarkt
	uv run python -m src.data.fetch_wiki_squads
	uv run python -m src.data.fetch_kalshi_markets
	uv run python -m src.data.build_match_log

data-refresh:
	uv run python -m src.data.fetch_elo
	uv run python -m src.data.fetch_espn_odds
	uv run python -m src.data.fetch_kalshi_markets
	uv run python -m src.data.fetch_wiki_squads
	uv run python -m src.data.build_match_log

features:
	uv run python -m src.features.build_table

train:
	uv run python -m src.eval.generate_oof
	uv run python -m src.models.train_stacker

sim:
	uv run python -m src.predict_wc2026 --n 50000

quiniela:
	uv run python -m src.strategy.make_quiniela

web:
	uv run gradio web/app.py

test:
	uv run pytest -ra

lint:
	uv run ruff check src tests
	uv run mypy src

format:
	uv run ruff format src tests web

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov build dist
	find . -type d -name __pycache__ -exec rm -rf {} +
