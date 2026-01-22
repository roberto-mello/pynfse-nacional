# NFSe Nacional - Debug Session Summary

## Date: 2026-01-18

## Current Issue

**Error:** E1226 - "Estrutura descompactada mal formada" (Malformed decompressed structure)

The API is receiving our request but rejecting the XML structure.

## What's Working

1. Certificate loading from PKCS12 (.pfx) file
2. XML digital signature using signxml library
3. GZIP compression and Base64 encoding
4. HTTP client with mTLS authentication
5. API communication (getting proper error responses)

## Current Configuration

### API Endpoints (constants.py)
- Homologacao: `https://sefin.producaorestrita.nfse.gov.br/SefinNacional`
- Submit DPS: `/nfse` (POST)

### Certificate Info
- Path: `ronald/DR RONALDO S L80OUS6LL02XV7.pfx`
- Password: `L80OUS6LL02XV7`
- CNPJ from cert: `42713924000185`
- Inscricao Municipal: `51034401`

### Test Data
- Municipio: Manaus/AM - codigo `1302603`
- Codigo LC116: `04.03.03` (Clinicas, sanatorios)
- Codigo CNAE: `8630503`

## Files Modified

1. `src/pynfse_nacional/xml_builder.py` - Rebuilt to match NFSe Nacional schema
2. `src/pynfse_nacional/xml_signer.py` - Fixed to:
   - Parse XML string to lxml element
   - Sign the infDPS element (signature inside infDPS)
   - Use reference_uri pointing to infDPS Id
   - Use C14N canonicalization
3. `src/pynfse_nacional/constants.py` - Fixed API URLs
4. `src/pynfse_nacional/client.py` - Better error message handling
5. `ronald/test_nfse.py` - Test script with real data

## Current XML Structure Generated

```xml
<?xml version='1.0' encoding='utf-8'?>
<DPS xmlns="http://www.sped.fazenda.gov.br/nfse" versao="1.00">
  <infDPS Id="DPS1302603142713924000185000NF000000000000001">
    <tpAmb>2</tpAmb>
    <dhEmi>2026-01-18T20:30:00-03:00</dhEmi>
    <verAplic>pynfse-1.0</verAplic>
    <serie>NF</serie>
    <nDPS>1</nDPS>
    <dCompet>2026-01-18</dCompet>
    <tpEmit>1</tpEmit>
    <cLocEmi>1302603</cLocEmi>
    <prest>
      <CNPJ>42713924000185</CNPJ>
      <IM>51034401</IM>
      <regTrib>
        <opSimpNac>1</opSimpNac>
        <regEspTrib>0</regEspTrib>
      </regTrib>
    </prest>
    <toma>
      <CPF>52998224725</CPF>
      <xNome>Cliente Teste</xNome>
    </toma>
    <serv>
      <locPrest>
        <cLocPrestacao>1302603</cLocPrestacao>
      </locPrest>
      <cServ>
        <cTribNac>040303</cTribNac>
        <xDescServ>Consultas psiquiatricas...</xDescServ>
      </cServ>
    </serv>
    <valores>
      <vServPrest>
        <vServ>500.00</vServ>
      </vServPrest>
      <trib>
        <tribMun>
          <tribISSQN>1</tribISSQN>
          <tpRetISSQN>2</tpRetISSQN>
        </tribMun>
        <totTrib>
          <pTotTrib>
            <pTotTribFed>0</pTotTribFed>
            <pTotTribEst>0</pTotTribEst>
            <pTotTribMun>0</pTotTribMun>
          </pTotTrib>
        </totTrib>
      </trib>
    </valores>
    <ds:Signature>...</ds:Signature>
  </infDPS>
</DPS>
```

## DPS ID Format

Format: `DPS{cLocEmi:7}{type:1}{CNPJ:14}{serie:5}{numero:15}` = 45 chars total

Example: `DPS1302603142713924000185000NF000000000000001`

## Next Steps to Debug

1. **Download and validate against official XSD schema:**
   - URL: https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260101.zip
   - Validate our XML against the DPS XSD

2. **Compare XML element order** - XSD schemas are strict about element order

3. **Check for missing required fields** - The schema may require fields we're not including

4. **Verify namespace handling** - Make sure namespaces are correctly applied

5. **Check signature format** - NFSe Nacional may have specific signature requirements

## Reference XML (Working Example)

From https://github.com/nfe/poc-nfse-nacional:

```xml
<DPS versao="1.00" xmlns="http://www.sped.fazenda.gov.br/nfse">
  <infDPS Id="DPS140015924771279500012400900000001028360962">
    <tpAmb>2</tpAmb>
    <dhEmi>2022-09-21T11:25:21-03:00</dhEmi>
    <verAplic>POC_0.0.0</verAplic>
    <serie>900</serie>
    <nDPS>1028360962</nDPS>
    <dCompet>2022-09-21</dCompet>
    <tpEmit>1</tpEmit>
    <cLocEmi>1400159</cLocEmi>
    <prest>
      <CNPJ>47712795000124</CNPJ>
      <IM>47712795000124</IM>
      <regTrib>
        <opSimpNac>1</opSimpNac>
        <regEspTrib>1</regEspTrib>
      </regTrib>
    </prest>
    <toma>
      <CPF>16690232816</CPF>
      <IM>999999999</IM>
      <xNome>ROSIO VICTORIA GONZALES SANCHEZ</xNome>
      <end>
        <endNac>
          <cMun>1400159</cMun>
          <CEP>69380000</CEP>
        </endNac>
        <xLgr>Rua Sem Nome</xLgr>
        <nro>098</nro>
        <xCpl>APTO 1234</xCpl>
        <xBairro>Bairro Sem Nome</xBairro>
      </end>
    </toma>
    <serv>
      <locPrest>
        <cLocPrestacao>1400159</cLocPrestacao>
      </locPrest>
      <cServ>
        <cTribNac>010301</cTribNac>
        <xDescServ>...</xDescServ>
      </cServ>
    </serv>
    <valores>
      <vServPrest>
        <vServ>6.73</vServ>
      </vServPrest>
      <trib>
        <tribMun>
          <tribISSQN>1</tribISSQN>
          <tpRetISSQN>1</tpRetISSQN>
        </tribMun>
        <totTrib>
          <pTotTrib>
            <pTotTribFed>1</pTotTribFed>
            <pTotTribEst>1</pTotTribEst>
            <pTotTribMun>1</pTotTribMun>
          </pTotTrib>
        </totTrib>
      </trib>
    </valores>
  </infDPS>
</DPS>
```

## Key Differences to Investigate

1. Reference has `<IM>` inside `<toma>` - we don't have this
2. Reference has full `<end>` address for tomador - we only add if endereco exists
3. The `pTotTrib` values are `1` in reference, we use `0`

## Commands to Run Test

```bash
cd /Users/rbm/Documents/projects/pynfse-nacional
uv run python ronald/test_nfse.py
```

## Resources

### Official Documentation (Current)
- **All Documentation:** https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual
- **XSD Schemas:** https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/documentacao-atual/nfse-esquemas_xsd-v1-01-20260101.zip
- **API Docs:** https://www.gov.br/nfse/pt-br/biblioteca/documentacao-tecnica/apis-prod-restrita-e-producao

### Community Resources
- Reference Implementation: https://github.com/nfe/poc-nfse-nacional
- PHP Library: https://github.com/nfse-nacional/nfse-php
