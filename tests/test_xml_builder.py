"""Tests for XMLBuilder."""

from datetime import datetime
from decimal import Decimal
from xml.etree import ElementTree as ET

import pytest

from backend.lib.pynfse_nacional.constants import Ambiente
from backend.lib.pynfse_nacional.models import DPS, Endereco, Prestador, Servico, Tomador
from backend.lib.pynfse_nacional.xml_builder import XMLBuilder

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
def sample_tomador():
    """Sample service taker (patient) for testing."""
    return Tomador(
        cpf="12345678901",
        razao_social="Joao Silva",
        email="paciente@email.com",
        telefone="1988888888",
    )


@pytest.fixture
def sample_servico():
    """Sample service for testing."""
    return Servico(
        codigo_cnae="8630503",
        codigo_lc116="403",
        discriminacao="Consulta medica",
        valor_servicos=Decimal("500.00"),
        iss_retido=False,
        aliquota_iss=Decimal("2.00"),
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
        id_dps="11222333000181NF0000000001",
        serie="NF",
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

    def test_build_dps_includes_id_attribute(self, sample_dps):
        """infDPS should have Id attribute set to id_dps."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)

        assert infDPS.attrib.get("Id") == "11222333000181NF0000000001"

    def test_build_dps_includes_emission_date(self, sample_dps):
        """build_dps should include dhEmi with ISO format."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)
        dhEmi = infDPS.find("nfse:dhEmi", NS)

        assert dhEmi.text == "2026-01-15T10:30:00"

    def test_build_dps_includes_serie_and_numero(self, sample_dps):
        """build_dps should include serie and nDPS."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)
        serie = infDPS.find("nfse:serie", NS)
        nDPS = infDPS.find("nfse:nDPS", NS)

        assert serie.text == "NF"
        assert nDPS.text == "1"

    def test_build_dps_includes_competencia(self, sample_dps):
        """build_dps should include dCompet."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        infDPS = root.find("nfse:infDPS", NS)
        dCompet = infDPS.find("nfse:dCompet", NS)

        assert dCompet.text == "2026-01"


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

    def test_build_dps_includes_prestador_im(self, sample_dps):
        """Prestador section should include inscricao municipal."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        im = prest.find("nfse:IM", NS)

        assert im.text == "12345"

    def test_build_dps_includes_prestador_name(self, sample_dps):
        """Prestador section should include razao social."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        xNome = prest.find("nfse:xNome", NS)

        assert xNome.text == "Clinica Teste LTDA"

    def test_build_dps_includes_prestador_fantasia(self, sample_dps):
        """Prestador section should include nome fantasia."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        xFant = prest.find("nfse:xFant", NS)

        assert xFant.text == "Clinica Teste"

    def test_build_dps_omits_fantasia_if_none(self, sample_dps):
        """Prestador should omit xFant if nome_fantasia is None."""
        sample_dps.prestador.nome_fantasia = None
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        xFant = prest.find("nfse:xFant", NS)

        assert xFant is None

    def test_build_dps_includes_prestador_address(self, sample_dps):
        """Prestador section should include address."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        ender = root.find("nfse:infDPS/nfse:prest/nfse:enderPrest", NS)

        assert ender.find("nfse:xLgr", NS).text == "Rua Teste"
        assert ender.find("nfse:nro", NS).text == "100"
        assert ender.find("nfse:xCpl", NS).text == "Sala 1"
        assert ender.find("nfse:xBairro", NS).text == "Centro"
        assert ender.find("nfse:cMun", NS).text == "3509502"
        assert ender.find("nfse:UF", NS).text == "SP"
        assert ender.find("nfse:CEP", NS).text == "13000000"

    def test_build_dps_includes_prestador_email(self, sample_dps):
        """Prestador section should include email."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        email = prest.find("nfse:email", NS)

        assert email.text == "contato@clinica.com"

    def test_build_dps_includes_regime_tributario(self, sample_dps):
        """Prestador section should include regTrib."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        regTrib = prest.find("nfse:regTrib", NS)

        assert regTrib.text == "1"

    def test_build_dps_maps_regime_normal(self, sample_dps):
        """regTrib should be 3 for normal regime."""
        sample_dps.regime_tributario = "normal"
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        regTrib = prest.find("nfse:regTrib", NS)

        assert regTrib.text == "3"

    def test_build_dps_maps_regime_mei(self, sample_dps):
        """regTrib should be 4 for MEI regime."""
        sample_dps.regime_tributario = "mei"
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        regTrib = prest.find("nfse:regTrib", NS)

        assert regTrib.text == "4"

    def test_build_dps_includes_optante_simples(self, sample_dps):
        """Prestador section should include optSN."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        optSN = prest.find("nfse:optSN", NS)

        assert optSN.text == "1"

    def test_build_dps_optante_simples_false(self, sample_dps):
        """optSN should be 2 when optante_simples is False."""
        sample_dps.optante_simples = False
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        prest = root.find("nfse:infDPS/nfse:prest", NS)
        optSN = prest.find("nfse:optSN", NS)

        assert optSN.text == "2"


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

    def test_build_dps_includes_tomador_name(self, sample_dps):
        """Tomador section should include razao social."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        toma = root.find("nfse:infDPS/nfse:toma", NS)
        xNome = toma.find("nfse:xNome", NS)

        assert xNome.text == "Joao Silva"

    def test_build_dps_includes_tomador_email(self, sample_dps):
        """Tomador section should include email."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        toma = root.find("nfse:infDPS/nfse:toma", NS)
        email = toma.find("nfse:email", NS)

        assert email.text == "paciente@email.com"

    def test_build_dps_omits_tomador_address_if_none(self, sample_dps):
        """Tomador should omit enderToma if address is None."""
        sample_dps.tomador.endereco = None
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        toma = root.find("nfse:infDPS/nfse:toma", NS)
        ender = toma.find("nfse:enderToma", NS)

        assert ender is None


class TestXMLBuilderServico:
    """Tests for servico section."""

    def test_build_dps_includes_servico_code(self, sample_dps):
        """Servico section should include cServ (LC116 code)."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        serv = root.find("nfse:infDPS/nfse:serv", NS)
        cServ = serv.find("nfse:cServ", NS)

        assert cServ.text == "403"

    def test_build_dps_includes_cnae(self, sample_dps):
        """Servico section should include CNAE."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        serv = root.find("nfse:infDPS/nfse:serv", NS)
        cnae = serv.find("nfse:CNAE", NS)

        assert cnae.text == "8630503"

    def test_build_dps_includes_description(self, sample_dps):
        """Servico section should include xDescServ."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        serv = root.find("nfse:infDPS/nfse:serv", NS)
        xDescServ = serv.find("nfse:xDescServ", NS)

        assert xDescServ.text == "Consulta medica"

    def test_build_dps_includes_municipality_code(self, sample_dps):
        """Servico section should include cMunInc."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        serv = root.find("nfse:infDPS/nfse:serv", NS)
        cMunInc = serv.find("nfse:cMunInc", NS)

        assert cMunInc.text == "3509502"


class TestXMLBuilderValores:
    """Tests for valores (values) section."""

    def test_build_dps_includes_valor_servicos(self, sample_dps):
        """Valores section should include vServPrest."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        valores = root.find("nfse:infDPS/nfse:valores", NS)
        vServPrest = valores.find("nfse:vServPrest", NS)

        assert vServPrest.text == "500.00"

    def test_build_dps_includes_deducoes(self, sample_dps):
        """Valores section should include vDeducoes."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        valores = root.find("nfse:infDPS/nfse:valores", NS)
        vDeducoes = valores.find("nfse:vDeducoes", NS)

        assert vDeducoes.text == "0.00"

    def test_build_dps_includes_tributos(self, sample_dps):
        """Valores section should include all tax fields."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        valores = root.find("nfse:infDPS/nfse:valores", NS)

        assert valores.find("nfse:vPIS", NS).text == "0.00"
        assert valores.find("nfse:vCOFINS", NS).text == "0.00"
        assert valores.find("nfse:vINSS", NS).text == "0.00"
        assert valores.find("nfse:vIR", NS).text == "0.00"
        assert valores.find("nfse:vCSLL", NS).text == "0.00"

    def test_build_dps_iss_not_retained(self, sample_dps):
        """indISSRet should be 2 when ISS not retained."""
        sample_dps.servico.iss_retido = False
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        valores = root.find("nfse:infDPS/nfse:valores", NS)
        indISSRet = valores.find("nfse:indISSRet", NS)

        assert indISSRet.text == "2"

    def test_build_dps_iss_retained(self, sample_dps):
        """indISSRet should be 1 when ISS retained."""
        sample_dps.servico.iss_retido = True
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        valores = root.find("nfse:infDPS/nfse:valores", NS)
        indISSRet = valores.find("nfse:indISSRet", NS)

        assert indISSRet.text == "1"

    def test_build_dps_includes_aliquota_iss(self, sample_dps):
        """Valores section should include aliqISS when provided."""
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        valores = root.find("nfse:infDPS/nfse:valores", NS)
        aliqISS = valores.find("nfse:aliqISS", NS)

        assert aliqISS.text == "2.00"

    def test_build_dps_omits_aliquota_if_none(self, sample_dps):
        """Valores should omit aliqISS if aliquota_iss is None."""
        sample_dps.servico.aliquota_iss = None
        builder = XMLBuilder()

        xml_str = builder.build_dps(sample_dps)
        root = ET.fromstring(xml_str)

        valores = root.find("nfse:infDPS/nfse:valores", NS)
        aliqISS = valores.find("nfse:aliqISS", NS)

        assert aliqISS is None
