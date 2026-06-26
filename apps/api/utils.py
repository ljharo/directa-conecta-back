import unicodedata


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s or "").strip().lower())
    return "".join(c for c in s if not unicodedata.combining(c))


def _build_map(choices_class):
    """Devuelve dict normalizado → valor interno, aceptando valor Y label."""
    m = {}
    for value, label in choices_class.choices:
        m[_norm(value)] = value
        m[_norm(label)] = value
    return m


def _resolve(raw, mapping):
    """Resuelve raw al valor interno del choice o devuelve None si no existe."""
    if not raw:
        return ""
    key = _norm(raw)
    if key in mapping:
        return mapping[key]
    for norm_key, value in mapping.items():
        if norm_key.startswith(key) or key.startswith(norm_key):
            return value
    return None
