import re

from django.core.exceptions import ValidationError


def validar_cnpj(valor: str) -> str:
    """Retorna o CNPJ só com dígitos ou levanta ValidationError."""
    cnpj = re.sub(r'\D', '', valor or '')
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        raise ValidationError('CNPJ inválido.')

    def dv(base, pesos):
        resto = sum(int(d) * p for d, p in zip(base, pesos)) % 11
        return '0' if resto < 2 else str(11 - resto)

    d1 = dv(cnpj[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = dv(cnpj[:12] + d1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    if cnpj[12:] != d1 + d2:
        raise ValidationError('CNPJ inválido.')
    return cnpj
