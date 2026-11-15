.DEFAULT_GOAL := help
PYTHON ?= python

.PHONY: help build serve

help: ## Show this help
	@awk 'BEGIN { FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n" } \
	/^[a-zA-Z0-9_.-]+:.*##/ { printf "  \033[36m%-12s\033[0m%s\n", $$1, $$2 } \
	/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Build

build: ## Build the blog (posts, index, feed), stamp asset hashes, check news.json
	@$(PYTHON) blog/build.py

serve: ## Serve the site on 0.0.0.0:8000
	$(PYTHON) -m http.server 8000 --bind 0.0.0.0
