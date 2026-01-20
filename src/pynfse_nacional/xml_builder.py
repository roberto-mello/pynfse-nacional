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
        root = ET.Element("DPS", versao="1.01", xmlns=self.NAMESPACE)

        infDPS = ET.SubElement(root, "infDPS", Id=dps.id_dps)

        # NOTE: Based on real NFSe XML, tpAmb in DPS is always "1" for production data
        # even when submitting to homologacao environment (which uses ambGer in response)
        tpAmb = "1" if self.ambiente == Ambiente.PRODUCAO else "2"
        ET.SubElement(infDPS, "tpAmb").text = tpAmb
        ET.SubElement(infDPS, "dhEmi").text = dps.data_emissao.strftime("%Y-%m-%dT%H:%M:%S-03:00")
        ET.SubElement(infDPS, "verAplic").text = "pynfse-1.0"
        ET.SubElement(infDPS, "serie").text = dps.serie
        ET.SubElement(infDPS, "nDPS").text = str(dps.numero)
        ET.SubElement(infDPS, "dCompet").text = dps.data_emissao.strftime("%Y-%m-%d")
        ET.SubElement(infDPS, "tpEmit").text = "1"
        ET.SubElement(infDPS, "cLocEmi").text = str(dps.prestador.endereco.codigo_municipio)

        self._add_prestador(infDPS, dps)
        self._add_tomador(infDPS, dps)
        self._add_servico(infDPS, dps)
        self._add_valores(infDPS, dps)

        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _add_prestador(self, parent: ET.Element, dps: DPS) -> None:
        prest = ET.SubElement(parent, "prest")
        ET.SubElement(prest, "CNPJ").text = dps.prestador.cnpj

        # IM padded with spaces to 15 chars as seen in real NFSe
        im_padded = dps.prestador.inscricao_municipal.rjust(15)
        ET.SubElement(prest, "IM").text = im_padded

        if dps.prestador.telefone:
            ET.SubElement(prest, "fone").text = dps.prestador.telefone

        if dps.prestador.email:
            ET.SubElement(prest, "email").text = dps.prestador.email

        regTrib = ET.SubElement(prest, "regTrib")

        # opSimpNac: 1=Não Optante, 2=MEI, 3=ME/EPP
        ET.SubElement(regTrib, "opSimpNac").text = "3" if dps.optante_simples else "1"

        # regApTribSN: Required for Simples Nacional ME/EPP
        # 1=Tributos federais e municipal pelo SN
        # 2=Tributos federais pelo SN, ISSQN por fora
        # 3=Tributos federais e municipal por fora do SN
        if dps.optante_simples:
            ET.SubElement(regTrib, "regApTribSN").text = "1"

        ET.SubElement(regTrib, "regEspTrib").text = self._map_regime_especial(dps.regime_tributario)

    def _add_tomador(self, parent: ET.Element, dps: DPS) -> None:
        toma = ET.SubElement(parent, "toma")

        if dps.tomador.cpf:
            ET.SubElement(toma, "CPF").text = dps.tomador.cpf
        elif dps.tomador.cnpj:
            ET.SubElement(toma, "CNPJ").text = dps.tomador.cnpj

        ET.SubElement(toma, "xNome").text = dps.tomador.razao_social

        if dps.tomador.endereco:
            end = ET.SubElement(toma, "end")
            endNac = ET.SubElement(end, "endNac")
            ET.SubElement(endNac, "cMun").text = str(dps.tomador.endereco.codigo_municipio)
            ET.SubElement(endNac, "CEP").text = dps.tomador.endereco.cep

            ET.SubElement(end, "xLgr").text = dps.tomador.endereco.logradouro
            ET.SubElement(end, "nro").text = dps.tomador.endereco.numero

            if dps.tomador.endereco.complemento:
                ET.SubElement(end, "xCpl").text = dps.tomador.endereco.complemento

            ET.SubElement(end, "xBairro").text = dps.tomador.endereco.bairro

    def _add_servico(self, parent: ET.Element, dps: DPS) -> None:
        serv = ET.SubElement(parent, "serv")

        locPrest = ET.SubElement(serv, "locPrest")
        ET.SubElement(locPrest, "cLocPrestacao").text = str(dps.prestador.endereco.codigo_municipio)

        cServ = ET.SubElement(serv, "cServ")
        codigo = dps.servico.codigo_lc116.replace(".", "")
        ET.SubElement(cServ, "cTribNac").text = codigo.zfill(6)

        # cTribMun - municipal code (optional but used in real NFSe)
        if hasattr(dps.servico, 'codigo_tributacao_municipal') and dps.servico.codigo_tributacao_municipal:
            ET.SubElement(cServ, "cTribMun").text = dps.servico.codigo_tributacao_municipal

        ET.SubElement(cServ, "xDescServ").text = dps.servico.discriminacao

        # cNBS - NBS code (optional but used in real NFSe)
        if hasattr(dps.servico, 'codigo_nbs') and dps.servico.codigo_nbs:
            ET.SubElement(cServ, "cNBS").text = dps.servico.codigo_nbs

    def _add_valores(self, parent: ET.Element, dps: DPS) -> None:
        valores = ET.SubElement(parent, "valores")

        vServPrest = ET.SubElement(valores, "vServPrest")
        ET.SubElement(vServPrest, "vServ").text = self._format_decimal(dps.servico.valor_servicos)

        trib = ET.SubElement(valores, "trib")

        tribMun = ET.SubElement(trib, "tribMun")
        ET.SubElement(tribMun, "tribISSQN").text = "1"

        # tpRetISSQN: 1=Não Retido, 2=Retido Tomador, 3=Retido Intermediário
        ET.SubElement(tribMun, "tpRetISSQN").text = "2" if dps.servico.iss_retido else "1"

        totTrib = ET.SubElement(trib, "totTrib")

        # For Simples Nacional, use pTotTribSN with estimated tax percentage
        if dps.optante_simples:
            # Default to a reasonable Simples Nacional tax estimate
            aliquota_sn = getattr(dps.servico, 'aliquota_simples', None) or Decimal("18.83")
            ET.SubElement(totTrib, "pTotTribSN").text = self._format_decimal(aliquota_sn)
        else:
            # For non-Simples, use percentage breakdown
            pTotTrib = ET.SubElement(totTrib, "pTotTrib")
            ET.SubElement(pTotTrib, "pTotTribFed").text = "0"
            ET.SubElement(pTotTrib, "pTotTribEst").text = "0"
            ET.SubElement(pTotTrib, "pTotTribMun").text = "0"

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

    def _map_regime_especial(self, regime: str) -> str:
        """Map special tax regime. 0 = none."""
        mapping = {
            "mei": "4",
            "cooperativa": "1",
            "estimativa": "2",
            "sociedade_profissionais": "3",
            "microempresario_individual": "4",
            "microempresa_epp": "5",
        }

        return mapping.get(regime, "0")
