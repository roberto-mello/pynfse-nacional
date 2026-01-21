#!/usr/bin/env python3
"""Emitir NFSe Nacional via linha de comando.

Este utilitario ajuda a emitir notas fiscais de servicos eletronicas (NFSe)
atraves do sistema nacional de NFSe do Brasil (Padrao Nacional).

Uso:
    # Usando arquivo de config para dados do emissor (prestador):
    python issue_nfse.py --config issuer.ini \\
        --tomador-cpf 12345678901 \\
        --tomador-nome "Joao da Silva" \\
        --servico-codigo "4.03.03" \\
        --servico-descricao "Consultoria em tecnologia" \\
        --servico-valor 1500.00

    # Com endereco completo do tomador:
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

    # Ambiente de producao:
    python issue_nfse.py --config issuer.ini --producao \\
        --tomador-cpf 12345678901 \\
        --tomador-nome "Cliente Final" \\
        --servico-codigo "4.03.03" \\
        --servico-descricao "Servico prestado" \\
        --servico-valor 200.00

    # Gerar PDF apos emissao:
    python issue_nfse.py --config issuer.ini \\
        --tomador-cpf 12345678901 \\
        --tomador-nome "Cliente" \\
        --servico-codigo "4.03.03" \\
        --servico-descricao "Servico" \\
        --servico-valor 100.00 \\
        --gerar-pdf --pdf-output ./notas/

Exemplos usando variaveis de ambiente para o certificado:
    export NFSE_CERT_PATH=/caminho/para/cert.pfx
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
    """Carrega configuracao do emissor de arquivo INI."""

    if not Path(config_path).exists():
        print(f"Erro: Arquivo de configuracao nao encontrado: {config_path}")
        print("Copie issuer.example.ini para issuer.ini e preencha seus dados.")
        sys.exit(1)

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    return config


def get_certificate_info(config: configparser.ConfigParser, args) -> tuple[str, str]:
    """Obtem caminho e senha do certificado de config, args ou ambiente."""

    # Prioridade: args > ambiente > arquivo de config
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
        print("Erro: Caminho do certificado nao fornecido.")
        print("Use --cert-path, variavel NFSE_CERT_PATH ou configure no arquivo.")
        sys.exit(1)

    if not cert_password:
        print("Erro: Senha do certificado nao fornecida.")
        print("Use --cert-password, variavel NFSE_CERT_PASSWORD ou configure no arquivo.")
        sys.exit(1)

    if not Path(cert_path).exists():
        print(f"Erro: Arquivo de certificado nao encontrado: {cert_path}")
        sys.exit(1)

    return cert_path, cert_password


def build_prestador(config: configparser.ConfigParser) -> Prestador:
    """Constroi Prestador a partir do arquivo de config."""

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
    """Constroi Tomador a partir dos argumentos de linha de comando."""

    if not args.tomador_cpf and not args.tomador_cnpj:
        print("Erro: --tomador-cpf ou --tomador-cnpj e obrigatorio.")
        sys.exit(1)

    if not args.tomador_nome:
        print("Erro: --tomador-nome e obrigatorio.")
        sys.exit(1)

    endereco = None

    if args.tomador_logradouro:

        if not all([args.tomador_bairro, args.tomador_municipio, args.tomador_uf, args.tomador_cep]):
            print("Erro: Ao fornecer endereco do tomador, todos os campos sao obrigatorios:")
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
    """Constroi Servico a partir dos argumentos e config."""

    if not args.servico_codigo:
        print("Erro: --servico-codigo e obrigatorio (ex: '4.03.03').")
        sys.exit(1)

    if not args.servico_descricao:
        print("Erro: --servico-descricao e obrigatorio.")
        sys.exit(1)

    if args.servico_valor is None:
        print("Erro: --servico-valor e obrigatorio.")
        sys.exit(1)

    # Obtem aliquota_simples de args ou config
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
    """Obtem proximo numero de DPS e incrementa no arquivo de config."""

    numero = config.getint("nfse", "proximo_numero", fallback=1)

    # Atualiza arquivo de config com proximo numero
    config.set("nfse", "proximo_numero", str(numero + 1))

    with open(config_path, "w", encoding="utf-8") as f:
        config.write(f)

    return numero


def generate_pdf(nfse_xml_b64: str, chave_acesso: str, output_dir: str, header_config=None):
    """Gera PDF do DANFSE a partir do XML da NFSe."""

    try:
        from pynfse_nacional.pdf_generator import generate_danfse_from_base64, HeaderConfig

    except ImportError:
        print("Aviso: Geracao de PDF requer dependencias opcionais.")
        print("Instale com: pip install pynfse-nacional[pdf]")
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
        description="Emitir NFSe Nacional (nota fiscal de servicos eletronica brasileira)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Uso basico com arquivo de config:
  %(prog)s --config issuer.ini \\
      --tomador-cpf 12345678901 --tomador-nome "Cliente" \\
      --servico-codigo "4.03.03" --servico-descricao "Consultoria" \\
      --servico-valor 1000.00

  # Ambiente de producao:
  %(prog)s --config issuer.ini --producao \\
      --tomador-cpf 12345678901 --tomador-nome "Cliente" \\
      --servico-codigo "4.03.03" --servico-descricao "Consultoria" \\
      --servico-valor 1000.00

  # Com geracao de PDF:
  %(prog)s --config issuer.ini --gerar-pdf --pdf-output ./notas/ ...

Variaveis de ambiente:
  NFSE_CERT_PATH      Caminho do certificado (sobrescreve config)
  NFSE_CERT_PASSWORD  Senha do certificado (sobrescreve config)
""",
    )

    # Config e ambiente
    parser.add_argument(
        "--config", "-c",
        required=True,
        help="Caminho para arquivo de configuracao do emissor (formato INI)",
    )

    parser.add_argument(
        "--producao",
        action="store_true",
        help="Usar ambiente de producao (padrao: homologacao)",
    )

    # Opcoes de certificado (sobrescrevem config/env)
    parser.add_argument(
        "--cert-path",
        help="Caminho para arquivo do certificado (sobrescreve config e env)",
    )

    parser.add_argument(
        "--cert-password",
        help="Senha do certificado (sobrescreve config e env)",
    )

    # Opcoes do tomador (destinatario do servico)
    tomador_group = parser.add_argument_group("Tomador (destinatario do servico)")

    tomador_group.add_argument(
        "--tomador-cpf",
        help="CPF do tomador (11 digitos)",
    )

    tomador_group.add_argument(
        "--tomador-cnpj",
        help="CNPJ do tomador (14 digitos)",
    )

    tomador_group.add_argument(
        "--tomador-nome",
        required=True,
        help="Nome do tomador (razao social)",
    )

    tomador_group.add_argument(
        "--tomador-email",
        help="Email do tomador",
    )

    tomador_group.add_argument(
        "--tomador-telefone",
        help="Telefone do tomador",
    )

    # Endereco do tomador (opcional)
    tomador_addr_group = parser.add_argument_group("Endereco do tomador (opcional)")

    tomador_addr_group.add_argument(
        "--tomador-logradouro",
        help="Nome da rua",
    )

    tomador_addr_group.add_argument(
        "--tomador-numero",
        help="Numero",
    )

    tomador_addr_group.add_argument(
        "--tomador-complemento",
        help="Complemento do endereco",
    )

    tomador_addr_group.add_argument(
        "--tomador-bairro",
        help="Bairro",
    )

    tomador_addr_group.add_argument(
        "--tomador-municipio",
        type=int,
        help="Codigo do municipio IBGE (7 digitos)",
    )

    tomador_addr_group.add_argument(
        "--tomador-uf",
        help="Estado (2 letras)",
    )

    tomador_addr_group.add_argument(
        "--tomador-cep",
        help="CEP (8 digitos)",
    )

    # Opcoes do servico
    servico_group = parser.add_argument_group("Servico (detalhes do servico)")

    servico_group.add_argument(
        "--servico-codigo",
        required=True,
        help="Codigo LC 116 do servico (ex: '4.03.03' para consultoria em TI)",
    )

    servico_group.add_argument(
        "--servico-descricao",
        required=True,
        help="Descricao do servico (discriminacao)",
    )

    servico_group.add_argument(
        "--servico-valor",
        type=float,
        required=True,
        help="Valor do servico em BRL",
    )

    servico_group.add_argument(
        "--servico-cnae",
        help="Codigo CNAE (opcional)",
    )

    servico_group.add_argument(
        "--servico-codigo-municipal",
        help="Codigo de tributacao municipal (opcional)",
    )

    servico_group.add_argument(
        "--servico-nbs",
        help="Codigo NBS (opcional)",
    )

    # Opcoes de tributos
    tax_group = parser.add_argument_group("Opcoes de tributos")

    tax_group.add_argument(
        "--iss-retido",
        action="store_true",
        help="ISS retido pelo tomador",
    )

    tax_group.add_argument(
        "--aliquota-iss",
        type=float,
        help="Aliquota do ISS (percentual)",
    )

    tax_group.add_argument(
        "--aliquota-simples",
        type=float,
        help="Aliquota total do Simples Nacional (sobrescreve config)",
    )

    # Opcoes da DPS
    dps_group = parser.add_argument_group("Opcoes da DPS")

    dps_group.add_argument(
        "--numero",
        type=int,
        help="Numero da DPS (padrao: auto-incremento do config)",
    )

    dps_group.add_argument(
        "--serie",
        help="Serie da DPS (padrao: do config ou '900')",
    )

    dps_group.add_argument(
        "--competencia",
        help="Competencia YYYY-MM (padrao: mes atual)",
    )

    # Opcoes de saida
    output_group = parser.add_argument_group("Opcoes de saida")

    output_group.add_argument(
        "--gerar-pdf",
        action="store_true",
        help="Gerar PDF do DANFSE apos emissao",
    )

    output_group.add_argument(
        "--pdf-output",
        default=".",
        help="Diretorio de saida do PDF (padrao: diretorio atual)",
    )

    output_group.add_argument(
        "--json",
        action="store_true",
        help="Saida do resultado em formato JSON",
    )

    output_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Saida minima (apenas erros e informacoes essenciais)",
    )

    args = parser.parse_args()

    # Carrega configuracao
    config = load_config(args.config)

    # Obtem informacoes do certificado
    cert_path, cert_password = get_certificate_info(config, args)

    # Determina ambiente
    ambiente = "producao" if args.producao else "homologacao"

    if not args.quiet:
        print(f"Ambiente: {ambiente.upper()}")
        print(f"Certificado: {cert_path}")
        print()

    # Constroi modelos
    prestador = build_prestador(config)
    tomador = build_tomador(args)
    servico = build_servico(args, config)

    # Obtem numero da DPS
    numero = args.numero or get_next_numero(config, args.config)
    serie = args.serie or config.get("nfse", "serie", fallback="900")

    # Obtem competencia
    if args.competencia:
        competencia = args.competencia
    else:
        competencia = datetime.now().strftime("%Y-%m")

    # Obtem informacoes de regime tributario do config
    optante_simples = config.getboolean("tributacao", "optante_simples", fallback=False)
    regime_tributario = config.get("tributacao", "regime_tributario", fallback="normal")

    # Constroi DPS
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
        print(f"Emitindo NFSe:")
        print(f"  Numero DPS: {numero}")
        print(f"  Serie: {serie}")
        print(f"  Competencia: {competencia}")
        print(f"  Prestador: {prestador.razao_social} ({prestador.cnpj})")
        print(f"  Tomador: {tomador.razao_social} ({tomador.cpf or tomador.cnpj})")
        print(f"  Servico: {servico.codigo_lc116} - R$ {servico.valor_servicos:.2f}")
        print(f"  Descricao: {servico.discriminacao[:50]}...")
        print()

    # Cria cliente e envia
    try:
        client = NFSeClient(
            cert_path=cert_path,
            cert_password=cert_password,
            ambiente=ambiente,
            timeout=60.0,
        )

        if not args.quiet:
            print("Enviando DPS para SEFIN...")

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
                print("SUCESSO!")
                print(f"  Chave de Acesso: {response.chave_acesso}")
                print(f"  Numero NFSe: {response.nfse_number}")

                if response.nfse_xml_gzip_b64:
                    result["has_xml"] = True

            # Gera PDF se solicitado
            if args.gerar_pdf and response.nfse_xml_gzip_b64:

                if not args.quiet:
                    print()
                    print("Gerando PDF...")

                try:
                    pdf_path = generate_pdf(
                        response.nfse_xml_gzip_b64,
                        response.chave_acesso,
                        args.pdf_output,
                    )

                    if pdf_path:
                        result["pdf_path"] = str(pdf_path)

                        if not args.json:
                            print(f"  PDF salvo: {pdf_path}")

                except Exception as e:

                    if not args.json:
                        print(f"  Aviso: Falha ao gerar PDF: {e}")

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
                print("FALHOU!")
                print(f"  Codigo do Erro: {response.error_code}")
                print(f"  Mensagem de Erro: {response.error_message}")

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
            print(f"Erro de Certificado: {e}")

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
            print(f"Erro da API: {e.code} - {e.message}")

            if e.status_code:
                print(f"  Status HTTP: {e.status_code}")

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
            print(f"Erro: {e}")

        sys.exit(1)


if __name__ == "__main__":
    main()
