from pynfse_nacional import REGIME_TO_SIMPLES_NACIONAL


def test_regime_mapping_exports_expected_contract() -> None:
    assert REGIME_TO_SIMPLES_NACIONAL == {
        "normal": {
            "opSimpNac": "1",
            "regApTribSn": None,
        },
        "mei": {
            "opSimpNac": "2",
            "regApTribSn": None,
        },
        "simples_nacional": {
            "opSimpNac": "3",
            "regApTribSn": "1",
        },
        "simples_excesso": {
            "opSimpNac": "3",
            "regApTribSn": "2",
        },
    }
