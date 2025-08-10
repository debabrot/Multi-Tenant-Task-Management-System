install:
	pip install -r requirements.txt

test:
	pytest

up:
	docker compose up

up-build:
	docker compose up --build