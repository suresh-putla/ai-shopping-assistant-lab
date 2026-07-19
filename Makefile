run-docker-compose: clean
	uv sync
	docker compose up  --build -d

clean:
	docker compose down --rmi all --volumes --remove-orphans

run-eval-retriever:
	uv sync
	PYTHONPATH=${PWD}/apps/api:${PWD}/apps/api/src:$$PYTHONPATH:${PWD} uv run --env-file .env python -m evals.eval_retriever

run-eval-retriever-extended:
	uv sync
	cd apps/api/src && PYTHONPATH=${PWD}/apps/api:${PWD}/apps/api/src:$$PYTHONPATH:${PWD} uv run --env-file ../../../.env python -m evals.eval_retriever_extended


