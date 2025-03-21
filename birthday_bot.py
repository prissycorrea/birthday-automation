import pandas as pd
from datetime import datetime
from twilio.rest import Client
import os
import pytz

# Configurações do Twilio
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_whatsapp = os.getenv("TWILIO_FROM")

# Converte os números para uma lista (removendo espaços extras)
to_whatsapp_numbers = [num.strip() for num in os.getenv("TWILIO_TO", "").split(",")]

# Obtém a data correta considerando fuso horário do Brasil
fuso_brasil = pytz.timezone('America/Sao_Paulo')
hoje = datetime.now(fuso_brasil).strftime('%m-%d')

# Carrega aniversários
csv_path = "birthdays.csv"
df = pd.read_csv(csv_path)

# Filtra aniversariantes de hoje
aniversariantes = df[df['data'].apply(lambda d: datetime.strptime(d, '%Y-%m-%d').strftime('%m-%d') == hoje)]

if not aniversariantes.empty:
    client = Client(account_sid, auth_token)
    
    for _, row in aniversariantes.iterrows():
        nome = row['nome']
        mensagem = f"🎉 Hoje é aniversário do(a) {nome}! Não esqueça de dar os parabéns. 🥳"

        for to_whatsapp in to_whatsapp_numbers:
            client.messages.create(
                body=mensagem,
                from_=from_whatsapp,
                to=to_whatsapp
            )
            print(f"Mensagem enviada para {to_whatsapp}: {mensagem}")
else:
    print("Nenhum aniversariante hoje.")
