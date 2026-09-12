.PHONY: bump-css

bump-css:
	@V=$$(md5sum styles.css | cut -c1-8) && \
	find . -name "*.html" -exec sed -i "s/styles\.css?v=[a-f0-9]*/styles.css?v=$$V/g" {} \;
	@echo "styles.css version → $$(md5sum styles.css | cut -c1-8)"
