import argparse
import sys
import webbrowser

from . import ingresso, nucleo, notify, servidor


def main(argv=None):
    p = argparse.ArgumentParser(prog="cinema_classicos")
    p.add_argument("--dry-run", action="store_true", help="busca e mostra, sem enviar aviso nem gravar estado")
    p.add_argument("--testar", action="store_true", help="diagnóstico por cinema (mesmo do botão Testar)")
    p.add_argument("--servidor", action="store_true", help="abre a página com os botões Buscar e Testar")
    p.add_argument("--porta", type=int, default=8765)
    p.add_argument("--abrir", action="store_true", help="abre pagina.html ao terminar a busca")
    p.add_argument("--diagnostico", action="store_true", help="lista cinemas da cidade")
    p.add_argument("--teste-ntfy", action="store_true", help="envia notificação de teste")
    a = p.parse_args(argv)
    try:
        return _executar(a)
    except Exception as e:
        print(f"ERRO: {e}")
        return 1


def _executar(a):
    cfg = nucleo.carregar_config()

    if a.teste_ntfy:
        notify.enviar(cfg["ntfy"], "Cinema Clássicos", "Teste: o aviso está funcionando 🎬")
        print("Enviado.")
    elif a.diagnostico:
        cs = ingresso.cinemas(cfg["ingresso"]["city_id"])
        print(f"{len(cs)} cinemas na cidade {cfg['ingresso']['city_id']}")
        for c in cs:
            print("-", c.get("id"), c.get("name"))
    elif a.servidor:
        servidor.servir(a.porta)
    elif a.testar:
        nucleo.testar()
    else:
        nucleo.buscar(dry_run=a.dry_run)
        if a.abrir:
            webbrowser.open((nucleo.ROOT / "pagina.html").as_uri())
    return 0


if __name__ == "__main__":
    sys.exit(main())
