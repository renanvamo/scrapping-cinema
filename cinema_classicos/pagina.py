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
  .pcab { display:flex; align-items:center; gap:8px; margin-bottom:8px; }
  .pcab h2 { flex:1; margin:0; }
  .pcab button { padding:5px 10px; font-size:.85rem; }
  #log { display:block; width:100%; height:300px; resize:vertical; padding:10px; border:1px solid var(--line); border-radius:8px; background:var(--bg); color:var(--ink); font:12.5px/1.5 ui-monospace, Consolas, monospace; white-space:pre-wrap; overflow:auto; }
  pre.bruto { max-height:220px; overflow:auto; margin:6px 0 0; padding:8px; background:var(--bg); border:1px solid var(--line); border-radius:6px; font:11.5px/1.4 ui-monospace, Consolas, monospace; white-space:pre-wrap; color:var(--mute); }
  table.t { width:100%; border-collapse:collapse; font-size:.85rem; margin-top:12px; }
  table.t th, table.t td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
  table.t td.n { text-align:right; font-variant-numeric:tabular-nums; }
  .bad { color:#c0392b; } .warn { color:#b9770e; } .good { color:#2e8b57; }
  details summary { cursor:pointer; color:var(--accent); }
  details ul { margin:6px 0 0; padding-left:18px; color:var(--mute); }
  .tokenbox { display:none; background:var(--card); border:1px solid var(--line); border-radius:12px; padding:14px; margin-bottom:16px; font-size:.9rem; }
  .tokenbox.on { display:block; }
  .tokenbox ol { margin:8px 0; padding-left:20px; } .tokenbox li { margin:3px 0; }
  .tokenbox input { width:100%; padding:9px 12px; border:1px solid var(--line); border-radius:8px; background:var(--bg); color:var(--ink); font:inherit; margin:6px 0 8px; }
  .tokenbox code { background:var(--chip); padding:1px 5px; border-radius:4px; }
  a.btn { font:inherit; padding:9px 16px; border-radius:8px; border:1px solid var(--line); color:var(--ink); text-decoration:none; background:var(--card); }
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
    <a class="btn" id="aExec" target="_blank" rel="noopener" style="display:none">📋 Ver execuções</a>
    <button id="bToken" style="display:none" title="Trocar ou remover o token">🔑</button>
  </div>
  <div class="tokenbox" id="tokenBox">
    <strong>Conectar ao GitHub (uma vez só)</strong>
    <ol>
      <li>Abra <a id="aTok" href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">github.com/settings/personal-access-tokens/new</a>.</li>
      <li>Em <em>Repository access</em>, escolha <em>Only select repositories</em> e marque só este repositório.</li>
      <li>Em <em>Permissions → Repository permissions</em>, deixe <code>Actions</code> em <em>Read and write</em>.</li>
      <li>Gere o token, copie e cole abaixo. Ele fica salvo só neste navegador.</li>
    </ol>
    <input id="tokInput" type="password" placeholder="github_pat_…" autocomplete="off">
    <button class="prim" id="tokSalvar">Salvar e continuar</button>
    <button id="tokRemover">Remover token</button>
    <button id="tokFechar">Fechar</button>
  </div>
  <div class="painel" id="painel">
    <div class="pcab">
      <h2 id="pTitulo">Log</h2>
      <button id="pCopiar" title="Copiar o log">📋 Copiar</button>
      <button id="pFechar" title="Fechar">✕ Fechar</button>
    </div>
    <textarea id="log" readonly spellcheck="false"></textarea>
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
let fechado = false;
$("pFechar").onclick = () => { fechado = true; $("painel").classList.remove("on"); };
$("pCopiar").onclick = async () => {
  const t = $("log").value, b = $("pCopiar");
  try { await navigator.clipboard.writeText(t); }
  catch (e) { $("log").select(); document.execCommand("copy"); }
  b.textContent = "✓ Copiado"; setTimeout(() => b.textContent = "📋 Copiar", 1500);
};
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
    const cru = c.bruto ? `<details><summary>ver</summary><pre class="bruto">${esc(c.bruto)}${c.bruto.length >= 4000 ? "\n… (cortado)" : ""}</pre></details>` : "—";
    return `<tr><td>${esc(c.cinema)}</td><td class="${cls}">${st}</td><td class="n">${c.salas}</td><td>${lista}</td><td>${cru}</td><td class="n">${c.sessoes}</td><td>${esc(c.de)}${c.ate ? " → " + esc(c.ate) : ""}</td><td class="n">${c.classicos}</td></tr>`;
  }).join("");
  $("tabela").innerHTML = `<table class="t"><thead><tr><th>Cinema</th><th>Status</th><th>Salas</th><th>Filmes</th><th>Resposta crua</th><th>Sessões</th><th>Período</th><th>Clássicos</th></tr></thead><tbody>${linhas}</tbody></table>`;
}
async function atualizarStatus() {
  const st = await api("/api/status");
  if (!fechado) $("painel").classList.add("on");
  $("pTitulo").textContent = (st.modo === "testar" ? "Teste da busca" : "Busca") + (st.rodando ? " — em andamento…" : " — concluída");
  const lg = $("log"), fim = lg.scrollTop + lg.clientHeight >= lg.scrollHeight - 20;
  lg.value = st.linhas.join("\n");
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
  fechado = false;
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

// --- Botões na versão publicada (GitHub Pages): disparam o workflow pela API do GitHub ---
const naNuvem = location.hostname.endsWith(".github.io");
const GH = {dono: location.hostname.split(".")[0], repo: location.pathname.split("/")[1] || "", wf: "buscar.yml", ref: "master"};
const tok = {
  get() { try { return localStorage.getItem("gh_token_cinema") || ""; } catch (e) { return ""; } },
  set(v) { try { localStorage.setItem("gh_token_cinema", v); } catch (e) {} },
  del() { try { localStorage.removeItem("gh_token_cinema"); } catch (e) {} },
};
const ghBase = `https://api.github.com/repos/${GH.dono}/${GH.repo}`;
const ghHead = () => ({"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", ...(tok.get() ? {"Authorization": "Bearer " + tok.get()} : {})});
const execUrl = `https://github.com/${GH.dono}/${GH.repo}/actions/workflows/${GH.wf}`;
let modoPendente = null;
const painelNuvem = (titulo, linhas) => {
  if (!fechado) $("painel").classList.add("on"); $("pTitulo").textContent = titulo; $("log").value = linhas.join("\n"); $("tabela").innerHTML = "";
};
async function dispararNuvem(modo) {
  fechado = false;
  if (!tok.get()) { modoPendente = modo; $("tokenBox").classList.add("on"); $("tokInput").focus(); return; }
  $("bBuscar").disabled = $("bTestar").disabled = true;
  const t0 = Date.now();
  const nome = modo === "testar" ? "Teste da busca" : "Busca";
  painelNuvem(nome + " — enviando pedido ao GitHub…", []);
  try {
    const r = await fetch(`${ghBase}/actions/workflows/${GH.wf}/dispatches`, {
      method: "POST", headers: {...ghHead(), "Content-Type": "application/json"},
      body: JSON.stringify({ref: GH.ref, inputs: {modo}}),
    });
    if (r.status !== 204) {
      const msg = r.status === 401 ? "Token inválido ou expirado." :
        (r.status === 403 || r.status === 404) ? "O token não tem permissão (precisa de Actions: Read and write neste repositório)." : `Erro HTTP ${r.status}.`;
      painelNuvem(nome + " — não foi possível iniciar", [msg, "Clique em 🔑 para trocar o token."]);
      $("bBuscar").disabled = $("bTestar").disabled = false;
      return;
    }
  } catch (e) {
    painelNuvem(nome + " — falha de rede", [String(e)]); $("bBuscar").disabled = $("bTestar").disabled = false; return;
  }
  const linhas = ["Pedido enviado. Aguardando o GitHub iniciar a execução…"];
  painelNuvem(nome + " — em andamento…", linhas);
  for (let i = 0; i < 180; i++) {            // até ~18 min
    await new Promise(ok => setTimeout(ok, 6000));
    let run = null;
    try {
      const r = await fetch(`${ghBase}/actions/workflows/${GH.wf}/runs?event=workflow_dispatch&per_page=5`, {headers: ghHead()});
      const j = await r.json();
      run = (j.workflow_runs || []).find(x => new Date(x.created_at).getTime() >= t0 - 120000);
    } catch (e) { continue; }
    if (!run) continue;
    const st = {queued: "na fila", in_progress: "rodando", completed: "concluída", waiting: "aguardando"}[run.status] || run.status;
    painelNuvem(nome + " — " + (run.status === "completed" ? "concluída" : "em andamento…"),
      [`Execução ${st}.`, `Log completo: ${run.html_url}`]);
    if (run.status === "completed") {
      const ok = run.conclusion === "success";
      const fim = [ok ? "✓ Execução concluída com sucesso." : `✗ Execução terminou com: ${run.conclusion}.`, `Log completo (cada cinema, salas, sessões): ${run.html_url}`];
      if (ok && modo === "buscar") { fim.push("A página será recarregada em 60 s (o GitHub leva um pouco para publicar)."); setTimeout(() => location.reload(), 60000); }
      painelNuvem(nome + (ok ? " — concluída" : " — falhou"), fim);
      break;
    }
  }
  $("bBuscar").disabled = $("bTestar").disabled = false;
}
if (naNuvem) {
  $("barra").classList.add("on");
  $("aExec").style.display = ""; $("aExec").href = execUrl;
  $("bToken").style.display = "";
  $("aTok").href = "https://github.com/settings/personal-access-tokens/new";
  $("bBuscar").onclick = () => dispararNuvem("buscar");
  $("bTestar").onclick = () => dispararNuvem("testar");
  $("bToken").onclick = () => $("tokenBox").classList.toggle("on");
  $("tokFechar").onclick = () => { modoPendente = null; $("tokenBox").classList.remove("on"); };
  $("tokRemover").onclick = () => { tok.del(); $("tokInput").value = ""; };
  $("tokSalvar").onclick = () => {
    const v = $("tokInput").value.trim(); if (!v) return;
    tok.set(v); $("tokInput").value = ""; $("tokenBox").classList.remove("on");
    if (modoPendente) { const m = modoPendente; modoPendente = null; dispararNuvem(m); }
  };
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
