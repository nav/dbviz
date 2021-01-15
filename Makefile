SHELL := /bin/bash
PIPENV_RUN := cd src && pipenv run

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show this help
	@echo 'Usage: make <command>'
	@echo
	@echo 'The following commands are available:'
	@echo
	@grep '^[[:alnum:]_-]*:.* ##' $(MAKEFILE_LIST) \
	| sort | awk 'BEGIN {FS=":"}; {printf "%-15s %s\n", $$1, $$2};' \
	| sed -e "s/## //"

.PHONY: install
install: ## Install dependencies
	PIPENV_VENV_IN_PROJECT=1 pipenv install --dev

.PHONY: run
run: ## Run application
	${PIPENV_RUN} uvicorn main:app --reload

