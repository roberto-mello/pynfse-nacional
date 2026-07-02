# IBSCBS

IBSCBS entra na DPS quando o serviço exige o leiaute RTC do NFSe Nacional.
Os modelos ficam em `pynfse_nacional.models_ibscbs`.

## Exemplo mínimo

```python
from pynfse_nacional import (
    GIBSCBS,
    IBSCBS,
    TribIBSCBS,
    ValoresIBSCBS,
)

# Assuma que `dps` já foi montada no fluxo da DPS.
dps.ibscbs = IBSCBS(
    fin_nfse="0",
    c_ind_op="020101",
    ind_dest="0",
    valores=ValoresIBSCBS(
        trib=TribIBSCBS(
            g_ibscbs=GIBSCBS(
                cst="001",
                c_class_trib="123456",
            )
        )
    ),
)
```

## Regras principais

- `c_ind_op` precisa existir na tabela oficial do anexo IBSCBS.
- `op_simp_nac="3"` e `"4"` exigem `reg_ap_trib_sn` e
  `reg_ap_ibs_cbs_sn`.
- `op_simp_nac="1"` e `"2"` não aceitam esses campos.
- Se o XML retornar IBSCBS na resposta, a biblioteca também consegue parsear
  esses dados.

## Quando vale usar

Use este bloco quando a DPS precisar carregar a estrutura tributária completa
do novo layout e você quiser manter a geração e a leitura do XML no mesmo
pacote.
