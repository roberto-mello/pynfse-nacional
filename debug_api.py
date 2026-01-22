#!/usr/bin/env python3
"""Debug script to test the exact API call."""

import os
import sys
import json
import tempfile
from pathlib import Path

import httpx

CERT_PATH = os.environ.get("NFSE_CERT_PATH", "")
CERT_PASSWORD = os.environ.get("NFSE_CERT_PASSWORD", "")

if not CERT_PATH or not CERT_PASSWORD:
    print("Set NFSE_CERT_PATH and NFSE_CERT_PASSWORD environment variables")
    sys.exit(1)

CODIGO_MUNICIPIO = int(sys.argv[1]) if len(sys.argv) > 1 else 1302603

from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption

with open(CERT_PATH, "rb") as f:
    pkcs12_data = f.read()

private_key, certificate, _ = pkcs12.load_key_and_certificates(
    pkcs12_data, CERT_PASSWORD.encode()
)

key_pem = private_key.private_bytes(
    encoding=Encoding.PEM,
    format=PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=NoEncryption(),
)

cert_pem = certificate.public_bytes(Encoding.PEM)

with tempfile.NamedTemporaryFile(mode="wb", suffix=".pem", delete=False) as cert_file:
    cert_file.write(cert_pem)
    cert_file_path = cert_file.name

with tempfile.NamedTemporaryFile(mode="wb", suffix=".pem", delete=False) as key_file:
    key_file.write(key_pem)
    key_file_path = key_file.name

try:
    client = httpx.Client(
        cert=(cert_file_path, key_file_path),
        verify=True,
        timeout=30.0,
    )

    print(f"Testing for municipality {CODIGO_MUNICIPIO}")
    print("=" * 70)

    # Try the SEFIN API base (not ADN parametrizacao)
    # The documentation mentions /parametros_municipais/{codigoMunicipio}/{codigoServico}
    base_urls = [
        "https://sefin.producaorestrita.nfse.gov.br/SefinNacional",
        "https://sefin.producaorestrita.nfse.gov.br",
        "https://adn.producaorestrita.nfse.gov.br",
    ]

    codes = ["040301", "040301000", "04.03.01"]

    for base in base_urls:
        print(f"\nBase: {base}")
        print("-" * 60)

        for code in codes:
            # Try the documented format without competencia
            url = f"{base}/parametros_municipais/{CODIGO_MUNICIPIO}/{code}"
            response = client.get(url)

            try:
                if response.status_code == 200:
                    data = response.json()
                    print(f"  {code}: {response.status_code} - SUCCESS: {json.dumps(data)[:200]}")
                elif response.status_code == 404:
                    print(f"  {code}: 404 - Not found")
                else:
                    data = response.json()
                    msg = data.get("mensagem", str(data))[:60]
                    print(f"  {code}: {response.status_code} - {msg}")
            except:
                print(f"  {code}: {response.status_code} - {response.text[:60]}")

    # Try the swagger from SEFIN API
    print("\n\nChecking SEFIN API swagger...")
    for base in base_urls:
        for swagger_path in ["/swagger/v1/swagger.json", "/docs/swagger.json", "/openapi.json"]:
            url = f"{base}{swagger_path}"
            response = client.get(url)

            if response.status_code == 200:
                print(f"\nFound swagger at: {url}")

                try:
                    spec = response.json()
                    paths = spec.get("paths", {})

                    for path in paths.keys():
                        if "parametro" in path.lower() or "aliquota" in path.lower():
                            print(f"  {path}")

                except:
                    pass

    client.close()

finally:
    Path(cert_file_path).unlink(missing_ok=True)
    Path(key_file_path).unlink(missing_ok=True)
