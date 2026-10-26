"""Fonte de dados: API pública (não documentada) do Ingresso.com.

Cobre Cinemark, Cinépolis, UCI, Kinoplex etc. na cidade de São Paulo.
Os endpoints abaixo são os usados pelo site/app e podem mudar. Se algo quebrar,
rode `python -m cinema_classicos --diagnostico` para ver a resposta crua.
"""
import json
import time
import requests

BASE = "https://api-content.ingresso.com/v0"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; cinema-classicos/1.0; uso pessoal)",
    "Accept": "application/json",
}


def _get(path: str, **params):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params or None, timeout=30)
    r.raise_for_status()
    return r.json()


def cidades_sp():
    """Lista as cidades de SP (para descobrir o id da capital)."""
    return _get("/states/SP")


def cinemas(city_id: int):
    data = _get(f"/theaters/city/{city_id}")
    return data if isinstance(data, list) else data.get("items", [])


def coletar(cfg: dict, progresso=None, bruto: bool = False) -> list:
    """Retorna sessões normalizadas (cinema, titulo, inicio, link, formato, sala).

    `progresso`, se dado, é chamado após cada cinema com um dict-relatório:
    {id, cinema, ok, erro, sessoes, salas, filmes, pares, de, ate, bruto}.
    Com bruto=True, guarda um trecho da resposta crua da fonte (para diagnóstico).
    """
    city = cfg["city_id"]
    pausa = cfg.get("pause_seconds", 1.0)
    out = []
    for c in cinemas(city):
        tid = c.get("id")
        nome = c.get("name") or c.get("title") or str(tid)
        rel = {"id": tid, "cinema": nome, "ok": True, "erro": ""}
        sessoes = []
        try:
            blocos = _get(f"/sessions/city/{city}/theater/{tid}")
            if bruto:
                rel["bruto"] = json.dumps(blocos, ensure_ascii=False, indent=1)[:4000]
            sessoes = _normalizar(nome, blocos)
        except requests.RequestException as e:
            resp = getattr(e, "response", None)
            rel.update(ok=False, erro=f"HTTP {resp.status_code}" if resp is not None else str(e))
        datas = sorted(s["inicio"] for s in sessoes if s["inicio"])
        rel.update(
            sessoes=len(sessoes),
            salas=len({s["sala"] for s in sessoes if s["sala"]}),
            filmes=sorted({s["titulo"] for s in sessoes if s["titulo"]}),
            pares=sorted({(s["titulo"], s.get("titulo_original", "")) for s in sessoes if s["titulo"]}),
            de=datas[0][:10] if datas else "",
            ate=datas[-1][:10] if datas else "",
        )
        if progresso:
            progresso(rel)
        out.extend(sessoes)
        time.sleep(pausa)
    return out


def _normalizar(cinema: str, blocos) -> list:
    """Converte a resposta (lista de dias -> filmes -> sessões) em linhas planas."""
    sessoes = []
    if isinstance(blocos, dict):
        blocos = blocos.get("items") or blocos.get("data") or [blocos]
    for dia in blocos or []:
        for filme in dia.get("movies", []):
            titulo = filme.get("title") or filme.get("originalTitle") or ""
            link = filme.get("siteURL") or ""
            for room in filme.get("rooms", []):
                for s in room.get("sessions", []):
                    sessoes.append({
                        "cinema": cinema,
                        "titulo": titulo,
                        "titulo_original": filme.get("originalTitle", ""),
                        "inicio": s.get("date", {}).get("localDate")
                                  or f"{dia.get('date', '')} {s.get('time', '')}".strip(),
                        "formato": ", ".join(s.get("type", []) or []),
                        "sala": room.get("name", ""),
                        "link": s.get("siteURL") or link,
                    })
    return sessoes
