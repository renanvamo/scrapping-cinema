"""Servidor local (só no seu PC) para a página ter os botões Buscar e Testar."""
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import nucleo, pagina

_lock = threading.Lock()
_job = {"rodando": False, "modo": "", "linhas": [], "resultado": None}


def _iniciar(modo):
    with _lock:
        if _job["rodando"]:
            return False
        _job.update(rodando=True, modo=modo, linhas=[], resultado=None)

    def log(msg):
        _job["linhas"].append(str(msg))

    def run():
        try:
            fn = nucleo.buscar if modo == "buscar" else nucleo.testar
            _job["resultado"] = fn(log=log)
            log("Concluído.")
        except Exception as e:
            log(f"ERRO: {e}")
        finally:
            _job["rodando"] = False

    threading.Thread(target=run, daemon=True).start()
    return True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _host_ok(self):
        return self.headers.get("Host", "").split(":")[0] in ("localhost", "127.0.0.1")

    def _send(self, code, body, tipo="application/json; charset=utf-8"):
        if isinstance(body, (dict, list)):
            body = json.dumps(body, ensure_ascii=False)
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if not self._host_ok():
            return self._send(403, {"erro": "host inválido"})
        if self.path in ("/", "/pagina.html"):
            arq = nucleo.ROOT / "pagina.html"
            return self._send(200, arq.read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/status":
            return self._send(200, _job)
        self._send(404, {"erro": "não encontrado"})

    def do_POST(self):
        # O cabeçalho customizado impede que outros sites disparem a busca por você.
        if not self._host_ok() or self.headers.get("X-Cinema") != "1":
            return self._send(403, {"erro": "negado"})
        if self.path in ("/api/buscar", "/api/testar"):
            ok = _iniciar(self.path.rsplit("/", 1)[1])
            return self._send(200 if ok else 409, {"iniciado": ok})
        self._send(404, {"erro": "não encontrado"})


def servir(porta=8765, abrir=True):
    arq = nucleo.ROOT / "pagina.html"
    if not arq.exists():
        pagina.gerar([], arq)
    srv = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    url = f"http://localhost:{porta}/"
    print(f"Servidor rodando em {url}  (feche esta janela ou Ctrl+C para parar)")
    if abrir:
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return srv
