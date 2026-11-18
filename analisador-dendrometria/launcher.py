"""Launcher local: escolhe porta livre, inicia o Streamlit, abre o navegador e
encerra de forma controlada (Ctrl+C, fechar a janela ou botão 'Encerrar')."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

HERE = os.path.dirname(os.path.abspath(__file__))


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_ready(url: str, proc: subprocess.Popen, timeout: float = 90) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            return False
        try:
            with urllib.request.urlopen(url + "/_stcore/health", timeout=1) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.4)
    return False


def main() -> int:
    port = free_port()
    url = f"http://127.0.0.1:{port}"
    cmd = [sys.executable, "-m", "streamlit", "run", os.path.join(HERE, "app.py"),
           "--server.port", str(port), "--server.address", "127.0.0.1", "--server.headless", "true",
           "--browser.gatherUsageStats", "false", "--global.developmentMode", "false"]
    print("Analisador de Dendrometria")
    print(f"Iniciando em {url} ...")
    proc = subprocess.Popen(cmd, cwd=HERE)
    try:
        if not wait_ready(url, proc):
            print("Não foi possível iniciar a aplicação. Veja as mensagens acima.")
            proc.terminate()
            return 1
        webbrowser.open(url)
        print("Aplicação aberta no navegador. Para encerrar: botão 'Encerrar aplicação', Ctrl+C ou feche esta janela.")
        return proc.wait()
    except KeyboardInterrupt:
        print("Encerrando...")
        return 0
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    sys.exit(main())
