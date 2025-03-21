# 🤖 Bot de Aniversários (Telegram + Google Sheets)

Este é um bot automatizado que envia mensagens de **aviso de aniversário via Telegram**, usando os dados de uma planilha privada do **Google Sheets**. Ideal para quem quer lembrar todos os dias de aniversários importantes, direto no Telegram!

---

## 💡 O que este bot faz

- 📆 Verifica se **hoje ou amanhã** é aniversário de alguém
- 🤖 Envia uma **mensagem automática via Telegram avisando sobre o aniversário de hoje ou amanhã**
- 🕖 Funciona todos os dias às **07h da manhã (horário de Brasília)** com GitHub Actions

---

## 📂 Estrutura da planilha

Sua planilha no Google Sheets deve:

- Se chamar **`birthdays`**
- Ter duas colunas: `nome` e `data`
- As datas devem estar no formato `YYYY-MM-DD`

### Exemplo:

| nome           | data       |
|----------------|------------|
| João da Silva  | 1990-03-21 |
| Maria Souza    | 1985-07-15 |

> 🔸 A primeira linha deve conter os cabeçalhos  
> 🔸 A planilha deve estar compartilhada com a conta de serviço do Google

---

## ⚙️ Como configurar

### 1. Crie seu bot no Telegram

1. Fale com o [@BotFather](https://t.me/BotFather)
2. Envie o comando `/newbot` e siga os passos
3. Copie o **token de API** gerado

### 2. Pegue seu `chat_id` do Telegram

1. Mande uma mensagem para o seu bot
2. Acesse:

```
https://api.telegram.org/bot<SEU_TOKEN>/getUpdates
```

3. Copie o campo `"chat": { "id": ... }`

> Você pode usar **mais de um ID**, separando-os por vírgula.

---

### 3. Configure o acesso ao Google Sheets

1. Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/)
2. Ative as APIs:
   - ✅ Google Sheets API
   - ✅ Google Drive API
3. Crie uma **conta de serviço**
4. Baixe o arquivo `.json` da chave
5. Compartilhe a planilha com o e-mail da conta de serviço (como leitor)

---

### 4. Adicione os secrets no GitHub

Vá em: `Settings > Secrets and variables > Actions`

Crie os seguintes secrets:

| Nome                      | Valor                                          |
|---------------------------|------------------------------------------------|
| `GSHEETS_CREDENTIALS_JSON` | Conteúdo completo do `.json` da conta de serviço |
| `TELEGRAM_BOT_TOKEN`      | Token do bot do Telegram                       |
| `TELEGRAM_CHAT_ID`        | Chat ID(s) que vão receber as mensagens        |

---

## 🛠️ Estrutura do projeto

- `telegram_bot.py`: script principal que lê a planilha e envia mensagens
- `.github/workflows/birthday.yml`: workflow agendado com GitHub Actions
- `README.md`: este arquivo ✨

---

## ⏰ Agendamento

O bot é executado todos os dias às **07:00 da manhã (horário de Brasília)**:

```yaml
schedule:
  - cron: '0 10 * * *'  # 10h UTC = 07h BRT
```

Você também pode executar manualmente pela aba **Actions** do GitHub.

---

## 👩‍💻 Autor

Feito com carinho por [@prissycorrea](https://github.com/prissycorrea) 💜  
Sinta-se à vontade para usar, modificar e compartilhar!
