#!/usr/bin/env python3
"""Query if a service code is adhered by a municipality."""

import os
import sys

from pynfse_nacional import NFSeClient

CERT_PATH = os.environ.get("NFSE_CERT_PATH", "")
CERT_PASSWORD = os.environ.get("NFSE_CERT_PASSWORD", "")

if not CERT_PATH or not CERT_PASSWORD:
    print("Set NFSE_CERT_PATH and NFSE_CERT_PASSWORD environment variables")
    sys.exit(1)

# Default to Manaus
CODIGO_MUNICIPIO = int(sys.argv[1]) if len(sys.argv) > 1 else 1302603
CODIGO_SERVICO = sys.argv[2] if len(sys.argv) > 2 else "040301"
COMPETENCIA = sys.argv[3] if len(sys.argv) > 3 else "2026-01"

client = NFSeClient(
    cert_path=CERT_PATH,
    cert_password=CERT_PASSWORD,
    ambiente="homologacao",
)

# Normalize service code to 9 digits
codigo_limpo = CODIGO_SERVICO.replace(".", "")
if len(codigo_limpo) == 6:
    codigo_9dig = codigo_limpo + "000"
else:
    codigo_9dig = codigo_limpo

print(f"Consultando servico {CODIGO_SERVICO} (codigo API: {codigo_9dig})")
print(f"Municipio: {CODIGO_MUNICIPIO}")
print(f"Competencia: {COMPETENCIA}")
print()

try:
    result = client.query_aliquota_servico(CODIGO_MUNICIPIO, CODIGO_SERVICO, COMPETENCIA)

    if result.aderido:
        print("SERVICO ADERIDO")
        print(f"Codigo: {result.codigo_servico}")
        print(f"Aliquota: {result.aliquota}%")

        if result.raw_data:
            print(f"Dados: {result.raw_data}")
    else:
        print("SERVICO NAO ADERIDO")
        print("O municipio nao aderiu a este codigo de servico.")
        print()
        print("Tente outro codigo. Exemplos de codigos da LC 116:")
        print("  01.01.01 - Analise e desenvolvimento de sistemas")
        print("  01.02.01 - Programacao")
        print("  04.03.01 - Medicina geral")
        print("  17.02.01 - Datilografia e digitacao")

except Exception as e:
    print(f"Erro: {e}")
    sys.exit(1)
