"""Unit tests for integration-layer E1xxx schema rejection guard."""

import pytest

from tests.test_client_integration import (
    assert_dps_rejection_acceptable,
    is_schema_rejection,
)


class TestIsSchemaRejection:
    def test_e1235_code(self):
        assert is_schema_rejection("E1235", "The element regTrib has invalid child")

    def test_e1xxx_case_insensitive(self):
        assert is_schema_rejection("e1235", None)

    def test_business_rule_e2_allowed(self):
        assert not is_schema_rejection("E2001", "business rule")

    def test_business_rule_e3_allowed(self):
        assert not is_schema_rejection("E3001", "another business rule")

    def test_message_invalid_child_without_code(self):
        assert is_schema_rejection(
            None,
            "The element regTrib has invalid child element regApIBSCBSSN",
        )

    def test_empty_not_schema(self):
        assert not is_schema_rejection(None, None)
        assert not is_schema_rejection("", "")

    def test_http_status_code_not_schema(self):
        assert not is_schema_rejection("400", "Bad Request")

    def test_nfse_e_prefix_not_e1_class(self):
        assert not is_schema_rejection("NFSE-E-400", "JSON não é um objeto")


class TestAssertDpsRejectionAcceptable:
    def test_fails_on_e1235(self):
        with pytest.raises(pytest.fail.Exception, match="Schema/structure rejection"):
            assert_dps_rejection_acceptable(
                "E1235",
                "The element regTrib has invalid child element regApIBSCBSSN",
            )

    def test_allows_e2xxx(self):
        assert_dps_rejection_acceptable("E2001", "CNPJ não autorizado")

    def test_requires_code_or_message(self):
        with pytest.raises(AssertionError, match="error_code or error_message"):
            assert_dps_rejection_acceptable(None, None)
