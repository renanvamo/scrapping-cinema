"""Lembra o que já foi avisado (evita notificação repetida). Guarda em JSON."""
import json
import sqlite3
from datetime import date, timedelta
from pathlib import Path


class State:
    def __init__(self, path):
        self.path = Path(path)
        self.d = {}
        if self.path.exists():
            self.d = json.loads(self.path.read_text(encoding="utf-8"))
        else:
            self._migrar_sqlite()

    def _migrar_sqlite(self):
        """Versões antigas usavam estado.sqlite; aproveita o que já foi avisado."""
        antigo = self.path.with_name("estado.sqlite")
        if not antigo.exists():
            return
        try:
            db = sqlite3.connect(str(antigo))
            for chave, criado in db.execute("SELECT chave, criado_em FROM avisados"):
                self.d[chave] = (criado or "")[:10]
            db.close()
        except sqlite3.Error:
            pass

    @staticmethod
    def chave(s: dict) -> str:
        return f"{s['cinema']}|{s['titulo_lista']}|{s['inicio']}"

    def novo(self, s: dict) -> bool:
        return self.chave(s) not in self.d

    def marcar(self, s: dict) -> None:
        self.d[self.chave(s)] = date.today().isoformat()

    def salvar(self) -> None:
        corte = (date.today() - timedelta(days=90)).isoformat()
        self.d = {k: v for k, v in self.d.items() if (v or "9999") >= corte}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.d, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")
