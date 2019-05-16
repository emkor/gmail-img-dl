all: test build

PY3 = python3
VENV_DIR = .venv/gmail-img-dl
VENV_PY = .venv/gmail-img-dl/bin/python

venv:
	@echo "---- Cleanup ----"
	@rm -rf $(VENV_DIR)
	@mkdir -p $(VENV_DIR)
	@echo "---- Creating virtualenv ----"
	@$(PY3) -m venv $(VENV_DIR)
	@echo "---- Installing dependencies ----"
	@$(VENV_PY) -m pip install --upgrade pip
	@$(VENV_PY) -m pip install -e .[dev]

build:
	@echo "---- Building ---- "
	@mkdir -p ./dist
	@$(VENV_PY) setup.py sdist bdist_wheel --python-tag py3 --dist-dir ./dist

test:
	@echo "---- Testing ---- "
	@$(VENV_PY) -m mypy --ignore-missing-imports ./gmail_img_dl

.PHONY: all venv test build
