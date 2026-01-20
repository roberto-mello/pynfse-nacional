"""Tests for XMLBuilder."""

import warnings
from datetime import datetime
from decimal import Decimal
from xml.etree import ElementTree as ET

import pytest

from pynfse_nacional.constants import Ambiente
from pynfse_nacional.models import DPS, Endereco, Prestador, Servico, Tomador
from pynfse_nacional.xml_builder import XMLBuilder

NS = {"nfse": "http://www.sped.fazenda.gov.br/nfse"}


@pytest.fixture
def sample_endereco():
    """Sample address for testing."""
    return Endereco(
        logradouro="Rua Teste",
        numero="100",
        complemento="Sala 1",
        bairro="Centro",
        codigo_municipio=3509502,
        uf="SP",
        cep="13000000",
    )


@pytest.fixture
def sample_prestador(sample_endereco):
    """Sample service provider for testing."""
    return Prestador(
        cnpj="11222333000181",
        inscricao_municipal="12345",
        razao_social="Clinica Teste LTDA",
        nome_fantasia="Clinica Teste",
        endereco=sample_endereco,
        email="contato@clinica.com",
        telefone="1999999999",
    )


@pytest.fixture
def sample_tomador(sample_endereco):
    """Sample service taker (patient) for testing."""
    return Tomador(
        cpf="12345678901",
        razao_social="Joao Silva",
        email="paciente@email.com",
        telefone="1988888888",
        endereco=sample_endereco,
    )


@pytest.fixture
def sample_servico():
    """Sample service for testing."""
    return Servico(
        codigo_cnae="8630503",
        codigo_lc116="4.03.03",
        codigo_tributacao_municipal="123456",
        codigo_nbs="1.0101.01.00",
        discriminacao="Consulta medica",
        valor_servicos=Decimal("500.00"),
        iss_retido=False,
        aliquota_iss=Decimal("2.00"),
        aliquota_simples=Decimal("15.50"),
        valor_deducoes=Decimal("0.00"),
        valor_pis=Decimal("0.00"),
        valor_cofins=Decimal("0.00"),
        valor_inss=Decimal("0.00"),
        valor_ir=Decimal("0.00"),
        valor_csll=Decimal("0.00"),
    )


@pytest.fixture
def sample_dps(sample_prestador, sample_tomador, sample_servico):
    """Sample DPS for testing."""
    return DPS(
        serie="900",
        numero=1,
        competencia="2026-01",
        data_emissao=datetime(2026, 1, 15, 10, 30, 0),
        prestador=sample_prestador,
        tomador=sample_tomador,
        servico=sample_servico,
        regime_tributario="simples_nacional",
        optante_simples=True,
        incentivador_cultural=False,
    )


class TestXMLBuilderInit:
    """Tests for XMLBuilder initialization."""

    def test_default_ambiente_is_homologacao(self):
        """Builder should default to homologacao ambiente."""
        builder = XMLBuilder()

        assert builder.ambiente == Ambiente.HOMOLOGACAO

    def test_can_set_producao_ambiente(self):
        """Builder should accept producao ambiente."""
        builder = XMLBuilder(ambiente=Ambiente.PRODUCAO)

        assert builder.ambiente == Ambiente.PRODUCAO


class TestXMLBuilderBuildDPSId:
    """Tests for _build_dps_id method."""

    def test_build_dps_id_format(self, sample_dps):
        """_build_dps_id should return correct format."""
        builder = XMLBuilder()

        dps_id = builder._build_dps_id(sample_dps)

        # Format: DPS + cLocEmi(7) + tpInsc(1) + CNPJ(14) + serie(5) + nDPS(15)
        # cLocEmi: 3509502 (7 digits)
        # tpInsc: 2 (CNPJ)
        # CNPJ: 11222333000181 (14 digits)
        # serie: 00900 (5 digits, zero-padded)
        # nDPS: 000000000000001 (15 digits, zero-padded)
        expected = "DPS350950221122233300018100900000000000000001"

        assert dps_id == expected
        assert len(dps_id) == 45

    def test_build_dps_id_with_custom_values(self, sample_dps):
        """_build_dps_id should handle different values."""
        sample_dps.numero = 12345
        sample_dps.serie = "NF"
        builder = XMLBuilder()

        dps_id = builder._build_dps_id(sample_dps)

        assert "000NF" in dps_id
        assert "000000000012345" in dps_id


class TestXMLBuilderBuildDPS:
    """Tests for build_dps method."""

    def test_build_dps_returns_valid_xml(self, sample_dps):
        """build_dps should return valid XML string."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)

        assert xml_str.startswith("<?xml version='1.0' encoding='utf-8'?>")

        root = ET.fromstring(xml_str)

        assert root.tag == "{http://www.sped.fazenda.gov.br/nfse}DPS"

    def test_build_dps_includes_namespace(self, sample_dps):
        """build_dps should include correct namespace."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)

        assert "http://www.sped.fazenda.gov.br/nfse" in xml_str

    def test_build_dps_sets_homolog_ambiente(self, sample_dps):
        """build_dps should set tpAmb=2 for homologacao."""
        builder = XMLBuilder(ambiente=Ambiente.HOMOLOGACAO)

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)
        tpAmb = infDPS.find("nfse:tpAmb", NS)

        assert tpAmb.text == "2"

    def test_build_dps_sets_prod_ambiente(self, sample_dps):
        """build_dps should set tpAmb=1 for producao."""
        builder = XMLBuilder(ambiente=Ambiente.PRODUCAO)

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)
        tpAmb = infDPS.find("nfse:tpAmb", NS)

        assert tpAmb.text == "1"

    def test_build_dps_generates_id_when_not_provided(self, sample_dps):
        """infDPS should have auto-generated Id when id_dps is None."""
        sample_dps.id_dps = None
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)

        assert infDPS.attrib.get("Id").startswith("DPS")
        assert len(infDPS.attrib.get("Id")) == 45

    def test_build_dps_uses_provided_id(self, sample_dps):
        """infDPS should use provided id_dps when set."""
        sample_dps.id_dps = "DPS350950221122233300018100900000000000000001"
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)

        assert infDPS.attrib.get("Id") == "DPS350950221122233300018100900000000000000001"

    def test_build_dps_includes_emission_date_with_timezone(self, sample_dps):
        """build_dps should include dhEmi with ISO format and timezone."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)
        dhEmi = infDPS.find("nfse:dhEmi", NS)

        assert dhEmi.text == "2026-01-15T10:30:00-03:00"

    def test_build_dps_includes_serie_and_numero(self, sample_dps):
        """build_dps should include serie and nDPS."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)
        serie = infDPS.find("nfse:serie", NS)
        nDPS = infDPS.find("nfse:nDPS", NS)

        assert serie.text == "900"
        assert nDPS.text == "1"

    def test_build_dps_includes_dcompet_as_date(self, sample_dps):
        """build_dps should include dCompet as YYYY-MM-DD."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)
        dCompet = infDPS.find("nfse:dCompet", NS)

        assert dCompet.text == "2026-01-15"

    def test_build_dps_includes_cloc_emi(self, sample_dps):
        """build_dps should include cLocEmi with municipality code."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)
        cLocEmi = infDPS.find("nfse:cLocEmi", NS)

        assert cLocEmi.text == "3509502"


class TestXMLBuilderPrestador:
    """Tests for prestador (service provider) section."""

    def test_build_dps_includes_prestador_cnpj(self, sample_dps):
        """Prestador section should include CNPJ."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        cnpj = prest.find("nfse:CNPJ", NS)

        assert cnpj.text == "11222333000181"

    def test_build_dps_includes_prestador_im_padded(self, sample_dps):
        """Prestador section should include IM right-padded to 15 chars."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        im = prest.find("nfse:IM", NS)

        assert im.text == "          12345"
        assert len(im.text) == 15

    def test_build_dps_includes_prestador_fone(self, sample_dps):
        """Prestador section should include fone."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        fone = prest.find("nfse:fone", NS)

        assert fone.text == "1999999999"

    def test_build_dps_includes_prestador_email(self, sample_dps):
        """Prestador section should include email."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        email = prest.find("nfse:email", NS)

        assert email.text == "contato@clinica.com"

    def test_build_dps_includes_regtrib(self, sample_dps):
        """Prestador section should include regTrib element."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        regTrib = prest.find("nfse:regTrib", NS)

        assert regTrib is not None

    def test_build_dps_opsimpnac_for_simples(self, sample_dps):
        """opSimpNac should be 3 for optante simples (ME/EPP)."""
        sample_dps.optante_simples = True
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        opSimpNac = root.find("nfse:infDPS/nfse:prest/nfse:regTrib/nfse:opSimpNac", NS)

        assert opSimpNac.text == "3"

    def test_build_dps_opsimpnac_for_non_simples(self, sample_dps):
        """opSimpNac should be 1 for non-optante."""
        sample_dps.optante_simples = False
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        opSimpNac = root.find("nfse:infDPS/nfse:prest/nfse:regTrib/nfse:opSimpNac", NS)

        assert opSimpNac.text == "1"

    def test_build_dps_regaptribsn_for_simples(self, sample_dps):
        """regApTribSN should be 1 for Simples Nacional."""
        sample_dps.optante_simples = True
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        regApTribSN = root.find("nfse:infDPS/nfse:prest/nfse:regTrib/nfse:regApTribSN", NS)

        assert regApTribSN.text == "1"

    def test_build_dps_regaptribsn_absent_for_non_simples(self, sample_dps):
        """regApTribSN should not be present for non-Simples."""
        sample_dps.optante_simples = False
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        regApTribSN = root.find("nfse:infDPS/nfse:prest/nfse:regTrib/nfse:regApTribSN", NS)

        assert regApTribSN is None

    def test_build_dps_regesptrib_default(self, sample_dps):
        """regEspTrib should default to 0."""
        sample_dps.regime_tributario = "unknown"
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        regEspTrib = root.find("nfse:infDPS/nfse:prest/nfse:regTrib/nfse:regEspTrib", NS)

        assert regEspTrib.text == "0"

    def test_build_dps_regesptrib_mei(self, sample_dps):
        """regEspTrib should be 4 for MEI."""
        sample_dps.regime_tributario = "mei"
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        regEspTrib = root.find("nfse:infDPS/nfse:prest/nfse:regTrib/nfse:regEspTrib", NS)

        assert regEspTrib.text == "4"


class TestXMLBuilderTomador:
    """Tests for tomador (service taker) section."""

    def test_build_dps_includes_tomador_cpf(self, sample_dps):
        """Tomador section should include CPF when provided."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        toma = root.find("nfse:infDPS/nfse:toma", NS)
        cpf = toma.find("nfse:CPF", NS)

        assert cpf.text == "12345678901"

    def test_build_dps_includes_tomador_cnpj(self, sample_dps):
        """Tomador section should include CNPJ when CPF is None."""
        sample_dps.tomador.cpf = None
        sample_dps.tomador.cnpj = "99888777000166"
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        toma = root.find("nfse:infDPS/nfse:toma", NS)
        cnpj = toma.find("nfse:CNPJ", NS)
        cpf = toma.find("nfse:CPF", NS)

        assert cnpj.text == "99888777000166"
        assert cpf is None

    def test_build_dps_includes_tomador_xnome(self, sample_dps):
        """Tomador section should include xNome."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        toma = root.find("nfse:infDPS/nfse:toma", NS)
        xNome = toma.find("nfse:xNome", NS)

        assert xNome.text == "Joao Silva"

    def test_build_dps_includes_tomador_address(self, sample_dps):
        """Tomador section should include address with endNac."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        end = root.find("nfse:infDPS/nfse:toma/nfse:end", NS)
        endNac = end.find("nfse:endNac", NS)

        assert endNac.find("nfse:cMun", NS).text == "3509502"
        assert endNac.find("nfse:CEP", NS).text == "13000000"
        assert end.find("nfse:xLgr", NS).text == "Rua Teste"
        assert end.find("nfse:nro", NS).text == "100"
        assert end.find("nfse:xCpl", NS).text == "Sala 1"
        assert end.find("nfse:xBairro", NS).text == "Centro"

    def test_build_dps_omits_tomador_address_if_none(self, sample_dps):
        """Tomador should omit end if address is None."""
        sample_dps.tomador.endereco = None
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        toma = root.find("nfse:infDPS/nfse:toma", NS)
        end = toma.find("nfse:end", NS)

        assert end is None


class TestXMLBuilderServico:
    """Tests for servico section."""

    def test_build_dps_includes_loc_prest(self, sample_dps):
        """Servico section should include locPrest."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        locPrest = root.find("nfse:infDPS/nfse:serv/nfse:locPrest", NS)
        cLocPrestacao = locPrest.find("nfse:cLocPrestacao", NS)

        assert cLocPrestacao.text == "3509502"

    def test_build_dps_includes_ctribnac(self, sample_dps):
        """Servico section should include cTribNac (LC116 code without dots, 6 digits)."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        cServ = root.find("nfse:infDPS/nfse:serv/nfse:cServ", NS)
        cTribNac = cServ.find("nfse:cTribNac", NS)

        # "4.03.03" -> "40303" -> "040303" (6 digits)
        assert cTribNac.text == "040303"

    def test_build_dps_includes_ctribmun(self, sample_dps):
        """Servico section should include cTribMun when provided."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        cServ = root.find("nfse:infDPS/nfse:serv/nfse:cServ", NS)
        cTribMun = cServ.find("nfse:cTribMun", NS)

        assert cTribMun.text == "123456"

    def test_build_dps_omits_ctribmun_when_none(self, sample_dps):
        """Servico section should omit cTribMun when not provided."""
        sample_dps.servico.codigo_tributacao_municipal = None
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        cServ = root.find("nfse:infDPS/nfse:serv/nfse:cServ", NS)
        cTribMun = cServ.find("nfse:cTribMun", NS)

        assert cTribMun is None

    def test_build_dps_includes_xdescserv(self, sample_dps):
        """Servico section should include xDescServ."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        cServ = root.find("nfse:infDPS/nfse:serv/nfse:cServ", NS)
        xDescServ = cServ.find("nfse:xDescServ", NS)

        assert xDescServ.text == "Consulta medica"

    def test_build_dps_includes_cnbs(self, sample_dps):
        """Servico section should include cNBS when provided."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        cServ = root.find("nfse:infDPS/nfse:serv/nfse:cServ", NS)
        cNBS = cServ.find("nfse:cNBS", NS)

        assert cNBS.text == "1.0101.01.00"

    def test_build_dps_omits_cnbs_when_none(self, sample_dps):
        """Servico section should omit cNBS when not provided."""
        sample_dps.servico.codigo_nbs = None
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        cServ = root.find("nfse:infDPS/nfse:serv/nfse:cServ", NS)
        cNBS = cServ.find("nfse:cNBS", NS)

        assert cNBS is None


class TestXMLBuilderValores:
    """Tests for valores (values) section."""

    def test_build_dps_includes_vserv(self, sample_dps):
        """Valores section should include vServ."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        vServPrest = root.find("nfse:infDPS/nfse:valores/nfse:vServPrest", NS)
        vServ = vServPrest.find("nfse:vServ", NS)

        assert vServ.text == "500.00"

    def test_build_dps_includes_tribissqn(self, sample_dps):
        """Valores section should include tribISSQN=1."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        tribMun = root.find("nfse:infDPS/nfse:valores/nfse:trib/nfse:tribMun", NS)
        tribISSQN = tribMun.find("nfse:tribISSQN", NS)

        assert tribISSQN.text == "1"

    def test_build_dps_tpretissqn_not_retained(self, sample_dps):
        """tpRetISSQN should be 1 when ISS not retained."""
        sample_dps.servico.iss_retido = False
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        tribMun = root.find("nfse:infDPS/nfse:valores/nfse:trib/nfse:tribMun", NS)
        tpRetISSQN = tribMun.find("nfse:tpRetISSQN", NS)

        assert tpRetISSQN.text == "1"

    def test_build_dps_tpretissqn_retained(self, sample_dps):
        """tpRetISSQN should be 2 when ISS retained."""
        sample_dps.servico.iss_retido = True
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        tribMun = root.find("nfse:infDPS/nfse:valores/nfse:trib/nfse:tribMun", NS)
        tpRetISSQN = tribMun.find("nfse:tpRetISSQN", NS)

        assert tpRetISSQN.text == "2"

    def test_build_dps_ptottribsn_for_simples(self, sample_dps):
        """pTotTribSN should be set for Simples Nacional."""
        sample_dps.optante_simples = True
        sample_dps.servico.aliquota_simples = Decimal("15.50")
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        totTrib = root.find("nfse:infDPS/nfse:valores/nfse:trib/nfse:totTrib", NS)
        pTotTribSN = totTrib.find("nfse:pTotTribSN", NS)

        assert pTotTribSN.text == "15.50"

    def test_build_dps_ptottribsn_default_with_warning(self, sample_dps):
        """pTotTribSN should default to 18.83 with warning when not provided."""
        sample_dps.optante_simples = True
        sample_dps.servico.aliquota_simples = None
        builder = XMLBuilder()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            xml_str = builder.build_dps(sample_dps)
            root = ET.fromstring(xml_str)

            totTrib = root.find("nfse:infDPS/nfse:valores/nfse:trib/nfse:totTrib", NS)
            pTotTribSN = totTrib.find("nfse:pTotTribSN", NS)

            assert pTotTribSN.text == "18.83"
            assert len(w) == 1
            assert "aliquota_simples not provided" in str(w[0].message)

    def test_build_dps_ptottrib_for_non_simples(self, sample_dps):
        """pTotTrib should be set for non-Simples Nacional."""
        sample_dps.optante_simples = False
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        totTrib = root.find("nfse:infDPS/nfse:valores/nfse:trib/nfse:totTrib", NS)
        pTotTrib = totTrib.find("nfse:pTotTrib", NS)

        assert pTotTrib.find("nfse:pTotTribFed", NS).text == "0"
        assert pTotTrib.find("nfse:pTotTribEst", NS).text == "0"
        assert pTotTrib.find("nfse:pTotTribMun", NS).text == "0"
