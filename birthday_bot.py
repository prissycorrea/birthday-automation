import pandas as pd
from datetime import datetime, timedelta
from twilio.rest import Client
import os
import pytz

# Configurações do Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_whatsapp = os.getenv("TWILIO_FROM")
to_whatsapp = os.getenv("TWILIO_TO")

# Configurações de fuso horário (Brasil)
fuso_brasil = pytz.timezone('America/Sao_Paulo')
hoje = datetime.now(fuso_brasil).strftime('%m-%d')
amanha = (datetime.now(fuso_brasil) + timedelta(days=1)).strftime('%m-%d')

# Carrega aniversários
csv_path = "birthdays.csv"
df = pd.read_csv(csv_path)

# Filtra aniversariantes de hoje e amanhã
aniversariantes = df[df['data'].apply(lambda d: datetime.strptime(d, "%Y-%m-%d").strftime('%m-%d') in [hoje, amanha])]

if not aniversariantes.empty:
    client = Client(account_sid, auth_token)
    
    for _, row in aniversariantes.iterrows():
        nome = row['nome']
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
        print(f"Mensagem enviada para {to_whatsapp}: {mensagem}")
else:
    print("Nenhum aniversariante hoje ou amanhã.")
