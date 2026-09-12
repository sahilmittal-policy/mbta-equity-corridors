.PHONY: help install test figures fiscal lint clean all

help:
	@echo "install   pip install -e '.[dev]'"
	@echo "test      run the test suite"
	@echo "figures   regenerate everything in figures/"
	@echo "fiscal    print the full cost-benefit model"
	@echo "lint      ruff check"
	@echo "all       install, test, figures"

install:
	pip install -e ".[dev]"

test:
	pytest

figures:
	python scripts/make_figures.py

fiscal:
	python scripts/03_fiscal_model.py --sensitivity speed_improvement

lint:
	ruff check src scripts tests

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__

all: install test figures
