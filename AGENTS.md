## Como desenvolver na API de Usuários

### Setup Inicial

1. Crie um arquivo `.env` na raiz do projeto:

```bash
DATABASE_URL=sqlite+aiosqlite:///./users.db
SECRET_KEY=your-secret-key-here
```

2. Instale as dependências:

```bash
poetry install
```

3. Gere uma chave de segurança se necessário, adicione ao `.env`:

```bash
poetry run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Comandos Úteis

```bash
# Instalar dependências
poetry install

# Atualizar dependências
poetry update

# Listar dependências
poetry show

# Adicionar nova dependência
poetry add <package>
poetry add <package> --group dev

# Remover dependência
poetry remove <package>

# Sincronizar dependências com pyproject.toml
poetry lock
poetry install
```

### API Endpoints

- `POST /users` - Criar usuário
- `GET /users` - Listar usuários
- `GET /users/{user_id}` - Buscar usuário por ID
- `GET /users/email/{email}` - Buscar usuário por email
- `PUT /users/{user_id}` - Atualizar usuário
- `DELETE /users/{user_id}` - Remover usuário
- `POST /users/check-email` - Verificar duplicidade

### Código

- **Models**: `models/`
- **Schemas**: `schemas/`
- **CRUD**: `crud/`
- **Routers**: `api/routers/`
- **Core**: `core/`
- **Main**: `main.py`
