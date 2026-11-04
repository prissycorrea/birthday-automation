# 🤖 Bot de Aniversários (Google Sheets + Telegram)

Bot que lê os aniversários de uma planilha do **Google Sheets** e manda lembretes no **Telegram** (e, opcionalmente, no WhatsApp via Twilio) todos os dias às **07h (Brasília)**, rodando no GitHub Actions.

Agora com um **web app** (Google Apps Script) para cadastrar, editar e excluir aniversários direto na planilha e **disparar a automação** com um clique — funciona no celular.

---

## 💡 O que ele faz

- 📆 Avisa quem faz aniversário **hoje** e **amanhã** (antecedências configuráveis, ex.: `0,1,7`)
- 🧮 Mostra a **idade** que a pessoa vai fazer, quando o ano é informado
- 📨 Manda **uma mensagem só** por dia, agrupando todos os aniversariantes
- 📋 Modo **resumo**: lista os aniversários dos próximos 30 dias
- ✅ Modo **teste**: confirma que o Telegram/WhatsApp está funcionando
- 🧪 **Simulação** (dry-run) e **simular outra data** para testar sem enviar nada
- 🛡️ Linhas com data inválida não derrubam o bot: aparecem como aviso no log
- 🗓️ Quem nasceu em 29/02 é lembrado em 28/02 nos anos não bissextos

---

## 📂 Estrutura da planilha

Planilha chamada **`birthdays`** (ou defina `SHEET_ID`), com cabeçalho na primeira linha:

| nome          | data       | ativo | obs              |
|---------------|------------|-------|------------------|
| João da Silva | 1990-03-21 | sim   | primo            |
| Maria Souza   | 15/07      |       | sem ano, tudo bem |
| Pedro         | 02/03/1992 | não   | não lembrar      |

- `nome` e `data` são obrigatórias. `ativo` e `obs` são opcionais (o web app cria se faltar).
- Formatos de data aceitos: `YYYY-MM-DD`, `DD/MM/YYYY`, `DD/MM` (sem ano).
- `ativo` = `não`/`false`/`0` desliga o lembrete daquela pessoa.

---

## 🖥️ Web app (Apps Script)

O código está em [`apps-script/`](apps-script/).

### 1. Criar o projeto

1. Abra a planilha **birthdays** → **Extensões → Apps Script**
2. Substitua o conteúdo de `Código.gs` pelo de [`apps-script/Code.gs`](apps-script/Code.gs)
3. Crie um arquivo HTML chamado **`Index`** e cole [`apps-script/Index.html`](apps-script/Index.html)
4. (Opcional) Em **Configurações do projeto**, marque “Mostrar o arquivo de manifesto” e cole [`apps-script/appsscript.json`](apps-script/appsscript.json)

> Prefere linha de comando? Use o [`clasp`](https://github.com/google/clasp): `clasp clone <scriptId>` e `clasp push` a partir da pasta `apps-script/`.

### 2. Token do GitHub (para o botão “Disparar”)

1. GitHub → **Settings → Developer settings → Fine-grained tokens → Generate new token**
2. **Repository access**: só este repositório
3. **Permissions → Actions: Read and write** (nada mais)
4. Copie o token

### 3. Propriedades do script

Em **Configurações do projeto → Propriedades do script**:

| Propriedade      | Valor                                                      |
|------------------|------------------------------------------------------------|
| `GITHUB_TOKEN`   | o token do passo anterior                                  |
| `GITHUB_REPO`    | `prissycorrea/birthday-automation` (padrão)                |
| `SHEET_ID`       | id da planilha (o trecho entre `/d/` e `/edit` na URL) — recomendado |
| `ALLOWED_EMAILS` | e-mails que podem usar o app, separados por vírgula — recomendado |

Opcionais: `GITHUB_WORKFLOW` (padrão `birthday.yml`), `GITHUB_REF` (padrão `master`), `SHEET_TAB` (padrão: primeira aba).

### 4. Publicar

1. **Implantar → Nova implantação → App da Web**
2. **Executar como:** *Usuário que acessa o app da Web*
3. **Quem pode acessar:** *Qualquer pessoa com uma Conta do Google*
4. Autorize e copie a URL (dá pra salvar na tela inicial do celular)

🔒 Segurança: o app roda com a conta de quem acessa, então só quem tem acesso à planilha (e está em `ALLOWED_EMAILS`, se definido) consegue ver os dados ou disparar o workflow. O token do GitHub fica nas propriedades do script, nunca vai para o navegador.

Depois de publicar, a planilha ganha o menu **🎂 Aniversários** (abrir app / disparar lembretes).

---

## ⚙️ Configuração do bot (GitHub Actions)

### 1. Bot do Telegram

1. Fale com o [@BotFather](https://t.me/BotFather), envie `/newbot` e copie o **token**
2. Mande uma mensagem para o bot e abra `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
3. Copie o `"chat": { "id": ... }` — pode usar **vários IDs** separados por vírgula

### 2. Acesso ao Google Sheets

1. No [Google Cloud Console](https://console.cloud.google.com/), ative **Google Sheets API** e **Google Drive API**
2. Crie uma **conta de serviço** e baixe a chave `.json`
3. Compartilhe a planilha com o e-mail da conta de serviço (leitor)

### 3. Secrets e variáveis

`Settings → Secrets and variables → Actions`

**Secrets**

| Nome                       | Valor                                           |
|----------------------------|-------------------------------------------------|
| `GSHEETS_CREDENTIALS_JSON` | conteúdo completo do `.json` da conta de serviço |
| `TELEGRAM_BOT_TOKEN`       | token do bot                                    |
| `TELEGRAM_CHAT_ID`         | chat ID(s), separados por vírgula               |
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM`, `TWILIO_TO` | *(opcional)* WhatsApp via Twilio — só é usado se os quatro existirem |

**Variables** (opcionais)

| Nome            | Padrão      | Para quê                                        |
|-----------------|-------------|-------------------------------------------------|
| `LEMBRETE_DIAS` | `0,1`       | antecedências do lembrete (ex.: `0,1,7`)        |
| `RESUMO_DIAS`   | `30`        | janela do modo resumo                           |
| `SHEET_ID`      | —           | abre a planilha pelo id em vez do nome          |
| `SHEET_NAME`    | `birthdays` | nome da planilha                                |

---

## ⏰ Execução

- **Automática:** todo dia às 07:00 (Brasília) — `cron: '0 10 * * *'`
- **Manual:** pelo web app ou em **Actions → Enviar lembrete de aniversários → Run workflow**, escolhendo modo, simulação e data
- O workflow `keepalive` faz um commit mensal para o GitHub não desativar o agendamento por inatividade

### Rodando localmente

```bash
pip install -r requirements-dev.txt
export GSHEETS_CREDENTIALS_JSON="$(cat chave.json)"
python main.py --dry-run                     # mostra a mensagem de hoje
python main.py --modo resumo --dry-run       # próximos 30 dias
python main.py --data 2026-03-20 --dry-run   # simula outro dia
python -m pytest                             # testes
```

---

## 🛠️ Estrutura do projeto

```
main.py                    # entrada: lê a planilha, monta e envia a mensagem
bot/birthdays.py           # regras (datas, idade, 29/02, mensagens) — sem I/O
bot/integrations.py        # Google Sheets, Telegram e WhatsApp
tests/                     # testes (pytest)
apps-script/               # web app (Code.gs, Index.html, appsscript.json)
.github/workflows/
  birthday.yml             # agendamento diário + disparo manual
  tests.yml                # roda os testes em push/PR
  keepalive.yml            # mantém o agendamento ativo
```

---

## 👩‍💻 Autor

Feito com carinho por [@prissycorrea](https://github.com/prissycorrea) 💜
Sinta-se à vontade para usar, modificar e compartilhar!
