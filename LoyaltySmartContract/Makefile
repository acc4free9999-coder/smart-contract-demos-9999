install:
	python3 -m pip install -r requirements.txt

start-blockchain:
	./scripts/start_blockchain.sh

seed:
	python3 scripts/seed_data.py

run-api:
	uvicorn server.main:app --reload

run-client:
	python3 client/main.py

check:
	pytest -q
