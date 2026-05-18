.PHONY: help install data data-refresh features train sim web live-update test lint format clean

help:
	@echo "Available targets:"
	@echo "  install      - sync uv environment with dev extras"
	@echo "  data         - fetch all raw data + build unified match log"
	@echo "  data-refresh - re-fetch volatile sources (Elo, FIFA, Kalshi, Wikipedia)"
	@echo "  features     - build feature store from raw data"
	@echo "  train        - fit all models (Dixon-Coles, Bayesian, LightGBM, stacker)"
	@echo "  sim          - run Monte Carlo bracket (50k sims)"
	@echo "  web          - launch Gradio app locally"
	@echo "  live-update  - end-to-end live pipeline (post-match)"
	@echo "  test         - run pytest"
	@echo "  lint         - ruff check + mypy"
	@echo "  format       - ruff format"
	@echo "  clean        - remove caches and build artifacts"

install:
	uv sync --extra dev

data:
	python -m src.data.fetch_kaggle_martj42
	python -m src.data.fetch_rsssf
	python -m src.data.fetch_elo
	python -m src.data.fetch_fifa_ranking
	python -m src.data.fetch_statsbomb
	python -m src.data.fetch_transfermarkt
	python -m src.data.fetch_wikipedia_squads
	python -m src.data.fetch_kalshi
	python -m src.data.build_match_log

data-refresh:
	python -m src.data.fetch_elo
	python -m src.data.fetch_fifa_ranking
	python -m src.data.fetch_kalshi
	python -m src.data.fetch_wikipedia_squads
	python -m src.data.build_match_log

features:
	python -m src.features.build_table

train:
	python -m src.models.dixon_coles --fit
	python -m src.models.bayesian --fit
	python -m src.models.gbm --fit
	python -m src.models.stacker --fit

sim:
	python -m src.sims.tournament --n 50000 --fixtures wc2026

web:
	gradio web/app.py

live-update:
	python -m src.live.update_loop

test:
	pytest -ra

lint:
	ruff check src tests
	mypy src

format:
	ruff format src tests web

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov build dist
	find . -type d -name __pycache__ -exec rm -rf {} +
