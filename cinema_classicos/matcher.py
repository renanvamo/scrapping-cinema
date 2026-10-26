"""Cruzamento de títulos: normaliza e compara com a lista de clássicos."""
import re
import unicodedata
from difflib import SequenceMatcher

# Ruído comum em títulos de programação (formato, idioma, etc.)
_NOISE = re.compile(
    r"\b(dublado|legendado|dub|leg|3d|2d|xd|imax|4dx|d-?box|prime|vip|"
    r"cine ?cl[aá]ssicos?|cl[aá]ssicos?|reexibi[cç][aã]o|re-?estreia|"
    r"sess[aã]o especial|nacional|remasterizado|\d+ ?anos?)\b"
)


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c)).lower()
    text = re.sub(r"\([^)]*\)", " ", text)          # remove (2001), (dublado)...
    text = _NOISE.sub(" ", text)
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    text = re.sub(r"\b(o|a|os|as|e|de|do|da|dos|das|the|of|and)\b", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _tokens(s: str) -> set:
    return set(s.split())


def score(a: str, b: str) -> float:
    """Similaridade 0..1 entre dois títulos já normalizados."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    seq = SequenceMatcher(None, a, b).ratio()
    ta, tb = _tokens(a), _tokens(b)
    # Números/"parte 2"/"2" precisam bater: evita confundir Harry Potter 1 com 2.
    na = {t for t in ta if t.isdigit()}
    nb = {t for t in tb if t.isdigit()}
    if na != nb:
        return min(seq, 0.6)
    return seq


class Matcher:
    def __init__(self, movies: list, threshold: float = 0.88):
        self.threshold = threshold
        self.entries = []  # (titulo original, nome normalizado)
        for m in movies:
            for name in [m["titulo"], *m.get("aliases", [])]:
                n = normalize(name)
                if n:
                    self.entries.append((m["titulo"], n))

    def match(self, title: str):
        """Retorna (titulo_da_lista, score) ou None."""
        n = normalize(title)
        best = (None, 0.0)
        for original, cand in self.entries:
            s = score(n, cand)
            if s > best[1]:
                best = (original, s)
        return best if best[1] >= self.threshold else None
