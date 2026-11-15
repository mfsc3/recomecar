import hashlib

from django.core.cache import cache


def permitido(escopo, identificador, limite, janela):
    digest = hashlib.sha256(str(identificador).encode('utf-8')).hexdigest()
    key = f'rl:{escopo}:{digest}'
    if cache.add(key, 1, janela):
        return True
    try:
        count = cache.incr(key)
    except ValueError:
        cache.add(key, 1, janela)
        count = 1
    return count <= limite
