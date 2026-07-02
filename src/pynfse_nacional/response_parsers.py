"""Shared XML response parsers for NFSe Nacional."""

from __future__ import annotations

from decimal import Decimal
from typing import Optional
from xml.etree import ElementTree as ET

from .models_ibscbs import IBSCBS

NFSE_NAMESPACE = "http://www.sped.fazenda.gov.br/nfse"
NFSE_NAMESPACES = {"nfse": NFSE_NAMESPACE}


def parse_nfse_root(xml_content: str) -> ET.Element:
    """Parse XML once with the standard library parser."""

    return ET.fromstring(xml_content.encode("utf-8"))


def _expand_path(path: str) -> str:
    return path.replace("nfse:", f"{{{NFSE_NAMESPACE}}}")


def _find(element: ET.Element, path: str) -> Optional[ET.Element]:
    found = element.find(path, NFSE_NAMESPACES)
    if found is not None:
        return found
    return element.find(_expand_path(path))


def _text(element: ET.Element, path: str) -> str:
    found = _find(element, path)
    if found is not None and found.text:
        return found.text.strip()
    return ""


def extract_nfse_number(root: ET.Element) -> Optional[str]:
    """Extract nNFSe from a parsed response XML tree."""

    nfse_elem = root.find(".//nfse:nNFSe", NFSE_NAMESPACES)
    if nfse_elem is None:
        nfse_elem = root.find(f".//{{{NFSE_NAMESPACE}}}nNFSe")

    if nfse_elem is not None and nfse_elem.text:
        return nfse_elem.text.strip()

    return None


def parse_ibscbs(
    xml_content: str | None = None,
    *,
    root: ET.Element | None = None,
) -> Optional[IBSCBS]:
    """Parse the IBSCBS subtree from a response XML document.

    The caller may pass a pre-parsed root element to avoid reparsing the XML.
    Returns ``None`` when the subtree is absent or validation fails.
    """

    if root is None:
        if xml_content is None:
            raise ValueError("xml_content ou root deve ser informado.")

        root = parse_nfse_root(xml_content)

    ibscbs_elem = _find(root, ".//nfse:IBSCBS")
    if ibscbs_elem is None:
        return None

    try:
        valores_data: dict[str, object] = {
            "trib": {
                "g_ibscbs": {
                    "cst": _text(ibscbs_elem, ".//nfse:gIBSCBS/nfse:CST"),
                    "c_class_trib": _text(
                        ibscbs_elem, ".//nfse:gIBSCBS/nfse:cClassTrib"
                    ),
                }
            }
        }

        c_cred_pres = _text(ibscbs_elem, ".//nfse:gIBSCBS/nfse:cCredPres")
        if c_cred_pres:
            valores_data["trib"]["g_ibscbs"]["c_cred_pres"] = c_cred_pres

        g_trib_regular = _find(ibscbs_elem, ".//nfse:gIBSCBS/nfse:gTribRegular")
        if g_trib_regular is not None:
            valores_data["trib"]["g_ibscbs"]["g_trib_regular"] = {
                "cst_reg": _text(g_trib_regular, ".//nfse:CSTReg"),
                "c_class_trib_reg": _text(g_trib_regular, ".//nfse:cClassTribReg"),
            }

        g_dif = _find(ibscbs_elem, ".//nfse:gIBSCBS/nfse:gDif")
        if g_dif is not None:
            valores_data["trib"]["g_ibscbs"]["g_dif"] = {
                "p_dif_uf": Decimal(_text(g_dif, ".//nfse:pDifUF")),
                "p_dif_mun": Decimal(_text(g_dif, ".//nfse:pDifMun")),
                "p_dif_cbs": Decimal(_text(g_dif, ".//nfse:pDifCBS")),
            }

        g_ree_rep_res = _find(ibscbs_elem, ".//nfse:valores/nfse:gReeRepRes")
        if g_ree_rep_res is not None:
            documentos_data = []
            for documentos in g_ree_rep_res.findall("nfse:documentos", NFSE_NAMESPACES):
                documentos_item: dict[str, object] = {}

                dfe_nacional = _find(documentos, "./nfse:dFeNacional")
                if dfe_nacional is not None:
                    documentos_item["d_fe_nacional"] = {
                        "tipo_chave_dfe": _text(
                            dfe_nacional, "./nfse:tipoChaveDFe"
                        ),
                        "x_tipo_chave_dfe": _text(
                            dfe_nacional, "./nfse:xTipoChaveDFe"
                        )
                        or None,
                        "chave_dfe": _text(dfe_nacional, "./nfse:chaveDFe"),
                    }

                doc_fiscal_outro = _find(documentos, "./nfse:docFiscalOutro")
                if doc_fiscal_outro is not None:
                    documentos_item["doc_fiscal_outro"] = {
                        "c_mun_doc_fiscal": _text(
                            doc_fiscal_outro, "./nfse:cMunDocFiscal"
                        ),
                        "n_doc_fiscal": _text(
                            doc_fiscal_outro, "./nfse:nDocFiscal"
                        ),
                        "x_doc_fiscal": _text(
                            doc_fiscal_outro, "./nfse:xDocFiscal"
                        ),
                    }

                doc_outro = _find(documentos, "./nfse:docOutro")
                if doc_outro is not None:
                    documentos_item["doc_outro"] = {
                        "n_doc": _text(doc_outro, "./nfse:nDoc"),
                        "x_doc": _text(doc_outro, "./nfse:xDoc"),
                    }

                fornec = _find(documentos, "./nfse:fornec")
                if fornec is not None:
                    fornec_data: dict[str, object] = {
                        "x_nome": _text(fornec, "./nfse:xNome"),
                    }
                    for field in ("CNPJ", "CPF", "NIF", "cNaoNIF"):
                        value = _text(fornec, f"./nfse:{field}")
                        if value:
                            key = "c_nao_nif" if field == "cNaoNIF" else field.lower()
                            fornec_data[key] = value
                    documentos_item["fornec"] = fornec_data

                documentos_item["dt_emi_doc"] = _text(documentos, "./nfse:dtEmiDoc")
                documentos_item["dt_comp_doc"] = _text(
                    documentos, "./nfse:dtCompDoc"
                )
                documentos_item["tp_ree_rep_res"] = _text(
                    documentos, "./nfse:tpReeRepRes"
                )
                x_tp_ree_rep_res = _text(documentos, "./nfse:xTpReeRepRes")
                if x_tp_ree_rep_res:
                    documentos_item["x_tp_ree_rep_res"] = x_tp_ree_rep_res
                documentos_item["vlr_ree_rep_res"] = Decimal(
                    _text(documentos, "./nfse:vlrReeRepRes")
                )

                documentos_data.append(documentos_item)

            if documentos_data:
                valores_data["g_ree_rep_res"] = documentos_data

        data: dict[str, object] = {
            "fin_nfse": _text(ibscbs_elem, ".//nfse:finNFSe"),
            "ind_final": _text(ibscbs_elem, ".//nfse:indFinal") or None,
            "c_ind_op": _text(ibscbs_elem, ".//nfse:cIndOp"),
            "tp_oper": _text(ibscbs_elem, ".//nfse:tpOper") or None,
            "tp_ente_gov": _text(ibscbs_elem, ".//nfse:tpEnteGov") or None,
            "ind_dest": _text(ibscbs_elem, ".//nfse:indDest"),
            "valores": valores_data,
        }

        tp_nfse_credito = _text(ibscbs_elem, ".//nfse:tpNFSeCredito")
        if tp_nfse_credito:
            data["tp_nfse_credito"] = tp_nfse_credito

        tp_nfse_debito = _text(ibscbs_elem, ".//nfse:tpNFSeDebito")
        if tp_nfse_debito:
            data["tp_nfse_debito"] = tp_nfse_debito

        g_ref_nfse = _find(ibscbs_elem, ".//nfse:gRefNFSe")
        if g_ref_nfse is not None:
            refs = [
                child.text.strip()
                for child in g_ref_nfse.findall(".//nfse:refNFSe", NFSE_NAMESPACES)
                if child.text
            ]
            if not refs:
                refs = [
                    child.text.strip()
                    for child in g_ref_nfse.findall(
                        f".//{{{NFSE_NAMESPACE}}}refNFSe"
                    )
                    if child.text
                ]
            if refs:
                data["g_ref_nfse"] = {"ref_nfse": refs}

        dest = _find(ibscbs_elem, ".//nfse:dest")
        if dest is not None:
            dest_data: dict[str, object] = {
                "x_nome": _text(dest, ".//nfse:xNome"),
            }
            for field in ("CNPJ", "CPF", "NIF", "cNaoNIF"):
                value = _text(dest, f".//nfse:{field}")
                if value:
                    key = "c_nao_nif" if field == "cNaoNIF" else field.lower()
                    dest_data[key] = value

            end = _find(dest, ".//nfse:end")
            if end is not None:
                end_nac = _find(end, ".//nfse:endNac")
                if end_nac is not None:
                    dest_data["end"] = {
                        "codigo_municipio": int(_text(end_nac, ".//nfse:cMun") or "0"),
                        "cep": _text(end_nac, ".//nfse:CEP"),
                        "logradouro": _text(end, ".//nfse:xLgr"),
                        "numero": _text(end, ".//nfse:nro"),
                        "bairro": _text(end, ".//nfse:xBairro"),
                        "complemento": _text(end, ".//nfse:xCpl") or None,
                    }

            fone = _text(dest, ".//nfse:fone")
            if fone:
                dest_data["fone"] = fone

            email = _text(dest, ".//nfse:email")
            if email:
                dest_data["email"] = email

            if len(dest_data) > 1:
                data["dest"] = dest_data

        imovel = _find(ibscbs_elem, ".//nfse:imovel")
        if imovel is not None:
            imovel_data: dict[str, object] = {}
            insc_imob_fisc = _text(imovel, ".//nfse:inscImobFisc")
            if insc_imob_fisc:
                imovel_data["insc_imob_fisc"] = insc_imob_fisc

            c_cib = _text(imovel, ".//nfse:cCIB")
            if c_cib:
                imovel_data["c_cib"] = c_cib
            else:
                end = _find(imovel, ".//nfse:end")
                if end is not None:
                    end_nac = _find(end, ".//nfse:endNac")
                    if end_nac is not None:
                        imovel_data["end"] = {
                            "codigo_municipio": int(
                                _text(end_nac, ".//nfse:cMun") or "0"
                            ),
                            "cep": _text(end_nac, ".//nfse:CEP"),
                            "logradouro": _text(end, ".//nfse:xLgr"),
                            "numero": _text(end, ".//nfse:nro"),
                            "bairro": _text(end, ".//nfse:xBairro"),
                            "complemento": _text(end, ".//nfse:xCpl") or None,
                        }

            if imovel_data:
                data["imovel"] = imovel_data

        return IBSCBS.model_validate(data)

    except Exception:
        return None
