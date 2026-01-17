import base64
import gzip
import re


def compress_encode(data: str) -> str:
    """Compress with GZip and encode with Base64."""
    compressed = gzip.compress(data.encode("utf-8"))
    return base64.b64encode(compressed).decode("ascii")


# Alias for consistency with __init__.py exports
compress_and_encode = compress_encode


def decode_decompress(data: str) -> str:
    """Decode Base64 and decompress GZip."""
    decoded = base64.b64decode(data)
    return gzip.decompress(decoded).decode("utf-8")


# Alias for consistency with __init__.py exports
decode_and_decompress = decode_decompress


def validate_cnpj(cnpj: str) -> bool:
    """Validate Brazilian CNPJ number."""
    cnpj = re.sub(r"[^0-9]", "", cnpj)

    if len(cnpj) != 14:
        return False

    if cnpj == cnpj[0] * 14:
        return False

    def calc_digit(cnpj_partial: str, weights: list) -> int:
        total = sum(int(c) * w for c, w in zip(cnpj_partial, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    d1 = calc_digit(cnpj[:12], weights1)
    d2 = calc_digit(cnpj[:12] + str(d1), weights2)

    return cnpj[-2:] == f"{d1}{d2}"


def validate_cpf(cpf: str) -> bool:
    """Validate Brazilian CPF number."""
    cpf = re.sub(r"[^0-9]", "", cpf)

    if len(cpf) != 11:
        return False

    if cpf == cpf[0] * 11:
        return False

    def calc_digit(cpf_partial: str, factor: int) -> int:
        total = sum(int(c) * (factor - i) for i, c in enumerate(cpf_partial))
        remainder = (total * 10) % 11
        return 0 if remainder >= 10 else remainder

    d1 = calc_digit(cpf[:9], 10)
    d2 = calc_digit(cpf[:9] + str(d1), 11)

    return cpf[-2:] == f"{d1}{d2}"


def format_cnpj(cnpj: str) -> str:
    """Format CNPJ with punctuation."""
    cnpj = re.sub(r"[^0-9]", "", cnpj)

    if len(cnpj) != 14:
        return cnpj

    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"


def normalize_document(doc: str) -> str:
    """Remove all non-numeric characters from document."""
    return re.sub(r"[^0-9]", "", doc)


# Alias for consistency with __init__.py exports
clean_document = normalize_document


def format_cpf(cpf: str) -> str:
    """Format CPF with punctuation."""
    cpf = re.sub(r"[^0-9]", "", cpf)

    if len(cpf) != 11:
        return cpf

    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
