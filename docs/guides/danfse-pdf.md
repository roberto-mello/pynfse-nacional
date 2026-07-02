# DANFSe PDF

Há duas formas de gerar o DANFSe:

1. baixar o PDF pela API oficial;
2. gerar localmente a partir do XML retornado.

## Via API oficial

```python
pdf_bytes = client.download_danfse(
    "[REDACTED-ACCESS-KEY]"
)
```

Essa rota depende do serviço oficial de DANFSe. Se a API estiver fora do ar,
use a geração local.

## Geração local

```python
from pynfse_nacional.pdf_generator import (
    HeaderConfig,
    generate_danfse_from_base64,
    generate_danfse_from_xml,
)

response = client.submit_dps(dps)

if response.success and response.nfse_xml_gzip_b64:
    pdf_bytes = generate_danfse_from_base64(
        nfse_xml_gzip_b64=response.nfse_xml_gzip_b64,
        output_path="/caminho/para/danfse.pdf",
    )
```

Ou, se você já tiver o XML em texto:

```python
pdf_bytes = generate_danfse_from_xml(
    xml_content=response.xml_nfse,
    output_path="/caminho/para/danfse.pdf",
)
```

## Cabeçalho personalizado

```python
header = HeaderConfig(
    image_path="/caminho/para/logo.png",
    title="Nome da Empresa",
    subtitle="Serviços Médicos",
    phone="(11) 99999-9999",
    email="contato@empresa.com",
)

pdf_bytes = generate_danfse_from_base64(
    nfse_xml_gzip_b64=response.nfse_xml_gzip_b64,
    output_path="/caminho/para/danfse.pdf",
    header_config=header,
)
```

## Dependência opcional

Para usar a geração local, instale o extra:

```bash
uv add "pynfse-nacional[pdf]"
```

