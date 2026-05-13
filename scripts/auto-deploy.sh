#!/usr/bin/env bash
# =============================================================================
# auto-deploy.sh — Polling de novas releases no GitHub
# Roda no servidor via cron a cada 5 minutos.
# =============================================================================

set -euo pipefail

APP_DIR="/opt/quick-stash"
DEPLOY_ENV="$APP_DIR/.deploy_env"
VERSION_FILE="$APP_DIR/.deployed_version"
WORK_DIR="/tmp/quick-stash-deploy"
LOG_TAG="[quick-stash-deploy]"

log() { echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') $LOG_TAG $*"; }

# ---------------------------------------------------------------------------
# Carregar configuração
# ---------------------------------------------------------------------------

[[ -f "$DEPLOY_ENV" ]] || { log "ERROR: $DEPLOY_ENV não encontrado."; exit 1; }
# shellcheck source=/dev/null
source "$DEPLOY_ENV"

: "${GH_REPO:?GH_REPO não definido em $DEPLOY_ENV}"

# ---------------------------------------------------------------------------
# Consultar última release no GitHub
# ---------------------------------------------------------------------------

GH_PAT="${GH_PAT:-}"
if [[ -n "$GH_PAT" ]]; then
  LATEST_JSON=$(curl -fsSL \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $GH_PAT" \
    "https://api.github.com/repos/${GH_REPO}/releases?per_page=1")
else
  LATEST_JSON=$(curl -fsSL \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com/repos/${GH_REPO}/releases?per_page=1")
fi || {
  log "ERROR: Falha ao consultar a API do GitHub."
  exit 1
}

LATEST_TAG=$(echo "$LATEST_JSON" | grep '"tag_name"' | head -1 | sed 's/.*"tag_name": *"\([^"]*\)".*/\1/')
ASSET_URL=$(echo "$LATEST_JSON" | grep '"browser_download_url"' | head -1 | sed 's/.*"browser_download_url": *"\([^"]*\)".*/\1/')

[[ -n "$LATEST_TAG" ]] || { log "ERROR: Não foi possível determinar a tag da release."; exit 1; }
[[ -n "$ASSET_URL" ]]  || { log "ERROR: Nenhum asset encontrado na release $LATEST_TAG."; exit 1; }

# ---------------------------------------------------------------------------
# Verificar se já está na versão mais recente
# ---------------------------------------------------------------------------

CURRENT_TAG=""
[[ -f "$VERSION_FILE" ]] && CURRENT_TAG=$(cat "$VERSION_FILE")

if [[ "$CURRENT_TAG" == "$LATEST_TAG" ]]; then
  exit 0
fi

log "Nova versão detectada: ${CURRENT_TAG:-'none'} → $LATEST_TAG"

# ---------------------------------------------------------------------------
# Download do artifact
# ---------------------------------------------------------------------------

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

ARCHIVE="$WORK_DIR/release.tar.gz"

log "Baixando $ASSET_URL..."
curl -fsSL -o "$ARCHIVE" "$ASSET_URL" || {
  log "ERROR: Falha ao baixar o artifact."
  rm -rf "$WORK_DIR"
  exit 1
}

# ---------------------------------------------------------------------------
# Extrair e aplicar
# ---------------------------------------------------------------------------

log "Extraindo artifact..."
tar -xzf "$ARCHIVE" -C "$WORK_DIR"

# Preservar .env antes de substituir os arquivos
ENV_BACKUP="$WORK_DIR/.env.bak"
[[ -f "$APP_DIR/.env" ]] && cp "$APP_DIR/.env" "$ENV_BACKUP"

log "Aplicando nova versão..."
rsync -a --delete \
  --exclude=".env" \
  --exclude=".deploy_env" \
  --exclude=".deployed_version" \
  --exclude="users.db" \
  --exclude="__pycache__" \
  --exclude="*.egg-info" \
  --exclude=".kilo" \
  "$WORK_DIR/" "$APP_DIR/"

# Restaurar .env
[[ -f "$ENV_BACKUP" ]] && cp "$ENV_BACKUP" "$APP_DIR/.env"

# ---------------------------------------------------------------------------
# Instalar dependências com poetry
# ---------------------------------------------------------------------------

log "Instalando dependências com poetry..."
cd "$APP_DIR"

# Garantir que pyenv está disponível
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)" 2>/dev/null || true
eval "$(pyenv init -)" 2>/dev/null || true

# Encontrar versão do Python instalada pelo pyenv
PYTHON_VERSION=$(pyenv versions --bare | grep "3.12" | head -1)

if [[ -z "$PYTHON_VERSION" ]]; then
  log "ERROR: Python 3.12 não encontrado no pyenv. Execute o bootstrap.sh novamente."
  rm -rf "$WORK_DIR"
  exit 1
fi

PYTHON_PATH="$HOME/.pyenv/versions/$PYTHON_VERSION/bin/python"

# Verificar se o poetry virtual env existe, senão criar
if [[ ! -d "$APP_DIR/.venv" ]]; then
  log "Criando virtualenv..."
  "$PYTHON_PATH" -m venv "$APP_DIR/.venv"
fi

log "Executando poetry install..."
# Usar o poetry instalado globalmente, mas apontar para o venv do projeto
PATH="$HOME/.local/bin:$PATH" poetry install --no-interaction --no-ansi 2>&1 | tail -5 || {
  log "WARN: poetry install falhou, tentando com pip..."
  "$PYTHON_PATH" -m pip install -r /dev/null 2>&1 || true
}

# ---------------------------------------------------------------------------
# Reiniciar serviço via systemd
# ---------------------------------------------------------------------------

log "Reiniciando serviço..."
sudo systemctl daemon-reload

# Atualizar o ExecStart no unit file com o caminho correto do Python
sudo sed -i "s|ExecStart=.*|ExecStart=$HOME/.pyenv/versions/$PYTHON_VERSION/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000|" /etc/systemd/system/quick-stash.service

sudo systemctl restart quick-stash || {
  log "ERROR: Falha ao reiniciar o serviço."
  rm -rf "$WORK_DIR"
  exit 1
}

# Verificar se o serviço está rodando
sleep 2
if ! systemctl is-active --quiet quick-stash; then
  log "ERROR: O serviço quick-stash não está ativo após reinício."
  log "Verifique: systemctl status quick-stash"
  rm -rf "$WORK_DIR"
  exit 1
fi

# ---------------------------------------------------------------------------
# Registrar versão deployada
# ---------------------------------------------------------------------------

echo "$LATEST_TAG" > "$VERSION_FILE"

log "Deploy concluído: $LATEST_TAG"

# Limpeza
rm -rf "$WORK_DIR"
