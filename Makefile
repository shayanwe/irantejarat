.PHONY: install test lint clean build publish

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest

lint:
	flake8 bot tests
	black --check bot tests
	isort --check-only bot tests
	mypy bot tests

format:
	black bot tests
	isort bot tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .tox/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".tox" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +

build:
	python setup.py sdist bdist_wheel

publish:
	twine upload dist/*

run:
	python bot/main.py

docker-build:
	docker build -t telegram-ad-bot .

docker-run:
	docker run -d --name telegram-ad-bot telegram-ad-bot

docker-stop:
	docker stop telegram-ad-bot
	docker rm telegram-ad-bot

docker-logs:
	docker logs -f telegram-ad-bot

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code"
	@echo "  make clean      - Clean build files"
	@echo "  make build      - Build package"
	@echo "  make publish    - Publish package"
	@echo "  make run        - Run bot"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container"
	@echo "  make docker-stop  - Stop Docker container"
	@echo "  make docker-logs  - Show Docker logs"
	@echo "  make help       - Show this help message" 