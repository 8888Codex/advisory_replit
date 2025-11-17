#!/bin/sh
# Script para build do servidor com verificação de arquivo

set -e

# Verificar se estamos no diretório correto
if [ ! -f "esbuild.config.mjs" ]; then
  echo "❌ Erro: esbuild.config.mjs não encontrado no diretório atual: $(pwd)"
  echo "📂 Arquivos no diretório:"
  ls -la | head -20
  exit 1
fi

# Executar build
NODE_ENV=production node esbuild.config.mjs

