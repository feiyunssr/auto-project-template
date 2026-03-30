#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
CERT_DIR="$ROOT_DIR/infra/nginx/certs"
CA_DIR="$ROOT_DIR/infra/tls/internal-ca"

APP_DOMAIN="${APP_DOMAIN:-ai-auto.test}"
TLS_CA_NAME="${TLS_CA_NAME:-AI Auto Hub Internal Root CA}"
TLS_CA_VALID_DAYS="${TLS_CA_VALID_DAYS:-3650}"
TLS_CERT_VALID_DAYS="${TLS_CERT_VALID_DAYS:-825}"
TLS_CERT_EXTRA_DNS_SANS="${TLS_CERT_EXTRA_DNS_SANS:-}"
TLS_CERT_IP_SANS="${TLS_CERT_IP_SANS:-}"
TLS_FORCE_ROTATE_CA="${TLS_FORCE_ROTATE_CA:-0}"

CA_KEY_PATH="$CA_DIR/root-ca.key"
CA_CERT_PATH="$CA_DIR/root-ca.crt"
CA_SERIAL_PATH="$CA_DIR/root-ca.srl"
SERVER_KEY_PATH="$CERT_DIR/tls.key"
SERVER_CSR_PATH="$CERT_DIR/tls.csr"
SERVER_CERT_PATH="$CERT_DIR/tls.crt"
SERVER_FULLCHAIN_PATH="$CERT_DIR/tls.fullchain.crt"

require_binary() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

join_sans() {
  local prefix="$1"
  local items="$2"
  local output=""

  IFS=',' read -r -a values <<<"$items"
  for value in "${values[@]}"; do
    value="${value// /}"
    if [[ -z "$value" ]]; then
      continue
    fi
    if [[ -n "$output" ]]; then
      output+=","
    fi
    output+="${prefix}:${value}"
  done

  printf '%s' "$output"
}

main() {
  require_binary openssl

  mkdir -p "$CERT_DIR" "$CA_DIR"

  if [[ "$TLS_FORCE_ROTATE_CA" == "1" ]]; then
    rm -f "$CA_KEY_PATH" "$CA_CERT_PATH" "$CA_SERIAL_PATH"
  fi

  if [[ ! -f "$CA_KEY_PATH" || ! -f "$CA_CERT_PATH" ]]; then
    openssl genrsa -out "$CA_KEY_PATH" 4096 >/dev/null 2>&1
    openssl req -x509 -new -sha256 \
      -key "$CA_KEY_PATH" \
      -days "$TLS_CA_VALID_DAYS" \
      -out "$CA_CERT_PATH" \
      -subj "/CN=${TLS_CA_NAME}" >/dev/null 2>&1
    chmod 600 "$CA_KEY_PATH"
  fi

  local san_entries="DNS:${APP_DOMAIN}"
  local extra_dns
  local extra_ips
  extra_dns="$(join_sans "DNS" "$TLS_CERT_EXTRA_DNS_SANS")"
  extra_ips="$(join_sans "IP" "$TLS_CERT_IP_SANS")"

  if [[ -n "$extra_dns" ]]; then
    san_entries="${san_entries},${extra_dns}"
  fi
  if [[ -n "$extra_ips" ]]; then
    san_entries="${san_entries},${extra_ips}"
  fi

  local extfile
  extfile="$(mktemp)"
  cat >"$extfile" <<EOF
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage=digitalSignature,keyEncipherment
extendedKeyUsage=serverAuth
subjectAltName=${san_entries}
EOF

  openssl genrsa -out "$SERVER_KEY_PATH" 2048 >/dev/null 2>&1
  openssl req -new \
    -key "$SERVER_KEY_PATH" \
    -out "$SERVER_CSR_PATH" \
    -subj "/CN=${APP_DOMAIN}" >/dev/null 2>&1
  openssl x509 -req \
    -in "$SERVER_CSR_PATH" \
    -CA "$CA_CERT_PATH" \
    -CAkey "$CA_KEY_PATH" \
    -CAcreateserial \
    -out "$SERVER_CERT_PATH" \
    -days "$TLS_CERT_VALID_DAYS" \
    -sha256 \
    -extfile "$extfile" >/dev/null 2>&1

  cat "$SERVER_CERT_PATH" "$CA_CERT_PATH" >"$SERVER_FULLCHAIN_PATH"

  chmod 600 "$SERVER_KEY_PATH"
  rm -f "$SERVER_CSR_PATH" "$extfile"

  echo "Generated internal TLS assets:"
  echo "  Root CA:      $CA_CERT_PATH"
  echo "  Server cert:  $SERVER_CERT_PATH"
  echo "  Full chain:   $SERVER_FULLCHAIN_PATH"
  echo "  Server key:   $SERVER_KEY_PATH"
  echo
  echo "Install the root CA on client devices before accessing https://${APP_DOMAIN}"
}

main "$@"
