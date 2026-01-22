"""Tests for Pydantic models validation."""

from datetime import datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError

from pynfse_nacional.models import DPS, Endereco, Prestador, Servico, Tomador


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def valid_endereco():
    """Endereco valido para testes."""
    return Endereco(
        logradouro="Rua Teste",
        numero="100",
        bairro="Centro",
        codigo_municipio=3509502,
        uf="SP",
        cep="13000000",
    )


@pytest.fixture
def valid_prestador(valid_endereco):
    """Prestador valido para testes."""
    return Prestador(
        cnpj="11222333000181",
        inscricao_municipal="12345",
        razao_social="Empresa Teste LTDA",
        endereco=valid_endereco,
    )


@pytest.fixture
def valid_tomador():
    """Tomador valido para testes."""
    return Tomador(
        cpf="52998224725",
        razao_social="Joao Silva",
    )


@pytest.fixture
def valid_servico():
    """Servico valido para testes."""
    return Servico(
        codigo_lc116="04.03.01",
        discriminacao="Consulta medica",
        valor_servicos=Decimal("500.00"),
    )


# =============================================================================
# Tests: Endereco
# =============================================================================


class TestEnderecoCodigoMunicipio:
    """Testes para validacao do codigo_municipio."""

    def test_accepts_valid_7_digit_code(self):
        """Deve aceitar codigo IBGE com 7 digitos."""
        endereco = Endereco(
            logradouro="Rua Teste",
            numero="100",
            bairro="Centro",
            codigo_municipio=3550308,
            uf="SP",
            cep="01310100",
        )

        assert endereco.codigo_municipio == 3550308

    def test_rejects_code_with_less_than_7_digits(self):
        """Deve rejeitar codigo com menos de 7 digitos."""
        with pytest.raises(ValidationError) as exc_info:
            Endereco(
                logradouro="Rua Teste",
                numero="100",
                bairro="Centro",
                codigo_municipio=7221,
                uf="RN",
                cep="59000000",
            )

        assert "codigo_municipio deve ter 7 digitos" in str(exc_info.value)

    def test_rejects_code_with_more_than_7_digits(self):
        """Deve rejeitar codigo com mais de 7 digitos."""
        with pytest.raises(ValidationError) as exc_info:
            Endereco(
                logradouro="Rua Teste",
                numero="100",
                bairro="Centro",
                codigo_municipio=35503080,
                uf="SP",
                cep="01310100",
            )

        assert "codigo_municipio deve ter 7 digitos" in str(exc_info.value)


class TestEnderecoUF:
    """Testes para validacao da UF."""

    def test_accepts_valid_uf(self):
        """Deve aceitar UF valida."""
        endereco = Endereco(
            logradouro="Rua Teste",
            numero="100",
            bairro="Centro",
            codigo_municipio=3550308,
            uf="SP",
            cep="01310100",
        )

        assert endereco.uf == "SP"

    def test_accepts_lowercase_uf(self):
        """Deve aceitar UF em minusculo e converter para maiusculo."""
        endereco = Endereco(
            logradouro="Rua Teste",
            numero="100",
            bairro="Centro",
            codigo_municipio=3550308,
            uf="sp",
            cep="01310100",
        )

        assert endereco.uf == "SP"

    def test_rejects_invalid_uf(self):
        """Deve rejeitar UF invalida."""
        with pytest.raises(ValidationError) as exc_info:
            Endereco(
                logradouro="Rua Teste",
                numero="100",
                bairro="Centro",
                codigo_municipio=3550308,
                uf="XX",
                cep="01310100",
            )

        assert "UF invalida" in str(exc_info.value)


class TestEnderecoCEP:
    """Testes para validacao do CEP."""

    def test_accepts_8_digit_cep(self):
        """Deve aceitar CEP com 8 digitos."""
        endereco = Endereco(
            logradouro="Rua Teste",
            numero="100",
            bairro="Centro",
            codigo_municipio=3550308,
            uf="SP",
            cep="01310100",
        )

        assert endereco.cep == "01310100"

    def test_accepts_formatted_cep(self):
        """Deve aceitar CEP formatado e limpar."""
        endereco = Endereco(
            logradouro="Rua Teste",
            numero="100",
            bairro="Centro",
            codigo_municipio=3550308,
            uf="SP",
            cep="01310-100",
        )

        assert endereco.cep == "01310100"

    def test_rejects_cep_with_wrong_length(self):
        """Deve rejeitar CEP com tamanho errado."""
        with pytest.raises(ValidationError) as exc_info:
            Endereco(
                logradouro="Rua Teste",
                numero="100",
                bairro="Centro",
                codigo_municipio=3550308,
                uf="SP",
                cep="1234567",
            )

        assert "CEP deve conter 8 digitos" in str(exc_info.value)


# =============================================================================
# Tests: Prestador
# =============================================================================


class TestPrestadorCNPJ:
    """Testes para validacao do CNPJ do prestador."""

    def test_accepts_valid_cnpj(self, valid_endereco):
        """Deve aceitar CNPJ valido."""
        prestador = Prestador(
            cnpj="11222333000181",
            inscricao_municipal="12345",
            razao_social="Empresa Teste",
            endereco=valid_endereco,
        )

        assert prestador.cnpj == "11222333000181"

    def test_accepts_formatted_cnpj(self, valid_endereco):
        """Deve aceitar CNPJ formatado e limpar."""
        prestador = Prestador(
            cnpj="11.222.333/0001-81",
            inscricao_municipal="12345",
            razao_social="Empresa Teste",
            endereco=valid_endereco,
        )

        assert prestador.cnpj == "11222333000181"

    def test_rejects_cnpj_with_invalid_check_digits(self, valid_endereco):
        """Deve rejeitar CNPJ com digitos verificadores invalidos."""
        with pytest.raises(ValidationError) as exc_info:
            Prestador(
                cnpj="11222333000199",
                inscricao_municipal="12345",
                razao_social="Empresa Teste",
                endereco=valid_endereco,
            )

        assert "CNPJ invalido (digitos verificadores incorretos)" in str(exc_info.value)

    def test_rejects_cnpj_with_wrong_length(self, valid_endereco):
        """Deve rejeitar CNPJ com tamanho errado."""
        with pytest.raises(ValidationError) as exc_info:
            Prestador(
                cnpj="1122233300018",
                inscricao_municipal="12345",
                razao_social="Empresa Teste",
                endereco=valid_endereco,
            )

        assert "CNPJ deve conter 14 digitos" in str(exc_info.value)


class TestPrestadorTelefone:
    """Testes para validacao do telefone do prestador."""

    def test_accepts_valid_telefone(self, valid_endereco):
        """Deve aceitar telefone valido."""
        prestador = Prestador(
            cnpj="11222333000181",
            inscricao_municipal="12345",
            razao_social="Empresa Teste",
            endereco=valid_endereco,
            telefone="11999999999",
        )

        assert prestador.telefone == "11999999999"

    def test_accepts_formatted_telefone(self, valid_endereco):
        """Deve aceitar telefone formatado e limpar."""
        prestador = Prestador(
            cnpj="11222333000181",
            inscricao_municipal="12345",
            razao_social="Empresa Teste",
            endereco=valid_endereco,
            telefone="+55 (11) 99999-9999",
        )

        assert prestador.telefone == "5511999999999"

    def test_rejects_telefone_too_short(self, valid_endereco):
        """Deve rejeitar telefone muito curto."""
        with pytest.raises(ValidationError) as exc_info:
            Prestador(
                cnpj="11222333000181",
                inscricao_municipal="12345",
                razao_social="Empresa Teste",
                endereco=valid_endereco,
                telefone="12345",
            )

        assert "Telefone deve conter entre 6 e 20 digitos" in str(exc_info.value)


# =============================================================================
# Tests: Tomador
# =============================================================================


class TestTomadorCPF:
    """Testes para validacao do CPF do tomador."""

    def test_accepts_valid_cpf(self):
        """Deve aceitar CPF valido."""
        tomador = Tomador(
            cpf="52998224725",
            razao_social="Joao Silva",
        )

        assert tomador.cpf == "52998224725"

    def test_accepts_formatted_cpf(self):
        """Deve aceitar CPF formatado e limpar."""
        tomador = Tomador(
            cpf="529.982.247-25",
            razao_social="Joao Silva",
        )

        assert tomador.cpf == "52998224725"

    def test_rejects_cpf_with_invalid_check_digits(self):
        """Deve rejeitar CPF com digitos verificadores invalidos."""
        with pytest.raises(ValidationError) as exc_info:
            Tomador(
                cpf="12345678901",
                razao_social="Joao Silva",
            )

        assert "CPF invalido (digitos verificadores incorretos)" in str(exc_info.value)

    def test_rejects_cpf_with_all_same_digits(self):
        """Deve rejeitar CPF com todos os digitos iguais."""
        with pytest.raises(ValidationError) as exc_info:
            Tomador(
                cpf="11111111111",
                razao_social="Joao Silva",
            )

        assert "CPF invalido" in str(exc_info.value)


class TestTomadorCPFOrCNPJ:
    """Testes para validacao de CPF ou CNPJ obrigatorio."""

    def test_accepts_only_cpf(self):
        """Deve aceitar tomador apenas com CPF."""
        tomador = Tomador(
            cpf="52998224725",
            razao_social="Joao Silva",
        )

        assert tomador.cpf == "52998224725"
        assert tomador.cnpj is None

    def test_accepts_only_cnpj(self):
        """Deve aceitar tomador apenas com CNPJ."""
        tomador = Tomador(
            cnpj="11222333000181",
            razao_social="Empresa Cliente",
        )

        assert tomador.cnpj == "11222333000181"
        assert tomador.cpf is None

    def test_rejects_without_cpf_or_cnpj(self):
        """Deve rejeitar tomador sem CPF e sem CNPJ."""
        with pytest.raises(ValidationError) as exc_info:
            Tomador(
                razao_social="Joao Silva",
            )

        assert "Tomador deve ter CPF ou CNPJ informado" in str(exc_info.value)


# =============================================================================
# Tests: Servico
# =============================================================================


class TestServicoCodigoLC116:
    """Testes para validacao do codigo_lc116."""

    def test_accepts_full_code_with_dots(self):
        """Deve aceitar codigo completo com pontos."""
        servico = Servico(
            codigo_lc116="04.03.01",
            discriminacao="Consulta medica",
            valor_servicos=Decimal("500.00"),
        )

        assert servico.codigo_lc116 == "04.03.01"

    def test_accepts_6_digit_code(self):
        """Deve aceitar codigo com 6 digitos sem pontos."""
        servico = Servico(
            codigo_lc116="040301",
            discriminacao="Consulta medica",
            valor_servicos=Decimal("500.00"),
        )

        assert servico.codigo_lc116 == "040301"

    def test_rejects_partial_code_without_subitem(self):
        """Deve rejeitar codigo sem subitem completo."""
        with pytest.raises(ValidationError) as exc_info:
            Servico(
                codigo_lc116="4.03",
                discriminacao="Consulta medica",
                valor_servicos=Decimal("500.00"),
            )

        assert "codigo_lc116 deve incluir o subitem completo" in str(exc_info.value)

    def test_rejects_partial_code_4_digits(self):
        """Deve rejeitar codigo com apenas 4 digitos."""
        with pytest.raises(ValidationError) as exc_info:
            Servico(
                codigo_lc116="0403",
                discriminacao="Consulta medica",
                valor_servicos=Decimal("500.00"),
            )

        assert "codigo_lc116 deve incluir o subitem completo" in str(exc_info.value)


class TestServicoValorServicos:
    """Testes para validacao do valor_servicos."""

    def test_accepts_positive_value(self):
        """Deve aceitar valor positivo."""
        servico = Servico(
            codigo_lc116="04.03.01",
            discriminacao="Consulta medica",
            valor_servicos=Decimal("500.00"),
        )

        assert servico.valor_servicos == Decimal("500.00")

    def test_rejects_zero_value(self):
        """Deve rejeitar valor zero."""
        with pytest.raises(ValidationError) as exc_info:
            Servico(
                codigo_lc116="04.03.01",
                discriminacao="Consulta medica",
                valor_servicos=Decimal("0"),
            )

        assert "valor_servicos deve ser maior que zero" in str(exc_info.value)

    def test_rejects_negative_value(self):
        """Deve rejeitar valor negativo."""
        with pytest.raises(ValidationError) as exc_info:
            Servico(
                codigo_lc116="04.03.01",
                discriminacao="Consulta medica",
                valor_servicos=Decimal("-100.00"),
            )

        assert "valor_servicos deve ser maior que zero" in str(exc_info.value)


# =============================================================================
# Tests: DPS
# =============================================================================


class TestDPSSerie:
    """Testes para validacao da serie."""

    def test_accepts_numeric_serie(self, valid_prestador, valid_tomador, valid_servico):
        """Deve aceitar serie numerica."""
        dps = DPS(
            serie="900",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=valid_prestador,
            tomador=valid_tomador,
            servico=valid_servico,
            regime_tributario="simples_nacional",
        )

        assert dps.serie == "900"

    def test_rejects_alphabetic_serie(self, valid_prestador, valid_tomador, valid_servico):
        """Deve rejeitar serie alfabetica."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                serie="NF",
                numero=1,
                competencia="2026-01",
                data_emissao=datetime.now(),
                prestador=valid_prestador,
                tomador=valid_tomador,
                servico=valid_servico,
                regime_tributario="simples_nacional",
            )

        assert "serie deve ser numerica" in str(exc_info.value)


class TestDPSCompetencia:
    """Testes para validacao da competencia."""

    def test_accepts_valid_competencia(self, valid_prestador, valid_tomador, valid_servico):
        """Deve aceitar competencia valida."""
        dps = DPS(
            serie="900",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=valid_prestador,
            tomador=valid_tomador,
            servico=valid_servico,
            regime_tributario="simples_nacional",
        )

        assert dps.competencia == "2026-01"

    def test_rejects_invalid_month(self, valid_prestador, valid_tomador, valid_servico):
        """Deve rejeitar mes invalido."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                serie="900",
                numero=1,
                competencia="2026-13",
                data_emissao=datetime.now(),
                prestador=valid_prestador,
                tomador=valid_tomador,
                servico=valid_servico,
                regime_tributario="simples_nacional",
            )

        assert "competencia deve estar no formato YYYY-MM" in str(exc_info.value)

    def test_rejects_wrong_format(self, valid_prestador, valid_tomador, valid_servico):
        """Deve rejeitar formato errado."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                serie="900",
                numero=1,
                competencia="01/2026",
                data_emissao=datetime.now(),
                prestador=valid_prestador,
                tomador=valid_tomador,
                servico=valid_servico,
                regime_tributario="simples_nacional",
            )

        assert "competencia deve estar no formato YYYY-MM" in str(exc_info.value)


class TestDPSRegimeTributario:
    """Testes para validacao do regime_tributario."""

    def test_accepts_valid_regime(self, valid_prestador, valid_tomador, valid_servico):
        """Deve aceitar regime valido."""
        dps = DPS(
            serie="900",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=valid_prestador,
            tomador=valid_tomador,
            servico=valid_servico,
            regime_tributario="simples_nacional",
        )

        assert dps.regime_tributario == "simples_nacional"

    def test_rejects_invalid_regime(self, valid_prestador, valid_tomador, valid_servico):
        """Deve rejeitar regime invalido."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                serie="900",
                numero=1,
                competencia="2026-01",
                data_emissao=datetime.now(),
                prestador=valid_prestador,
                tomador=valid_tomador,
                servico=valid_servico,
                regime_tributario="invalido",
            )

        assert "regime_tributario invalido" in str(exc_info.value)


class TestDPSIdDps:
    """Testes para validacao do id_dps."""

    def test_accepts_none(self, valid_prestador, valid_tomador, valid_servico):
        """Deve aceitar id_dps None (auto-gerado)."""
        dps = DPS(
            serie="900",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=valid_prestador,
            tomador=valid_tomador,
            servico=valid_servico,
            regime_tributario="simples_nacional",
        )

        assert dps.id_dps is None

    def test_accepts_valid_format(self, valid_prestador, valid_tomador, valid_servico):
        """Deve aceitar formato valido de 45 caracteres."""
        valid_id = "DPS350950221122233300018100900000000000000001"

        dps = DPS(
            id_dps=valid_id,
            serie="900",
            numero=1,
            competencia="2026-01",
            data_emissao=datetime.now(),
            prestador=valid_prestador,
            tomador=valid_tomador,
            servico=valid_servico,
            regime_tributario="simples_nacional",
        )

        assert dps.id_dps == valid_id

    def test_rejects_missing_prefix(self, valid_prestador, valid_tomador, valid_servico):
        """Deve rejeitar id sem prefixo DPS."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                id_dps="350950221122233300018100900000000000000001",
                serie="900",
                numero=1,
                competencia="2026-01",
                data_emissao=datetime.now(),
                prestador=valid_prestador,
                tomador=valid_tomador,
                servico=valid_servico,
                regime_tributario="simples_nacional",
            )

        assert "id_dps deve seguir o padrao" in str(exc_info.value)

    def test_rejects_wrong_length(self, valid_prestador, valid_tomador, valid_servico):
        """Deve rejeitar id com tamanho errado."""
        with pytest.raises(ValidationError) as exc_info:
            DPS(
                id_dps="DPS12345",
                serie="900",
                numero=1,
                competencia="2026-01",
                data_emissao=datetime.now(),
                prestador=valid_prestador,
                tomador=valid_tomador,
                servico=valid_servico,
                regime_tributario="simples_nacional",
            )

        assert "45 caracteres" in str(exc_info.value)
