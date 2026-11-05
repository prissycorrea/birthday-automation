"""I/O: leitura do Google Sheets e envio de mensagens."""
from __future__ import annotations

import json
import logging
import os

import requests

log = logging.getLogger(__name__)


# ------------------------------------------------------------------ Google Sheets

def ler_planilha() -> list[dict]:
    import gspread  # import tardio: os testes não precisam da lib

    creds = json.loads(os.environ["GSHEETS_CREDENTIALS_JSON"])
    gc = gspread.service_account_from_dict(creds)

    sheet_id = os.getenv("SHEET_ID", "").strip()
    planilha = gc.open_by_key(sheet_id) if sheet_id else gc.open(os.getenv("SHEET_NAME", "birthdays"))
    aba_nome = os.getenv("SHEET_TAB", "").strip()
    aba = planilha.worksheet(aba_nome) if aba_nome else planilha.sheet1

    # FORMATTED_VALUE (padrão) devolve datas como texto, o que o parser entende.
    return aba.get_all_records(default_blank="")


# ------------------------------------------------------------------ Notificadores

class Notificador:
    nome = "base"

    def enviar(self, texto: str) -> None:  # pragma: no cover
        raise NotImplementedError


class Telegram(Notificador):
    nome = "telegram"

    def __init__(self, token: str, chat_ids: list[str]):
        self.token = token
        self.chat_ids = chat_ids

    def enviar(self, texto: str) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        falhas = []
        for chat_id in self.chat_ids:
            r = requests.post(url, data={"chat_id": chat_id, "text": texto}, timeout=20)
            if r.ok:
                log.info("Telegram: enviado para %s", chat_id)
            else:
                # não loga o token; a descrição do Telegram já explica o erro
                desc = r.json().get("description", r.text) if r.headers.get("content-type", "").startswith("application/json") else r.text
                log.error("Telegram: falha para %s (%s): %s", chat_id, r.status_code, desc)
                falhas.append(chat_id)
        if falhas:
            raise RuntimeError(f"Telegram falhou para {len(falhas)} chat(s)")


class WhatsAppTwilio(Notificador):
    nome = "whatsapp"

    def __init__(self, sid: str, token: str, origem: str, destinos: list[str]):
        self.sid, self.token, self.origem, self.destinos = sid, token, origem, destinos

    def enviar(self, texto: str) -> None:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.sid}/Messages.json"
        falhas = []
        for destino in self.destinos:
            r = requests.post(url, auth=(self.sid, self.token),
                              data={"From": self.origem, "To": destino, "Body": texto}, timeout=20)
            if r.ok:
                log.info("WhatsApp: enviado para %s", destino)
            else:
                log.error("WhatsApp: falha para %s (%s): %s", destino, r.status_code, r.text[:300])
                falhas.append(destino)
        if falhas:
            raise RuntimeError(f"WhatsApp falhou para {len(falhas)} destino(s)")


def _lista(env: str) -> list[str]:
    return [x.strip() for x in os.getenv(env, "").split(",") if x.strip()]


def notificadores_configurados() -> list[Notificador]:
    """Ativa cada canal só se os secrets dele existirem."""
    canais: list[Notificador] = []
    if os.getenv("TELEGRAM_BOT_TOKEN") and _lista("TELEGRAM_CHAT_ID"):
        canais.append(Telegram(os.environ["TELEGRAM_BOT_TOKEN"], _lista("TELEGRAM_CHAT_ID")))
    if all(os.getenv(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM")) and _lista("TWILIO_TO"):
        canais.append(WhatsAppTwilio(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"],
                                     os.environ["TWILIO_FROM"], _lista("TWILIO_TO")))
    return canais
