.DEFAULT_GOAL := help
DIR := ${CURDIR}
.PHONY: checkov format format-check install kics lint check help

checkov: ## Run checkov
	docker run --rm -v $(DIR):/tf --workdir /tf -t bridgecrew/checkov --directory /tf

format: ## Format repository code
	terraform fmt -recursive

format-check: ## Check the code format with no actual side effects
	terraform fmt -recursive --check

install: ## Install dependencies
	terraform init

kics: ## Run kics
	docker run --rm -v $(DIR):/path -t checkmarx/kics scan -p /path -o "/path/" --ci

lint: ## Launch the linting tools
	docker run --rm -v $(DIR):/data -t ghcr.io/terraform-linters/tflint 

trivy:
	docker run -v $(DIR):/app aquasec/trivy fs --scanners misconfig /app

validate: ## Validate terraform syntax
	terraform validate .

secure: checkov trivy kics
check: validate format lint secure # Run all checks

help: ## Show the available commands
	@echo Available commands:
ifeq ($(OS),Windows_NT)
	@for /f "tokens=1,2* delims=#" %%a in ('@findstr /r /c:"^[a-zA-Z-_]*:[ ]*## .*$$" $(MAKEFILE_LIST)') do @echo %%a%%b
else
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'
endif