.PHONY: js
js:
	npm install --include dev
	npx webpack

.PHONY: devserve
devserve: js
	QRMAGIC_USE_WHITENOISE=True python3 -m qrmagic.api

.PHONY: docker
docker: js
	docker build --tag qrmagic .
