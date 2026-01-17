from decimal import Decimal
from xml.etree import ElementTree as ET

from .constants import Ambiente
from .models import DPS


class XMLBuilder:
    """Build DPS XML for NFSe Nacional submission."""

    NAMESPACE = "http://www.sped.fazenda.gov.br/nfse"
    NAMESPACE_MAP = {"": NAMESPACE}

    def __init__(self, ambiente: Ambiente = Ambiente.HOMOLOGACAO):
        self.ambiente = ambiente

    def build_dps(self, dps: DPS) -> str:
        """Build DPS XML from model."""
        root = ET.Element("DPS", xmlns=self.NAMESPACE)

        infDPS = ET.SubElement(root, "infDPS", Id=dps.id_dps)

        tpAmb = "1" if self.ambiente == Ambiente.PRODUCAO else "2"
        ET.SubElement(infDPS, "tpAmb").text = tpAmb
        ET.SubElement(infDPS, "dhEmi").text = dps.data_emissao.isoformat()
        ET.SubElement(infDPS, "verAplic").text = "medsimples-1.0"
        ET.SubElement(infDPS, "serie").text = dps.serie
        ET.SubElement(infDPS, "nDPS").text = str(dps.numero)
        ET.SubElement(infDPS, "dCompet").text = dps.competencia

        self._add_prestador(infDPS, dps)
        self._add_tomador(infDPS, dps)
        self._add_servico(infDPS, dps)
        self._add_valores(infDPS, dps)

        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _add_prestador(self, parent: ET.Element, dps: DPS) -> None:
        prest = ET.SubElement(parent, "prest")
        ET.SubElement(prest, "CNPJ").text = dps.prestador.cnpj
        ET.SubElement(prest, "IM").text = dps.prestador.inscricao_municipal
        ET.SubElement(prest, "xNome").text = dps.prestador.razao_social

        if dps.prestador.nome_fantasia:
            ET.SubElement(prest, "xFant").text = dps.prestador.nome_fantasia

        self._add_endereco(prest, dps.prestador.endereco, "enderPrest")

        if dps.prestador.email:
            ET.SubElement(prest, "email").text = dps.prestador.email

        if dps.prestador.telefone:
            ET.SubElement(prest, "fone").text = dps.prestador.telefone

        ET.SubElement(prest, "regTrib").text = self._map_regime(dps.regime_tributario)
        ET.SubElement(prest, "optSN").text = "1" if dps.optante_simples else "2"
        ET.SubElement(prest, "incCult").text = "1" if dps.incentivador_cultural else "2"

    def _add_tomador(self, parent: ET.Element, dps: DPS) -> None:
        toma = ET.SubElement(parent, "toma")

        if dps.tomador.cpf:
            ET.SubElement(toma, "CPF").text = dps.tomador.cpf
        elif dps.tomador.cnpj:
            ET.SubElement(toma, "CNPJ").text = dps.tomador.cnpj

        ET.SubElement(toma, "xNome").text = dps.tomador.razao_social

        if dps.tomador.endereco:
            self._add_endereco(toma, dps.tomador.endereco, "enderToma")

        if dps.tomador.email:
            ET.SubElement(toma, "email").text = dps.tomador.email

        if dps.tomador.telefone:
            ET.SubElement(toma, "fone").text = dps.tomador.telefone

    def _add_endereco(self, parent: ET.Element, endereco, tag_name: str) -> None:
        ender = ET.SubElement(parent, tag_name)
        ET.SubElement(ender, "xLgr").text = endereco.logradouro
        ET.SubElement(ender, "nro").text = endereco.numero

        if endereco.complemento:
            ET.SubElement(ender, "xCpl").text = endereco.complemento

        ET.SubElement(ender, "xBairro").text = endereco.bairro
        ET.SubElement(ender, "cMun").text = str(endereco.codigo_municipio)
        ET.SubElement(ender, "UF").text = endereco.uf
        ET.SubElement(ender, "CEP").text = endereco.cep

    def _add_servico(self, parent: ET.Element, dps: DPS) -> None:
        serv = ET.SubElement(parent, "serv")
        ET.SubElement(serv, "cServ").text = dps.servico.codigo_lc116
        ET.SubElement(serv, "CNAE").text = dps.servico.codigo_cnae
        ET.SubElement(serv, "xDescServ").text = dps.servico.discriminacao
        ET.SubElement(serv, "cMunInc").text = str(
            dps.prestador.endereco.codigo_municipio
        )

    def _add_valores(self, parent: ET.Element, dps: DPS) -> None:
        valores = ET.SubElement(parent, "valores")
        ET.SubElement(valores, "vServPrest").text = self._format_decimal(
            dps.servico.valor_servicos
        )
        ET.SubElement(valores, "vDeducoes").text = self._format_decimal(
            dps.servico.valor_deducoes
        )
        ET.SubElement(valores, "vPIS").text = self._format_decimal(
            dps.servico.valor_pis
        )
        ET.SubElement(valores, "vCOFINS").text = self._format_decimal(
            dps.servico.valor_cofins
        )
        ET.SubElement(valores, "vINSS").text = self._format_decimal(
            dps.servico.valor_inss
        )
        ET.SubElement(valores, "vIR").text = self._format_decimal(dps.servico.valor_ir)
        ET.SubElement(valores, "vCSLL").text = self._format_decimal(
            dps.servico.valor_csll
        )

        if dps.servico.iss_retido:
            ET.SubElement(valores, "indISSRet").text = "1"
        else:
            ET.SubElement(valores, "indISSRet").text = "2"

        if dps.servico.aliquota_iss:
            ET.SubElement(valores, "aliqISS").text = self._format_decimal(
                dps.servico.aliquota_iss
            )

    def _format_decimal(self, value: Decimal) -> str:
        return f"{value:.2f}"

    def _map_regime(self, regime: str) -> str:
        mapping = {
            "simples_nacional": "1",
            "simples_excesso": "2",
            "normal": "3",
            "mei": "4",
        }
        return mapping.get(regime, "3")
