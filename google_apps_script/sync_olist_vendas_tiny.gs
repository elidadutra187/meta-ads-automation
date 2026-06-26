/**
 * Sincroniza pedidos do Tiny ERP para a aba "Olist Vendas / Mês".
 *
 * Como instalar:
 * 1. Na planilha, abra Extensoes > Apps Script.
 * 2. Cole este arquivo no editor.
 * 3. Em Configurações do projeto > Propriedades do script, salve TINY_TOKEN.
 * 4. Execute sincronizarOlistVendasTiny() para testar.
 * 5. Execute aCriarGatilhoAgora() para rodar automaticamente a cada 1 hora.
 */

const SPREADSHEET_ID = '1SIrBdhLKB9TROzjciUkcyhUk9A4avaAtcUKE9IN3rYE';
const SHEET_NAME = 'Olist Vendas / Mês';
const TINY_BASE_URL = 'https://api.tiny.com.br/api2';
const MONTHS_PT = [
  'Janeiro',
  'Fevereiro',
  'Março',
  'Abril',
  'Maio',
  'Junho',
  'Julho',
  'Agosto',
  'Setembro',
  'Outubro',
  'Novembro',
  'Dezembro',
];

function aSincronizarAgora() {
  return sincronizarOlistVendasTiny();
}

function aCriarGatilhoAgora() {
  return criarGatilhoSincronizacaoTiny();
}

function aCorrigirCanceladosAgora() {
  return corrigirValoresCanceladosHistoricos();
}

function aAtualizarStatusCanceladosAgora() {
  return sincronizarStatusCanceladosTiny();
}

function configurarTinyToken() {
  const token = PropertiesService.getScriptProperties().getProperty('TINY_TOKEN');
  if (!token) {
    throw new Error('TINY_TOKEN ainda não está salvo. Abra Configurações do projeto > Propriedades do script e adicione TINY_TOKEN.');
  }

  return {
    status: 'ok',
    mensagem: 'TINY_TOKEN já está salvo nas propriedades do script.',
  };
}

function criarGatilhoSincronizacaoTiny() {
  const triggers = ScriptApp.getProjectTriggers();
  triggers
    .filter(trigger => trigger.getHandlerFunction() === 'sincronizarOlistVendasTiny')
    .forEach(trigger => ScriptApp.deleteTrigger(trigger));

  ScriptApp.newTrigger('sincronizarOlistVendasTiny')
    .timeBased()
    .everyHours(1)
    .create();

  return {
    status: 'ok',
    mensagem: 'Gatilho criado: sincronizar a cada 1 hora.',
  };
}

function sincronizarOlistVendasTiny() {
  const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
  if (!sheet) throw new Error(`Aba não encontrada: ${SHEET_NAME}`);

  const existing = carregarPedidosExistentes_(sheet);
  const maiorNumeroExistente = maiorNumeroPedidoExistente_(sheet);
  const maiorDataExistente = maiorDataPedidoExistente_(sheet);
  const pedidosResumo = listarTodosPedidosTiny_();
  const novasLinhas = [];
  const atualizacoes = coletarAtualizacoesStatusCancelado_(sheet, existing, pedidosResumo);

  pedidosResumo.forEach(resumo => {
    const numero = String(resumo.numero || '').trim();
    if (!numero) return;

    const rowIndex = existing[numero];
    if (rowIndex) return;

    const dataResumo = parseTinyDateOrNull_(resumo.data_pedido);
    if (!deveImportarPedidoNovo_(numero, dataResumo, maiorNumeroExistente, maiorDataExistente)) return;

    const detalhe = obterPedidoTiny_(resumo.id);
    novasLinhas.push(montarLinhaPlanilha_(detalhe));
  });

  if (novasLinhas.length > 0) {
    const startRow = encontrarProximaLinhaVendas_(sheet);
    sheet.getRange(startRow, 1, novasLinhas.length, 10).setValues(novasLinhas);
  }

  atualizacoes.forEach(item => {
    sheet.getRange(item.rowIndex, 6).setValue(item.status);
  });

  const resultado = {
    novosPedidos: novasLinhas.length,
    cancelamentosAtualizados: atualizacoes.length,
    verificados: pedidosResumo.length,
    maiorPedidoTiny: pedidosResumo.reduce((max, pedido) => Math.max(max, Number(pedido.numero || 0)), 0),
    maiorPedidoPlanilha: maiorNumeroExistente,
    maiorDataPlanilha: maiorDataExistente ? Utilities.formatDate(maiorDataExistente, Session.getScriptTimeZone(), 'dd/MM/yyyy') : null,
  };
  Logger.log(JSON.stringify(resultado));
  return resultado;
}

function sincronizarStatusCanceladosTiny() {
  const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
  if (!sheet) throw new Error(`Aba não encontrada: ${SHEET_NAME}`);

  const existing = carregarPedidosExistentes_(sheet);
  const pedidosResumo = listarTodosPedidosTiny_();
  const atualizacoes = coletarAtualizacoesStatusCancelado_(sheet, existing, pedidosResumo);

  atualizacoes.forEach(item => {
    sheet.getRange(item.rowIndex, 6).setValue(item.status);
  });

  const resultado = {
    status: 'ok',
    cancelamentosAtualizados: atualizacoes.length,
    verificados: pedidosResumo.length,
  };
  Logger.log(JSON.stringify(resultado));
  return resultado;
}

function coletarAtualizacoesStatusCancelado_(sheet, existing, pedidosResumo) {
  const atualizacoes = [];

  pedidosResumo.forEach(resumo => {
    const numero = String(resumo.numero || '').trim();
    if (!numero || !isCancelado_(resumo.situacao)) return;

    const rowIndex = existing[numero];
    if (!rowIndex) return;

    const statusAtual = sheet.getRange(rowIndex, 6).getDisplayValue();
    if (statusAtual !== 'CANCELADO') {
      atualizacoes.push({ rowIndex, status: 'CANCELADO' });
    }
  });

  return atualizacoes;
}

function encontrarProximaLinhaVendas_(sheet) {
  const lastRow = Math.max(sheet.getLastRow(), 2);
  const values = sheet.getRange(2, 3, lastRow - 1, 1).getValues();

  for (let index = values.length - 1; index >= 0; index -= 1) {
    if (String(values[index][0] || '').trim()) {
      return index + 3;
    }
  }

  return 2;
}

function carregarPedidosExistentes_(sheet) {
  const lastRow = sheet.getLastRow();
  const existing = {};
  if (lastRow < 2) return existing;

  const values = sheet.getRange(2, 3, lastRow - 1, 1).getValues();
  values.forEach((row, index) => {
    const numero = String(row[0] || '').trim();
    if (numero) existing[numero] = index + 2;
  });
  return existing;
}

function maiorNumeroPedidoExistente_(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return 0;

  const values = sheet.getRange(2, 3, lastRow - 1, 1).getValues();
  return values.reduce((max, row) => {
    const numero = Number(row[0] || 0);
    return Number.isFinite(numero) ? Math.max(max, numero) : max;
  }, 0);
}

function maiorDataPedidoExistente_(sheet) {
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return null;

  const values = sheet.getRange(2, 4, lastRow - 1, 1).getValues();
  return values.reduce((max, row) => {
    const data = row[0] instanceof Date ? row[0] : parseTinyDateOrNull_(row[0]);
    if (!data || Number.isNaN(data.getTime())) return max;
    if (!max || data.getTime() > max.getTime()) return data;
    return max;
  }, null);
}

function deveImportarPedidoNovo_(numero, dataPedido, maiorNumeroExistente, maiorDataExistente) {
  const numeroPedido = Number(numero || 0);
  if (Number.isFinite(numeroPedido) && numeroPedido > maiorNumeroExistente) return true;
  if (!maiorDataExistente || !dataPedido || Number.isNaN(dataPedido.getTime())) return false;

  const margemMs = 7 * 24 * 60 * 60 * 1000;
  return dataPedido.getTime() >= maiorDataExistente.getTime() - margemMs;
}

function listarTodosPedidosTiny_() {
  const pedidos = [];
  let pagina = 1;

  while (true) {
    let retorno;
    try {
      retorno = tinyRequest_('pedidos.pesquisa.php', { pagina });
    } catch (error) {
      const message = String(error && error.message ? error.message : error);
      if (message.indexOf('página que') >= 0 || message.indexOf('pagina') >= 0) break;
      throw error;
    }

    const paginaPedidos = retorno.pedidos || [];
    paginaPedidos.forEach(item => pedidos.push(item.pedido || item));

    if (paginaPedidos.length === 0 || paginaPedidos.length < 100) break;
    pagina += 1;
    if (pagina > 30) throw new Error('Limite de segurança de páginas do Tiny atingido.');
  }

  return pedidos;
}

function obterPedidoTiny_(pedidoId) {
  const retorno = tinyRequest_('pedido.obter.php', { id: pedidoId });
  return retorno.pedido || retorno;
}

function corrigirValoresCanceladosHistoricos() {
  const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(SHEET_NAME);
  if (!sheet) throw new Error(`Aba não encontrada: ${SHEET_NAME}`);

  const valoresPorLinha = {
    7: 1052.30,
    16: 3277.09,
    35: 4282.40,
    36: 1257.26,
    41: 1167.60,
    46: 1801.10,
    50: 960.00,
    51: 1116.45,
    53: 5649.60,
    59: 1116.45,
    63: 1500.00,
    77: 2900.00,
    79: 1005.76,
    81: 3251.84,
    84: 3277.99,
    85: 8704.80,
    91: 1324.52,
    100: 6745.60,
    109: 11720.12,
    112: 2700.00,
    115: 1980.15,
    118: 1658.00,
    121: 3300.00,
    131: 1958.36,
    141: 3280.00,
    142: 9280.02,
    143: 1623.35,
    146: 8701.00,
    150: 1607.20,
    173: 1400.00,
    175: 900.00,
    185: 1540.00,
    188: 22890.40,
    223: 1459.90,
    237: 7000.00,
    246: 1152.00,
    247: 4211.74,
    249: 1800.00,
    256: 1383.73,
    266: 3800.00,
    268: 1150.00,
    281: 1166.00,
    284: 9286.92,
    289: 5337.95,
    291: 5594.50,
    294: 5639.93,
    305: 1460.20,
    308: 1539.78,
    314: 5533.99,
    316: 17719.74,
    336: 68.59,
    345: 2600.00,
    347: 8458.81,
    350: 1007.46,
    352: 31199.99,
    353: 1799.28,
    360: 280.00,
    366: 2603.07,
    381: 12303.19,
  };

  Object.keys(valoresPorLinha).forEach(row => {
    sheet.getRange(Number(row), 5).setValue(valoresPorLinha[row]);
  });

  return {
    status: 'ok',
    linhasCorrigidas: Object.keys(valoresPorLinha).length,
  };
}

function tinyRequest_(endpoint, params) {
  const token = PropertiesService.getScriptProperties().getProperty('TINY_TOKEN');
  if (!token) throw new Error('TINY_TOKEN não configurado. Execute configurarTinyToken().');

  const payload = Object.assign({ token, formato: 'json' }, params || {});
  const formBody = Object.keys(payload)
    .filter(key => payload[key] !== undefined && payload[key] !== null && payload[key] !== '')
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(String(payload[key]))}`)
    .join('&');

  const response = UrlFetchApp.fetch(`${TINY_BASE_URL}/${endpoint}`, {
    method: 'post',
    contentType: 'application/x-www-form-urlencoded',
    payload: formBody,
    muteHttpExceptions: true,
  });

  const code = response.getResponseCode();
  const text = response.getContentText();
  if (code < 200 || code >= 300) {
    throw new Error(`Tiny HTTP ${code}: ${text}`);
  }

  const data = JSON.parse(text);
  const retorno = data.retorno || data;
  if (retorno.status === 'Erro') {
    throw new Error(`Tiny erro: ${JSON.stringify(retorno.erros || retorno)}`);
  }
  return retorno;
}

function montarLinhaPlanilha_(pedido) {
  const data = parseTinyDate_(pedido.data_pedido);
  const cliente = pedido.cliente || {};
  const numeroEcommerce = String(pedido.numero_ecommerce || '').trim();
  const venda = numeroEcommerce ? 'NuvemShop' : 'Loja Física';
  const valor = Number(pedido.total_pedido || pedido.valor || 0);
  const status = isCancelado_(pedido.situacao) ? 'CANCELADO' : 'EFETIVO';

  return [
    data.getFullYear(),
    MONTHS_PT[data.getMonth()],
    Number(pedido.numero),
    data,
    valor,
    status,
    inferirEmpresa_(pedido),
    venda,
    String(cliente.uf || '').trim(),
    String(cliente.cidade || '').trim(),
  ];
}

function parseTinyDate_(value) {
  const parts = String(value || '').split('/');
  if (parts.length !== 3) return new Date();
  return new Date(Number(parts[2]), Number(parts[1]) - 1, Number(parts[0]));
}

function parseTinyDateOrNull_(value) {
  if (value instanceof Date) return value;
  const parts = String(value || '').split('/');
  if (parts.length !== 3) return null;
  const data = new Date(Number(parts[2]), Number(parts[1]) - 1, Number(parts[0]));
  return Number.isNaN(data.getTime()) ? null : data;
}

function isCancelado_(situacao) {
  return String(situacao || '').toLowerCase().indexOf('cancel') >= 0;
}

function inferirEmpresa_(pedido) {
  const text = [
    pedido.obs,
    pedido.obs_interna,
    pedido.deposito,
    pedido.descricao_lista_preco,
    JSON.stringify(pedido.marcadores || []),
    JSON.stringify(pedido.itens || []),
  ].join(' ').toLowerCase();

  if (text.indexOf('marmoraria') >= 0) return 'Marmoraria';
  return 'Saldão';
}
