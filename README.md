# Quick Stash — Backend API

API RESTful construída com **FastAPI** para gerenciamento de usuários com autenticação JWT (access + refresh tokens).

## Tecnologias

- **FastAPI** — Framework web assíncrono
- **SQLAlchemy 2.0** — ORM assíncrono
- **SQLite + aiosqlite** — Banco de dados
- **python-jose** — JWT (HS256)
- **bcrypt** — Hash de senhas
- **Pydantic** — Validação de schemas

## Setup

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
DATABASE_URL=sqlite+aiosqlite:///./users.db
SECRET_KEY=sua-chave-secreta-aqui
```

Variáveis disponíveis:

| Variável | Tipo | Padrão | Descrição |
|----------|------|--------|-----------|
| `DATABASE_URL` | string | — | URL de conexão do banco |
| `SECRET_KEY` | string | — | Chave para assinar JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `15` | Duração do access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | `7` | Duração do refresh token |
| `ALGORITHM` | string | `HS256` | Algoritmo JWT |

### 2. Instalar Dependências

```bash
poetry install
```

### 3. Rodar o Servidor

```bash
poetry run python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Documentação interativa (Swagger): `http://localhost:8000/docs`

## Fluxo de Autenticação

```
┌──────────┐     POST /auth/register          ┌─────────────┐
│  Front   │ ────────────────────────────>    │   Backend   │
│          │                                  │             │
│          │ <────────────────────────────    │ 201 Created |
│          │     { id, name, email }          │             │
│          │                                  │             │
│          │     POST /auth/login             │             │
│          │ ────────────────────────────>    │             │
│          │                                  │             │
│          │ <────────────────────────────    │   200 OK    │
│          │  { access_token, refresh_token } |             │
│          │                                  │             │
│          │  Header: Bearer <token>          │             │
│          │     GET /users ─────────────>    │             │
│          │ <────────────────────────────    │   200 OK    │
│          │     { [users] }                  │             │
│          │                                  │             │
│          │     POST /auth/refresh           │             │
│          │ ────────────────────────────>    │             │
│          │                                  │             │
│          │ <────────────────────────────    │   200 OK    │
│          │  { access_token, refresh_token } │             │
│          │                                  │             │
│          │     POST /auth/logout ──────>    │             │
│          │                                  │             │
│          │ <────────────────────────────    │   200 OK    │
└──────────┘                                  └─────────────┘
```

## Endpoints

### Autenticação (`/auth`)

#### `POST /auth/register`

Registra um novo usuário.

**Request Body:**

```json
{
  "name": "user",
  "email": "user@email.com",
  "password": "P@ssw0rd"
}
```

**Response — 201 Created:**

```json
{
  "name": "user",
  "email": "user@email.com",
  "is_active": true,
  "id": "221d4df9-d768-4443-b664-f1e470ada284",
  "created_at": "2026-05-12T10:46:38.093787"
}
```

| Status | Condição |
|--------|----------|
| `201` | Usuário criado com sucesso |
| `409` | E-mail já cadastrado |

---

#### `POST /auth/login`

Autentica e retorna tokens JWT.

**Request Body:**

```json
{
  "email": "user@email.com",
  "password": "P@ssw0rd"
}
```

**Response — 200 OK:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

| Status | Condição |
|--------|----------|
| `200` | Login bem-sucedido |
| `401` | Credenciais inválidas |

---

#### `POST /auth/refresh`

Renova os tokens usando o refresh token.

**Request Body:**

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response — 200 OK:**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

| Status | Condição |
|--------|----------|
| `200` | Tokens renovados |
| `401` | Token inválido, expirado ou revogado |

---

#### `POST /auth/logout`

Invalida o refresh token do usuário atual.

**Headers:** `Authorization: Bearer <access_token>`

**Response — 200 OK:**

```json
{
  "detail": "Logout realizado com sucesso"
}
```

| Status | Condição |
|--------|----------|
| `200` | Logout realizado |
| `401` | Token inválido ou ausente |

---

### Usuários (`/users`)

Todas as rotas abaixo exigem `Authorization: Bearer <access_token>`.

#### `POST /users`

Criar novo usuário.

**Response — 201 Created:** `UserResponse`

---

#### `GET /users`

Listar todos os usuários com paginação.

**Query Params:**

| Param | Tipo | Padrão | Descrição |
|-------|------|--------|-----------|
| `limit` | int | `100` | Máximo de resultados |
| `offset` | int | `0` | Deslocamento |

**Response — 200 OK:**

```json
[
  {
    "name": "user",
    "email": "user@email.com",
    "is_active": true,
    "id": "221d4df9-d768-4443-b664-f1e470ada284",
    "created_at": "2026-05-12T10:46:38.093787"
  }
]
```

---

#### `GET /users/{user_id}`

Buscar usuário por ID.

**Response — 200 OK:** `UserResponse`

| Status | Condição |
|--------|----------|
| `200` | Usuário encontrado |
| `404` | Usuário não encontrado |

---

#### `GET /users/email/{email}`

Buscar usuário por e-mail.

**Response — 200 OK:** `UserResponse`

| Status | Condição |
|--------|----------|
| `200` | Usuário encontrado |
| `404` | Usuário não encontrado |

---

#### `PUT /users/{user_id}`

Atualizar usuário (campos opcionais).

**Request Body:**

```json
{
  "name": "User Alterado",
  "email": "user.alterado@email.com",
  "password": "novaSenha123",
  "is_active": true
}
```

**Response — 200 OK:** `UserResponse`

| Status | Condição |
|--------|----------|
| `200` | Usuário atualizado |
| `404` | Usuário não encontrado |

---

#### `DELETE /users/{user_id}`

Excluir usuário.

**Response — 204 No Content**

| Status | Condição |
|--------|----------|
| `204` | Usuário excluído |
| `404` | Usuário não encontrado |

---

#### `POST /users/check-email`

Verificar se um e-mail já está cadastrado.

**Query Param:** `email=teste@email.com`

**Response — 409 Conflict** (email existe):

```json
{
  "detail": "O e-mail teste@email.com já está cadastrado"
}
```

**Response — 204 No Content** (email disponível)

---

#### `POST /users/change-password`

Alterar a senha do usuário autenticado.

**Headers:** `Authorization: Bearer <access_token>`

**Request Body:**

```json
{
  "old_password": "senhaAntiga123",
  "new_password": "novaSenha456"
}
```

**Response — 200 OK**

| Status | Condição |
|--------|----------|
| `200` | Senha alterada com sucesso |
| `400` | Senha antiga incorreta |
| `401` | Token inválido ou ausente |

---

## Tokens JWT

| Token | Duração | Uso |
|-------|---------|-----|
| `access_token` | 15 min | Autenticar requisições protegidas |
| `refresh_token` | 7 dias | Renovar access token expirado |

**Estrutura do JWT:**

```json
{
  "sub": "user-uuid",
  "exp": 1778584754,
  "iat": 1778583854,
  "type": "access"
}
```

| Claim | Descrição |
|-------|-----------|
| `sub` | UUID do usuário |
| `exp` | Expiração (Unix timestamp) |
| `iat` | Emissão (Unix timestamp) |
| `type` | `"access"` ou `"refresh"` |

**Header esperado:**

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Estrutura do Projeto

```
.
├── api/
│   ├── __init__.py
│   ├── deps.py              # Dependências (get_current_user, OAuth2)
│   └── routers/
│       ├── auth.py          # Rotas de autenticação
│       └── users.py         # Rotas de CRUD de usuários
├── core/
│   ├── config.py            # Configurações (Settings)
│   ├── database.py          # Engine, session, Base
│   └── security.py          # JWT, bcrypt, hash
├── crud/
│   └── user.py              # Operações de banco
├── models/
│   └── user.py              # Modelo SQLAlchemy
├── schemas/
│   ├── __init__.py
│   └── user.py              # Schemas Pydantic
├── tests/
│   ├── __init__.py
│   └── test_auth.py         # Testes de autenticação
├── .env                     # Variáveis de ambiente
├── .env.example             # Exemplo de variáveis
├── main.py                  # Aplicação FastAPI
├── pyproject.toml
└── poetry.lock
```

## Testes

```bash
poetry run pytest
```

## Comandos Úteis

```bash
# Instalar dependências
poetry install

# Atualizar dependências
poetry update

# Adicionar dependência
poetry add <package>
poetry add <package> --group dev

# Remover dependência
poetry remove <package>

# Lint
poetry run ruff check .

# Formatar
poetry run ruff format .

# Rodar testes com cobertura
poetry run pytest --cov=api --cov=core --cov=crud --cov=schemas
```

## Exemplos de Uso

### cURL — Registro

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"user","email":"user@email.com","password":"P@ssw0rd"}'
```

### cURL — Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@email.com","password":"P@ssw0rd"}'
```

### cURL — Requisição Protegida

```bash
curl http://localhost:8000/users \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### JavaScript — Fluxo Completo

```javascript
const BASE_URL = 'http://localhost:8000';

// 1. Registrar
const register = async (data) => {
  const res = await fetch(`${BASE_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
};

// 2. Login
const login = async (email, password) => {
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  return res.json();
};

// 3. Requisição protegida
const getUsers = async (token) => {
  const res = await fetch(`${BASE_URL}/users`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
};

// 4. Renovar token
const refreshToken = async (refreshToken) => {
  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  return res.json();
};

// 5. Logout
const logout = async (token) => {
  const res = await fetch(`${BASE_URL}/auth/logout`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  return res.json();
};
```

## Respostas de Erro

```json
{
  "detail": "Mensagem de erro"
}
```

| Status | Significado |
|--------|-------------|
| `400` | Bad Request (validação falhou) |
| `401` | Não autorizado (token inválido/ausente) |
| `404` | Recurso não encontrado |
| `409` | Conflito (recurso duplicado) |
