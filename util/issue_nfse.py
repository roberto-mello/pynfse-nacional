#!/usr/bin/env python3
"""Issue NFSe Nacional from command line.

This utility helps you issue electronic service invoices (NFSe) through
Brazil's national NFSe system (Padrao Nacional).

Usage:
    # Using config file for issuer (prestador) data:
    python issue_nfse.py --config issuer.ini \\
        --tomador-cpf 12345678901 \\
        --tomador-nome "Joao da Silva" \\
        --servico-codigo "4.03.03" \\
        --servico-descricao "Consultoria em tecnologia" \\
        --servico-valor 1500.00

    # With full tomador address:
    python issue_nfse.py --config issuer.ini \\
        --tomador-cnpj 99888777000166 \\
        --tomador-nome "Empresa Cliente LTDA" \\
        --tomador-logradouro "Av. Paulista" \\
        --tomador-numero "1000" \\
        --tomador-bairro "Bela Vista" \\
        --tomador-municipio 3550308 \\
        --tomador-uf SP \\
        --tomador-cep 01310100 \\
        --servico-codigo "4.03.03" \\
        --servico-descricao "Desenvolvimento de software" \\
        --servico-valor 5000.00

    # Production environment:
    python issue_nfse.py --config issuer.ini --producao \\
        --tomador-cpf 12345678901 \\
        --tomador-nome "Cliente Final" \\
        --servico-codigo "4.03.03" \\
        --servico-descricao "Servico prestado" \\
        --servico-valor 200.00

    # Generate PDF after issuing:
    python issue_nfse.py --config issuer.ini \\
        --tomador-cpf 12345678901 \\
        --tomador-nome "Cliente" \\
        --servico-codigo "4.03.03" \\
        --servico-descricao "Servico" \\
        --servico-valor 100.00 \\
        --gerar-pdf --pdf-output ./notas/

Examples using environment variables for certificate:
    export NFSE_CERT_PATH=/path/to/cert.pfx
    export NFSE_CERT_PASSWORD=senha123
    python issue_nfse.py --config issuer.ini ...
"""

import argparse
import configparser
import json
import os
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

# Add parent directory to path for imports when running directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pynfse_nacional import NFSeClient, NFSeAPIError, NFSeCertificateError
from pynfse_nacional.models import DPS, Prestador, Tomador, Servico, Endereco


def load_config(config_path: str) -> configparser.ConfigParser:
    """Load issuer configuration from INI file."""
    if not Path(config_path).exists():
        print(f"Error: Config file not found: {config_path}")
        print("Copy issuer.example.ini to issuer.ini and fill in your details.")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    return config


def get_certificate_info(config: configparser.ConfigParser, args) -> tuple[str, str]:
    """Get certificate path and password from config, args, or environment."""
    # Priority: args > environment > config file
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
        print("Use --cert-path, NFSE_CERT_PATH env var, or set in config file.")
        sys.exit(1)

    if not cert_password:
        print("Error: Certificate password not provided.")
        print("Use --cert-password, NFSE_CERT_PASSWORD env var, or set in config file.")
        sys.exit(1)

    if not Path(cert_path).exists():
        print(f"Error: Certificate file not found: {cert_path}")
        sys.exit(1)

    return cert_path, cert_password


def build_prestador(config: configparser.ConfigParser) -> Prestador:
    """Build Prestador from config file."""
    endereco = Endereco(
        logradouro=config.get("endereco", "logradouro"),
        numero=config.get("endereco", "numero"),
        complemento=config.get("endereco", "complemento", fallback=None),
        bairro=config.get("endereco", "bairro"),
        codigo_municipio=config.getint("endereco", "codigo_municipio"),
        uf=config.get("endereco", "uf"),
        cep=config.get("endereco", "cep"),
    )

    return Prestador(
        cnpj=config.get("prestador", "cnpj"),
        inscricao_municipal=config.get("prestador", "inscricao_municipal"),
        razao_social=config.get("prestador", "razao_social"),
        nome_fantasia=config.get("prestador", "nome_fantasia", fallback=None),
        endereco=endereco,
        email=config.get("prestador", "email", fallback=None),
        telefone=config.get("prestador", "telefone", fallback=None),
    )


def build_tomador(args) -> Tomador:
    """Build Tomador from command line arguments."""
    if not args.tomador_cpf and not args.tomador_cnpj:
        print("Error: Either --tomador-cpf or --tomador-cnpj is required.")
        sys.exit(1)

    if not args.tomador_nome:
        print("Error: --tomador-nome is required.")
        sys.exit(1)

    endereco = None

    if args.tomador_logradouro:
        if not all([args.tomador_bairro, args.tomador_municipio, args.tomador_uf, args.tomador_cep]):
            print("Error: When providing tomador address, all fields are required:")
            print("  --tomador-logradouro, --tomador-numero, --tomador-bairro,")
            print("  --tomador-municipio, --tomador-uf, --tomador-cep")
            sys.exit(1)

        endereco = Endereco(
            logradouro=args.tomador_logradouro,
            numero=args.tomador_numero or "S/N",
            complemento=args.tomador_complemento,
            bairro=args.tomador_bairro,
            codigo_municipio=args.tomador_municipio,
            uf=args.tomador_uf,
            cep=args.tomador_cep,
        )

    return Tomador(
        cpf=args.tomador_cpf,
        cnpj=args.tomador_cnpj,
        razao_social=args.tomador_nome,
        endereco=endereco,
        email=args.tomador_email,
        telefone=args.tomador_telefone,
    )


def build_servico(args, config: configparser.ConfigParser) -> Servico:
    """Build Servico from command line arguments and config."""
    if not args.servico_codigo:
        print("Error: --servico-codigo is required (e.g., '4.03.03').")
        sys.exit(1)

    if not args.servico_descricao:
        print("Error: --servico-descricao is required.")
        sys.exit(1)

    if args.servico_valor is None:
        print("Error: --servico-valor is required.")
        sys.exit(1)

    # Get aliquota_simples from args or config
    aliquota_simples = None

    if args.aliquota_simples:
        aliquota_simples = Decimal(str(args.aliquota_simples))
    elif config.has_option("tributacao", "aliquota_simples"):
        aliquota_simples = Decimal(config.get("tributacao", "aliquota_simples"))

    return Servico(
        codigo_lc116=args.servico_codigo,
        codigo_cnae=args.servico_cnae,
        codigo_tributacao_municipal=args.servico_codigo_municipal,
        codigo_nbs=args.servico_nbs,
        discriminacao=args.servico_descricao,
        valor_servicos=Decimal(str(args.servico_valor)),
        iss_retido=args.iss_retido,
        aliquota_iss=Decimal(str(args.aliquota_iss)) if args.aliquota_iss else None,
        aliquota_simples=aliquota_simples,
    )


def get_next_numero(config: configparser.ConfigParser, config_path: str) -> int:
    """Get next DPS number and increment in config file."""
    numero = config.getint("nfse", "proximo_numero", fallback=1)

    # Update config file with next number
    config.set("nfse", "proximo_numero", str(numero + 1))

    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)

    return numero


def generate_pdf(nfse_xml_b64: str, chave_acesso: str, output_dir: str, header_config=None):
    """Generate DANFSE PDF from NFSe XML."""
    try:
        from pynfse_nacional.pdf_generator import generate_danfse_from_base64, HeaderConfig
    except ImportError:
        print("Warning: PDF generation requires optional dependencies.")
        print("Install with: pip install pynfse-nacional[pdf]")
        return None

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pdf_path = output_path / f"nfse_{chave_acesso}.pdf"

    generate_danfse_from_base64(
        nfse_xml_b64,
        output_path=str(pdf_path),
        header_config=header_config,
    )

    return pdf_path


def main():
    parser = argparse.ArgumentParser(
        description="Issue NFSe Nacional (Brazilian electronic service invoice)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with config file:
  %(prog)s --config issuer.ini \\
      --tomador-cpf 12345678901 --tomador-nome "Cliente" \\
      --servico-codigo "4.03.03" --servico-descricao "Consultoria" \\
      --servico-valor 1000.00

  # Production environment:
  %(prog)s --config issuer.ini --producao \\
      --tomador-cpf 12345678901 --tomador-nome "Cliente" \\
      --servico-codigo "4.03.03" --servico-descricao "Consultoria" \\
      --servico-valor 1000.00

  # With PDF generation:
  %(prog)s --config issuer.ini --gerar-pdf --pdf-output ./notas/ ...

Environment variables:
  NFSE_CERT_PATH      Path to certificate (overrides config)
  NFSE_CERT_PASSWORD  Certificate password (overrides config)
""",
    )

    # Config and environment
    parser.add_argument(
        "--config", "-c",
        required=True,
        help="Path to issuer configuration file (INI format)",
    )

    parser.add_argument(
        "--producao",
        action="store_true",
        help="Use production environment (default: homologacao)",
    )

    # Certificate options (override config/env)
    parser.add_argument(
        "--cert-path",
        help="Path to certificate file (overrides config and env)",
    )

    parser.add_argument(
        "--cert-password",
        help="Certificate password (overrides config and env)",
    )

    # Tomador (service recipient) options
    tomador_group = parser.add_argument_group("Tomador (service recipient)")

    tomador_group.add_argument(
        "--tomador-cpf",
        help="Tomador CPF (11 digits)",
    )

    tomador_group.add_argument(
        "--tomador-cnpj",
        help="Tomador CNPJ (14 digits)",
    )

    tomador_group.add_argument(
        "--tomador-nome",
        required=True,
        help="Tomador name (razao social)",
    )

    tomador_group.add_argument(
        "--tomador-email",
        help="Tomador email",
    )

    tomador_group.add_argument(
        "--tomador-telefone",
        help="Tomador phone",
    )

    # Tomador address (optional)
    tomador_addr_group = parser.add_argument_group("Tomador address (optional)")

    tomador_addr_group.add_argument(
        "--tomador-logradouro",
        help="Street name",
    )

    tomador_addr_group.add_argument(
        "--tomador-numero",
        help="Street number",
    )

    tomador_addr_group.add_argument(
        "--tomador-complemento",
        help="Address complement",
    )

    tomador_addr_group.add_argument(
        "--tomador-bairro",
        help="Neighborhood",
    )

    tomador_addr_group.add_argument(
        "--tomador-municipio",
        type=int,
        help="IBGE municipality code (7 digits)",
    )

    tomador_addr_group.add_argument(
        "--tomador-uf",
        help="State (2 letters)",
    )

    tomador_addr_group.add_argument(
        "--tomador-cep",
        help="ZIP code (8 digits)",
    )

    # Servico (service) options
    servico_group = parser.add_argument_group("Servico (service details)")

    servico_group.add_argument(
        "--servico-codigo",
        required=True,
        help="LC 116 service code (e.g., '4.03.03' for IT consulting)",
    )

    servico_group.add_argument(
        "--servico-descricao",
        required=True,
        help="Service description (discriminacao)",
    )

    servico_group.add_argument(
        "--servico-valor",
        type=float,
        required=True,
        help="Service value in BRL",
    )

    servico_group.add_argument(
        "--servico-cnae",
        help="CNAE code (optional)",
    )

    servico_group.add_argument(
        "--servico-codigo-municipal",
        help="Municipal tax code (optional)",
    )

    servico_group.add_argument(
        "--servico-nbs",
        help="NBS code (optional)",
    )

    # Tax options
    tax_group = parser.add_argument_group("Tax options")

    tax_group.add_argument(
        "--iss-retido",
        action="store_true",
        help="ISS retained by tomador",
    )

    tax_group.add_argument(
        "--aliquota-iss",
        type=float,
        help="ISS rate (percentage)",
    )

    tax_group.add_argument(
        "--aliquota-simples",
        type=float,
        help="Simples Nacional total tax rate (overrides config)",
    )

    # DPS options
    dps_group = parser.add_argument_group("DPS options")

    dps_group.add_argument(
        "--numero",
        type=int,
        help="DPS number (default: auto-increment from config)",
    )

    dps_group.add_argument(
        "--serie",
        help="DPS series (default: from config or '900')",
    )

    dps_group.add_argument(
        "--competencia",
        help="Competencia YYYY-MM (default: current month)",
    )

    # Output options
    output_group = parser.add_argument_group("Output options")

    output_group.add_argument(
        "--gerar-pdf",
        action="store_true",
        help="Generate DANFSE PDF after issuing",
    )

    output_group.add_argument(
        "--pdf-output",
        default=".",
        help="Output directory for PDF (default: current directory)",
    )

    output_group.add_argument(
        "--json",
        action="store_true",
        help="Output result as JSON",
    )

    output_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Minimal output (only errors and essential info)",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Get certificate info
    cert_path, cert_password = get_certificate_info(config, args)

    # Determine environment
    ambiente = "producao" if args.producao else "homologacao"

    if not args.quiet:
        print(f"Environment: {ambiente.upper()}")
        print(f"Certificate: {cert_path}")
        print()

    # Build models
    prestador = build_prestador(config)
    tomador = build_tomador(args)
    servico = build_servico(args, config)

    # Get DPS number
    numero = args.numero or get_next_numero(config, args.config)
    serie = args.serie or config.get("nfse", "serie", fallback="900")

    # Get competencia
    if args.competencia:
        competencia = args.competencia
    else:
        competencia = datetime.now().strftime("%Y-%m")

    # Get tax regime info from config
    optante_simples = config.getboolean("tributacao", "optante_simples", fallback=False)
    regime_tributario = config.get("tributacao", "regime_tributario", fallback="normal")

    # Build DPS
    dps = DPS(
        serie=serie,
        numero=numero,
        competencia=competencia,
        data_emissao=datetime.now(),
        prestador=prestador,
        tomador=tomador,
        servico=servico,
        regime_tributario=regime_tributario,
        optante_simples=optante_simples,
        incentivador_cultural=False,
    )

    if not args.quiet:
        print(f"Issuing NFSe:")
        print(f"  DPS Number: {numero}")
        print(f"  Serie: {serie}")
        print(f"  Competencia: {competencia}")
        print(f"  Prestador: {prestador.razao_social} ({prestador.cnpj})")
        print(f"  Tomador: {tomador.razao_social} ({tomador.cpf or tomador.cnpj})")
        print(f"  Servico: {servico.codigo_lc116} - R$ {servico.valor_servicos:.2f}")
        print(f"  Descricao: {servico.discriminacao[:50]}...")
        print()

    # Create client and submit
    try:
        client = NFSeClient(
            cert_path=cert_path,
            cert_password=cert_password,
            ambiente=ambiente,
            timeout=60.0,
        )

        if not args.quiet:
            print("Submitting DPS to SEFIN...")

        response = client.submit_dps(dps)

        if response.success:
            result = {
                "success": True,
                "chave_acesso": response.chave_acesso,
                "nfse_number": response.nfse_number,
                "ambiente": ambiente,
                "dps_numero": numero,
                "dps_serie": serie,
            }

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("SUCCESS!")
                print(f"  Chave de Acesso: {response.chave_acesso}")
                print(f"  NFSe Number: {response.nfse_number}")

                if response.nfse_xml_gzip_b64:
                    result["has_xml"] = True

            # Generate PDF if requested
            if args.gerar_pdf and response.nfse_xml_gzip_b64:
                if not args.quiet:
                    print()
                    print("Generating PDF...")

                try:
                    pdf_path = generate_pdf(
                        response.nfse_xml_gzip_b64,
                        response.chave_acesso,
                        args.pdf_output,
                    )

                    if pdf_path:
                        result["pdf_path"] = str(pdf_path)

                        if not args.json:
                            print(f"  PDF saved: {pdf_path}")

                except Exception as e:
                    if not args.json:
                        print(f"  Warning: Failed to generate PDF: {e}")

                    result["pdf_error"] = str(e)

            if args.json and result != {}:
                print(json.dumps(result, indent=2))

        else:
            result = {
                "success": False,
                "error_code": response.error_code,
                "error_message": response.error_message,
            }

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("FAILED!")
                print(f"  Error Code: {response.error_code}")
                print(f"  Error Message: {response.error_message}")

            sys.exit(1)

    except NFSeCertificateError as e:
        error_result = {
            "success": False,
            "error_type": "certificate",
            "error_message": str(e),
        }

        if args.json:
            print(json.dumps(error_result, indent=2))
        else:
            print(f"Certificate Error: {e}")

        sys.exit(1)

    except NFSeAPIError as e:
        error_result = {
            "success": False,
            "error_type": "api",
            "error_code": e.code,
            "error_message": e.message,
        }

        if e.status_code:
            error_result["status_code"] = e.status_code

        if args.json:
            print(json.dumps(error_result, indent=2))
        else:
            print(f"API Error: {e.code} - {e.message}")

            if e.status_code:
                print(f"  HTTP Status: {e.status_code}")

        sys.exit(1)

    except Exception as e:
        error_result = {
            "success": False,
            "error_type": "unknown",
            "error_message": str(e),
        }

        if args.json:
            print(json.dumps(error_result, indent=2))
        else:
            print(f"Error: {e}")

        sys.exit(1)


if __name__ == "__main__":
    main()
