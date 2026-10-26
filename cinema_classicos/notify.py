"""Envio de notificação via ntfy."""
import requests


def enviar(cfg: dict, titulo: str, corpo: str, link: str = "", prioridade: str = "default"):
    headers = {
        "Title": titulo.encode("utf-8"),
        "Tags": "clapper,movie_camera",
        "Priority": prioridade,
    }
    if link:
        headers["Click"] = link
    if cfg.get("token"):
        headers["Authorization"] = f"Bearer {cfg['token']}"
    url = f"{cfg.get('server', 'https://ntfy.sh').rstrip('/')}/{cfg['topic']}"
    r = requests.post(url, data=corpo.encode("utf-8"), headers=headers, timeout=20)
    r.raise_for_status()
