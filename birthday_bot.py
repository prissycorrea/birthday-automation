import pandas as pd
from datetime import datetime, timedelta
from twilio.rest import Client
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import os
import pytz
import json

# ================== AUTENTICAÇÃO GOOGLE SHEETS ==================

# Lê as credenciais do JSON (armazenadas como string no secret)
creds_dict = json.loads(os.getenv("GSHEETS_CREDENTIALS_JSON"))

# Define escopo de acesso
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Cria as credenciais com base no dicionário
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

# Autoriza cliente do Google Sheets
gs_client = gspread.authorize(creds)

# Nome da planilha (deve ser exato ao que está no Google Sheets)
SHEET_NAME = "Aniversarios"  # ou use open_by_key("ID_DA_PLANILHA")
sheet = gs_client.open(SHEET_NAME).sheet1

# Lê os dados da planilha
records = sheet.get_all_records()
df = pd.DataFrame(records)

# ================== LÓGICA DO BOT ==================

# Configurações do Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_whatsapp = os.getenv("TWILIO_FROM")
to_whatsapp = os.getenv("TWILIO_TO")
client = Client(account_sid, auth_token)

# Fuso horário do Brasil
fuso_brasil = pytz.timezone("America/Sao_Paulo")
hoje = datetime.now(fuso_brasil).strftime("%m-%d")
amanha = (datetime.now(fuso_brasil) + timedelta(days=1)).strftime("%m-%d")

# Filtra aniversariantes de hoje ou amanhã
aniversariantes = df[df["data"].apply(lambda d: datetime.strptime(d, "%Y-%m-%d").strftime('%m-%d') in [hoje, amanha])]

if not aniversariantes.empty:
    for _, row in aniversariantes.iterrows():
        nome = row["nome"]
        data_aniversario = datetime.strptime(row["data"], "%Y-%m-%d").strftime("%d/%m")

        if data_aniversario == datetime.now(fuso_brasil).strftime("%d/%m"):
            mensagem = f"🎉 Hoje é aniversário do(a) {nome}! Não esqueça de dar os parabéns. 🥳"
        else:
            mensagem = f"🔔 Amanhã é aniversário do(a) {nome}! Se quiser planejar algo, ainda dá tempo. 🎁"

        client.messages.create(
            body=mensagem,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        print(f"Mensagem enviada: {mensagem}")
else:
    print("Nenhum aniversariante hoje ou amanhã.")
