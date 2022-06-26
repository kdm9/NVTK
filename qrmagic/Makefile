.PHONY: js
js:
	npm install --include dev
	npx webpack

.PHONY: devserve
devserve: js
	python3 -m qrmagic.api

.PHONY: docker
docker: js
	docker build --tag qrmagic .
