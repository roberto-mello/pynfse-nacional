from xml.etree import ElementTree as ET

import pytest
from defusedxml.common import EntitiesForbidden

from pynfse_nacional import response_parsers
from pynfse_nacional.response_parsers import parse_ibscbs, parse_nfse_root

SAMPLE_IBSCBS_XML = """\
<NFSe xmlns="http://www.sped.fazenda.gov.br/nfse">
  <infNFSe>
    <DPS>
      <infDPS>
        <IBSCBS>
          <finNFSe>0</finNFSe>
          <indFinal>0</indFinal>
          <cIndOp>020101</cIndOp>
          <indDest>0</indDest>
          <valores>
            <trib>
              <gIBSCBS>
                <CST>001</CST>
                <cClassTrib>123456</cClassTrib>
              </gIBSCBS>
            </trib>
          </valores>
        </IBSCBS>
      </infDPS>
    </DPS>
  </infNFSe>
</NFSe>
"""


def test_parse_ibscbs_returns_model_for_valid_xml():
    ibscbs = parse_ibscbs(SAMPLE_IBSCBS_XML)

    assert ibscbs is not None
    assert ibscbs.c_ind_op == "020101"


def test_parse_nfse_root_rejects_entity_expansion():
    """defusedxml must block billion-laughs style payloads."""
    lol = "&lol;" * 10
    lol1 = "&lol1;" * 10
    bomb = (
        '<?xml version="1.0"?>'
        "<!DOCTYPE lolz ["
        '  <!ENTITY lol "lol">'
        f'  <!ENTITY lol1 "{lol}">'
        f'  <!ENTITY lol2 "{lol1}">'
        "]>"
        "<lolz>&lol2;</lolz>"
    )
    with pytest.raises(EntitiesForbidden):
        parse_nfse_root(bomb)


def test_parse_ibscbs_propagates_unexpected_errors(monkeypatch: pytest.MonkeyPatch):
    root = ET.fromstring(SAMPLE_IBSCBS_XML)

    def boom(data):
        raise KeyError("unexpected")

    monkeypatch.setattr(response_parsers.IBSCBS, "model_validate", boom)

    with pytest.raises(KeyError, match="unexpected"):
        parse_ibscbs(root=root)
