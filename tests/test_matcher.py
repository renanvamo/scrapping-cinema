import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from cinema_classicos.matcher import Matcher
from cinema_classicos.nucleo import encontrar, agrupar_msg
from cinema_classicos.ingresso import _normalizar

movies = json.loads((Path(__file__).resolve().parent.parent / "movies.json").read_text(encoding="utf-8"))
m = Matcher(movies, 0.88)

DEVE_CASAR = {
    "Harry Potter e a Pedra Filosofal - Dublado": "Harry Potter e a Pedra Filosofal",
    "O SENHOR DOS ANÉIS: A SOCIEDADE DO ANEL (Reexibição)": "O Senhor dos Anéis: A Sociedade do Anel",
    "Braveheart - Coração Valente": None,   # aceito casar ou não; só não pode quebrar
    "Coração Valente": "Coração Valente",
    "Jurassic Park": "Jurassic Park - O Parque dos Dinossauros",
    "Star Wars: Episódio IV - Uma Nova Esperança": "Star Wars: Episódio IV - Uma Nova Esperança",
    "O Último dos Moicanos": "O Último dos Moicanos",
    "Matrix - 3D": "Matrix",
}
NAO_DEVE_CASAR = [
    "Jurassic World: Recomeço",
    "Harry Potter e a Câmara Secreta 2",   # número divergente
    "Matrix Resurrections",
    "Homem-Aranha 3",
    "Avatar: Fogo e Cinzas",
    "Mickey 17",
]

falhas = 0
for t, esperado in DEVE_CASAR.items():
    r = m.match(t)
    if esperado is None:
        continue
    if not r or r[0] != esperado:
        print("FALHOU casar:", t, "->", r); falhas += 1
for t in NAO_DEVE_CASAR:
    r = m.match(t)
    if r:
        print("FALHOU (falso positivo):", t, "->", r); falhas += 1

# Fluxo completo com resposta simulada no formato da fonte
fake = [{"date": "2026-11-01", "movies": [
    {"title": "Harry Potter e a Pedra Filosofal", "originalTitle": "Harry Potter and the Sorcerer's Stone",
     "siteURL": "https://ingresso.com/x", "rooms": [{"name": "Sala 3", "sessions": [
        {"time": "19:30", "type": ["Dublado"], "date": {"localDate": "2026-11-01T19:30:00"}}]}]},
    {"title": "Filme Novo Qualquer", "rooms": [{"name": "Sala 1", "sessions": [{"time": "20:00", "type": []}]}]},
]}]
ss = _normalizar("Cinemark Eldorado", fake)
ach = encontrar(ss, m)
assert len(ss) == 2 and len(ach) == 1, (ss, ach)
print(agrupar_msg(ach))
print("OK" if not falhas else f"{falhas} falhas")
sys.exit(1 if falhas else 0)
