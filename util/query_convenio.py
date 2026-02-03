#!/usr/bin/env python3
"""Query if a municipality has joined the NFSe Nacional system.

This utility checks whether a given municipality has an agreement with the
national NFSe system by querying the SEFIN parametrization API.

Usage:
    python query_convenio.py --config issuer.ini --municipio 1302603

    # With different municipality:
    python query_convenio.py --config issuer.ini --municipio 3550308

    # JSON output for integration:
    python query_convenio.py --config issuer.ini --municipio 1302603 --json
"""

import argparse
import configparser
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional import NFSeClient, NFSeAPIError, NFSeCertificateError


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
        description="Query if a municipality has joined NFSe Nacional system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check if Manaus has joined:
  %(prog)s --config issuer.ini --municipio 1302603

  # Check Sao Paulo:
  %(prog)s --config issuer.ini --municipio 3550308

  # JSON output:
  %(prog)s --config issuer.ini --municipio 1302603 --json

Common municipality codes (IBGE):
  Sao Paulo/SP: 3550308
  Rio de Janeiro/RJ: 3304557
  Belo Horizonte/MG: 3106200
  Manaus/AM: 1302603
  Curitiba/PR: 4106902

Find codes at: https://www.ibge.gov.br/explica/codigos-dos-municipios.php
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
        required=True,
        help="Municipality IBGE code (7 digits)",
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

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format",
    )

    args = parser.parse_args()

    config = load_config(args.config)
    cert_path, cert_password = get_certificate_info(config, args)

    ambiente = "producao" if args.producao else "homologacao"

    if not args.json:
        print(f"Environment: {ambiente.upper()}")
        print(f"Municipality code: {args.municipio}")
        print()

    try:
        client = NFSeClient(
            cert_path=cert_path,
            cert_password=cert_password,
            ambiente=ambiente,
        )

        result = client.query_convenio_municipal(args.municipio)

        if args.json:
            output = {
                "success": True,
                "codigo_municipio": result.codigo_municipio,
                "aderido": result.aderido,
            }

            if result.raw_data:
                output["raw_data"] = result.raw_data

            print(json.dumps(output, indent=2))

        else:
            if result.aderido:
                print("MUNICIPALITY HAS JOINED")
                print(f"Code: {result.codigo_municipio}")

                if result.raw_data:
                    print(f"Data: {result.raw_data}")

            else:
                print("MUNICIPALITY HAS NOT JOINED")
                print("This municipality has not joined the NFSe Nacional system.")
                print()
                print("The service provider's municipality must have an agreement")
                print("with the national system to issue NFSe through this API.")

    except NFSeCertificateError as e:

        if args.json:
            print(json.dumps({"success": False, "error_type": "certificate", "error_message": str(e)}, indent=2))

        else:
            print(f"Certificate Error: {e}")

        sys.exit(1)

    except NFSeAPIError as e:

        if args.json:
            print(json.dumps({"success": False, "error_type": "api", "error_code": e.code, "error_message": e.message}, indent=2))

        else:
            print(f"API Error: {e.code} - {e.message}")

        sys.exit(1)

    except Exception as e:

        if args.json:
            print(json.dumps({"success": False, "error_type": "unknown", "error_message": str(e)}, indent=2))

        else:
            print(f"Error: {e}")

        sys.exit(1)


if __name__ == "__main__":
    main()
