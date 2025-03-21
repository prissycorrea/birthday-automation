import pandas as pd
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pytz
import os
import json
import requests

# === Google Sheets ===
creds_dict = json.loads(os.getenv("GSHEETS_CREDENTIALS_JSON"))

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gs_client = gspread.authorize(creds)

# Nome da planilha
sheet = gs_client.open("birthdays").sheet1
records = sheet.get_all_records()
df = pd.DataFrame(records)
df.columns = df.columns.str.strip().str.lower()

# === Telegram ===
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# === Lógica de aniversário ===
fuso_brasil = pytz.timezone("America/Sao_Paulo")
hoje = datetime.now(fuso_brasil).strftime("%m-%d")
amanha = (datetime.now(fuso_brasil) + timedelta(days=1)).strftime("%m-%d")

aniversariantes = df[df["data"].apply(lambda d: datetime.strptime(d, "%Y-%m-%d").strftime('%m-%d') in [hoje, amanha])]

# Pega a lista de chat_ids separados por vírgula
CHAT_IDS = os.getenv("TELEGRAM_CHAT_ID").split(",")

def enviar_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        data = {
            "chat_id": chat_id.strip(),
            "text": msg
        }
        r = requests.post(url, data=data)
        print(f"Enviado para {chat_id.strip()}: {msg} | Status: {r.status_code}")


if not aniversariantes.empty:
    for _, row in aniversariantes.iterrows():
        nome = row["nome"]
        data_nasc = datetime.strptime(row["data"], "%Y-%m-%d").strftime("%d/%m")
        if data_nasc == datetime.now(fuso_brasil).strftime("%d/%m"):
            mensagem = f"🎉 Hoje é aniversário do(a) {nome}! Não esqueça de dar os parabéns. 🥳"
        else:
            mensagem = f"🔔 Amanhã é aniversário do(a) {nome}! Se quiser planejar algo, ainda dá tempo. 🎁"
        enviar_telegram(mensagem)
else:
    print("Nenhum aniversariante hoje ou amanhã.")
