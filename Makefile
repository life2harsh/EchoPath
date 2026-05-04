PYTHON ?= python3

.PHONY: backend-install backend-dev backend-test frontend-install frontend-dev frontend-build

backend-install:
	cd backend && $(PYTHON) -m pip install -e .[dev]

backend-dev:
	cd backend && uvicorn app.main:app --reload

backend-test:
	cd backend && pytest

frontend-install:
	cd frontend && npm install

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build
