"""Ponto de entrada do bot.

Modos:
  lembretes  (padrão) avisa quem faz aniversário hoje / amanhã / daqui a N dias
  resumo     lista os aniversários dos próximos RESUMO_DIAS dias (padrão 30)
  teste      envia uma mensagem de teste para confirmar que os canais funcionam

Exemplos:
  python main.py --dry-run
  python main.py --modo resumo --dry-run
  python main.py --data 2026-03-20 --dry-run   # simula outro dia
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

from bot import birthdays as b
from bot.integrations import ler_planilha, notificadores_configurados

log = logging.getLogger("bot")


def _bool(v: str | None) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "sim", "yes", "y"}


def _dias(v: str) -> list[int]:
    dias = sorted({int(x) for x in v.split(",") if x.strip()})
    if any(d < 0 for d in dias):
        raise ValueError("LEMBRETE_DIAS não aceita valores negativos")
    return dias


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lembretes de aniversário")
    p.add_argument("--modo", choices=["lembretes", "resumo", "teste"], default=os.getenv("MODO") or "lembretes")
    p.add_argument("--data", default=os.getenv("DATA_REFERENCIA") or "", help="YYYY-MM-DD (simula outro dia)")
    p.add_argument("--dry-run", action="store_true", default=_bool(os.getenv("DRY_RUN")),
                   help="mostra a mensagem sem enviar")
    p.add_argument("--dias", default=os.getenv("LEMBRETE_DIAS") or "0,1",
                   help="antecedências em dias, separadas por vírgula (padrão 0,1)")
    p.add_argument("--resumo-dias", type=int, default=int(os.getenv("RESUMO_DIAS") or 30))
    return p.parse_args(argv)


def hoje_referencia(texto: str) -> date:
    if texto.strip():
        return date.fromisoformat(texto.strip())
    tz = ZoneInfo(os.getenv("TZ_BOT", "America/Sao_Paulo"))
    return datetime.now(tz).date()


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = parse_args(argv)
    hoje = hoje_referencia(args.data)
    log.info("Modo=%s | data=%s | dry_run=%s", args.modo, hoje.isoformat(), args.dry_run)

    if args.modo == "teste":
        texto = f"✅ Teste do bot de aniversários — {hoje:%d/%m/%Y}. Se você recebeu isto, está tudo certo!"
    else:
        aniversarios, avisos = b.carregar(ler_planilha())
        log.info("%d aniversário(s) carregado(s) da planilha", len(aniversarios))
        for aviso in avisos:
            log.warning(aviso)
            if os.getenv("GITHUB_ACTIONS"):
                print(f"::warning title=Linha inválida na planilha::{aviso}")

        if args.modo == "resumo":
            texto = b.mensagem_resumo(b.ate(aniversarios, hoje, args.resumo_dias), hoje, args.resumo_dias)
        else:
            texto = b.mensagem_lembretes(b.proximos(aniversarios, hoje, _dias(args.dias)), hoje)

    if not texto:
        log.info("Nenhum aniversário para avisar hoje.")
        return 0

    print("-" * 40 + "\n" + texto + "\n" + "-" * 40)
    if args.dry_run:
        log.info("Dry-run: nada foi enviado.")
        return 0

    canais = notificadores_configurados()
    if not canais:
        log.error("Nenhum canal configurado (defina TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID ou os secrets do Twilio).")
        return 1

    erros = 0
    for canal in canais:
        try:
            canal.enviar(texto)
        except Exception as e:  # um canal com problema não impede os outros
            log.error("%s: %s", canal.nome, e)
            erros += 1
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
