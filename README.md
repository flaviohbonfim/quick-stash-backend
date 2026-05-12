API RESTful de CRUD de Usuários

## Setup Inicial

```bash
poetry install
```

## Rodar Servidor

```bash
poetry run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Testes

```bash
poetry run pytest
```