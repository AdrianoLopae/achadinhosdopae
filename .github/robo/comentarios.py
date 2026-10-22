"""Responde comentários dos Reels (roda no GitHub Actions a cada poucos minutos).

Sem banco: um comentário já respondido tem uma resposta nossa embaixo, então é pulado.
Quem comenta a palavra do post (ou "quero"/"link"/"eu") recebe o link no direct e uma resposta pública.
"""
import json
import random
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import ig

POSTS = Path(__file__).resolve().parents[2] / "posts.json"
PUBLICAS = ["Te mandei no direct! 📩", "Corre no direct que o link tá lá 😉", "Enviado! Olha sua DM 💌",
            "Mandei lá no seu direct 🙌", "Link no seu direct! 📲"]


def base(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if (c.isalnum() or c == " ") and unicodedata.category(c) != "Mn")


def pede_link(texto, palavra):
    t = base(texto)
    return bool(palavra and base(palavra) in t) or any(w in t.split() for w in ("quero", "link", "eu"))


def mensagem(p):
    if p.get("ali") and p.get("link") and p["ali"] != p["link"]:
        return (f"Opa! Aqui estão os links do {p['nome']} 👇\n\n🛒 Shopee (chega mais rápido):\n{p['link']}\n\n"
                f"🌏 AliExpress (às vezes sai mais barato):\n{p['ali']}\n\n"
                f"Se precisar de novo, é o nº {p['n']} no link da bio 😉")
    return (f"Opa! Aqui está o link do {p['nome']} 👇\n\n{p.get('link') or p.get('ali')}\n\n"
            f"Se precisar de novo, é o nº {p['n']} no link da bio 😉")


def main():
    if not POSTS.exists():
        return
    limite = datetime.now(timezone.utc) - timedelta(days=10)
    for p in json.loads(POSTS.read_text(encoding="utf-8")):
        quando = datetime.fromisoformat(p.get("postado") or "2000-01-01")
        if quando.tzinfo is None:  # data gravada pelo PC (horário de Brasília)
            quando = quando.replace(tzinfo=timezone(timedelta(hours=-3)))
        if p.get("manychat") or not p.get("ig_id") or quando < limite:
            continue
        try:
            coms = ig.get(f"{p['ig_id']}/comments", fields="id,text,username,replies{username}", limit=50)
        except Exception as e:
            print(f"nº {p['n']}: {e}")
            continue
        for c in coms.get("data", []):
            if (c.get("username") or "").lower() == ig.EU:
                continue
            ja = any((r.get("username") or "").lower() == ig.EU for r in (c.get("replies") or {}).get("data", []))
            if ja or not pede_link(c.get("text"), p.get("palavra")):
                continue
            dm = True
            try:
                ig.post(f"{ig.UID}/messages", json={"recipient": {"comment_id": c["id"]},
                                                     "message": {"text": mensagem(p)}})
            except Exception as e:
                dm = False
                print(f"nº {p['n']} direct falhou: {e}")
            try:
                ig.post(f"{c['id']}/replies", data={"message": random.choice(PUBLICAS) if dm
                                                     else f"Procura o nº {p['n']} no link da bio 😉"})
            except Exception as e:
                print(f"nº {p['n']} resposta falhou: {e}")
            print(f"nº {p['n']}: respondi '{(c.get('text') or '')[:30]}' (direct {dm})")


if __name__ == "__main__":
    main()
