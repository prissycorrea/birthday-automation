import pandas as pd
from datetime import datetime
from twilio.rest import Client
import os

# Lê variáveis de ambiente
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
from_whatsapp = os.getenv("TWILIO_FROM")
to_whatsapp = os.getenv("TWILIO_TO")

# Carrega aniversários
df = pd.read_csv("aniversarios.csv")
hoje = datetime.today().strftime('%m-%d')

# Filtra aniversariantes de hoje
aniversariantes = df[df['data'].apply(lambda d: datetime.strptime(d, '%Y-%m-%d').strftime('%m-%d') == hoje)]

if not aniversariantes.empty:
    client = Client(account_sid, auth_token)
    for _, row in aniversariantes.iterrows():
        nome = row['nome']
        mensagem = f"🎉 Hoje é aniversário do(a) {nome}! Não esqueça de dar os parabéns. 🥳"
        client.messages.create(
            body=mensagem,
            from_=from_whatsapp,
            to=to_whatsapp
        )
        print(f"Mensagem enviada: {mensagem}")
else:
    print("Nenhum aniversariante hoje.")
