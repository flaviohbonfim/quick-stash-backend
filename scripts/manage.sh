#!/usr/bin/env bash
# =============================================================================
# manage.sh — Gerenciamento remoto do Quick Stash Backend
# Execute do seu Mac: bash scripts/manage.sh <comando>
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

show_usage() {
  echo "Uso: $0 <comando>"
  echo ""
  echo "Comandos:"
  echo "  status           Verifica status do serviço e versão deployada"
  echo "  deploy           Força deploy imediato (sem esperar cron)"
  echo "  logs             Mostra últimas 50 linhas do log de deploy"
  echo "  service-status   Mostra status detalhado do serviço systemd"
  echo "  service-restart  Reinicia o serviço via systemd"
  echo "  service-enable   Habilita serviço para iniciar no boot"
  echo "  service-disable  Desabilita serviço do boot"
  echo "  env              Mostra variáveis de ambiente (sem valores sensíveis)"
}

cmd_status() {
  section "STATUS DO SERVIÇO"

  info "Verificando serviço..."
  ssh_run "systemctl is-active --quiet quick-stash && echo 'active' || echo 'inactive'" | while read -r status; do
    if [[ "$status" == "active" ]]; then
      echo -e "  Status: ${GREEN}ativo${NC}"
    else
      echo -e "  Status: ${RED}inativo${NC}"
    fi
  done

  info "Verificando versão..."
  CURRENT_TAG=$(ssh_run "cat /opt/quick-stash/.deployed_version 2>/dev/null || echo 'nunca deployado'")
  echo "  Versão atual: $CURRENT_TAG"

  LATEST_TAG=$(ssh_run "curl -fsSL -H 'Accept: application/vnd.github+json' \
    'https://api.github.com/repos/flaviohbonfim/quick-stash-backend/releases?per_page=1' \
    | grep '\"tag_name\"' | head -1 | sed 's/.*\"tag_name\": *\"\\([^\"]*\\)\".*/\\1/'")
  echo "  Última release: ${LATEST_TAG:-'não encontrada'}"

  if [[ "$CURRENT_TAG" == "$LATEST_TAG" ]]; then
    echo -e "  ${GREEN}✓ Atualizado${NC}"
  else
    echo -e "  ${YELLOW}⚠ Atualização disponível${NC}"
  fi

  info "Verificando porta 8000..."
  PORT_STATUS=$(ssh_run "ss -tlnp 2>/dev/null | grep ':8000' || echo 'não escutando'")
  if [[ "$PORT_STATUS" == "não escutando" ]]; then
    echo -e "  ${RED}Porta 8000 não está escutando${NC}"
  else
    echo -e "  ${GREEN}Porta 8000 está escutando${NC}"
  fi
}

cmd_deploy() {
  section "DEPLOY IMEDIATO"
  info "Forçando deploy no servidor..."
  ssh_run "/usr/local/bin/quick-stash-auto-deploy.sh"
  info "Deploy concluído!"
}

cmd_logs() {
  section "LOGS DE DEPLOY"
  ssh_run "tail -50 /var/log/quick-stash-deploy.log 2>/dev/null || echo 'Log não encontrado'"
}

cmd_service_status() {
  section "STATUS DO SYSTEMD"
  ssh_run "systemctl status quick-stash --no-pager"
}

cmd_service_restart() {
  section "REINICIAR SERVIÇO"
  info "Reiniciando serviço..."
  ssh_run "sudo systemctl restart quick-stash && echo 'Serviço reiniciado com sucesso'"
}

cmd_service_enable() {
  section "HABILITAR NO BOOT"
  info "Habilitando serviço para iniciar no boot..."
  ssh_run "sudo systemctl enable quick-stash && echo 'Serviço habilitado no boot'"
}

cmd_service_disable() {
  section "DESABILITAR NO BOOT"
  info "Desabilitando serviço do boot..."
  ssh_run "sudo systemctl disable quick-stash && echo 'Serviço desabilitado do boot'"
}

cmd_env() {
  section "VARIÁVEIS DE AMBIENTE"
  ssh_run "cat /opt/quick-stash/.env 2>/dev/null | sed 's/=.*/=***/' || echo '.env não encontrado'"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

COMMAND="${1:-}"

if [[ -z "$COMMAND" ]]; then
  show_usage
  exit 1
fi

case "$COMMAND" in
  status)         cmd_status ;;
  deploy)         cmd_deploy ;;
  logs)           cmd_logs ;;
  service-status) cmd_service_status ;;
  service-restart) cmd_service_restart ;;
  service-enable) cmd_service_enable ;;
  service-disable) cmd_service_disable ;;
  env)            cmd_env ;;
  *)
    echo "Comando desconhecido: $COMMAND"
    echo ""
    show_usage
    exit 1
    ;;
esac
