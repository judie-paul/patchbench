PYTHON ?= .venv/bin/python

.PHONY: setup lint format typecheck test test-docker test-network fixtures pipeline bench bench-docker clean
setup:
	uv venv --python 3.12 .venv
	uv pip install --python $(PYTHON) -e '.[dev,docker,service,hf]'
lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .
format:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .
typecheck:
	$(PYTHON) -m mypy
test:
	$(PYTHON) -m pytest -m 'not network and not docker'
test-docker:
	$(PYTHON) -m pytest -m docker --no-cov
test-network:
	$(PYTHON) -m pytest -m network --no-cov
fixtures:
	$(PYTHON) scripts/build_fixtures.py
pipeline: bench
bench:
	$(PYTHON) -m patchbench bench --executor local --out runs/bench-local.json
bench-docker:
	$(PYTHON) -m patchbench bench --executor docker --out runs/bench-docker.json
clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov build dist .coverage runs
