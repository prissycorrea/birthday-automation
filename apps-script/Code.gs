/**
 * Web app de aniversários — Google Apps Script.
 *
 * Crie o projeto pela própria planilha (Extensões > Apps Script) e configure em
 * Configurações do projeto > Propriedades do script:
 *
 *   GITHUB_TOKEN     token fine-grained com "Actions: Read and write" só neste repo   (obrigatório p/ disparar)
 *   GITHUB_REPO      dono/repositorio            (padrão: prissycorrea/birthday-automation)
 *   GITHUB_WORKFLOW  arquivo do workflow         (padrão: birthday.yml)
 *   GITHUB_REF       branch                      (padrão: master)
 *   SHEET_ID         id da planilha              (só se o script NÃO estiver vinculado à planilha)
 *   SHEET_TAB        nome da aba                 (padrão: primeira aba)
 *   ALLOWED_EMAILS   e-mails liberados, separados por vírgula (opcional, recomendado)
 */

const HEADERS = ['nome', 'data', 'ativo', 'obs'];
const TZ = 'America/Sao_Paulo';

// ------------------------------------------------------------------ entrada

function doGet() {
  const email = usuarioAtual_();
  let permitido = acessoPermitido_(email);
  if (permitido) {
    try {
      aba_();
    } catch (e) {
      permitido = false;
    }
  }
  if (!permitido) {
    return HtmlService.createHtmlOutput(
      '<p style="font-family:sans-serif;padding:24px">Acesso negado para ' +
        (email ? escapeHtml_(email) : 'esta conta') + '.</p>'
    ).setTitle('Acesso negado');
  }
  return HtmlService.createTemplateFromFile('Index')
    .evaluate()
    .setTitle('Aniversários')
    .addMetaTag('viewport', 'width=device-width, initial-scale=1');
}

/** Menu na planilha com atalho para o app. */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('🎂 Aniversários')
    .addItem('Abrir app', 'abrirApp')
    .addItem('Disparar lembretes agora', 'dispararDoMenu')
    .addToUi();
}

function abrirApp() {
  const url = ScriptApp.getService().getUrl();
  const html = url
    ? `<p>Abrindo… se não abrir, <a href="${url}" target="_blank">clique aqui</a>.</p><script>window.open(${JSON.stringify(url)});google.script.host.close();</script>`
    : '<p>Publique o web app primeiro: Implantar &gt; Nova implantação &gt; App da Web.</p>';
  SpreadsheetApp.getUi().showModalDialog(HtmlService.createHtmlOutput(html).setHeight(80), 'Aniversários');
}

function dispararDoMenu() {
  const r = dispararWorkflow({ modo: 'lembretes', dryRun: false });
  SpreadsheetApp.getUi().alert(r.mensagem);
}

// ------------------------------------------------------------------ API chamada pelo front (google.script.run)

function getDados() {
  exigirAcesso_();
  const sh = aba_();
  const hoje = hoje_();
  const lista = [];
  const n = sh.getLastRow() - 1;
  if (n > 0) {
    const col = colunas_(sh);
    const largura = sh.getLastColumn();
    const valores = sh.getRange(2, 1, n, largura).getValues();
    const exibidos = sh.getRange(2, 1, n, largura).getDisplayValues();
    for (let i = 0; i < n; i++) {
      const nome = String(exibidos[i][col.nome] || '').trim();
      const bruto = valores[i][col.data];
      if (!nome && !bruto) continue;
      const d = parseData_(bruto, exibidos[i][col.data]);
      const item = {
        linha: i + 2,
        nome,
        dataTexto: exibidos[i][col.data],
        ativo: col.ativo == null ? true : ativo_(exibidos[i][col.ativo]),
        obs: col.obs == null ? '' : String(exibidos[i][col.obs] || ''),
        valido: !!d,
      };
      if (d) {
        const prox = proximaData_(d.dia, d.mes, hoje);
        Object.assign(item, {
          dia: d.dia, mes: d.mes, ano: d.ano,
          diasAte: Math.round((prox - hoje) / 864e5),
          proxima: Utilities.formatDate(prox, TZ, 'yyyy-MM-dd'),
          idade: d.ano ? prox.getFullYear() - d.ano : null,
        });
      }
      lista.push(item);
    }
  }
  const p = props_();
  return {
    aniversarios: lista,
    hoje: Utilities.formatDate(hoje, TZ, 'yyyy-MM-dd'),
    github: { configurado: !!p.GITHUB_TOKEN, repo: repo_() },
    planilhaUrl: sh.getParent().getUrl(),
    usuario: usuarioAtual_(),
  };
}

function salvarAniversario(dados) {
  exigirAcesso_();
  const nome = String(dados.nome || '').trim();
  const dia = Number(dados.dia), mes = Number(dados.mes);
  const ano = dados.ano ? Number(dados.ano) : null;
  if (!nome) throw new Error('Informe o nome.');
  if (!dataValida_(dia, mes, ano)) throw new Error('Data inválida.');
  if (ano && (ano < 1900 || ano > new Date().getFullYear())) throw new Error('Ano inválido.');

  const texto = ano ? `${ano}-${pad_(mes)}-${pad_(dia)}` : `${pad_(dia)}/${pad_(mes)}`;
  const linhaValores = [nome, texto, dados.ativo === false ? 'não' : 'sim', String(dados.obs || '').trim()];

  return comLock_(() => {
    const sh = aba_();
    const col = colunas_(sh, true);
    let linha;
    if (dados.linha) {
      linha = Number(dados.linha);
      conferirLinha_(sh, col, linha, dados.nomeOriginal);
    } else {
      linha = sh.getLastRow() + 1;
    }
    // só a célula gravada vira texto puro, para o Sheets não converter a data
    sh.getRange(linha, col.data + 1).setNumberFormat('@');
    HEADERS.forEach((h, i) => sh.getRange(linha, col[h] + 1).setValue(linhaValores[i]));
    return getDados();
  });
}

function excluirAniversario(linha, nomeOriginal) {
  exigirAcesso_();
  return comLock_(() => {
    const sh = aba_();
    conferirLinha_(sh, colunas_(sh), Number(linha), nomeOriginal);
    sh.deleteRow(Number(linha));
    return getDados();
  });
}

function dispararWorkflow(opcoes) {
  exigirAcesso_();
  const p = props_();
  if (!p.GITHUB_TOKEN) return { ok: false, mensagem: 'GITHUB_TOKEN não configurado nas propriedades do script.' };
  const modo = ['lembretes', 'resumo', 'teste'].indexOf(opcoes && opcoes.modo) >= 0 ? opcoes.modo : 'lembretes';
  const inputs = { modo, dry_run: !!(opcoes && opcoes.dryRun) };
  if (opcoes && /^\d{4}-\d{2}-\d{2}$/.test(opcoes.data || '')) inputs.data = opcoes.data;

  const r = github_('post', `/actions/workflows/${workflow_()}/dispatches`, {
    ref: p.GITHUB_REF || 'master',
    inputs,
  });
  if (r.getResponseCode() === 204) {
    return { ok: true, mensagem: `Automação disparada (${modo}${inputs.dry_run ? ', simulação' : ''}). Pode levar ~1 min.` };
  }
  return { ok: false, mensagem: `GitHub respondeu ${r.getResponseCode()}: ${resumoErro_(r)}` };
}

function getExecucoes() {
  exigirAcesso_();
  if (!props_().GITHUB_TOKEN) return [];
  const r = github_('get', `/actions/workflows/${workflow_()}/runs?per_page=8`);
  if (r.getResponseCode() !== 200) throw new Error(`GitHub respondeu ${r.getResponseCode()}: ${resumoErro_(r)}`);
  return JSON.parse(r.getContentText()).workflow_runs.map((x) => ({
    titulo: x.display_title,
    evento: x.event,
    status: x.status,
    conclusao: x.conclusion,
    criado: x.created_at,
    url: x.html_url,
  }));
}

// ------------------------------------------------------------------ planilha

function aba_() {
  const p = props_();
  const ss = p.SHEET_ID ? SpreadsheetApp.openById(p.SHEET_ID) : SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) throw new Error('Planilha não encontrada: vincule o script à planilha ou defina SHEET_ID.');
  const sh = p.SHEET_TAB ? ss.getSheetByName(p.SHEET_TAB) : ss.getSheets()[0];
  if (!sh) throw new Error(`Aba "${p.SHEET_TAB}" não encontrada.`);
  return sh;
}

/** Mapa cabeçalho -> índice (0-based). Com `criar`, adiciona colunas que faltam. */
function colunas_(sh, criar) {
  if (sh.getLastRow() === 0) {
    sh.getRange(1, 1, 1, HEADERS.length).setValues([HEADERS]).setFontWeight('bold');
    sh.setFrozenRows(1);
  }
  const larg = Math.max(sh.getLastColumn(), 1);
  const cab = sh.getRange(1, 1, 1, larg).getDisplayValues()[0].map((h) => String(h).trim().toLowerCase());
  const col = {};
  HEADERS.forEach((h) => {
    const i = cab.indexOf(h);
    if (i >= 0) col[h] = i;
  });
  if (col.nome == null || col.data == null) {
    if (!criar) throw new Error('A primeira linha precisa ter as colunas "nome" e "data".');
  }
  if (criar) {
    let prox = cab.filter((h) => h !== '').length ? larg : 0;
    HEADERS.forEach((h) => {
      if (col[h] == null) {
        sh.getRange(1, prox + 1).setValue(h).setFontWeight('bold');
        col[h] = prox++;
      }
    });
  }
  return col;
}

function conferirLinha_(sh, col, linha, nomeOriginal) {
  if (!(linha >= 2 && linha <= sh.getLastRow())) throw new Error('Linha não existe mais. Recarregue a lista.');
  const atual = String(sh.getRange(linha, col.nome + 1).getDisplayValue()).trim();
  if (nomeOriginal != null && atual !== String(nomeOriginal).trim()) {
    throw new Error('A planilha mudou desde que a lista foi carregada. Recarregue e tente de novo.');
  }
}

// ------------------------------------------------------------------ datas

function parseData_(valor, exibido) {
  if (valor instanceof Date && !isNaN(valor)) {
    const [a, m, d] = Utilities.formatDate(valor, TZ, 'yyyy-M-d').split('-').map(Number);
    return { dia: d, mes: m, ano: a };
  }
  const t = String(exibido || valor || '').trim().split(/[ T]/)[0];
  let m;
  let r = null;
  if ((m = t.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/))) r = { ano: +m[1], mes: +m[2], dia: +m[3] };
  else if ((m = t.match(/^(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})$/))) r = { dia: +m[1], mes: +m[2], ano: +m[3] };
  else if ((m = t.match(/^(\d{1,2})[/.-](\d{1,2})$/))) r = { dia: +m[1], mes: +m[2], ano: null };
  else if ((m = t.match(/^--(\d{1,2})-(\d{1,2})$/))) r = { mes: +m[1], dia: +m[2], ano: null };
  return r && dataValida_(r.dia, r.mes, r.ano) ? r : null;
}

function dataValida_(dia, mes, ano) {
  if (!(mes >= 1 && mes <= 12 && dia >= 1)) return false;
  const a = ano || 2000; // bissexto: aceita 29/02 sem ano
  return dia <= new Date(a, mes, 0).getDate();
}

function hoje_() {
  const [a, m, d] = Utilities.formatDate(new Date(), TZ, 'yyyy-M-d').split('-').map(Number);
  return new Date(a, m - 1, d);
}

function dataNoAno_(dia, mes, ano) {
  if (mes === 2 && dia === 29 && new Date(ano, 2, 0).getDate() === 28) return new Date(ano, 1, 28);
  return new Date(ano, mes - 1, dia);
}

function proximaData_(dia, mes, hoje) {
  let d = dataNoAno_(dia, mes, hoje.getFullYear());
  if (d < hoje) d = dataNoAno_(dia, mes, hoje.getFullYear() + 1);
  return d;
}

// ------------------------------------------------------------------ util

function github_(metodo, caminho, corpo) {
  const opts = {
    method: metodo,
    muteHttpExceptions: true,
    headers: {
      Authorization: 'Bearer ' + props_().GITHUB_TOKEN,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
    },
  };
  if (corpo) {
    opts.contentType = 'application/json';
    opts.payload = JSON.stringify(corpo);
  }
  return UrlFetchApp.fetch(`https://api.github.com/repos/${repo_()}${caminho}`, opts);
}

function resumoErro_(r) {
  try {
    return JSON.parse(r.getContentText()).message;
  } catch (e) {
    return r.getContentText().slice(0, 200);
  }
}

function props_() {
  return PropertiesService.getScriptProperties().getProperties();
}
function repo_() {
  return props_().GITHUB_REPO || 'prissycorrea/birthday-automation';
}
function workflow_() {
  return encodeURIComponent(props_().GITHUB_WORKFLOW || 'birthday.yml');
}
function ativo_(v) {
  return ['não', 'nao', 'n', 'false', 'falso', '0', 'no', 'inativo'].indexOf(String(v || '').trim().toLowerCase()) < 0;
}
function pad_(n) {
  return String(n).padStart(2, '0');
}
function usuarioAtual_() {
  return (Session.getActiveUser().getEmail() || '').toLowerCase();
}
function acessoPermitido_(email) {
  const lista = (props_().ALLOWED_EMAILS || '').split(',').map((s) => s.trim().toLowerCase()).filter(String);
  return lista.length === 0 || lista.indexOf(email) >= 0;
}
/**
 * O app roda como "usuário que acessa", então quem não tem acesso à planilha
 * não consegue abri-la — e por isso também não consegue disparar o workflow.
 */
function exigirAcesso_() {
  if (!acessoPermitido_(usuarioAtual_())) throw new Error('Acesso negado.');
  try {
    aba_();
  } catch (e) {
    throw new Error('Sem acesso à planilha. Peça para compartilharem com você.');
  }
}
function comLock_(fn) {
  const lock = LockService.getScriptLock();
  lock.waitLock(15000);
  try {
    return fn();
  } finally {
    lock.releaseLock();
  }
}
function escapeHtml_(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}
