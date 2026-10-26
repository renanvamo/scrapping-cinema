"""Gera uma página HTML única (abre com duplo clique) com os clássicos em cartaz."""
import json
from datetime import datetime, timedelta, timezone

TEMPLATE = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clássicos em cartaz — SP</title>
<style>
  :root { --bg:#faf8f5; --card:#fff; --ink:#1d1b19; --mute:#6f6a63; --line:#e6e1d9; --accent:#b4432d; --chip:#f1ece4; }
  @media (prefers-color-scheme: dark) {
    :root { --bg:#161513; --card:#201e1b; --ink:#f1ede6; --mute:#a39d93; --line:#34312c; --accent:#e8806a; --chip:#2a2723; }
  }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink); font:16px/1.45 system-ui, -apple-system, "Segoe UI", sans-serif; }
  main { max-width: 860px; margin: 0 auto; padding: 24px 16px 64px; }
  h1 { font-size: 1.6rem; margin: 0 0 4px; }
  .sub { color: var(--mute); margin: 0 0 20px; font-size: .9rem; }
  .filtros { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:20px; }
  .filtros input, .filtros select { flex:1 1 180px; padding:10px 12px; border:1px solid var(--line); border-radius:8px; background:var(--card); color:var(--ink); font:inherit; }
  .filme { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:16px; margin-bottom:16px; }
  .filme h2 { font-size:1.15rem; margin:0 0 2px; }
  .orig { color:var(--mute); font-size:.85rem; margin:0 0 10px; }
  .cinema { margin-top:12px; }
  .cinema h3 { font-size:.95rem; margin:0 0 6px; color:var(--accent); font-weight:600; }
  .dia { display:flex; gap:10px; align-items:baseline; margin:4px 0; }
  .dia .d { min-width:108px; font-size:.85rem; color:var(--mute); }
  .horas { display:flex; flex-wrap:wrap; gap:6px; }
  a.h, span.h { background:var(--chip); border:1px solid var(--line); border-radius:6px; padding:2px 8px; font-size:.85rem; text-decoration:none; color:var(--ink); }
  a.h:hover { border-color:var(--accent); color:var(--accent); }
  .barra { display:none; gap:8px; flex-wrap:wrap; margin-bottom:16px; }
  .barra.on { display:flex; }
  button { font:inherit; padding:9px 16px; border-radius:8px; border:1px solid var(--line); background:var(--card); color:var(--ink); cursor:pointer; }
  button.prim { background:var(--accent); border-color:var(--accent); color:#fff; }
  button:disabled { opacity:.5; cursor:wait; }
  .painel { display:none; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; margin-bottom:20px; }
  .painel.on { display:block; }
  .painel h2 { font-size:1rem; margin:0 0 8px; }
  #log { margin:0; max-height:260px; overflow:auto; font:12.5px/1.5 ui-monospace, Consolas, monospace; white-space:pre-wrap; color:var(--mute); }
  table.t { width:100%; border-collapse:collapse; font-size:.85rem; margin-top:12px; }
  table.t th, table.t td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
  table.t td.n { text-align:right; font-variant-numeric:tabular-nums; }
  .bad { color:#c0392b; } .warn { color:#b9770e; } .good { color:#2e8b57; }
  details summary { cursor:pointer; color:var(--accent); }
  details ul { margin:6px 0 0; padding-left:18px; color:var(--mute); }
  .vazio { text-align:center; color:var(--mute); padding:48px 0; }
  @media (max-width:520px){ .dia{flex-direction:column; gap:2px} .dia .d{min-width:0} }
</style>
</head>
<body>
<main>
  <h1>🎬 Clássicos em cartaz — São Paulo</h1>
  <p class="sub" id="sub"></p>
  <div class="barra" id="barra">
    <button class="prim" id="bBuscar">🔎 Buscar agora</button>
    <button id="bTestar">🧪 Testar busca</button>
  </div>
  <div class="painel" id="painel">
    <h2 id="pTitulo">Log</h2>
    <pre id="log"></pre>
    <div id="tabela"></div>
  </div>
  <div class="filtros">
    <input id="busca" type="search" placeholder="Buscar filme…">
    <select id="cinema"><option value="">Todos os cinemas</option></select>
  </div>
  <div id="lista"></div>
</main>
<script>
const DADOS = __DADOS__;
const GERADO = "__GERADO__";
const $ = id => document.getElementById(id);
const dt = s => new Date(s.replace(" ", "T"));
const fmtDia = d => d.toLocaleDateString("pt-BR", {weekday:"short", day:"2-digit", month:"2-digit"});
const fmtHora = d => d.toLocaleTimeString("pt-BR", {hour:"2-digit", minute:"2-digit"});
const esc = t => String(t ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const norm = t => t.normalize("NFD").replace(/[̀-ͯ]/g,"").toLowerCase();

const cinemas = [...new Set(DADOS.map(s => s.cinema))].sort();
cinemas.forEach(c => $("cinema").insertAdjacentHTML("beforeend", `<option>${esc(c)}</option>`));

function render() {
  const q = norm($("busca").value), cin = $("cinema").value;
  const agora = new Date();
  const itens = DADOS.filter(s => (!cin || s.cinema === cin) && (!q || norm(s.titulo_lista + " " + s.titulo).includes(q))
                                   && dt(s.inicio) >= new Date(agora.getTime() - 30*60000));
  const porFilme = {};
  for (const s of itens) ((porFilme[s.titulo_lista] ??= {})[s.cinema] ??= []).push(s);
  const filmes = Object.keys(porFilme).sort((a,b) => a.localeCompare(b, "pt-BR"));
  $("sub").textContent = `${filmes.length} filme(s) · ${itens.length} sessões · atualizado em ${GERADO}`;
  if (!filmes.length) { $("lista").innerHTML = '<div class="vazio">Nenhum clássico em cartaz com esses filtros.</div>'; return; }
  $("lista").innerHTML = filmes.map(f => {
    const cs = porFilme[f];
    const orig = [...new Set(Object.values(cs).flat().map(s => s.titulo))].filter(t => t !== f);
    const blocos = Object.keys(cs).sort().map(c => {
      const porDia = {};
      cs[c].sort((a,b) => dt(a.inicio) - dt(b.inicio)).forEach(s => (porDia[dt(s.inicio).toDateString()] ??= []).push(s));
      const dias = Object.values(porDia).map(ss => {
        const horas = ss.map(s => {
          const rot = fmtHora(dt(s.inicio)) + (s.formato ? ` · ${esc(s.formato)}` : "");
          return s.link ? `<a class="h" href="${esc(s.link)}" target="_blank" rel="noopener">${rot}</a>` : `<span class="h">${rot}</span>`;
        }).join("");
        return `<div class="dia"><span class="d">${fmtDia(dt(ss[0].inicio))}</span><div class="horas">${horas}</div></div>`;
      }).join("");
      return `<div class="cinema"><h3>${esc(c)}</h3>${dias}</div>`;
    }).join("");
    return `<section class="filme"><h2>${esc(f)}</h2>${orig.length ? `<p class="orig">No cinema: ${esc(orig.join(" / "))}</p>` : ""}${blocos}</section>`;
  }).join("");
}
$("busca").addEventListener("input", render);
$("cinema").addEventListener("change", render);

// --- Botões (só funcionam quando a página é aberta pelo servidor local) ---
const modoServidor = ["localhost", "127.0.0.1"].includes(location.hostname);
let poll = null;
async function api(caminho, metodo) {
  const r = await fetch(caminho, {method: metodo || "GET", headers: {"X-Cinema": "1"}});
  return r.json();
}
function mostrarTabela(res) {
  if (!res || !res.cinemas) { $("tabela").innerHTML = ""; return; }
  const linhas = res.cinemas.map(c => {
    const cls = !c.ok ? "bad" : (!c.sessoes ? "warn" : "good");
    const st = !c.ok ? `✗ ${esc(c.erro)}` : (!c.sessoes ? "⚠ sem sessões" : "✓");
    const lista = c.filmes.length ? `<details><summary>${c.filmes.length} filmes</summary><ul>${c.filmes.map(f => `<li>${esc(f)}</li>`).join("")}</ul></details>` : "—";
    return `<tr><td>${esc(c.cinema)}</td><td class="${cls}">${st}</td><td class="n">${c.salas}</td><td>${lista}</td><td class="n">${c.sessoes}</td><td>${esc(c.de)}${c.ate ? " → " + esc(c.ate) : ""}</td><td class="n">${c.classicos}</td></tr>`;
  }).join("");
  $("tabela").innerHTML = `<table class="t"><thead><tr><th>Cinema</th><th>Status</th><th>Salas</th><th>Filmes</th><th>Sessões</th><th>Período</th><th>Clássicos</th></tr></thead><tbody>${linhas}</tbody></table>`;
}
async function atualizarStatus() {
  const st = await api("/api/status");
  $("painel").classList.add("on");
  $("pTitulo").textContent = (st.modo === "testar" ? "Teste da busca" : "Busca") + (st.rodando ? " — em andamento…" : " — concluída");
  const lg = $("log"), fim = lg.scrollTop + lg.clientHeight >= lg.scrollHeight - 20;
  lg.textContent = st.linhas.join("\n");
  if (fim) lg.scrollTop = lg.scrollHeight;
  $("bBuscar").disabled = $("bTestar").disabled = st.rodando;
  if (!st.rodando) {
    clearInterval(poll); poll = null;
    if (st.modo === "testar") mostrarTabela(st.resultado);
    if (st.modo === "buscar" && st.resultado) setTimeout(() => location.reload(), 1500);
  }
  return st;
}
async function iniciar(modo) {
  $("tabela").innerHTML = "";
  const r = await api("/api/" + modo, "POST");
  if (!r.iniciado) alert("Já existe uma busca em andamento.");
  await atualizarStatus();
  if (!poll) poll = setInterval(atualizarStatus, 1000);
}
if (modoServidor) {
  $("barra").classList.add("on");
  $("bBuscar").onclick = () => iniciar("buscar");
  $("bTestar").onclick = () => iniciar("testar");
  api("/api/status").then(st => { if (st.rodando) { atualizarStatus(); poll = setInterval(atualizarStatus, 1000); } }).catch(() => {});
}
render();
</script>
</body>
</html>
"""


def gerar(achados: list, destino) -> None:
    dados = [
        {k: s.get(k, "") for k in ("cinema", "titulo", "titulo_lista", "inicio", "formato", "sala", "link")}
        for s in achados
    ]
    html = (
        TEMPLATE
        .replace("__DADOS__", json.dumps(dados, ensure_ascii=False).replace("</", "<\\/"))
        .replace("__GERADO__", datetime.now(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M"))
    )
    destino.write_text(html, encoding="utf-8")
