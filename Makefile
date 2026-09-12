.PHONY: bump-css

bump-css:
	@V=$$(git rev-parse --short HEAD) && \
	find . -name "*.html" -exec sed -i "s/styles\.css?v=[a-f0-9]*/styles.css?v=$$V/g" {} \;
	@echo "styles.css version → $$(git rev-parse --short HEAD)"
