# Quick Stash — API de Autenticação

**Base URL:** `http://localhost:8000`
**Autenticação:** JWT Bearer Token (Header `Authorization`)
**Algoritmo:** HS256

---

## Tokens

| Token | Duração | Uso |
|-------|---------|-----|
| `access_token` | 15 minutos | Autenticar requisições protegidas |
| `refresh_token` | 7 dias | Renovar `access_token` expirado |

---

## Fluxo de Autenticação

```
┌──────────┐     POST /auth/register      ┌──────────┐
│  Front   │ ────────────────────────────> │  Backend │
│          │                               │          │
│          │ <──────────────────────────── │ 201 Created
│          │     { id, name, email }       │          │
│          │                               │          │
│          │     POST /auth/login          │          │
│          │ ────────────────────────────> │          │
│          │                               │          │
│          │ <──────────────────────────── │ 200 OK   │
│          │  { access_token, refresh_token }          │
│          │                               │          │
│          │  Header: Bearer <token>       │          │
│          │     GET /users ─────────────> │          │
│          │ <──────────────────────────── │ 200 OK   │
│          │     { [users] }               │          │
│          │                               │          │
│          │     POST /auth/refresh        │          │
│          │ ────────────────────────────> │          │
│          │                               │          │
│          │ <──────────────────────────── │ 200 OK   │
│          │  { access_token, refresh_token }          │
│          │                               │          │
│          │     POST /auth/logout ──────> │          │
│          │                               │          │
│          │ <──────────────────────────── │ 200 OK   │
└──────────┘                               └──────────┘
```

---

## 1. Registro de Usuário

Cria um novo usuário na plataforma.

```
POST /auth/register
Content-Type: application/json
```

### Request Body

```json
{
  "name": "Flavio",
  "email": "flavio@email.com",
  "password": "overtUre1928"
}
```

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `name` | string | Sim | Nome do usuário |
| `email` | string | Sim | E-mail (único no sistema) |
| `password` | string | Sim | Senha (min. 8 caracteres, hash bcrypt) |

### Response — 201 Created

```json
{
  "name": "Flavio",
  "email": "flavio@email.com",
  "is_active": true,
  "id": "221d4df9-d768-4443-b664-f1e470ada284",
  "created_at": "2026-05-12T10:46:38.093787"
}
```

### Erros

| Status | Condição |
|--------|----------|
| `409 Conflict` | E-mail já cadastrado |

---

## 2. Login

Autentica o usuário e retorna os tokens JWT.

```
POST /auth/login
Content-Type: application/json
```

### Request Body

```json
{
  "email": "flavio@email.com",
  "password": "overtUre1928"
}
```

### Response — 200 OK

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Erros

| Status | Condição |
|--------|----------|
| `401 Unauthorized` | E-mail ou senha inválidos |

---

## 3. Renovar Token

Gera novos tokens usando o refresh token.

```
POST /auth/refresh
Content-Type: application/json
```

### Request Body

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Response — 200 OK

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Erros

| Status | Condição |
|--------|----------|
| `401 Unauthorized` | Token inválido, expirado ou revogado |

---

## 4. Logout

Invalida o refresh token do usuário atual.

```
POST /auth/logout
Authorization: Bearer <access_token>
```

### Response — 200 OK

```json
{
  "detail": "Logout realizado com sucesso"
}
```

### Erros

| Status | Condição |
|--------|----------|
| `401 Unauthorized` | Token inválido ou ausente |

---

## 5. Endpoints Protegidos

Todas as rotas abaixo exigem `Authorization: Bearer <access_token>`.

### Listar Usuários

```
GET /users?limit=100&offset=0
Authorization: Bearer <token>
```

**Response — 200 OK**

```json
[
  {
    "name": "Flavio",
    "email": "flavio@email.com",
    "is_active": true,
    "id": "221d4df9-d768-4443-b664-f1e470ada284",
    "created_at": "2026-05-12T10:46:38.093787"
  }
]
```

### Buscar Usuário por ID

```
GET /users/{user_id}
Authorization: Bearer <token>
```

**Response — 200 OK**

```json
{
  "name": "Flavio",
  "email": "flavio@email.com",
  "is_active": true,
  "id": "221d4df9-d768-4443-b664-f1e470ada284",
  "created_at": "2026-05-12T10:46:38.093787"
}
```

**Response — 404 Not Found**

```json
{
  "detail": "Usuário não encontrado"
}
```

### Buscar Usuário por E-mail

```
GET /users/email/{email}
Authorization: Bearer <token>
```

### Atualizar Usuário

```
PUT /users/{user_id}
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Body** (todos os campos opcionais)

```json
{
  "name": "Flavio Silva",
  "email": "flavio.silva@email.com",
  "password": "novaSenha123",
  "is_active": true
}
```

### Excluir Usuário

```
DELETE /users/{user_id}
Authorization: Bearer <token>
```

**Response — 204 No Content**

### Verificar Duplicidade de E-mail

```
POST /users/check-email?email=teste@email.com
Authorization: Bearer <token>
```

**Response — 409 Conflict** (email já existe)

```json
{
  "detail": "O e-mail teste@email.com já está cadastrado"
}
```

**Response — 204 No Content** (email disponível)

---

## Esquema de Autenticação

O backend usa `OAuth2PasswordBearer` para extração do token.

**Header esperado:**

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

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

---

## Estrutura de Resposta de Erro

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

---

## Exemplos de Uso

### cURL — Registro

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Flavio","email":"flavio@email.com","password":"overtUre1928"}'
```

### cURL — Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"flavio@email.com","password":"overtUre1928"}'
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
