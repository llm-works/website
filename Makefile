.PHONY: bump-css bump-js

bump-css:
	@V=$$(md5sum styles.css | cut -c1-8) && \
	find . -name "*.html" -exec sed -i "s/styles\.css?v=[a-f0-9]*/styles.css?v=$$V/g" {} \;
	@echo "styles.css version → $$(md5sum styles.css | cut -c1-8)"

bump-js:
	@V=$$(md5sum script.js | cut -c1-8) && \
	find . -name "*.html" -exec sed -i "s/script\.js?v=[a-f0-9]*/script.js?v=$$V/g" {} \;
	@echo "script.js version → $$(md5sum script.js | cut -c1-8)"
