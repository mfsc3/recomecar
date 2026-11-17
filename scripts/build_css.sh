#!/usr/bin/env bash
set -euo pipefail
TAILWIND_VERSION="v3.4.17"
BIN="./tailwindcss"
if [ ! -x "$BIN" ]; then
  echo "Baixando Tailwind CLI standalone ${TAILWIND_VERSION}..."
  curl -sLo "$BIN" "https://github.com/tailwindlabs/tailwindcss/releases/download/${TAILWIND_VERSION}/tailwindcss-linux-x64"
  chmod +x "$BIN"
fi
mkdir -p static/css
"$BIN" -i static_src/input.css -o static/css/tailwind.css --minify
echo "CSS compilado em static/css/tailwind.css"
