.PHONY: help backend dashboard install-backend install-dashboard dev clean

help:
	@echo ""
	@echo "CAN Vision — Build Commands"
	@echo "----------------------------"
	@echo "  make install      Install all dependencies (backend + dashboard)"
	@echo "  make backend      Start the Python FastAPI backend (port 8000)"
	@echo "  make dashboard    Start the React dashboard dev server (port 5173)"
	@echo "  make dev          Start both backend and dashboard concurrently"
	@echo "  make clean        Remove uploaded files and build artifacts"
	@echo ""

install: install-backend install-dashboard

install-backend:
	cd backend && pip install -r requirements.txt

install-dashboard:
	cd dashboard && npm install

backend:
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000

dashboard:
	cd dashboard && npm run dev

dev:
	@echo "Starting CAN Vision..."
	@echo "  Backend  → http://localhost:8000"
	@echo "  Dashboard→ http://localhost:5173"
	@echo "  API docs → http://localhost:8000/docs"
	@echo ""
	cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
	cd dashboard && npm run dev

clean:
	rm -rf /tmp/can_vision_uploads
	rm -rf dashboard/dist
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
