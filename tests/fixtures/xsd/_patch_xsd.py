"""Regenerate vendored NFSe XSD fixtures from the official gov.br zip."""

# ruff: noqa: E501

from __future__ import annotations

import argparse
import tempfile
import zipfile
from pathlib import Path

_BROKEN_TSSERIEDPS_PATTERN = 'value="^0{0,4}\\d{1,5}$"'
_FIXED_TSSERIEDPS_PATTERN = 'value="0{0,4}\\d{1,5}"'
_TSOPSIMPNAC_BLOCK = (
    '<xs:simpleType name="TSOpSimpNac">\n'
    '    <xs:annotation>\n'
    '      <xs:documentation>\n'
    '        Situação perante o Simples Nacional:\n'
    '        1 - Não Optante;\n'
    '        2 - Optante - Microempreendedor Individual (MEI);\n'
    '        3 - Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP);\n'
    '      </xs:documentation>\n'
    '    </xs:annotation>\n'
    '    <xs:restriction base="xs:string">\n'
    '      <xs:whiteSpace value="preserve"/>\n'
    '      <xs:enumeration value="1"/>\n'
    '      <xs:enumeration value="2"/>\n'
    '      <xs:enumeration value="3"/>\n'
    '    </xs:restriction>\n'
    '  </xs:simpleType>'
)
_TSOPSIMPNAC_BLOCK_TABBED = (
    '<xs:simpleType name="TSOpSimpNac">\n'
    '\t\t<xs:annotation>\n'
    '\t\t\t<xs:documentation>\n'
    '\t\t\t\tSituação perante o Simples Nacional:\n'
    '\t\t\t\t1 - Não Optante;\n'
    '\t\t\t\t2 - Optante - Microempreendedor Individual (MEI);\n'
    '\t\t\t\t3 - Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP);\n'
    '\t\t\t</xs:documentation>\n'
    '\t\t</xs:annotation>\n'
    '\t\t<xs:restriction base="xs:string">\n'
    '\t\t\t<xs:whiteSpace value="preserve"/>\n'
    '\t\t\t<xs:enumeration value="1"/>\n'
    '\t\t\t<xs:enumeration value="2"/>\n'
    '\t\t\t<xs:enumeration value="3"/>\n'
    '\t\t</xs:restriction>\n'
    '\t</xs:simpleType>'
)
_TSOPSIMPNAC_BLOCK_PATCHED = (
    '<xs:simpleType name="TSOpSimpNac">\n'
    '    <xs:annotation>\n'
    '      <xs:documentation>\n'
    '        Situação perante o Simples Nacional:\n'
    '        1 - Não Optante;\n'
    '        2 - Optante - Microempreendedor Individual (MEI);\n'
    '        3 - Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP);\n'
    '        4 - Optante - Situação pendente no Simples Nacional;\n'
    '      </xs:documentation>\n'
    '    </xs:annotation>\n'
    '    <xs:restriction base="xs:string">\n'
    '      <xs:whiteSpace value="preserve"/>\n'
    '      <xs:enumeration value="1"/>\n'
    '      <xs:enumeration value="2"/>\n'
    '      <xs:enumeration value="3"/>\n'
    '      <xs:enumeration value="4"/>\n'
    '    </xs:restriction>\n'
    '  </xs:simpleType>'
)
_TSOPSIMPNAC_BLOCK_PATCHED_TABBED = (
    '<xs:simpleType name="TSOpSimpNac">\n'
    '\t\t<xs:annotation>\n'
    '\t\t\t<xs:documentation>\n'
    '\t\t\t\tSituação perante o Simples Nacional:\n'
    '\t\t\t\t1 - Não Optante;\n'
    '\t\t\t\t2 - Optante - Microempreendedor Individual (MEI);\n'
    '\t\t\t\t3 - Optante - Microempresa ou Empresa de Pequeno Porte (ME/EPP);\n'
    '\t\t\t\t4 - Optante - Situação pendente no Simples Nacional;\n'
    '\t\t\t</xs:documentation>\n'
    '\t\t</xs:annotation>\n'
    '\t\t<xs:restriction base="xs:string">\n'
    '\t\t\t<xs:whiteSpace value="preserve"/>\n'
    '\t\t\t<xs:enumeration value="1"/>\n'
    '\t\t\t<xs:enumeration value="2"/>\n'
    '\t\t\t<xs:enumeration value="3"/>\n'
    '\t\t\t<xs:enumeration value="4"/>\n'
    '\t\t</xs:restriction>\n'
    '\t</xs:simpleType>'
)
_TCREGTRIB_INSERTION = (
    '<xs:element name="regApTribSN" type="TSRegimeApuracaoSimpNac" minOccurs="0">\n'
    '        <xs:annotation>\n'
    '          <xs:documentation>\n'
    '            Opção para que o contribuinte optante pelo Simples Nacional ME/EPP (opSimpNac = 3) possa indicar, ao emitir o documento fiscal, em qual regime de apuração os tributos federais e municipal estão inseridos, caso tenha ultrapassado algum sublimite ou limite definido para o Simples Nacional.\n'
    '            1 – Regime de apuração dos tributos federais e municipal pelo SN;\n'
    '            2 – Regime de apuração dos tributos federais pelo SN e ISSQN  por fora do SN conforme respectiva legislação municipal do tributo;\n'
    '            3 – Regime de apuração dos tributos federais e municipal por fora do SN conforme respectivas legislações federal e municipal de cada tributo;\n'
    '          </xs:documentation>\n'
    '        </xs:annotation>\n'
    '      </xs:element>\n'
    '      <xs:element name="regEspTrib" type="TSRegEspTrib">'
)
_TCREGTRIB_INSERTION_TABBED = (
    '<xs:element name="regApTribSN" type="TSRegimeApuracaoSimpNac" minOccurs="0">\n'
    '\t\t<xs:annotation>\n'
    '\t\t\t<xs:documentation>\n'
    '\t\t\t\tOpção para que o contribuinte optante pelo Simples Nacional ME/EPP (opSimpNac = 3) possa indicar, ao emitir o documento fiscal, em qual regime de apuração os tributos federais e municipal estão inseridos, caso tenha ultrapassado algum sublimite ou limite definido para o Simples Nacional.\n'
    '\t\t\t\t1 – Regime de apuração dos tributos federais e municipal pelo SN;\n'
    '\t\t\t\t2 – Regime de apuração dos tributos federais pelo SN e ISSQN  por fora do SN conforme respectiva legislação municipal do tributo;\n'
    '\t\t\t\t3 – Regime de apuração dos tributos federais e municipal por fora do SN conforme respectivas legislações federal e municipal de cada tributo;\n'
    '\t\t\t</xs:documentation>\n'
    '\t\t</xs:annotation>\n'
    '\t</xs:element>\n'
    '\t<xs:element name="regEspTrib" type="TSRegEspTrib">'
)
_TCREGTRIB_INSERTION_PATCHED = (
    '<xs:element name="regApTribSN" type="TSRegimeApuracaoSimpNac" minOccurs="0">\n'
    '        <xs:annotation>\n'
    '          <xs:documentation>\n'
    '            Opção para que o contribuinte optante pelo Simples Nacional ME/EPP (opSimpNac = 3) possa indicar, ao emitir o documento fiscal, em qual regime de apuração os tributos federais e municipal estão inseridos, caso tenha ultrapassado algum sublimite ou limite definido para o Simples Nacional.\n'
    '            1 – Regime de apuração dos tributos federais e municipal pelo SN;\n'
    '            2 – Regime de apuração dos tributos federais pelo SN e ISSQN  por fora do SN conforme respectiva legislação municipal do tributo;\n'
    '            3 – Regime de apuração dos tributos federais e municipal por fora do SN conforme respectivas legislações federal e municipal de cada tributo;\n'
    '          </xs:documentation>\n'
    '        </xs:annotation>\n'
    '      </xs:element>\n'
    '      <xs:element name="regApIBSCBSSN" type="TSRegimeApuracaoSimpNac" minOccurs="0">\n'
    '        <xs:annotation>\n'
    '          <xs:documentation>\n'
    '            Regime de apuração do IBS/CBS para contribuintes optantes pelo Simples Nacional quando o leiaute IBSCBS estiver presente.\n'
    '            1 – IBS e CBS apurados pelo Simples Nacional;\n'
    '            2 – CBS pelo Simples Nacional e IBS fora do Simples Nacional;\n'
    '            3 – IBS e CBS apurados fora do Simples Nacional.\n'
    '          </xs:documentation>\n'
    '        </xs:annotation>\n'
    '      </xs:element>\n'
    '      <xs:element name="regEspTrib" type="TSRegEspTrib">'
)
_TCREGTRIB_INSERTION_PATCHED_TABBED = (
    '<xs:element name="regApTribSN" type="TSRegimeApuracaoSimpNac" minOccurs="0">\n'
    '\t\t<xs:annotation>\n'
    '\t\t\t<xs:documentation>\n'
    '\t\t\t\tOpção para que o contribuinte optante pelo Simples Nacional ME/EPP (opSimpNac = 3) possa indicar, ao emitir o documento fiscal, em qual regime de apuração os tributos federais e municipal estão inseridos, caso tenha ultrapassado algum sublimite ou limite definido para o Simples Nacional.\n'
    '\t\t\t\t1 – Regime de apuração dos tributos federais e municipal pelo SN;\n'
    '\t\t\t\t2 – Regime de apuração dos tributos federais pelo SN e ISSQN  por fora do SN conforme respectiva legislação municipal do tributo;\n'
    '\t\t\t\t3 – Regime de apuração dos tributos federais e municipal por fora do SN conforme respectivas legislações federal e municipal de cada tributo;\n'
    '\t\t\t</xs:documentation>\n'
    '\t\t</xs:annotation>\n'
    '\t</xs:element>\n'
    '\t<xs:element name="regApIBSCBSSN" type="TSRegimeApuracaoSimpNac" minOccurs="0">\n'
    '\t\t<xs:annotation>\n'
    '\t\t\t<xs:documentation>\n'
    '\t\t\t\tRegime de apuração do IBS/CBS para contribuintes optantes pelo Simples Nacional quando o leiaute IBSCBS estiver presente.\n'
    '\t\t\t\t1 – IBS e CBS apurados pelo Simples Nacional;\n'
    '\t\t\t\t2 – CBS pelo Simples Nacional e IBS fora do Simples Nacional;\n'
    '\t\t\t\t3 – IBS e CBS apurados fora do Simples Nacional.\n'
    '\t\t\t</xs:documentation>\n'
    '\t\t</xs:annotation>\n'
    '\t</xs:element>\n'
    '\t<xs:element name="regEspTrib" type="TSRegEspTrib">'
)


def patch_xsd_text(text: str) -> str:
    patched = text.replace(_BROKEN_TSSERIEDPS_PATTERN, _FIXED_TSSERIEDPS_PATTERN)
    patched = patched.replace(
        _TSOPSIMPNAC_BLOCK, _TSOPSIMPNAC_BLOCK_PATCHED
    ).replace(_TSOPSIMPNAC_BLOCK_TABBED, _TSOPSIMPNAC_BLOCK_PATCHED_TABBED)
    patched = patched.replace(
        _TCREGTRIB_INSERTION, _TCREGTRIB_INSERTION_PATCHED
    ).replace(_TCREGTRIB_INSERTION_TABBED, _TCREGTRIB_INSERTION_PATCHED_TABBED)
    return patched


def extract_and_patch(zip_path: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(tmp_dir)

        extracted_root = Path(tmp_dir)
        for source_path in extracted_root.rglob("*.xsd"):
            relative_path = source_path.relative_to(extracted_root)
            target_path = target_dir / relative_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(
                patch_xsd_text(source_path.read_text(encoding="utf-8")),
                encoding="utf-8",
            )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Patch the official NFSe XSD zip for local libxml2 validation."
    )
    parser.add_argument("zip_path", type=Path, help="Path to the official XSD zip")
    parser.add_argument(
        "target_dir",
        type=Path,
        help="Directory where vendored XSD files should be written",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    extract_and_patch(args.zip_path, args.target_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
