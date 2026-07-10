"""XML builder for NFSe DPS and events."""

# Canonical sources (verify before changing):
#   Pinned URLs and sha256 hashes live in src/pynfse_nacional/_canonical.py.
#   XSD: nfse-esquemas_xsd-v1-01-20260209.zip
#   Manual: manual-contribuintes-emissor-publico-api-sistema-nacional-
#   nfs-e-v1-2-out2025.pdf

import warnings
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from .constants import Ambiente
from .models import DPS

if TYPE_CHECKING:
    from .models import Endereco, EnderecoIBSCBS

try:
    _VERAPLIC = f"pynfse-{_pkg_version('pynfse-nacional')}"
except PackageNotFoundError:
    _VERAPLIC = "pynfse-0.5.0"


class XMLBuilder:
    """Build DPS XML for NFSe Nacional submission."""

    NAMESPACE = "http://www.sped.fazenda.gov.br/nfse"
    NAMESPACE_MAP = {"": NAMESPACE}

    # Cancellation event type code.
    # XSD element: e101101, TSIdPedRegEvt pattern PRE[0-9]{56}
    _EVENT_TYPE_CANCEL = "101101"

    def __init__(self, ambiente: Ambiente = Ambiente.HOMOLOGACAO):
        self.ambiente = ambiente

    def _build_dps_id(self, dps: DPS) -> str:
        """Build DPS ID in the correct format.

        Format: DPS + cLocEmi(7) + tpInsc(1) + CNPJ(14) + serie(5) + nDPS(15)
        - cLocEmi: IBGE municipality code (7 digits)
        - tpInsc: 1=CPF, 2=CNPJ
        - CNPJ: 14 digits
        - serie: 5 digits (zero-padded)
        - nDPS: 15 digits (zero-padded)
        """
        return dps.build_dps_id()

    def build_dps(self, dps: DPS) -> str:
        """Build DPS XML from model."""
        root = ET.Element("DPS", versao="1.01", xmlns=self.NAMESPACE)

        # Generate correct DPS ID if not provided or use provided one
        dps_id = dps.id_dps if dps.id_dps else self._build_dps_id(dps)
        inf_dps = ET.SubElement(root, "infDPS", Id=dps_id)

        # DPS tpAmb follows submission environment.
        tp_amb = "1" if self.ambiente == Ambiente.PRODUCAO else "2"
        ET.SubElement(inf_dps, "tpAmb").text = tp_amb
        ET.SubElement(inf_dps, "dhEmi").text = dps.data_emissao.strftime(
            "%Y-%m-%dT%H:%M:%S-03:00"
        )
        ET.SubElement(inf_dps, "verAplic").text = _VERAPLIC
        ET.SubElement(inf_dps, "serie").text = dps.serie
        ET.SubElement(inf_dps, "nDPS").text = str(dps.numero)
        ET.SubElement(inf_dps, "dCompet").text = dps.data_emissao.strftime("%Y-%m-%d")
        ET.SubElement(inf_dps, "tpEmit").text = "1"
        ET.SubElement(inf_dps, "cLocEmi").text = str(
            dps.prestador.endereco.codigo_municipio
        )

        # Add substitution info if present (must come before prest)
        if dps.substituicao:
            self._add_substituicao(inf_dps, dps)

        self._add_prestador(inf_dps, dps)
        self._add_tomador(inf_dps, dps)
        self._add_servico(inf_dps, dps)
        self._add_valores(inf_dps, dps)
        self._add_ibscbs(inf_dps, dps)

        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def build_cancel_event(
        self,
        chave_acesso: str,
        reason: str,
        codigo_motivo: int = 1,
        cnpj_prestador: str = "",
    ) -> str:
        """Build pedRegEvento XML for NFSe cancellation (event type e101101).

        Args:
            chave_acesso: 50-digit NFSe access key.
            reason: Free-text cancellation reason (max 255 chars).
            codigo_motivo: Cancellation reason code (1=erro na emissão,
                2=serviço não prestado, 4=duplicidade). Default 1.
            cnpj_prestador: CNPJ of the service provider (14 digits).
                Used in the CNPJAutor field. May be empty if not available.

        Returns:
            XML string for the cancellation event (unsigned).
        """
        # Id format: PRE + chNFSe (50 digits) + event type code (6 digits)
        # XSD type TSIdPedRegEvt pattern: PRE[0-9]{56} (total 59 chars)
        event_id = f"PRE{chave_acesso}{self._EVENT_TYPE_CANCEL}"

        brt = timezone(timedelta(hours=-3))
        dh_evento = datetime.now(tz=brt).strftime("%Y-%m-%dT%H:%M:%S-03:00")

        tp_amb = "1" if self.ambiente == Ambiente.PRODUCAO else "2"

        root = ET.Element("pedRegEvento", versao="1.00", xmlns=self.NAMESPACE)

        inf_ped_reg = ET.SubElement(root, "infPedReg", Id=event_id)
        ET.SubElement(inf_ped_reg, "tpAmb").text = tp_amb
        ET.SubElement(inf_ped_reg, "verAplic").text = _VERAPLIC
        ET.SubElement(inf_ped_reg, "dhEvento").text = dh_evento

        if cnpj_prestador:
            ET.SubElement(inf_ped_reg, "CNPJAutor").text = cnpj_prestador

        ET.SubElement(inf_ped_reg, "chNFSe").text = chave_acesso

        e101101 = ET.SubElement(inf_ped_reg, "e101101")
        ET.SubElement(e101101, "xDesc").text = "Cancelamento de NFS-e"
        ET.SubElement(e101101, "cMotivo").text = str(codigo_motivo)
        ET.SubElement(e101101, "xMotivo").text = reason[:255]

        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def _add_substituicao(self, parent: ET.Element, dps: DPS) -> None:
        """Add substitution information to DPS XML.

        This element references the NFSe being substituted and the reason.
        """
        subst = dps.substituicao

        inf_subst = ET.SubElement(parent, "subst")
        ET.SubElement(inf_subst, "chSubstda").text = subst.chave_nfse_substituida
        ET.SubElement(inf_subst, "cMotivo").text = str(subst.codigo_motivo)
        ET.SubElement(inf_subst, "xMotivo").text = subst.motivo

    def _add_prestador(self, parent: ET.Element, dps: DPS) -> None:
        prest = ET.SubElement(parent, "prest")
        ET.SubElement(prest, "CNPJ").text = dps.prestador.cnpj

        # IM padded with spaces to 15 chars as seen in real NFSe
        if dps.prestador.inscricao_municipal:
            im_padded = dps.prestador.inscricao_municipal.rjust(15)
            ET.SubElement(prest, "IM").text = im_padded

        if dps.prestador.telefone:
            ET.SubElement(prest, "fone").text = dps.prestador.telefone

        if dps.prestador.email:
            ET.SubElement(prest, "email").text = dps.prestador.email

        reg_trib = ET.SubElement(prest, "regTrib")

        # opSimpNac: 1=Não Optante, 2=MEI, 3=ME/EPP (official TSOpSimpNac)
        ET.SubElement(reg_trib, "opSimpNac").text = dps.op_simp_nac

        # regApTribSN: only valid for opSimpNac 3 (official TCRegTrib)
        if dps.op_simp_nac == "3":
            ET.SubElement(reg_trib, "regApTribSN").text = dps.reg_ap_trib_sn

        ET.SubElement(reg_trib, "regEspTrib").text = self._map_regime_especial(
            dps.regime_tributario
        )

    def _add_tomador(self, parent: ET.Element, dps: DPS) -> None:
        toma = ET.SubElement(parent, "toma")

        if dps.tomador.cpf:
            ET.SubElement(toma, "CPF").text = dps.tomador.cpf
        elif dps.tomador.cnpj:
            ET.SubElement(toma, "CNPJ").text = dps.tomador.cnpj

        ET.SubElement(toma, "xNome").text = dps.tomador.razao_social

        if dps.tomador.endereco:
            self._emit_endereco(toma, dps.tomador.endereco)

    def _add_servico(self, parent: ET.Element, dps: DPS) -> None:
        serv = ET.SubElement(parent, "serv")

        loc_prest = ET.SubElement(serv, "locPrest")
        ET.SubElement(loc_prest, "cLocPrestacao").text = str(
            dps.prestador.endereco.codigo_municipio
        )

        c_serv = ET.SubElement(serv, "cServ")
        codigo = dps.servico.codigo_lc116.replace(".", "")
        ET.SubElement(c_serv, "cTribNac").text = codigo.zfill(6)

        # cTribMun - municipal code (optional but used in real NFSe)
        if dps.servico.codigo_tributacao_municipal:
            ET.SubElement(
                c_serv, "cTribMun"
            ).text = dps.servico.codigo_tributacao_municipal

        ET.SubElement(c_serv, "xDescServ").text = dps.servico.discriminacao

        # cNBS - NBS code (optional but used in real NFSe)
        if dps.servico.codigo_nbs:
            ET.SubElement(c_serv, "cNBS").text = dps.servico.codigo_nbs

    def _add_valores(self, parent: ET.Element, dps: DPS) -> None:
        valores = ET.SubElement(parent, "valores")

        v_serv_prest = ET.SubElement(valores, "vServPrest")
        ET.SubElement(v_serv_prest, "vServ").text = self._format_decimal(
            dps.servico.valor_servicos
        )

        trib = ET.SubElement(valores, "trib")

        trib_mun = ET.SubElement(trib, "tribMun")
        ET.SubElement(trib_mun, "tribISSQN").text = "1"

        # tpRetISSQN: 1=Não Retido, 2=Retido Tomador, 3=Retido Intermediário
        ET.SubElement(trib_mun, "tpRetISSQN").text = (
            "2" if dps.servico.iss_retido else "1"
        )

        tot_trib = ET.SubElement(trib, "totTrib")

        # For Simples Nacional ME/EPP, use pTotTribSN with estimated tax percentage
        if dps.op_simp_nac == "3":
            # Use aliquota_simples from servico or default to 18.83%
            if dps.servico.aliquota_simples:
                aliquota_sn = dps.servico.aliquota_simples
            else:
                aliquota_sn = Decimal("18.83")

                warnings.warn(
                    "alíquota_simples não informada, usando 18,83% padrão. "
                    "Defina servico.aliquota_simples com a alíquota correta "
                    "para a sua empresa.",
                    UserWarning,
                    stacklevel=3,
                )

            ET.SubElement(tot_trib, "pTotTribSN").text = self._format_decimal(
                aliquota_sn
            )
        else:
            # For non-Simples, use percentage breakdown
            p_tot_trib = ET.SubElement(tot_trib, "pTotTrib")
            ET.SubElement(p_tot_trib, "pTotTribFed").text = "0"
            ET.SubElement(p_tot_trib, "pTotTribEst").text = "0"
            ET.SubElement(p_tot_trib, "pTotTribMun").text = "0"

    def _emit_endereco(
        self, parent: ET.Element, endereco: "Endereco | EnderecoIBSCBS"
    ) -> None:
        end = ET.SubElement(parent, "end")
        end_nac = ET.SubElement(end, "endNac")
        ET.SubElement(end_nac, "cMun").text = str(endereco.codigo_municipio)
        ET.SubElement(end_nac, "CEP").text = endereco.cep
        ET.SubElement(end, "xLgr").text = endereco.logradouro
        ET.SubElement(end, "nro").text = endereco.numero
        if endereco.complemento:
            ET.SubElement(end, "xCpl").text = endereco.complemento
        ET.SubElement(end, "xBairro").text = endereco.bairro

    def _add_ibscbs(self, parent: ET.Element, dps: DPS) -> None:
        if not dps.ibscbs:
            return

        ibscbs = dps.ibscbs
        inf_ibscbs = ET.SubElement(parent, "IBSCBS")

        ET.SubElement(inf_ibscbs, "finNFSe").text = ibscbs.fin_nfse
        if ibscbs.ind_final is not None:
            ET.SubElement(inf_ibscbs, "indFinal").text = ibscbs.ind_final

        ET.SubElement(inf_ibscbs, "cIndOp").text = ibscbs.c_ind_op

        if ibscbs.tp_oper is not None:
            ET.SubElement(inf_ibscbs, "tpOper").text = ibscbs.tp_oper

        if ibscbs.g_ref_nfse is not None:
            g_ref_nfse = ET.SubElement(inf_ibscbs, "gRefNFSe")
            for ref_nfse in ibscbs.g_ref_nfse.ref_nfse:
                ET.SubElement(g_ref_nfse, "refNFSe").text = ref_nfse

        if ibscbs.tp_ente_gov is not None:
            ET.SubElement(inf_ibscbs, "tpEnteGov").text = ibscbs.tp_ente_gov

        ET.SubElement(inf_ibscbs, "indDest").text = ibscbs.ind_dest

        if ibscbs.dest is not None:
            dest = ET.SubElement(inf_ibscbs, "dest")
            if ibscbs.dest.cnpj:
                ET.SubElement(dest, "CNPJ").text = ibscbs.dest.cnpj
            elif ibscbs.dest.cpf:
                ET.SubElement(dest, "CPF").text = ibscbs.dest.cpf
            elif ibscbs.dest.nif:
                ET.SubElement(dest, "NIF").text = ibscbs.dest.nif
            elif ibscbs.dest.c_nao_nif:
                ET.SubElement(dest, "cNaoNIF").text = ibscbs.dest.c_nao_nif

            ET.SubElement(dest, "xNome").text = ibscbs.dest.x_nome

            if ibscbs.dest.end is not None:
                self._emit_endereco(dest, ibscbs.dest.end)

            if ibscbs.dest.fone is not None:
                ET.SubElement(dest, "fone").text = ibscbs.dest.fone
            if ibscbs.dest.email is not None:
                ET.SubElement(dest, "email").text = ibscbs.dest.email

        if ibscbs.imovel is not None:
            imovel = ET.SubElement(inf_ibscbs, "imovel")
            if ibscbs.imovel.insc_imob_fisc is not None:
                ET.SubElement(
                    imovel, "inscImobFisc"
                ).text = ibscbs.imovel.insc_imob_fisc
            if ibscbs.imovel.c_cib is not None:
                ET.SubElement(imovel, "cCIB").text = ibscbs.imovel.c_cib
            elif ibscbs.imovel.end is not None:
                self._emit_endereco(imovel, ibscbs.imovel.end)

        valores = ET.SubElement(inf_ibscbs, "valores")

        if ibscbs.valores.g_ree_rep_res:
            g_ree_rep_res = ET.SubElement(valores, "gReeRepRes")
            for item in ibscbs.valores.g_ree_rep_res:
                documentos = ET.SubElement(g_ree_rep_res, "documentos")

                if item.d_fe_nacional is not None:
                    d_fe_nacional = ET.SubElement(documentos, "dFeNacional")
                    ET.SubElement(
                        d_fe_nacional, "tipoChaveDFe"
                    ).text = item.d_fe_nacional.tipo_chave_dfe
                    if item.d_fe_nacional.x_tipo_chave_dfe is not None:
                        ET.SubElement(
                            d_fe_nacional, "xTipoChaveDFe"
                        ).text = item.d_fe_nacional.x_tipo_chave_dfe
                    ET.SubElement(
                        d_fe_nacional, "chaveDFe"
                    ).text = item.d_fe_nacional.chave_dfe
                elif item.doc_fiscal_outro is not None:
                    doc_fiscal_outro = ET.SubElement(documentos, "docFiscalOutro")
                    ET.SubElement(
                        doc_fiscal_outro, "cMunDocFiscal"
                    ).text = item.doc_fiscal_outro.c_mun_doc_fiscal
                    ET.SubElement(
                        doc_fiscal_outro, "nDocFiscal"
                    ).text = item.doc_fiscal_outro.n_doc_fiscal
                    ET.SubElement(
                        doc_fiscal_outro, "xDocFiscal"
                    ).text = item.doc_fiscal_outro.x_doc_fiscal
                elif item.doc_outro is not None:
                    doc_outro = ET.SubElement(documentos, "docOutro")
                    ET.SubElement(doc_outro, "nDoc").text = item.doc_outro.n_doc
                    ET.SubElement(doc_outro, "xDoc").text = item.doc_outro.x_doc

                if item.fornec is not None:
                    fornec = ET.SubElement(documentos, "fornec")
                    if item.fornec.cnpj is not None:
                        ET.SubElement(fornec, "CNPJ").text = item.fornec.cnpj
                    elif item.fornec.cpf is not None:
                        ET.SubElement(fornec, "CPF").text = item.fornec.cpf
                    elif item.fornec.nif is not None:
                        ET.SubElement(fornec, "NIF").text = item.fornec.nif
                    elif item.fornec.c_nao_nif is not None:
                        ET.SubElement(fornec, "cNaoNIF").text = item.fornec.c_nao_nif
                    ET.SubElement(fornec, "xNome").text = item.fornec.x_nome

                ET.SubElement(documentos, "dtEmiDoc").text = item.dt_emi_doc.isoformat()
                ET.SubElement(
                    documentos, "dtCompDoc"
                ).text = item.dt_comp_doc.isoformat()
                ET.SubElement(documentos, "tpReeRepRes").text = item.tp_ree_rep_res
                if item.x_tp_ree_rep_res is not None:
                    ET.SubElement(
                        documentos, "xTpReeRepRes"
                    ).text = item.x_tp_ree_rep_res
                ET.SubElement(documentos, "vlrReeRepRes").text = self._format_decimal(
                    item.vlr_ree_rep_res
                )

        trib = ET.SubElement(valores, "trib")
        g_ibscbs = ET.SubElement(trib, "gIBSCBS")
        ET.SubElement(g_ibscbs, "CST").text = ibscbs.valores.trib.g_ibscbs.cst
        ET.SubElement(
            g_ibscbs, "cClassTrib"
        ).text = ibscbs.valores.trib.g_ibscbs.c_class_trib

        if ibscbs.valores.trib.g_ibscbs.c_cred_pres is not None:
            ET.SubElement(
                g_ibscbs, "cCredPres"
            ).text = ibscbs.valores.trib.g_ibscbs.c_cred_pres

        if ibscbs.valores.trib.g_ibscbs.g_trib_regular is not None:
            g_trib_regular = ET.SubElement(g_ibscbs, "gTribRegular")
            ET.SubElement(
                g_trib_regular, "CSTReg"
            ).text = ibscbs.valores.trib.g_ibscbs.g_trib_regular.cst_reg
            ET.SubElement(
                g_trib_regular, "cClassTribReg"
            ).text = ibscbs.valores.trib.g_ibscbs.g_trib_regular.c_class_trib_reg

        if ibscbs.valores.trib.g_ibscbs.g_dif is not None:
            g_dif = ET.SubElement(g_ibscbs, "gDif")
            ET.SubElement(g_dif, "pDifUF").text = self._format_decimal(
                ibscbs.valores.trib.g_ibscbs.g_dif.p_dif_uf
            )
            ET.SubElement(g_dif, "pDifMun").text = self._format_decimal(
                ibscbs.valores.trib.g_ibscbs.g_dif.p_dif_mun
            )
            ET.SubElement(g_dif, "pDifCBS").text = self._format_decimal(
                ibscbs.valores.trib.g_ibscbs.g_dif.p_dif_cbs
            )

    def _format_decimal(self, value: Decimal) -> str:
        return f"{value:.2f}"

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
