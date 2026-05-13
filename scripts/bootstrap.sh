#!/usr/bin/env bash
# =============================================================================
# bootstrap.sh — Configuração inicial do servidor Oracle Cloud Ubuntu
# Execute do seu Mac: bash scripts/bootstrap.sh
#
# Configuração (crie um arquivo .deploy.conf na raiz do projeto):
#   SERVER_IP=<ip do servidor>
#   SERVER_USER=<usuario ssh>
#   SERVER_KEY=<caminho da chave privada>   # opcional, default: ~/aptidev.key
# =============================================================================

set -euo pipefail

CONF_FILE="$(dirname "$0")/../.deploy.conf"
[[ -f "$CONF_FILE" ]] && source "$CONF_FILE"

SERVER_IP="${SERVER_IP:-}"
SERVER_USER="${SERVER_USER:-}"
SERVER_KEY="${SERVER_KEY:-$HOME/aptidev.key}"

[[ -n "$SERVER_IP" ]]   || { echo "Erro: SERVER_IP não definido. Crie o arquivo .deploy.conf"; exit 1; }
[[ -n "$SERVER_USER" ]] || { echo "Erro: SERVER_USER não definido. Crie o arquivo .deploy.conf"; exit 1; }
APP_DIR="/opt/quick-stash"

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }
section() { echo -e "\n${BOLD}=== $* ===${NC}"; }

ssh_run() {
  ssh -i "$SERVER_KEY" -o StrictHostKeyChecking=accept-new \
      "${SERVER_USER}@${SERVER_IP}" "$@"
}

scp_upload() {
  scp -i "$SERVER_KEY" -o StrictHostKeyChecking=accept-new "$1" \
      "${SERVER_USER}@${SERVER_IP}:$2"
}

# ---------------------------------------------------------------------------
section "PRÉ-REQUISITOS"
# ---------------------------------------------------------------------------

[[ -f "$SERVER_KEY" ]] || error "Chave SSH não encontrada em $SERVER_KEY"

# ---------------------------------------------------------------------------
section "TESTANDO CONEXÃO SSH"
# ---------------------------------------------------------------------------

info "Conectando ao servidor..."
ssh_run "echo 'SSH OK'"

# ---------------------------------------------------------------------------
section "CONFIGURANDO SERVIDOR"
# ---------------------------------------------------------------------------

info "Atualizando pacotes e instalando dependências base..."
ssh_run "sudo apt-get update -q && sudo apt-get install -y -q \
  curl git sqlite3 build-essential libsqlite3-dev libffi-dev \
  libssl-dev zlib1g-dev libncurses-dev libreadline-dev libbz2-dev \
  liblzma-dev tk-dev"

# ---------------------------------------------------------------------------
section "INSTALANDO PYENV"
# ---------------------------------------------------------------------------

info "Instalando pyenv..."
ssh_run 'if [[ ! -d "$HOME/.pyenv" ]]; then curl https://pyenv.run | bash; else echo "pyenv já instalado"; fi'

ssh_run 'cat >> ~/.bashrc << '"'"'PYENV_EOF'"'"'

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"
eval "$(pyenv init --path)"
eval "$(pyenv init -)"
PYENV_EOF'

ssh_run 'cat >> ~/.profile << '"'"'PROFILE_EOF'"'"'
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"
eval "$(pyenv init --path)" 2>/dev/null || true
eval "$(pyenv init -)" 2>/dev/null || true
PROFILE_EOF'

# ---------------------------------------------------------------------------
section "INSTALANDO POETRY"
# ---------------------------------------------------------------------------

info "Instalando poetry..."
ssh_run 'if command -v poetry &>/dev/null; then echo "poetry já instalado"; else curl -sSL https://install.python-poetry.org | python3 -; fi'

ssh_run 'cat >> ~/.bashrc << '"'"'POETRY_EOF'"'"'
export PATH="$HOME/.local/bin:$PATH"
POETRY_EOF'

ssh_run 'cat >> ~/.profile << '"'"'PROFILE2_EOF'"'"'
export PATH="$HOME/.local/bin:$PATH"
PROFILE2_EOF'

# ---------------------------------------------------------------------------
section "INSTALANDO PYTHON 3.12"
# ---------------------------------------------------------------------------

info "Instalando Python 3.12 via pyenv..."
ssh_run 'export PYENV_ROOT="$HOME/.pyenv" && export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH" && eval "$(pyenv init --path)" && if pyenv versions --bare | grep -q "3.12"; then echo "Python 3.12 já instalado"; else pyenv install 3.12.9 || pyenv install 3.12.8 || pyenv install 3.12.7; fi'

# ---------------------------------------------------------------------------
section "CRIANDO DIRETÓRIO DA APLICAÇÃO"
# ---------------------------------------------------------------------------

info "Criando diretório da aplicação..."
ssh_run "sudo mkdir -p $APP_DIR && sudo chown ubuntu:ubuntu $APP_DIR"

# ---------------------------------------------------------------------------
section "AUTO-DEPLOY — CONFIGURAÇÃO"
# ---------------------------------------------------------------------------

info "Criando .deploy_env..."
ssh_run "cat > $APP_DIR/.deploy_env << EOF
GH_REPO=flaviohbonfim/quick-stash-backend
EOF
chmod 600 $APP_DIR/.deploy_env"

info "Instalando auto-deploy.sh no servidor..."
scp_upload "$(dirname "$0")/auto-deploy.sh" "/tmp/auto-deploy.sh"
ssh_run "sudo mv /tmp/auto-deploy.sh /usr/local/bin/quick-stash-auto-deploy.sh && \
         sudo chmod +x /usr/local/bin/quick-stash-auto-deploy.sh"

info "Registrando cron (a cada 5 minutos)..."
ssh_run "echo 'PATH=/home/ubuntu/.pyenv/shims:/home/ubuntu/.pyenv/bin:/home/ubuntu/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin' > /tmp/qs-cron && echo '*/5 * * * * /usr/local/bin/quick-stash-auto-deploy.sh >> /var/log/quick-stash-deploy.log 2>&1' >> /tmp/qs-cron && (crontab -l 2>/dev/null | grep -v quick-stash-auto-deploy; cat /tmp/qs-cron) | crontab - && rm /tmp/qs-cron"

ssh_run "sudo touch /var/log/quick-stash-deploy.log && \
         sudo chown ubuntu:ubuntu /var/log/quick-stash-deploy.log"

# ---------------------------------------------------------------------------
section "SYSTEMD — UNIT FILE"
# ---------------------------------------------------------------------------

info "Criando unit file do systemd..."
ssh_run "sudo tee /etc/systemd/system/quick-stash.service > /dev/null << 'SYSTEMD_EOF'
[Unit]
Description=Quick Stash Backend API
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/quick-stash
ExecStart=/opt/quick-stash/.venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5
EnvironmentFile=/opt/quick-stash/.env

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF"

ssh_run "sudo systemctl daemon-reload"

# ---------------------------------------------------------------------------
section "VARIÁVEIS DE AMBIENTE DA APLICAÇÃO"
# ---------------------------------------------------------------------------

info "Criando .env.example no servidor..."
ssh_run "cat > $APP_DIR/.env.example << 'EOF'
DATABASE_URL=sqlite+aiosqlite:///./users.db
SECRET_KEY=sua-chave-secreta-aqui
EOF
chmod 600 $APP_DIR/.env.example"

# ---------------------------------------------------------------------------
section "PRIMEIRO DEPLOY"
# ---------------------------------------------------------------------------

info "Configuração inicial concluída!"
echo
info "Próximos passos:"
echo "  1. Crie o arquivo .env no servidor com suas variáveis:"
echo "     ssh -i ~/aptidev.key ubuntu@150.136.215.43"
echo "     cat > /opt/quick-stash/.env << EOF"
echo "     DATABASE_URL=sqlite+aiosqlite:///./users.db"
echo "     SECRET_KEY=<sua-secret-key>"
echo "     EOF"
echo "  2. Faça push na branch main para acionar o GitHub Actions"
echo "  3. Após a release ser criada, rode: ./manage.sh deploy"
echo "  4. Verifique o status: ./manage.sh status"
