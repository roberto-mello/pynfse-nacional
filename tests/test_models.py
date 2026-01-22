"""Tests for Pydantic models validation."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from pynfse_nacional.models import DPS, Endereco, Prestador, Servico, Tomador


@pytest.fixture
def sample_endereco():
    """Sample address for testing."""
    return Endereco(
        logradouro="Rua Teste",
        numero="100",
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
        razao_social="Empresa Teste LTDA",
        endereco=sample_endereco,
    )


@pytest.fixture
def sample_tomador():
    """Sample service taker for testing."""
    return Tomador(
        cpf="12345678901",
        razao_social="Joao Silva",
    )


@pytest.fixture
def sample_servico():
    """Sample service for testing."""
    return Servico(
        codigo_lc116="4.03",
        discriminacao="Consulta medica",
        valor_servicos=Decimal("500.00"),
    )


class TestDPSSerieValidation:
    """Tests for DPS serie field validation."""

    def test_serie_accepts_single_digit(self, sample_prestador, sample_tomador, sample_servico):
        """Serie should accept a single digit."""
        dps = DPS(
            serie="1",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=sample_prestador,
            tomador=sample_tomador,
            servico=sample_servico,
            regime_tributario="simples_nacional",
        )

        assert dps.serie == "1"

    def test_serie_accepts_multiple_digits(self, sample_prestador, sample_tomador, sample_servico):
        """Serie should accept multiple digits."""
        dps = DPS(
            serie="900",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=sample_prestador,
            tomador=sample_tomador,
            servico=sample_servico,
            regime_tributario="simples_nacional",
        )

        assert dps.serie == "900"

    def test_serie_accepts_leading_zeros(self, sample_prestador, sample_tomador, sample_servico):
        """Serie should accept leading zeros."""
        dps = DPS(
            serie="00001",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=sample_prestador,
            tomador=sample_tomador,
            servico=sample_servico,
            regime_tributario="simples_nacional",
        )

        assert dps.serie == "00001"

    def test_serie_rejects_alphabetic(self, sample_prestador, sample_tomador, sample_servico):
        """Serie should reject alphabetic values like 'NF'."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                serie="NF",
                numero=1,
                competencia="2026-01",
                data_emissao=datetime.now(),
                prestador=sample_prestador,
                tomador=sample_tomador,
                servico=sample_servico,
                regime_tributario="simples_nacional",
            )

        assert "serie must be numeric" in str(exc_info.value)
        assert "NF" in str(exc_info.value)

    def test_serie_rejects_alphanumeric(self, sample_prestador, sample_tomador, sample_servico):
        """Serie should reject alphanumeric values."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                serie="A123",
                numero=1,
                competencia="2026-01",
                data_emissao=datetime.now(),
                prestador=sample_prestador,
                tomador=sample_tomador,
                servico=sample_servico,
                regime_tributario="simples_nacional",
            )

        assert "serie must be numeric" in str(exc_info.value)

    def test_serie_rejects_too_long(self, sample_prestador, sample_tomador, sample_servico):
        """Serie should reject values longer than 5 digits."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                serie="123456",
                numero=1,
                competencia="2026-01",
                data_emissao=datetime.now(),
                prestador=sample_prestador,
                tomador=sample_tomador,
                servico=sample_servico,
                regime_tributario="simples_nacional",
            )

        assert "serie must be numeric" in str(exc_info.value)


class TestDPSIdValidation:
    """Tests for DPS id_dps field validation."""

    def test_id_dps_accepts_none(self, sample_prestador, sample_tomador, sample_servico):
        """id_dps should accept None (auto-generate)."""
        dps = DPS(
            serie="900",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=sample_prestador,
            tomador=sample_tomador,
            servico=sample_servico,
            regime_tributario="simples_nacional",
        )

        assert dps.id_dps is None

    def test_id_dps_accepts_valid_format(self, sample_prestador, sample_tomador, sample_servico):
        """id_dps should accept valid 45-char format."""
        valid_id = "DPS350950221122233300018100900000000000000001"

        dps = DPS(
            id_dps=valid_id,
            serie="900",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=sample_prestador,
            tomador=sample_tomador,
            servico=sample_servico,
            regime_tributario="simples_nacional",
        )

        assert dps.id_dps == valid_id

    def test_id_dps_rejects_missing_prefix(self, sample_prestador, sample_tomador, sample_servico):
        """id_dps should reject IDs without 'DPS' prefix."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                id_dps="350950221122233300018100900000000000000001",
                serie="900",
                numero=1,
                competencia="2026-01",
                data_emissao=datetime.now(),
                prestador=sample_prestador,
                tomador=sample_tomador,
                servico=sample_servico,
                regime_tributario="simples_nacional",
            )

        assert "DPS" in str(exc_info.value)

    def test_id_dps_rejects_wrong_length(self, sample_prestador, sample_tomador, sample_servico):
        """id_dps should reject IDs with wrong length."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                id_dps="DPS12345",
                serie="900",
                numero=1,
                competencia="2026-01",
                data_emissao=datetime.now(),
                prestador=sample_prestador,
                tomador=sample_tomador,
                servico=sample_servico,
                regime_tributario="simples_nacional",
            )

        assert "45 chars" in str(exc_info.value)

    def test_id_dps_rejects_letters_after_prefix(self, sample_prestador, sample_tomador, sample_servico):
        """id_dps should reject IDs with letters after DPS prefix."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                id_dps="DPS35095022112223330001810090NF00000000001",
                serie="900",
                numero=1,
                competencia="2026-01",
                data_emissao=datetime.now(),
                prestador=sample_prestador,
                tomador=sample_tomador,
                servico=sample_servico,
                regime_tributario="simples_nacional",
            )

        assert "42 digits" in str(exc_info.value)
