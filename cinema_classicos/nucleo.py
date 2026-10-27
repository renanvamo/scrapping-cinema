"""Lógica principal, usada pela linha de comando e pelo servidor local."""
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from . import ingresso, notify, pagina
from .matcher import Matcher, normalize
from .state import State

ROOT = Path(__file__).resolve().parent.parent


def carregar(nome):
    return json.loads((ROOT / nome).read_text(encoding="utf-8"))


def _mesclar(base, extra):
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _mesclar(base[k], v)
        else:
            base[k] = v


def carregar_config():
    """config.json + config.local.json (segredos, fora do repositório) + variáveis NTFY_*."""
    cfg = carregar("config.json")
    local = ROOT / "config.local.json"
    if local.exists():
        _mesclar(cfg, json.loads(local.read_text(encoding="utf-8")))
    for env, chave in (("NTFY_TOPIC", "topic"), ("NTFY_SERVER", "server"), ("NTFY_TOKEN", "token")):
        if os.environ.get(env):
            cfg["ntfy"][chave] = os.environ[env]
    return cfg


def na_nuvem():
    return os.environ.get("GITHUB_ACTIONS") == "true"


def validar_filmes(lista):
    """Valida e limpa a lista de filmes vinda da página. Levanta ValueError se estiver errada."""
    if not isinstance(lista, list) or len(lista) > 500:
        raise ValueError("lista inválida")
    saida, vistos = [], set()
    for f in lista:
        if not isinstance(f, dict):
            raise ValueError("item inválido")
        titulo = str(f.get("titulo", "")).strip()
        if not titulo or len(titulo) > 200:
            raise ValueError(f"título inválido: {titulo[:30]!r}")
        apelidos = [str(a).strip() for a in f.get("aliases", []) if str(a).strip()]
        if len(apelidos) > 20 or any(len(a) > 200 for a in apelidos):
            raise ValueError(f"apelidos inválidos em {titulo[:30]!r}")
        chave = normalize(titulo)
        if chave in vistos:
            continue
        vistos.add(chave)
        saida.append({"titulo": titulo, "aliases": apelidos})
    return saida


def salvar_filmes(lista):
    saida = validar_filmes(lista)
    tmp = ROOT / "movies.json.tmp"
    tmp.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ROOT / "movies.json")
    return saida


def resumo_em_cartaz(sessoes, matcher):
    """Agrupa TUDO que a fonte devolveu por filme (nomes parecidos viram um só)."""
    grupos = {}
    for s in sessoes:
        titulo = s.get("titulo") or s.get("titulo_original") or ""
        if not titulo:
            continue
        g = grupos.setdefault(normalize(titulo) or titulo.lower(),
                              {"nomes": Counter(), "orig": Counter(), "cinemas": Counter(), "datas": []})
        g["nomes"][titulo] += 1
        if s.get("titulo_original"):
            g["orig"][s["titulo_original"]] += 1
        g["cinemas"][s["cinema"]] += 1
        if s.get("inicio"):
            g["datas"].append(s["inicio"][:10])
    saida = []
    for g in grupos.values():
        nome = g["nomes"].most_common(1)[0][0]
        orig = g["orig"].most_common(1)[0][0] if g["orig"] else ""
        m = matcher.match(nome) or (matcher.match(orig) if orig else None)
        saida.append({
            "titulo": nome,
            "original": orig if orig.lower() != nome.lower() else "",
            "cinemas": [[c, n] for c, n in g["cinemas"].most_common()],
            "sessoes": sum(g["cinemas"].values()),
            "de": min(g["datas"]) if g["datas"] else "",
            "ate": max(g["datas"]) if g["datas"] else "",
            "classico": m[0] if m else "",
        })
    saida.sort(key=lambda x: normalize(x["titulo"]))
    return saida


def encontrar(sessoes, matcher):
    achados = []
    for s in sessoes:
        for t in (s["titulo"], s.get("titulo_original", "")):
            m = matcher.match(t) if t else None
            if m:
                achados.append({**s, "titulo_lista": m[0], "score": round(m[1], 2)})
                break
    return achados


def agrupar_msg(novos):
    por_filme = {}
    for s in novos:
        por_filme.setdefault((s["titulo_lista"], s["cinema"], s["titulo"]), []).append(s)
    linhas = []
    for (filme, cinema, original), ss in sorted(por_filme.items()):
        datas = sorted({x["inicio"][:16].replace("T", " ") for x in ss})
        horas = ", ".join(datas[:6]) + (f" (+{len(datas) - 6})" if len(datas) > 6 else "")
        nome = filme if original == filme else f"{filme} [no cinema: {original}]"
        linhas.append(f"• {nome} — {cinema}\n  {horas}")
    return "\n".join(linhas)


def _linha_cinema(rel):
    if not rel["ok"]:
        return f"✗ {rel['cinema']} — {rel['erro']}"
    if not rel["sessoes"]:
        return f"⚠ {rel['cinema']} — conectou, mas sem sessões"
    return (f"✓ {rel['cinema']} — {rel['salas']} salas, {len(rel['filmes'])} filmes, "
            f"{rel['sessoes']} sessões ({rel['de']} a {rel['ate']})")


def buscar(log=print, dry_run=False):
    """Busca, atualiza pagina.html e avisa no ntfy o que for novo."""
    cfg = carregar_config()
    matcher = Matcher(carregar("movies.json"), cfg.get("match_threshold", 0.88))
    log("Buscando programação…")
    sessoes = ingresso.coletar(cfg["ingresso"], progresso=lambda r: log(_linha_cinema(r)) if not r["ok"] else None)
    log(f"{len(sessoes)} sessões coletadas")
    if not sessoes:
        # Fonte fora do ar ou bloqueada: não apaga a página nem o histórico.
        raise RuntimeError("nenhuma sessão coletada (fonte indisponível ou bloqueando o acesso). Página mantida.")
    achados = encontrar(sessoes, matcher)
    todos = resumo_em_cartaz(sessoes, matcher)
    pagina.gerar(achados, ROOT / "pagina.html", todos)
    log(f"Página atualizada: pagina.html ({len(todos)} filmes em cartaz no total)")
    if na_nuvem():
        (ROOT / "docs").mkdir(exist_ok=True)
        pagina.gerar(achados, ROOT / "docs" / "index.html", todos)
    estado = State(ROOT / "dados" / "estado_nuvem.json" if na_nuvem() else ROOT / "estado.json")
    novos = [s for s in achados if estado.novo(s)]
    log(f"{len(achados)} sessões de clássicos, {len(novos)} novas")
    if novos:
        msg = agrupar_msg(novos)
        (ROOT / "ultimo_resultado.txt").write_text(msg, encoding="utf-8")
        log(msg)
        topico = str(cfg["ntfy"].get("topic", ""))
        if dry_run:
            pass
        elif not topico or topico.startswith("COLOQUE"):
            log("AVISO: tópico do ntfy não configurado; aviso não enviado (e não marcado como avisado).")
        else:
            try:
                titulo = f"🎬 {len({s['titulo_lista'] for s in novos})} clássico(s) em cartaz em SP"
                notify.enviar(cfg["ntfy"], titulo, msg, novos[0].get("link", ""))
                for s in novos:
                    estado.marcar(s)
                log("Aviso enviado no ntfy.")
            except Exception as e:  # não marca como avisado se falhou
                log(f"ERRO ao enviar ntfy: {e}")
    if not dry_run:
        estado.salvar()
    return {"sessoes": len(sessoes), "achados": len(achados), "novos": len(novos)}


def testar(log=print):
    """Diagnóstico por cinema. Não avisa nem grava estado.

    Na nuvem (GitHub Actions) também salva o log em docs/teste.json, que a página lê e
    mostra na tela (mesmo se a coleta falhar, o erro vai junto)."""
    linhas, erro, resultado = [], "", None

    def log2(msg):
        linhas.append(str(msg))
        log(msg)

    try:
        resultado = _testar(log2)
    except Exception as e:
        erro = str(e)
        log2(f"ERRO: {e}")
        if not na_nuvem():
            raise
    if na_nuvem():
        (ROOT / "docs").mkdir(exist_ok=True)
        (ROOT / "docs" / "teste.json").write_text(json.dumps({
            "gerado": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "linhas": linhas, "resultado": resultado, "erro": erro,
        }, ensure_ascii=False), encoding="utf-8")
    return resultado


def _testar(log):
    cfg = carregar_config()
    matcher = Matcher(carregar("movies.json"), cfg.get("match_threshold", 0.88))
    relatorios = []
    classicos = {}  # titulo da lista -> set de cinemas

    def prog(rel):
        relatorios.append(rel)
        log(_linha_cinema(rel))
        if not rel["ok"] or not rel["filmes"]:
            return
        log("   filmes: " + "; ".join(rel["filmes"]))
        for titulo, original in rel.get("pares", []):
            m = (matcher.match(titulo) if titulo else None) or (matcher.match(original) if original else None)
            if m:
                classicos.setdefault(m[0], set()).add(rel["cinema"])
                log(f"   ★ clássico: \"{titulo}\" → {m[0]} (similaridade {m[1]:.2f})")

    city = cfg["ingresso"]["city_id"]
    log(f"Fonte: Ingresso.com (api-content.ingresso.com), cidade {city}, {len(carregar('movies.json'))} filmes na sua lista.")
    log("Testando cada cinema (sem enviar aviso nem salvar nada)…")
    log("")
    sessoes = ingresso.coletar(cfg["ingresso"], progresso=prog, bruto=True)
    achados = encontrar(sessoes, matcher)
    por_cinema = {}
    for s in achados:
        por_cinema[s["cinema"]] = por_cinema.get(s["cinema"], 0) + 1
    for r in relatorios:
        r["classicos"] = por_cinema.get(r["cinema"], 0)
    ok = sum(1 for r in relatorios if r["ok"] and r["sessoes"])
    log("")
    log(f"RESUMO: {len(relatorios)} cinemas consultados, {ok} com sessões, {len(relatorios) - ok} sem.")
    log(f"{len(sessoes)} sessões no total, {len(achados)} de filmes da sua lista.")
    if classicos:
        log("Clássicos em cartaz agora:")
        for titulo in sorted(classicos):
            log(f"  • {titulo} — {', '.join(sorted(classicos[titulo]))}")
    else:
        log("Nenhum filme da sua lista em cartaz neste momento.")
    return {"cinemas": relatorios, "sessoes": len(sessoes), "achados": len(achados)}
