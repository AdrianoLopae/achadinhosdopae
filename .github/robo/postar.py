"""Posta o próximo vídeo da fila (roda no GitHub Actions, nos horários do agendamento).

A fila fica em fila/NNNN.json + fila/NNNN.mp4 (o PC manda pra cá depois de montar).
Depois de postar: registra em posts.json (lista da página da bio) e tira o vídeo da fila.
"""
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

import ig

RAIZ = Path(__file__).resolve().parents[2]
FILA = RAIZ / "fila"
POSTS = RAIZ / "posts.json"
SITE = "https://adrianolopae.github.io/achadinhosdopae"


def main():
    itens = sorted(FILA.glob("*.json"))
    if not itens:
        print("fila vazia")
        return
    arq = itens[0]
    p = json.loads(arq.read_text(encoding="utf-8"))
    n = p["numero"]
    url = f"{SITE}/fila/{arq.stem}.mp4"
    for _ in range(30):  # o vídeo precisa estar no ar no Pages
        if requests.head(url, timeout=20).status_code == 200:
            break
        time.sleep(10)
    print(f"postando nº {n}: {p.get('nome')}")
    ig_id = ig.publicar_reel(url, p["legenda"])
    posts = json.loads(POSTS.read_text(encoding="utf-8")) if POSTS.exists() else []
    posts.append({"n": n, "nome": p.get("nome"), "link": p.get("link"), "ali": p.get("link_ali"),
                  "img": p.get("imagem"), "palavra": p.get("palavra"), "ig_id": ig_id,
                  "manychat": bool(p.get("manychat")),
                  "postado": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    POSTS.write_text(json.dumps(posts, ensure_ascii=False, indent=1), encoding="utf-8")
    arq.unlink()
    (FILA / f"{arq.stem}.mp4").unlink(missing_ok=True)
    git = lambda *a: subprocess.run(["git", "-C", str(RAIZ), *a], check=True)
    git("config", "user.name", "robo-achadinhos")
    git("config", "user.email", "robo@users.noreply.github.com")
    git("add", "-A")
    git("commit", "-m", f"post {n} publicado")
    git("push")
    print(f"nº {n} publicado: {ig_id}")


if __name__ == "__main__":
    main()
