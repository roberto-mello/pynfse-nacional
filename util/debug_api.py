#!/usr/bin/env python3
"""Debug script to explore NFSe Nacional API endpoints.

This utility helps debug and explore the SEFIN API by making raw HTTP calls
to various endpoints. Useful for understanding API responses and testing
connectivity.

Usage:
    python debug_api.py --config issuer.ini --municipio 1302603

    # With different base URLs:
    python debug_api.py --config issuer.ini --municipio 3550308 --producao
"""

import argparse
import configparser
import json
import os
import sys
import tempfile
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional.constants import API_URLS, PARAMETRIZACAO_URLS, Ambiente


def load_config(config_path: str) -> configparser.ConfigParser:
    """Load configuration from INI file."""

    if not Path(config_path).exists():
        print(f"Error: Configuration file not found: {config_path}")
        print("Copy issuer.example.ini to issuer.ini and fill in your details.")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    return config


def get_certificate_info(config: configparser.ConfigParser, args) -> tuple[str, str]:
    """Get certificate path and password from config, args, or environment."""

    cert_path = (
        args.cert_path
        or os.environ.get("NFSE_CERT_PATH")
        or config.get("certificate", "path", fallback=None)
    )

    cert_password = (
        args.cert_password
        or os.environ.get("NFSE_CERT_PASSWORD")
        or config.get("certificate", "password", fallback=None)
    )

    if not cert_path:
        print("Error: Certificate path not provided.")
        print("Use --cert-path, NFSE_CERT_PATH env var, or configure in file.")
        sys.exit(1)

    if not cert_password:
        print("Error: Certificate password not provided.")
        print("Use --cert-password, NFSE_CERT_PASSWORD env var, or configure in file.")
        sys.exit(1)

    if not Path(cert_path).exists():
        print(f"Error: Certificate file not found: {cert_path}")
        sys.exit(1)

    return cert_path, cert_password


def main():
    parser = argparse.ArgumentParser(
        description="Debug and explore NFSe Nacional API endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Explore endpoints for Manaus:
  %(prog)s --config issuer.ini --municipio 1302603

  # Production environment:
  %(prog)s --config issuer.ini --municipio 1302603 --producao

This script makes raw HTTP calls to explore API endpoints and responses.
Useful for debugging connectivity and understanding API behavior.
""",
    )

    parser.add_argument(
        "--config", "-c",
        required=True,
        help="Path to issuer configuration file (INI format)",
    )

    parser.add_argument(
        "--municipio", "-m",
        type=int,
        default=1302603,
        help="Municipality IBGE code (default: 1302603 - Manaus)",
    )

    parser.add_argument(
        "--producao",
        action="store_true",
        help="Use production environment (default: homologacao)",
    )

    parser.add_argument(
        "--cert-path",
        help="Certificate file path (overrides config and env)",
    )

    parser.add_argument(
        "--cert-password",
        help="Certificate password (overrides config and env)",
    )

    args = parser.parse_args()

    config = load_config(args.config)
    cert_path, cert_password = get_certificate_info(config, args)

    ambiente = Ambiente.PRODUCAO if args.producao else Ambiente.HOMOLOGACAO

    try:
        from cryptography.hazmat.primitives.serialization import (
            pkcs12, Encoding, PrivateFormat, NoEncryption
        )

    except ImportError:
        print("Error: cryptography library not installed")
        sys.exit(1)

    with open(cert_path, "rb") as f:
        pkcs12_data = f.read()

    private_key, certificate, _ = pkcs12.load_key_and_certificates(
        pkcs12_data, cert_password.encode()
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

        print(f"Environment: {ambiente.value.upper()}")
        print(f"Testing for municipality {args.municipio}")
        print("=" * 70)

        base_urls = [
            API_URLS[ambiente],
            PARAMETRIZACAO_URLS[ambiente],
        ]

        codes = ["040301", "040301000", "04.03.01"]

        for base in base_urls:
            print(f"\nBase: {base}")
            print("-" * 60)

            for code in codes:
                url = f"{base}/parametros_municipais/{args.municipio}/{code}"
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

                except Exception:
                    print(f"  {code}: {response.status_code} - {response.text[:60]}")

        print("\n\nChecking API swagger...")

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

                    except Exception:
                        pass

        client.close()

    finally:
        Path(cert_file_path).unlink(missing_ok=True)
        Path(key_file_path).unlink(missing_ok=True)


if __name__ == "__main__":
    main()
