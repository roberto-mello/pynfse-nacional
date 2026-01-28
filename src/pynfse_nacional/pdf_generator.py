"""
DANFSE PDF Generator - Generate PDF from NFSe XML.

This module generates DANFSE (Documento Auxiliar da NFS-e) PDFs from NFSe XML data,
following the official layout pattern.
"""

import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from .utils import decode_decompress, format_cnpj, format_cpf

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Image,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
except ImportError:
    raise ImportError(
        "reportlab is required for PDF generation. "
        "Install with: pip install pynfse-nacional[pdf]"
    )

try:
    import qrcode
except ImportError:
    raise ImportError(
        "qrcode is required for PDF generation. "
        "Install with: pip install pynfse-nacional[pdf]"
    )


# NFSe Nacional portal URL for validation
# tpc=1 means query by chave de acesso
NFSE_PORTAL_URL = "https://www.nfse.gov.br/ConsultaPublica"
NFSE_QR_URL = "https://www.nfse.gov.br/ConsultaPublica/?tpc=1&chave={chave}"


@dataclass
class HeaderConfig:
    """Configuration for custom header in DANFSE PDF."""

    image_path: Optional[str] = None
    title: str = ""
    subtitle: str = ""
    phone: str = ""
    email: str = ""

    def has_custom_header(self) -> bool:
        return bool(self.image_path or self.title)


@dataclass
class NFSeData:
    """Parsed NFSe data for PDF generation."""

    # NFS-e identification
    chave_acesso: str = ""
    numero_nfse: str = ""
    competencia: str = ""
    data_hora_emissao: str = ""

    # DPS identification
    numero_dps: str = ""
    serie_dps: str = ""
    data_hora_dps: str = ""

    # Emitente (Prestador)
    emit_cnpj: str = ""
    emit_cpf: str = ""
    emit_im: str = ""
    emit_nome: str = ""
    emit_telefone: str = ""
    emit_email: str = ""
    emit_endereco: str = ""
    emit_municipio: str = ""
    emit_uf: str = ""
    emit_cep: str = ""
    emit_simples_nacional: str = ""
    emit_regime_apuracao: str = ""

    # Tomador
    toma_cnpj: str = ""
    toma_cpf: str = ""
    toma_im: str = ""
    toma_nome: str = ""
    toma_telefone: str = ""
    toma_email: str = ""
    toma_endereco: str = ""
    toma_municipio: str = ""
    toma_uf: str = ""
    toma_cep: str = ""

    # Servico
    cod_trib_nac: str = ""
    desc_trib_nac: str = ""
    cod_trib_mun: str = ""
    desc_trib_mun: str = ""
    local_prestacao: str = ""
    pais_prestacao: str = ""
    descricao_servico: str = ""

    # Tributacao Municipal
    trib_issqn: str = ""
    pais_resultado: str = ""
    mun_incidencia: str = ""
    regime_especial: str = ""
    tipo_imunidade: str = ""
    suspensao_issqn: str = ""
    num_processo_suspensao: str = ""
    beneficio_municipal: str = ""

    # Valores
    valor_servico: str = ""
    desconto_incond: str = ""
    total_deducoes: str = ""
    calculo_bm: str = ""
    bc_issqn: str = ""
    aliquota: str = ""
    retencao_issqn: str = ""
    issqn_apurado: str = ""

    # Tributacao Federal
    irrf: str = ""
    cp: str = ""
    csll: str = ""
    pis: str = ""
    cofins: str = ""
    retencao_pis_cofins: str = ""
    total_trib_federal: str = ""

    # Totais
    desconto_cond: str = ""
    issqn_retido: str = ""
    irrf_cp_csll_retidos: str = ""
    pis_cofins_retidos: str = ""
    valor_liquido: str = ""

    # Totais aproximados tributos
    trib_federais: str = ""
    trib_estaduais: str = ""
    trib_municipais: str = ""

    # Informacoes complementares
    nbs: str = ""
    info_complementar: str = ""


# XML namespace
NS = {"nfse": "http://www.sped.fazenda.gov.br/nfse"}


def _get_text(element: Optional[ET.Element], path: str, default: str = "") -> str:
    """Get text from XML element with namespace handling."""

    if element is None:
        return default

    # Try with namespace
    el = element.find(path, NS)

    if el is None:
        # Try without namespace prefix in path
        simple_path = path.replace("nfse:", "")
        el = element.find(f".//{{{NS['nfse']}}}{simple_path.split('/')[-1]}")

    if el is not None and el.text:
        return el.text.strip()

    return default


def _format_datetime(dt_str: str) -> str:
    """Format ISO datetime to Brazilian format."""

    if not dt_str:
        return ""

    try:
        # Handle timezone offset
        dt_str = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", dt_str)
        dt = datetime.fromisoformat(dt_str.replace("Z", "+0000"))
        return dt.strftime("%d/%m/%Y %H:%M:%S")
    except (ValueError, TypeError):
        return dt_str


def _format_date(dt_str: str) -> str:
    """Format ISO date to Brazilian format."""

    if not dt_str:
        return ""

    try:
        dt = datetime.fromisoformat(dt_str.split("T")[0])
        return dt.strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return dt_str


def _format_phone(phone: str) -> str:
    """Format phone number."""

    if not phone:
        return ""

    phone = re.sub(r"[^0-9]", "", phone)

    if len(phone) == 11:
        return f"({phone[:2]}) {phone[2:7]}-{phone[7:]}"
    elif len(phone) == 10:
        return f"({phone[:2]}) {phone[2:6]}-{phone[6:]}"

    return phone


def _format_currency(value: str) -> str:
    """Format value as Brazilian currency."""

    if not value:
        return "-"

    try:
        val = float(value)
        return f"R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return value


def _format_cep(cep: str) -> str:
    """Format CEP."""

    if not cep:
        return ""

    cep = re.sub(r"[^0-9]", "", cep)

    if len(cep) == 8:
        return f"{cep[:5]}-{cep[5:]}"

    return cep


def _get_simples_nacional_desc(op_simp_nac: str) -> str:
    """Get Simples Nacional description."""

    descs = {
        "1": "Optante - Microempreendedor Individual (MEI)",
        "2": "Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP) - Excesso de Sublimite",
        "3": "Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP)",
        "4": "Nao Optante",
    }
    return descs.get(op_simp_nac, "-")


def _get_regime_apuracao_desc(reg_ap: str) -> str:
    """Get regime de apuracao description."""

    descs = {
        "1": "Regime de apuração dos tributos federais e municipal pelo Simples Nacional",
        "2": "Regime de apuração dos tributos federais pelo Simples Nacional e ISSQN por fora",
        "3": "Regime de apuração dos tributos federais e municipal pelo Simples Nacional",
    }
    return descs.get(reg_ap, "-")


def _get_trib_issqn_desc(trib: str) -> str:
    """Get tributacao ISSQN description."""

    descs = {
        "1": "Operacao Tributavel",
        "2": "Imunidade",
        "3": "Exportacao de Servico",
        "4": "Nao Incidencia",
    }
    return descs.get(trib, "-")


def _get_retencao_issqn_desc(ret: str) -> str:
    """Get retencao ISSQN description."""

    descs = {
        "1": "Nao Retido",
        "2": "Retido pelo Tomador",
        "3": "Retido pelo Intermediario",
    }
    return descs.get(ret, "-")


def parse_nfse_xml(xml_content: str) -> NFSeData:
    """Parse NFSe XML and extract data for PDF generation."""

    root = ET.fromstring(xml_content.encode("utf-8"))
    data = NFSeData()

    # Find infNFSe element
    inf_nfse = root.find(".//nfse:infNFSe", NS)

    if inf_nfse is None:
        inf_nfse = root.find(".//{http://www.sped.fazenda.gov.br/nfse}infNFSe")

    if inf_nfse is None:
        raise ValueError("Could not find infNFSe element in XML")

    # Extract chave from Id attribute
    nfse_id = inf_nfse.get("Id", "")

    if nfse_id.startswith("NFS"):
        data.chave_acesso = nfse_id[3:]
    else:
        data.chave_acesso = nfse_id

    # NFS-e data
    data.numero_nfse = _get_text(inf_nfse, ".//nfse:nNFSe")
    data.data_hora_emissao = _format_datetime(_get_text(inf_nfse, ".//nfse:dhProc"))

    # Find DPS element
    dps = inf_nfse.find(".//nfse:DPS", NS)

    if dps is None:
        dps = inf_nfse.find(".//{http://www.sped.fazenda.gov.br/nfse}DPS")

    if dps is not None:
        inf_dps = dps.find(".//nfse:infDPS", NS)

        if inf_dps is None:
            inf_dps = dps.find(".//{http://www.sped.fazenda.gov.br/nfse}infDPS")

        if inf_dps is not None:
            data.numero_dps = _get_text(inf_dps, ".//nfse:nDPS")
            data.serie_dps = _get_text(inf_dps, ".//nfse:serie")
            data.data_hora_dps = _format_datetime(_get_text(inf_dps, ".//nfse:dhEmi"))
            data.competencia = _format_date(_get_text(inf_dps, ".//nfse:dCompet"))

            # Prestador
            prest = inf_dps.find(".//nfse:prest", NS)

            if prest is None:
                prest = inf_dps.find(".//{http://www.sped.fazenda.gov.br/nfse}prest")

            if prest is not None:
                data.emit_cnpj = _get_text(prest, ".//nfse:CNPJ")
                data.emit_cpf = _get_text(prest, ".//nfse:CPF")
                data.emit_im = _get_text(prest, ".//nfse:IM")
                data.emit_telefone = _format_phone(_get_text(prest, ".//nfse:fone"))
                data.emit_email = _get_text(prest, ".//nfse:email")

                reg_trib = prest.find(".//nfse:regTrib", NS)

                if reg_trib is None:
                    reg_trib = prest.find(
                        ".//{http://www.sped.fazenda.gov.br/nfse}regTrib"
                    )

                if reg_trib is not None:
                    op_simp = _get_text(reg_trib, ".//nfse:opSimpNac")
                    data.emit_simples_nacional = _get_simples_nacional_desc(op_simp)
                    reg_ap = _get_text(reg_trib, ".//nfse:regApTribSN")
                    data.emit_regime_apuracao = _get_regime_apuracao_desc(reg_ap)

            # Tomador
            toma = inf_dps.find(".//nfse:toma", NS)

            if toma is None:
                toma = inf_dps.find(".//{http://www.sped.fazenda.gov.br/nfse}toma")

            if toma is not None:
                data.toma_cnpj = _get_text(toma, ".//nfse:CNPJ")
                data.toma_cpf = _get_text(toma, ".//nfse:CPF")
                data.toma_nome = _get_text(toma, ".//nfse:xNome")
                data.toma_im = _get_text(toma, ".//nfse:IM")
                data.toma_telefone = _format_phone(_get_text(toma, ".//nfse:fone"))
                data.toma_email = _get_text(toma, ".//nfse:email")

                # Tomador address
                toma_end = toma.find(".//nfse:end", NS)

                if toma_end is None:
                    toma_end = toma.find(".//{http://www.sped.fazenda.gov.br/nfse}end")

                if toma_end is not None:
                    lgr = _get_text(toma_end, ".//nfse:xLgr")
                    nro = _get_text(toma_end, ".//nfse:nro")
                    bairro = _get_text(toma_end, ".//nfse:xBairro")
                    data.toma_endereco = f"{lgr}, {nro}, {bairro}".strip(", ")
                    data.toma_cep = _format_cep(_get_text(toma_end, ".//nfse:CEP"))

                    # Get municipality code and try to resolve name
                    end_nac = toma_end.find(".//nfse:endNac", NS)

                    if end_nac is None:
                        end_nac = toma_end.find(
                            ".//{http://www.sped.fazenda.gov.br/nfse}endNac"
                        )

                    if end_nac is not None:
                        c_mun = _get_text(end_nac, ".//nfse:cMun")

                        if c_mun:
                            data.toma_municipio = c_mun

                        data.toma_uf = _get_text(end_nac, ".//nfse:UF")

            # Servico
            serv = inf_dps.find(".//nfse:serv", NS)

            if serv is None:
                serv = inf_dps.find(".//{http://www.sped.fazenda.gov.br/nfse}serv")

            if serv is not None:
                c_serv = serv.find(".//nfse:cServ", NS)

                if c_serv is None:
                    c_serv = serv.find(
                        ".//{http://www.sped.fazenda.gov.br/nfse}cServ"
                    )

                if c_serv is not None:
                    data.cod_trib_nac = _get_text(c_serv, ".//nfse:cTribNac")
                    data.cod_trib_mun = _get_text(c_serv, ".//nfse:cTribMun")
                    data.descricao_servico = _get_text(c_serv, ".//nfse:xDescServ")
                    data.nbs = _get_text(c_serv, ".//nfse:cNBS")

                loc_prest = serv.find(".//nfse:locPrest", NS)

                if loc_prest is None:
                    loc_prest = serv.find(
                        ".//{http://www.sped.fazenda.gov.br/nfse}locPrest"
                    )

                if loc_prest is not None:
                    c_loc = _get_text(loc_prest, ".//nfse:cLocPrestacao")

                    if c_loc:
                        data.local_prestacao = c_loc

            # Valores
            valores = inf_dps.find(".//nfse:valores", NS)

            if valores is None:
                valores = inf_dps.find(
                    ".//{http://www.sped.fazenda.gov.br/nfse}valores"
                )

            if valores is not None:
                v_serv_prest = valores.find(".//nfse:vServPrest", NS)

                if v_serv_prest is None:
                    v_serv_prest = valores.find(
                        ".//{http://www.sped.fazenda.gov.br/nfse}vServPrest"
                    )

                if v_serv_prest is not None:
                    data.valor_servico = _get_text(v_serv_prest, ".//nfse:vServ")

                trib = valores.find(".//nfse:trib", NS)

                if trib is None:
                    trib = valores.find(
                        ".//{http://www.sped.fazenda.gov.br/nfse}trib"
                    )

                if trib is not None:
                    trib_mun = trib.find(".//nfse:tribMun", NS)

                    if trib_mun is None:
                        trib_mun = trib.find(
                            ".//{http://www.sped.fazenda.gov.br/nfse}tribMun"
                        )

                    if trib_mun is not None:
                        trib_issqn = _get_text(trib_mun, ".//nfse:tribISSQN")
                        data.trib_issqn = _get_trib_issqn_desc(trib_issqn)
                        tp_ret = _get_text(trib_mun, ".//nfse:tpRetISSQN")
                        data.retencao_issqn = _get_retencao_issqn_desc(tp_ret)

    # Emitente from infNFSe (more complete data)
    emit = inf_nfse.find(".//nfse:emit", NS)

    if emit is None:
        emit = inf_nfse.find(".//{http://www.sped.fazenda.gov.br/nfse}emit")

    if emit is not None:
        if not data.emit_cnpj:
            data.emit_cnpj = _get_text(emit, ".//nfse:CNPJ")

        if not data.emit_cpf:
            data.emit_cpf = _get_text(emit, ".//nfse:CPF")

        if not data.emit_im:
            data.emit_im = _get_text(emit, ".//nfse:IM")

        data.emit_nome = _get_text(emit, ".//nfse:xNome")

        if not data.emit_telefone:
            data.emit_telefone = _format_phone(_get_text(emit, ".//nfse:fone"))

        if not data.emit_email:
            data.emit_email = _get_text(emit, ".//nfse:email")

        ender = emit.find(".//nfse:enderNac", NS)

        if ender is None:
            ender = emit.find(".//{http://www.sped.fazenda.gov.br/nfse}enderNac")

        if ender is not None:
            lgr = _get_text(ender, ".//nfse:xLgr")
            nro = _get_text(ender, ".//nfse:nro")
            bairro = _get_text(ender, ".//nfse:xBairro")
            data.emit_endereco = f"{lgr}, {nro}, {bairro}".strip(", ")
            data.emit_uf = _get_text(ender, ".//nfse:UF")
            data.emit_cep = _format_cep(_get_text(ender, ".//nfse:CEP"))

    # Get municipality names from infNFSe
    data.emit_municipio = _get_text(inf_nfse, ".//nfse:xLocEmi")
    data.mun_incidencia = _get_text(inf_nfse, ".//nfse:xLocIncid")

    if not data.local_prestacao:
        data.local_prestacao = _get_text(inf_nfse, ".//nfse:xLocPrestacao")

    # Valores from infNFSe
    valores_nfse = inf_nfse.find(".//nfse:valores", NS)

    if valores_nfse is None:
        valores_nfse = inf_nfse.find(".//{http://www.sped.fazenda.gov.br/nfse}valores")

    if valores_nfse is not None:
        data.bc_issqn = _get_text(valores_nfse, ".//nfse:vBC")
        data.aliquota = _get_text(valores_nfse, ".//nfse:pAliqAplic")
        data.issqn_apurado = _get_text(valores_nfse, ".//nfse:vISSQN")
        data.valor_liquido = _get_text(valores_nfse, ".//nfse:vLiq")

    # Set default value for valor_liquido if not set
    if not data.valor_liquido and data.valor_servico:
        data.valor_liquido = data.valor_servico

    return data


def _generate_qr_code(chave_acesso: str) -> io.BytesIO:
    """Generate QR code for NFSe validation."""

    url = NFSE_QR_URL.format(chave=chave_acesso)
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=3,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer


def generate_danfse_pdf(
    nfse_data: NFSeData,
    output_path: Optional[str] = None,
    header_config: Optional[HeaderConfig] = None,
) -> bytes:
    """
    Generate DANFSE PDF from NFSe data.

    Args:
        nfse_data: Parsed NFSe data
        output_path: Optional path to save PDF file
        header_config: Optional custom header configuration

    Returns:
        PDF content as bytes
    """

    if header_config is None:
        header_config = HeaderConfig()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=7 * mm,
        leftMargin=7 * mm,
        topMargin=7 * mm,
        bottomMargin=7 * mm,
    )

    styles = getSampleStyleSheet()

    # Compact styles for single-page A4
    style_title = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=11,
        alignment=1,
        spaceAfter=0,
        spaceBefore=0,
        leading=12,
    )

    style_subtitle = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=7,
        alignment=1,
    )

    style_header_right = ParagraphStyle(
        "HeaderRight",
        parent=styles["Normal"],
        fontSize=6,
        alignment=2,
        leading=8,
    )

    style_section = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=7,
        fontName="Helvetica-Bold",
        backColor=colors.lightgrey,
        spaceBefore=1 * mm,
        spaceAfter=0,
        leftIndent=1 * mm,
        leading=9,
    )

    style_label = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=5,
        fontName="Helvetica-Bold",
        textColor=colors.darkgrey,
        leading=6,
    )

    style_value = ParagraphStyle(
        "Value",
        parent=styles["Normal"],
        fontSize=7,
        leading=8,
    )

    style_small = ParagraphStyle(
        "Small",
        parent=styles["Normal"],
        fontSize=5,
        leading=6,
    )

    style_chave = ParagraphStyle(
        "Chave",
        parent=styles["Normal"],
        fontSize=6,
        fontName="Courier",
        leading=7,
    )

    elements = []

    # Generate QR code
    qr_buffer = _generate_qr_code(nfse_data.chave_acesso)
    qr_image = Image(qr_buffer, width=20 * mm, height=20 * mm)

    # Header section
    # Left: NFS-e logo/title, Center: DANFSe title, Right: Custom header or default

    if header_config.has_custom_header():
        if header_config.image_path and Path(header_config.image_path).exists():
            header_img = Image(header_config.image_path, width=30 * mm, height=15 * mm)
        else:
            header_img = Paragraph("", style_value)

        header_right_text = f"""
        <b>{header_config.title}</b><br/>
        {header_config.subtitle}<br/>
        {header_config.phone}<br/>
        {header_config.email}
        """
    else:
        header_img = Paragraph(
            "<b>NFS</b><font size='6'>e</font><br/>"
            "<font size='6'>Nota Fiscal de<br/>Servico eletronica</font>",
            style_value,
        )
        header_right_text = f"""
        <b>Prefeitura de {nfse_data.emit_municipio or 'Manaus'}</b><br/>
        Secretaria Municipal de Financas<br/>
        """

    header_right = Paragraph(header_right_text, style_header_right)

    header_table = Table(
        [
            [
                header_img,
                Paragraph(
                    "<b>DANFSe v1.0</b><br/>Documento Auxiliar da NFS-e",
                    style_title,
                ),
                [
                    header_right,
                    qr_image,
                    Paragraph(
                        "A autenticidade desta NFS-e pode ser verificada<br/>"
                        "pela leitura deste codigo QR ou pela consulta da<br/>"
                        "chave de acesso no portal nacional da NFS-e",
                        style_small,
                    ),
                ],
            ]
        ],
        colWidths=[35 * mm, 95 * mm, 66 * mm],
    )

    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ALIGN", (1, 0), (1, 0), "CENTER"),
                ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ]
        )
    )

    elements.append(header_table)
    elements.append(Spacer(1, 1 * mm))

    # Chave de Acesso
    chave_table = Table(
        [
            [
                Paragraph("<b>Chave de Acesso da NFS-e</b>", style_label),
            ],
            [
                Paragraph(nfse_data.chave_acesso, style_chave),
            ],
        ],
        colWidths=[196 * mm],
    )

    chave_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
            ]
        )
    )

    elements.append(chave_table)

    # NFS-e / DPS identification
    def make_field(label: str, value: str) -> list:
        return [
            Paragraph(f"<b>{label}</b>", style_label),
            Paragraph(value or "-", style_value),
        ]

    id_data = [
        [
            make_field("Numero da NFS-e", nfse_data.numero_nfse),
            make_field("Competencia da NFS-e", nfse_data.competencia),
            make_field("Data e Hora da emissao da NFS-e", nfse_data.data_hora_emissao),
        ],
        [
            make_field("Numero da DPS", nfse_data.numero_dps),
            make_field("Serie da DPS", nfse_data.serie_dps),
            make_field("Data e Hora da emissao da DPS", nfse_data.data_hora_dps),
        ],
    ]

    id_table = Table(
        id_data,
        colWidths=[65 * mm, 65 * mm, 66 * mm],
    )

    id_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(id_table)

    # EMITENTE section
    elements.append(Paragraph("EMITENTE DA NFS-e", style_section))

    emit_doc = (
        format_cnpj(nfse_data.emit_cnpj)
        if nfse_data.emit_cnpj
        else format_cpf(nfse_data.emit_cpf)
    )

    emit_data = [
        [
            make_field("Prestador do Servico", ""),
            make_field("CNPJ / CPF / NIF", emit_doc),
            make_field("Inscricao Municipal", nfse_data.emit_im.strip()),
            make_field("Telefone", nfse_data.emit_telefone),
        ],
        [
            make_field("Nome / Nome Empresarial", nfse_data.emit_nome),
            [],
            make_field("E-mail", nfse_data.emit_email),
            [],
        ],
        [
            make_field("Endereco", nfse_data.emit_endereco),
            [],
            make_field(
                "Municipio",
                f"{nfse_data.emit_municipio} - {nfse_data.emit_uf}"
                if nfse_data.emit_uf
                else nfse_data.emit_municipio,
            ),
            make_field("CEP", nfse_data.emit_cep),
        ],
        [
            make_field(
                "Simples Nacional na Data de Competencia",
                nfse_data.emit_simples_nacional,
            ),
            [],
            make_field(
                "Regime de Apuracao Tributaria pelo SN",
                nfse_data.emit_regime_apuracao,
            ),
            [],
        ],
    ]

    emit_table = Table(
        emit_data,
        colWidths=[49 * mm, 49 * mm, 49 * mm, 49 * mm],
    )

    emit_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("SPAN", (0, 1), (1, 1)),
                ("SPAN", (2, 1), (3, 1)),
                ("SPAN", (0, 2), (1, 2)),
                ("SPAN", (0, 3), (1, 3)),
                ("SPAN", (2, 3), (3, 3)),
            ]
        )
    )

    elements.append(emit_table)

    # TOMADOR section
    elements.append(Paragraph("TOMADOR DO SERVICO", style_section))

    toma_doc = (
        format_cnpj(nfse_data.toma_cnpj)
        if nfse_data.toma_cnpj
        else format_cpf(nfse_data.toma_cpf)
    )

    toma_data = [
        [
            make_field("CNPJ / CPF / NIF", toma_doc),
            make_field("Inscricao Municipal", nfse_data.toma_im),
            make_field("Telefone", nfse_data.toma_telefone),
        ],
        [
            make_field("Nome / Nome Empresarial", nfse_data.toma_nome),
            make_field("E-mail", nfse_data.toma_email),
            [],
        ],
        [
            make_field("Endereco", nfse_data.toma_endereco or "-"),
            make_field(
                "Municipio",
                f"{nfse_data.toma_municipio} - {nfse_data.toma_uf}"
                if nfse_data.toma_municipio and nfse_data.toma_uf
                else (nfse_data.toma_municipio or "-"),
            ),
            make_field("CEP", nfse_data.toma_cep or "-"),
        ],
    ]

    toma_table = Table(
        toma_data,
        colWidths=[65 * mm, 65 * mm, 66 * mm],
    )

    toma_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("SPAN", (1, 1), (2, 1)),
            ]
        )
    )

    elements.append(toma_table)

    # INTERMEDIARIO section
    elements.append(
        Paragraph(
            "INTERMEDIARIO DO SERVICO NAO IDENTIFICADO NA NFS-e",
            style_section,
        )
    )

    # SERVICO section
    elements.append(Paragraph("SERVICO PRESTADO", style_section))

    # Format tributacao codes
    cod_trib_nac_fmt = nfse_data.cod_trib_nac

    if cod_trib_nac_fmt and len(cod_trib_nac_fmt) == 6:
        cod_trib_nac_fmt = (
            f"{cod_trib_nac_fmt[:2]}.{cod_trib_nac_fmt[2:4]}.{cod_trib_nac_fmt[4:]}"
        )

    serv_data = [
        [
            make_field("Codigo de Tributacao Nacional", cod_trib_nac_fmt),
            make_field("Codigo de Tributacao Municipal", nfse_data.cod_trib_mun),
            make_field("Local da Prestacao", nfse_data.local_prestacao),
            make_field("Pais da Prestacao", nfse_data.pais_prestacao or "-"),
        ],
        [
            make_field("Descricao do Servico", nfse_data.descricao_servico),
            [],
            [],
            [],
        ],
    ]

    serv_table = Table(
        serv_data,
        colWidths=[49 * mm, 49 * mm, 49 * mm, 49 * mm],
    )

    serv_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("SPAN", (0, 1), (3, 1)),
            ]
        )
    )

    elements.append(serv_table)

    # TRIBUTACAO MUNICIPAL section
    elements.append(Paragraph("TRIBUTACAO MUNICIPAL", style_section))

    trib_mun_data = [
        [
            make_field("Tributacao do ISSQN", nfse_data.trib_issqn),
            make_field("Pais Resultado da Prestacao", nfse_data.pais_resultado or "-"),
            make_field("Municipio de Incidencia do ISSQN", nfse_data.mun_incidencia),
            make_field("Regime Especial de Tributacao", nfse_data.regime_especial or "Nenhum"),
        ],
        [
            make_field("Tipo de Imunidade", nfse_data.tipo_imunidade or "-"),
            make_field("Suspensao da Exigibilidade do ISSQN", nfse_data.suspensao_issqn or "Nao"),
            make_field("Numero Processo Suspensao", nfse_data.num_processo_suspensao or "-"),
            make_field("Beneficio Municipal", nfse_data.beneficio_municipal or "-"),
        ],
        [
            make_field("Valor do Servico", _format_currency(nfse_data.valor_servico)),
            make_field("Desconto Incondicionado", nfse_data.desconto_incond or "-"),
            make_field("Total Deducoes/Reducoes", nfse_data.total_deducoes or "-"),
            make_field("Calculo do BM", nfse_data.calculo_bm or "-"),
        ],
        [
            make_field("BC ISSQN", _format_currency(nfse_data.bc_issqn) if nfse_data.bc_issqn else "-"),
            make_field("Aliquota Aplicada", f"{nfse_data.aliquota}%" if nfse_data.aliquota else "-"),
            make_field("Retencao do ISSQN", nfse_data.retencao_issqn),
            make_field("ISSQN Apurado", _format_currency(nfse_data.issqn_apurado) if nfse_data.issqn_apurado else "-"),
        ],
    ]

    trib_mun_table = Table(
        trib_mun_data,
        colWidths=[49 * mm, 49 * mm, 49 * mm, 49 * mm],
    )

    trib_mun_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(trib_mun_table)

    # TRIBUTACAO FEDERAL section
    elements.append(Paragraph("TRIBUTACAO FEDERAL", style_section))

    trib_fed_data = [
        [
            make_field("IRRF", nfse_data.irrf or "-"),
            make_field("CP", nfse_data.cp or "-"),
            make_field("CSLL", nfse_data.csll or "-"),
            [],
        ],
        [
            make_field("PIS", nfse_data.pis or "-"),
            make_field("COFINS", nfse_data.cofins or "-"),
            make_field("Retencao do PIS/COFINS", nfse_data.retencao_pis_cofins or "-"),
            make_field("TOTAL TRIBUTACAO FEDERAL", nfse_data.total_trib_federal or "-"),
        ],
    ]

    trib_fed_table = Table(
        trib_fed_data,
        colWidths=[49 * mm, 49 * mm, 49 * mm, 49 * mm],
    )

    trib_fed_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(trib_fed_table)

    # VALOR TOTAL section
    elements.append(Paragraph("VALOR TOTAL DA NFS-E", style_section))

    valor_total_data = [
        [
            make_field("Valor do Servico", _format_currency(nfse_data.valor_servico)),
            make_field("Desconto Condicionado", _format_currency(nfse_data.desconto_cond) if nfse_data.desconto_cond else "R$"),
            make_field("Desconto Incondicionado", _format_currency(nfse_data.desconto_incond) if nfse_data.desconto_incond else "R$"),
            make_field("ISSQN Retido", nfse_data.issqn_retido or "-"),
        ],
        [
            make_field("IRRF, CP, CSLL - Retidos", _format_currency(nfse_data.irrf_cp_csll_retidos) if nfse_data.irrf_cp_csll_retidos else "R$ 0,00"),
            make_field("PIS/COFINS Retidos", nfse_data.pis_cofins_retidos or "-"),
            [],
            make_field("Valor Liquido da NFS-e", _format_currency(nfse_data.valor_liquido)),
        ],
    ]

    valor_total_table = Table(
        valor_total_data,
        colWidths=[49 * mm, 49 * mm, 49 * mm, 49 * mm],
    )

    valor_total_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(valor_total_table)

    # TOTAIS APROXIMADOS section
    elements.append(Paragraph("TOTAIS APROXIMADOS DOS TRIBUTOS", style_section))

    totais_data = [
        [
            make_field("Federais", nfse_data.trib_federais or "-"),
            make_field("Estaduais", nfse_data.trib_estaduais or "-"),
            make_field("Municipais", nfse_data.trib_municipais or "-"),
        ],
    ]

    totais_table = Table(
        totais_data,
        colWidths=[65 * mm, 65 * mm, 66 * mm],
    )

    totais_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(totais_table)

    # INFORMACOES COMPLEMENTARES section
    elements.append(Paragraph("INFORMACOES COMPLEMENTARES", style_section))

    info_text = ""

    if nfse_data.nbs:
        info_text += f"NBS: {nfse_data.nbs}"

    if nfse_data.info_complementar:
        if info_text:
            info_text += "<br/>"

        info_text += nfse_data.info_complementar

    if not info_text:
        info_text = "-"

    info_data = [
        [Paragraph(info_text, style_value)],
    ]

    info_table = Table(
        info_data,
        colWidths=[196 * mm],
    )

    info_table.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, colors.black),
                ("TOPPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0.5 * mm),
                ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
            ]
        )
    )

    elements.append(info_table)

    # Build PDF
    doc.build(elements)
    pdf_content = buffer.getvalue()
    buffer.close()

    if output_path:
        Path(output_path).write_bytes(pdf_content)

    return pdf_content


def generate_danfse_from_xml(
    xml_content: str,
    output_path: Optional[str] = None,
    header_config: Optional[HeaderConfig] = None,
) -> bytes:
    """
    Generate DANFSE PDF from NFSe XML content.

    Args:
        xml_content: NFSe XML string
        output_path: Optional path to save PDF file
        header_config: Optional custom header configuration

    Returns:
        PDF content as bytes
    """

    nfse_data = parse_nfse_xml(xml_content)
    return generate_danfse_pdf(nfse_data, output_path, header_config)


def generate_danfse_from_base64(
    nfse_xml_gzip_b64: str,
    output_path: Optional[str] = None,
    header_config: Optional[HeaderConfig] = None,
) -> bytes:
    """
    Generate DANFSE PDF from base64-encoded gzipped NFSe XML.

    Args:
        nfse_xml_gzip_b64: Base64-encoded gzipped NFSe XML (as returned by API)
        output_path: Optional path to save PDF file
        header_config: Optional custom header configuration

    Returns:
        PDF content as bytes
    """

    xml_content = decode_decompress(nfse_xml_gzip_b64)
    return generate_danfse_from_xml(xml_content, output_path, header_config)
