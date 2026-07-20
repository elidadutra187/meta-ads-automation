/**
 * SINCRONIZAÇÃO TINY ERP → GOOGLE SHEETS
 *
 * Aba: Olist Vendas / Mês
 *
 * Estrutura:
 * A - Mês
 * B - Numero do Pedido
 * C - Data
 * D - Valor
 * E - Método de Pagamento
 * F - Banco
 * G - Parcelamento
 * H - Entregas
 * I - Status
 * J - Empresa
 * K - Venda
 * L - Estado
 * M - Cidade
 *
 * Pedidos até 794:
 * - Não são consultados para pagamento.
 * - Recebem "SEM DADOS".
 *
 * Pedidos a partir de 795:
 * - São consultados individualmente no Tiny.
 * - O método de pagamento é gravado na coluna F.
 *
 * Instalação:
 * 1. Abra Extensões > Apps Script.
 * 2. Apague o código anterior.
 * 3. Cole este código completo.
 * 4. Salve.
 * 5. Confirme o TINY_TOKEN nas Propriedades do script.
 * 6. Execute aSincronizarAgora para testar.
 * 7. Execute aIniciarAtualizacaoPagamentosHistoricos uma vez.
 */

const SPREADSHEET_ID =
  '1SIrBdhLKB9TROzjciUkcyhUk9A4avaAtcUKE9IN3rYE';

const SHEET_NAME = 'Olist Vendas / Mês';

const TINY_BASE_URL =
  'https://api.tiny.com.br/api2';

const PRIMEIRO_PEDIDO_COM_PAGAMENTO = 795;

const HISTORICO_PAGAMENTOS_CURSOR =
  'HISTORICO_PAGAMENTOS_CURSOR';

const HISTORICO_PAGAMENTOS_BATCH_SIZE = 10;

const COL_MES_ANO = 1;
const COL_NUMERO_PEDIDO = 2;
const COL_DATA = 3;
const COL_VALOR = 4;
const COL_METODO_PAGAMENTO = 5;
const COL_BANCO = 6;
const COL_PARCELAMENTO = 7;
const COL_ENTREGAS = 8;
const COL_STATUS = 9;
const COL_EMPRESA = 10;
const TOTAL_COLUNAS_VENDAS = 13;

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

/**
 * FUNÇÕES PARA EXECUTAR MANUALMENTE
 */

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

function aAtualizarEntregasAgora() {
  return sincronizarEntregasTiny();
}

function aReconciliarEntregasComTinyAgora() {
  return reconciliarEntregasComTiny_();
}

function aReestruturarPagamentosEEntregasAgora() {
  return reestruturarPagamentosEEntregasTiny_();
}

function aJuntarAnoMesAgora() {
  return juntarAnoMesPlanilha_();
}

function aOrdenarVendasPorDataAgora() {
  const sheet = obterAbaVendas_();

  return ordenarVendasPorData_(sheet);
}

function aAtualizarPagamentosHistoricosAgora() {
  return atualizarMetodosPagamentoHistoricosTiny();
}

function aNormalizarPagamentosAgora() {
  return normalizarMetodosPagamentoPlanilha_();
}

function aIniciarAtualizacaoPagamentosHistoricos() {
  const sheet = obterAbaVendas_();

  garantirCabecalhos_(sheet);

  const primeiraLinha =
    encontrarPrimeiraLinhaAPartirDoPedido_(
      sheet,
      PRIMEIRO_PEDIDO_COM_PAGAMENTO
    );

  const props =
    PropertiesService.getScriptProperties();

  props.setProperty(
    HISTORICO_PAGAMENTOS_CURSOR,
    String(primeiraLinha)
  );

  removerGatilhosDaFuncao_(
    'atualizarMetodosPagamentoHistoricosTiny'
  );

  ScriptApp
    .newTrigger(
      'atualizarMetodosPagamentoHistoricosTiny'
    )
    .timeBased()
    .everyMinutes(5)
    .create();

  const resultado =
    atualizarMetodosPagamentoHistoricosTiny();

  return {
    status: 'iniciado',
    primeiraLinha,
    primeiroPedido:
      PRIMEIRO_PEDIDO_COM_PAGAMENTO,
    resultadoPrimeiroLote: resultado,
  };
}

function aCancelarAtualizacaoPagamentosHistoricos() {
  PropertiesService
    .getScriptProperties()
    .deleteProperty(
      HISTORICO_PAGAMENTOS_CURSOR
    );

  removerGatilhosDaFuncao_(
    'atualizarMetodosPagamentoHistoricosTiny'
  );

  return {
    status: 'cancelado',
    mensagem:
      'A atualização histórica de pagamentos foi cancelada.',
  };
}

/**
 * TOKEN
 */

function configurarTinyToken() {
  const token =
    PropertiesService
      .getScriptProperties()
      .getProperty('TINY_TOKEN');

  if (!token) {
    throw new Error(
      'TINY_TOKEN ainda não está salvo. ' +
      'Abra Configurações do projeto > ' +
      'Propriedades do script e adicione TINY_TOKEN.'
    );
  }

  return {
    status: 'ok',
    mensagem:
      'TINY_TOKEN está configurado.',
  };
}

/**
 * GATILHO PRINCIPAL
 */

function criarGatilhoSincronizacaoTiny() {
  removerGatilhosDaFuncao_(
    'sincronizarOlistVendasTiny'
  );

  ScriptApp
    .newTrigger('sincronizarOlistVendasTiny')
    .timeBased()
    .everyHours(1)
    .create();

  return {
    status: 'ok',
    mensagem:
      'Gatilho criado para sincronizar a cada 1 hora.',
  };
}

/**
 * SINCRONIZAÇÃO DE NOVOS PEDIDOS
 */

function sincronizarOlistVendasTiny() {
  const lock =
    LockService.getScriptLock();

  if (!lock.tryLock(10000)) {
    return {
      status: 'ocupado',
      mensagem:
        'Já existe uma sincronização em execução.',
    };
  }

  try {
    const sheet = obterAbaVendas_();

    garantirCabecalhos_(sheet);

    const existing =
      carregarPedidosExistentes_(sheet);

    const maiorNumeroExistente =
      maiorNumeroPedidoExistente_(sheet);

    const maiorDataExistente =
      maiorDataPedidoExistente_(sheet);

    const pedidosResumo =
      listarTodosPedidosTiny_();

    const novasLinhas = [];

    const atualizacoes =
      coletarAtualizacoesStatusPedido_(
        sheet,
        existing,
        pedidosResumo
      );

    pedidosResumo.forEach(resumo => {
      const numero = String(
        resumo.numero || ''
      ).trim();

      if (!numero) {
        return;
      }

      const rowIndex = existing[numero];

      if (rowIndex) {
        return;
      }

      const dataResumo =
        parseTinyDateOrNull_(
          resumo.data_pedido
        );

      const deveImportar =
        deveImportarPedidoNovo_(
          numero,
          dataResumo,
          maiorNumeroExistente,
          maiorDataExistente
        );

      if (!deveImportar) {
        return;
      }

      try {
        const detalhe =
          obterPedidoTiny_(resumo.id);

        novasLinhas.push(
          montarLinhaPlanilha_(detalhe)
        );
      } catch (error) {
        Logger.log(
          `Erro ao obter pedido ${numero}: ` +
          `${obterMensagemErro_(error)}`
        );
      }
    });

    if (novasLinhas.length > 0) {
      const startRow =
        encontrarProximaLinhaVendas_(sheet);

      sheet
        .getRange(
          startRow,
          1,
          novasLinhas.length,
          TOTAL_COLUNAS_VENDAS
        )
        .setValues(novasLinhas);
    }

    atualizacoes.forEach(item => {
      if (item.entrega) {
        sheet
          .getRange(
            item.rowIndex,
            COL_ENTREGAS
          )
          .setValue(item.entrega);
      }

      if (item.status) {
        sheet
          .getRange(
            item.rowIndex,
            COL_STATUS
          )
          .setValue(item.status);
      }
    });

    const ordenacao =
      ordenarVendasPorData_(sheet);

    SpreadsheetApp.flush();

    const resultado = {
      status: 'ok',
      novosPedidos:
        novasLinhas.length,
      cancelamentosAtualizados:
        atualizacoes.length,
      pedidosVerificados:
        pedidosResumo.length,
      maiorPedidoTiny:
        pedidosResumo.reduce(
          (max, pedido) => {
            const numero =
              Number(pedido.numero || 0);

            return Number.isFinite(numero)
              ? Math.max(max, numero)
              : max;
          },
          0
        ),
      maiorPedidoPlanilha:
        maiorNumeroExistente,
      maiorDataPlanilha:
        maiorDataExistente
          ? Utilities.formatDate(
              maiorDataExistente,
              Session.getScriptTimeZone(),
              'dd/MM/yyyy'
            )
          : null,
      ordenacao,
    };

    Logger.log(
      JSON.stringify(resultado)
    );

    return resultado;
  } finally {
    lock.releaseLock();
  }
}

/**
 * ATUALIZAÇÃO DE CANCELAMENTOS
 */

function sincronizarStatusCanceladosTiny() {
  const sheet = obterAbaVendas_();

  const existing =
    carregarPedidosExistentes_(sheet);

  const pedidosResumo =
    listarTodosPedidosTiny_();

  const atualizacoes =
    coletarAtualizacoesStatusPedido_(
      sheet,
      existing,
      pedidosResumo
    );

  atualizacoes.forEach(item => {
    if (item.status) {
      sheet
        .getRange(
          item.rowIndex,
          COL_STATUS
        )
        .setValue(item.status);
    }
  });

  SpreadsheetApp.flush();

  const resultado = {
    status: 'ok',
    cancelamentosAtualizados:
      atualizacoes.length,
    verificados:
      pedidosResumo.length,
  };

  Logger.log(
    JSON.stringify(resultado)
  );

  return resultado;
}

function sincronizarEntregasTiny() {
  const sheet = obterAbaVendas_();

  garantirCabecalhos_(sheet);

  const existing =
    carregarPedidosExistentes_(sheet);

  const pedidosResumo =
    listarTodosPedidosTiny_();

  const atualizacoes =
    coletarAtualizacoesStatusPedido_(
      sheet,
      existing,
      pedidosResumo
    );

  atualizacoes.forEach(item => {
    if (item.entrega) {
      sheet
        .getRange(
          item.rowIndex,
          COL_ENTREGAS
        )
        .setValue(item.entrega);
    }

    if (item.status) {
      sheet
        .getRange(
          item.rowIndex,
          COL_STATUS
        )
        .setValue(item.status);
    }
  });

  SpreadsheetApp.flush();

  const resultado = {
    status: 'ok',
    entregasAtualizadas:
      atualizacoes.filter(item =>
        Boolean(item.entrega)
      ).length,
    statusAtualizados:
      atualizacoes.filter(item =>
        Boolean(item.status)
      ).length,
    verificados:
      pedidosResumo.length,
  };

  Logger.log(
    JSON.stringify(resultado)
  );

  return resultado;
}

function reconciliarEntregasComTiny_() {
  const sheet = obterAbaVendas_();

  garantirCabecalhos_(sheet);

  const lastRow =
    ultimaLinhaDePedidos_(sheet);

  if (lastRow < 2) {
    return {
      status: 'ok',
      linhasVerificadas: 0,
      entregues: 0,
      faltaEntregar: 0,
      cancelados: 0,
      naoEncontrados: 0,
    };
  }

  const pedidosResumo =
    listarTodosPedidosTiny_();

  const pedidosPorNumero = {};

  pedidosResumo.forEach(resumo => {
    const numero =
      String(resumo.numero || '')
        .trim();

    if (numero) {
      pedidosPorNumero[numero] =
        resumo;
    }
  });

  const quantidade =
    lastRow - 1;

  const numeros =
    sheet
      .getRange(
        2,
        COL_NUMERO_PEDIDO,
        quantidade,
        1
      )
      .getDisplayValues();

  const entregasAtuais =
    sheet
      .getRange(
        2,
        COL_ENTREGAS,
        quantidade,
        1
      )
      .getDisplayValues();

  const statusAtuais =
    sheet
      .getRange(
        2,
        COL_STATUS,
        quantidade,
        1
      )
      .getDisplayValues();

  const novasEntregas =
    entregasAtuais.map(row => [
      String(row[0] || '').trim(),
    ]);

  const novosStatus =
    statusAtuais.map(row => [
      String(row[0] || '').trim(),
    ]);

  let entregues = 0;
  let faltaEntregar = 0;
  let cancelados = 0;
  let naoEncontrados = 0;
  let linhasAlteradas = 0;

  numeros.forEach((row, index) => {
    const numero =
      String(row[0] || '')
        .trim();

    const pedido =
      pedidosPorNumero[numero];

    if (!pedido) {
      naoEncontrados += 1;
      return;
    }

    const entregaNova =
      obterStatusEntrega_(pedido);

    const statusNovo =
      isCancelado_(pedido.situacao)
        ? 'CANCELADO'
        : 'EFETIVO';

    if (entregaNova === 'Entregue') {
      entregues += 1;
    } else if (entregaNova === 'Cancelado') {
      cancelados += 1;
    } else {
      faltaEntregar += 1;
    }

    const entregaAtual =
      String(novasEntregas[index][0] || '')
        .trim();

    const statusAtual =
      String(novosStatus[index][0] || '')
        .trim();

    if (
      entregaAtual !== entregaNova ||
      statusAtual !== statusNovo
    ) {
      linhasAlteradas += 1;
    }

    novasEntregas[index][0] =
      entregaNova;

    novosStatus[index][0] =
      statusNovo;
  });

  sheet
    .getRange(
      2,
      COL_ENTREGAS,
      quantidade,
      1
    )
    .setValues(novasEntregas);

  sheet
    .getRange(
      2,
      COL_STATUS,
      quantidade,
      1
    )
    .setValues(novosStatus);

  SpreadsheetApp.flush();

  const resultado = {
    status: 'ok',
    linhasVerificadas:
      quantidade,
    pedidosTiny:
      pedidosResumo.length,
    linhasAlteradas,
    entregues,
    faltaEntregar,
    cancelados,
    naoEncontrados,
  };

  Logger.log(
    JSON.stringify(resultado)
  );

  return resultado;
}

function reestruturarPagamentosEEntregasTiny_() {
  const sheet = obterAbaVendas_();

  garantirCabecalhos_(sheet);

  const lastRow =
    ultimaLinhaDePedidos_(sheet);

  if (lastRow < 2) {
    return {
      status: 'ok',
      linhasVerificadas: 0,
      linhasAlteradas: 0,
    };
  }

  const quantidade =
    lastRow - 1;

  const numeros =
    sheet
      .getRange(
        2,
        COL_NUMERO_PEDIDO,
        quantidade,
        1
      )
      .getDisplayValues();

  const datasEValores =
    sheet
      .getRange(
        2,
        COL_DATA,
        quantidade,
        2
      )
      .getValues();

  const valoresAtuais =
    sheet
      .getRange(
        2,
        COL_METODO_PAGAMENTO,
        quantidade,
        COL_EMPRESA -
          COL_METODO_PAGAMENTO +
          1
      )
      .getDisplayValues();

  const pedidosResumo =
    listarTodosPedidosTiny_();

  const pedidosPorNumero = {};
  const pedidosPorChave = {};
  const chavesDuplicadas = {};

  pedidosResumo.forEach(resumo => {
    const numero =
      String(resumo.numero || '')
        .trim();

    if (numero) {
      pedidosPorNumero[numero] =
        resumo;
    }

    const chave =
      montarChaveDataValor_(
        resumo.data_pedido,
        resumo.valor
      );

    if (!chave) {
      return;
    }

    if (pedidosPorChave[chave]) {
      chavesDuplicadas[chave] =
        true;
    } else {
      pedidosPorChave[chave] =
        resumo;
    }
  });

  Object
    .keys(chavesDuplicadas)
    .forEach(chave => {
      delete pedidosPorChave[chave];
    });

  const novosValores = [];
  const novosNumeros = [];
  const pedidosUsados = {};

  let linhasAlteradas = 0;
  let encontrados = 0;
  let naoEncontrados = 0;
  let entregues = 0;
  let faltaEntregar = 0;
  let cancelados = 0;
  let encontradosPorChave = 0;
  let numerosCorrigidos = 0;
  let pedidosInseridos = 0;

  numeros.forEach((row, index) => {
    const numero =
      String(row[0] || '')
        .trim();

    const atual =
      valoresAtuais[index] || [];

    const atualMetodo =
      String(atual[0] || '').trim();

    const atualBanco =
      String(atual[1] || '').trim();

    const atualParcelamento =
      String(atual[2] || '').trim();

    const atualEntrega =
      String(atual[3] || '').trim();

    const atualStatus =
      String(atual[4] || '').trim();

    const atualEmpresa =
      String(atual[5] || '').trim();

    let pagamento =
      normalizarCamposPagamentoDaLinha_(
        atualMetodo,
        atualBanco,
        atualParcelamento
      );

    let entrega = atualEntrega;
    let statusPedido = atualStatus;
    let empresa = atualEmpresa;
    let numeroFinal = numero;

    let resumo =
      pedidosPorNumero[numero];

    if (
      resumo &&
      pedidosUsados[numero]
    ) {
      resumo = null;
    }

    if (
      !resumo &&
      datasEValores[index]
    ) {
      const chave =
        montarChaveDataValor_(
          datasEValores[index][0],
          datasEValores[index][1]
        );

      const resumoPorChave =
        pedidosPorChave[chave];

      if (
        resumoPorChave &&
        !pedidosUsados[
          resumoPorChave.numero
        ]
      ) {
        resumo = resumoPorChave;
        encontradosPorChave += 1;
      }
    }

    if (resumo) {
      encontrados += 1;
      pedidosUsados[
        String(resumo.numero || '')
          .trim()
      ] = true;

      numeroFinal =
        String(resumo.numero || '')
          .trim();

      if (
        numeroFinal &&
        numeroFinal !== numero
      ) {
        numerosCorrigidos += 1;
      }

      entrega =
        obterStatusEntrega_(resumo);

      statusPedido =
        isCancelado_(resumo.situacao)
          ? 'CANCELADO'
          : 'EFETIVO';

      empresa =
        inferirEmpresa_(resumo);
    } else {
      naoEncontrados += 1;
      entrega = '';
      statusPedido = '';
    }

    if (entrega === 'Entregue') {
      entregues += 1;
    } else if (entrega === 'Cancelado') {
      cancelados += 1;
    } else if (entrega) {
      faltaEntregar += 1;
    }

    const novo = [
      pagamento.metodo,
      pagamento.banco,
      pagamento.parcelamento,
      entrega,
      statusPedido,
      empresa,
    ];

    if (
      novo[0] !== atualMetodo ||
      novo[1] !== atualBanco ||
      novo[2] !== atualParcelamento ||
      novo[3] !== atualEntrega ||
      novo[4] !== atualStatus ||
      novo[5] !== atualEmpresa
    ) {
      linhasAlteradas += 1;
    }

    novosValores.push(novo);
    novosNumeros.push([
      numeroFinal,
    ]);
  });

  sheet
    .getRange(
      2,
      COL_NUMERO_PEDIDO,
      quantidade,
      1
    )
    .setValues(novosNumeros);

  sheet
    .getRange(
      2,
      COL_METODO_PAGAMENTO,
      quantidade,
      COL_EMPRESA -
        COL_METODO_PAGAMENTO +
        1
    )
    .setValues(novosValores);

  const pedidosAusentes =
    pedidosResumo
      .filter(resumo => {
        const numero =
          String(resumo.numero || '')
            .trim();

        return (
          numero &&
          !pedidosUsados[numero]
        );
      })
      .sort((a, b) => {
        const dataA =
          parseTinyDateOrNull_(
            a.data_pedido
          );

        const dataB =
          parseTinyDateOrNull_(
            b.data_pedido
          );

        return (
          (dataA ? dataA.getTime() : 0) -
          (dataB ? dataB.getTime() : 0)
        );
      });

  if (pedidosAusentes.length > 0) {
    const linhasAusentes =
      pedidosAusentes.map(resumo =>
        montarLinhaPlanilhaResumo_(
          resumo
        )
      );

    const startRow =
      encontrarProximaLinhaVendas_(sheet);

    sheet
      .getRange(
        startRow,
        1,
        linhasAusentes.length,
        TOTAL_COLUNAS_VENDAS
      )
      .setValues(linhasAusentes);

    pedidosInseridos =
      linhasAusentes.length;
  }

  SpreadsheetApp.flush();

  const resultado = {
    status: 'ok',
    linhasVerificadas:
      quantidade,
    pedidosTiny:
      pedidosResumo.length,
    encontrados,
    encontradosPorChave,
    numerosCorrigidos,
    naoEncontrados,
    pedidosInseridos,
    linhasAlteradas,
    entregues,
    faltaEntregar,
    cancelados,
  };

  Logger.log(
    JSON.stringify(resultado)
  );

  return resultado;
}

function coletarAtualizacoesStatusPedido_(
  sheet,
  existing,
  pedidosResumo
) {
  const atualizacoes = [];

  pedidosResumo.forEach(resumo => {
    const numero = String(
      resumo.numero || ''
    ).trim();

    if (!numero) {
      return;
    }

    const rowIndex =
      existing[numero];

    if (!rowIndex) {
      return;
    }

    const entregaAtual =
      sheet
        .getRange(
          rowIndex,
          COL_ENTREGAS
        )
        .getDisplayValue()
        .trim()
        .toUpperCase();

    const statusAtual =
      sheet
        .getRange(
          rowIndex,
          COL_STATUS
        )
        .getDisplayValue()
        .trim()
        .toUpperCase();

    const entregaNova =
      obterStatusEntrega_(resumo);

    const statusNovo =
      isCancelado_(resumo.situacao)
        ? 'CANCELADO'
        : 'EFETIVO';

    const atualizacao = {
      rowIndex,
    };

    if (
      entregaAtual !==
      entregaNova.toUpperCase()
    ) {
      atualizacao.entrega =
        entregaNova;
    }

    if (
      statusAtual !== statusNovo
    ) {
      atualizacao.status =
        statusNovo;
    }

    if (
      atualizacao.entrega ||
      atualizacao.status
    ) {
      atualizacoes.push(
        atualizacao
      );
    }
  });

  return atualizacoes;
}

/**
 * ATUALIZAÇÃO HISTÓRICA DOS PAGAMENTOS
 */

function atualizarMetodosPagamentoHistoricosTiny() {
  const lock =
    LockService.getScriptLock();

  if (!lock.tryLock(5000)) {
    return {
      status: 'ocupado',
      mensagem:
        'Já existe uma atualização em execução.',
    };
  }

  try {
    const sheet = obterAbaVendas_();

    garantirCabecalhos_(sheet);

    const props =
      PropertiesService
        .getScriptProperties();

    const lastRow =
      ultimaLinhaDePedidos_(sheet);

    let startRow = Number(
      props.getProperty(
        HISTORICO_PAGAMENTOS_CURSOR
      ) || 0
    );

    if (
      !Number.isFinite(startRow) ||
      startRow < 2
    ) {
      startRow =
        encontrarPrimeiraLinhaAPartirDoPedido_(
          sheet,
          PRIMEIRO_PEDIDO_COM_PAGAMENTO
        );
    }

    if (
      lastRow < 2 ||
      startRow > lastRow
    ) {
      finalizarAtualizacaoPagamentosHistoricos_();

      return {
        status: 'concluido',
        mensagem:
          'Todos os pedidos existentes foram processados.',
        ultimaLinha: lastRow,
      };
    }

    const endRow = Math.min(
      startRow +
        HISTORICO_PAGAMENTOS_BATCH_SIZE -
        1,
      lastRow
    );

    const quantidade =
      endRow - startRow + 1;

    const numeros =
      sheet
        .getRange(
          startRow,
          COL_NUMERO_PEDIDO,
          quantidade,
          1
        )
        .getDisplayValues();

    const pagamentosAtuais =
      sheet
        .getRange(
          startRow,
          COL_METODO_PAGAMENTO,
          quantidade,
          3
        )
        .getDisplayValues();

    const novosPagamentos =
      pagamentosAtuais.map(row => [
        String(row[0] || '').trim(),
        String(row[1] || '').trim(),
        String(row[2] || '').trim(),
      ]);

    let atualizados = 0;
    let semDados = 0;
    let ignorados = 0;
    let naoEncontrados = 0;
    let erros = 0;

    numeros.forEach((row, index) => {
      const numeroTexto = String(
        row[0] || ''
      ).trim();

      const numeroPedido =
        Number(numeroTexto);

      if (!numeroTexto) {
        return;
      }

      if (
        !Number.isFinite(numeroPedido)
      ) {
        novosPagamentos[index][0] =
          'SEM DADOS';

        ignorados += 1;
        return;
      }

      if (
        numeroPedido <
        PRIMEIRO_PEDIDO_COM_PAGAMENTO
      ) {
        novosPagamentos[index][0] =
          'SEM DADOS';

        ignorados += 1;
        return;
      }

      try {
        const detalhe =
          obterPedidoTinyPorNumero_(
            numeroTexto
          );

        if (!detalhe) {
          novosPagamentos[index][0] =
            'SEM DADOS';

          naoEncontrados += 1;
          return;
        }

        const pagamento =
          obterCamposPagamento_(detalhe);

        novosPagamentos[index] = [
          pagamento.metodo,
          pagamento.banco,
          pagamento.parcelamento,
        ];

        if (
          pagamento.metodo === 'SEM DADOS'
        ) {
          semDados += 1;
        } else {
          atualizados += 1;
        }

        Utilities.sleep(400);
      } catch (error) {
        erros += 1;

        Logger.log(
          `Falha no pagamento do pedido ` +
          `${numeroTexto}: ` +
          `${obterMensagemErro_(error)}`
        );

        /*
         * Em caso de erro temporário,
         * preserva o conteúdo existente.
         */
      }
    });

    sheet
      .getRange(
        startRow,
        COL_METODO_PAGAMENTO,
        quantidade,
        3
      )
      .setValues(novosPagamentos);

    SpreadsheetApp.flush();

    const proximaLinha =
      endRow + 1;

    const concluido =
      proximaLinha > lastRow;

    if (concluido) {
      finalizarAtualizacaoPagamentosHistoricos_();
    } else {
      props.setProperty(
        HISTORICO_PAGAMENTOS_CURSOR,
        String(proximaLinha)
      );
    }

    const resultado = {
      status:
        concluido
          ? 'concluido'
          : 'em_andamento',
      primeiroPedidoConsultado:
        PRIMEIRO_PEDIDO_COM_PAGAMENTO,
      intervalo:
        `${startRow}:${endRow}`,
      linhasProcessadas:
        quantidade,
      pagamentosEncontrados:
        atualizados,
      semDados,
      ignoradosAntesDoPedido795:
        ignorados,
      pedidosNaoEncontrados:
        naoEncontrados,
      erros,
      proximaLinha:
        concluido
          ? null
          : proximaLinha,
      ultimaLinha:
        lastRow,
    };

    Logger.log(
      JSON.stringify(resultado)
    );

    return resultado;
  } finally {
    lock.releaseLock();
  }
}

function encontrarPrimeiraLinhaAPartirDoPedido_(
  sheet,
  numeroMinimo
) {
  const lastRow =
    ultimaLinhaDePedidos_(sheet);

  if (lastRow < 2) {
    return 2;
  }

  const numeros =
      sheet
        .getRange(
          2,
          COL_NUMERO_PEDIDO,
          lastRow - 1,
          1
        )
      .getDisplayValues();

  for (
    let index = 0;
    index < numeros.length;
    index += 1
  ) {
    const numero =
      Number(numeros[index][0]);

    if (
      Number.isFinite(numero) &&
      numero >= numeroMinimo
    ) {
      return index + 2;
    }
  }

  return lastRow + 1;
}

function finalizarAtualizacaoPagamentosHistoricos_() {
  PropertiesService
    .getScriptProperties()
    .deleteProperty(
      HISTORICO_PAGAMENTOS_CURSOR
    );

  removerGatilhosDaFuncao_(
    'atualizarMetodosPagamentoHistoricosTiny'
  );
}

/**
 * BUSCA DO PEDIDO PELO NÚMERO
 */

function obterPedidoTinyPorNumero_(
  numeroPedido
) {
  const numeroLimpo =
    String(numeroPedido || '').trim();

  if (!numeroLimpo) {
    return null;
  }

  let retornoPesquisa;

  try {
    retornoPesquisa =
      tinyRequest_(
        'pedidos.pesquisa.php',
        {
          numero: numeroLimpo,
        }
      );
  } catch (error) {
    if (tinyErroSemRegistros_(error)) {
      Logger.log(
        `Pedido ${numeroLimpo} não encontrado no Tiny.`
      );

      return null;
    }

    throw error;
  }

  const pedidos =
    normalizarListaTiny_(
      retornoPesquisa.pedidos
    );

  if (pedidos.length === 0) {
    Logger.log(
      `Pedido ${numeroLimpo} não encontrado no Tiny.`
    );

    return null;
  }

  const resumos =
    pedidos.map(item =>
      item && item.pedido
        ? item.pedido
        : item
    );

  const resumoExato =
    resumos.find(item =>
      String(
        item && item.numero
          ? item.numero
          : ''
      ).trim() === numeroLimpo
    );

  const resumo =
    resumoExato || resumos[0];

  if (
    !resumo ||
    !resumo.id
  ) {
    Logger.log(
      `Pedido ${numeroLimpo} encontrado sem ID interno.`
    );

    return null;
  }

  try {
    return obterPedidoTiny_(
      resumo.id
    );
  } catch (error) {
    if (tinyErroSemRegistros_(error)) {
      Logger.log(
        `Pedido ${numeroLimpo} sem detalhe no Tiny.`
      );

      return null;
    }

    throw error;
  }
}

function tinyErroSemRegistros_(
  error
) {
  const mensagem =
    obterMensagemErro_(error)
      .toLowerCase();

  return (
    mensagem.includes(
      'a consulta não retornou registros'
    ) ||
    mensagem.includes(
      'a consulta nao retornou registros'
    )
  );
}

/**
 * LISTAGEM E DETALHES DO TINY
 */

function listarTodosPedidosTiny_() {
  const pedidos = [];
  let pagina = 1;

  while (true) {
    let retorno;

    try {
      retorno =
        tinyRequest_(
          'pedidos.pesquisa.php',
          { pagina }
        );
    } catch (error) {
      const message =
        obterMensagemErro_(error)
          .toLowerCase();

      if (
        message.includes('página') ||
        message.includes('pagina')
      ) {
        break;
      }

      throw error;
    }

    const paginaPedidos =
      normalizarListaTiny_(
        retorno.pedidos
      );

    paginaPedidos.forEach(item => {
      pedidos.push(
        item && item.pedido
          ? item.pedido
          : item
      );
    });

    if (
      paginaPedidos.length === 0 ||
      paginaPedidos.length < 100
    ) {
      break;
    }

    pagina += 1;

    if (pagina > 30) {
      throw new Error(
        'Limite de segurança de páginas do Tiny atingido.'
      );
    }
  }

  return pedidos;
}

function obterPedidoTiny_(pedidoId) {
  if (!pedidoId) {
    throw new Error(
      'ID interno do pedido não informado.'
    );
  }

  const retorno =
    tinyRequest_(
      'pedido.obter.php',
      {
        id: pedidoId,
      }
    );

  return retorno.pedido || retorno;
}

/**
 * REQUISIÇÕES À API
 */

function tinyRequest_(endpoint, params) {
  const token =
    PropertiesService
      .getScriptProperties()
      .getProperty('TINY_TOKEN');

  if (!token) {
    throw new Error(
      'TINY_TOKEN não configurado. ' +
      'Abra as Propriedades do script.'
    );
  }

  const payload =
    Object.assign(
      {
        token,
        formato: 'json',
      },
      params || {}
    );

  const formBody =
    Object.keys(payload)
      .filter(key =>
        payload[key] !== undefined &&
        payload[key] !== null &&
        payload[key] !== ''
      )
      .map(key =>
        `${encodeURIComponent(key)}=` +
        `${encodeURIComponent(
          String(payload[key])
        )}`
      )
      .join('&');

  const response =
    UrlFetchApp.fetch(
      `${TINY_BASE_URL}/${endpoint}`,
      {
        method: 'post',
        contentType:
          'application/x-www-form-urlencoded',
        payload: formBody,
        muteHttpExceptions: true,
      }
    );

  const code =
    response.getResponseCode();

  const text =
    response.getContentText();

  if (
    code < 200 ||
    code >= 300
  ) {
    throw new Error(
      `Tiny HTTP ${code}: ${text}`
    );
  }

  let data;

  try {
    data = JSON.parse(text);
  } catch (error) {
    throw new Error(
      `Resposta inválida do Tiny: ${text}`
    );
  }

  const retorno =
    data.retorno || data;

  if (
    String(retorno.status || '')
      .toLowerCase() === 'erro'
  ) {
    throw new Error(
      `Tiny erro: ${JSON.stringify(
        retorno.erros || retorno
      )}`
    );
  }

  return retorno;
}

/**
 * MONTAGEM DA LINHA
 */

function montarLinhaPlanilha_(pedido) {
  const data =
    parseTinyDate_(
      pedido.data_pedido
    );

  const cliente =
    pedido.cliente || {};

  const numeroEcommerce =
    String(
      pedido.numero_ecommerce || ''
    ).trim();

  const venda =
    numeroEcommerce
      ? 'NuvemShop'
      : 'Loja Física';

  const valor =
    Number(
      pedido.total_pedido ||
      pedido.valor ||
      0
    );

  const numeroPedido =
    Number(pedido.numero || 0);

  const pagamento =
    numeroPedido <
    PRIMEIRO_PEDIDO_COM_PAGAMENTO
      ? {
          metodo: 'SEM DADOS',
          banco: '',
          parcelamento: '',
        }
      : obterCamposPagamento_(pedido);

  const status =
    isCancelado_(pedido.situacao)
      ? 'CANCELADO'
      : 'EFETIVO';

  return [
    formatarMesAno_(data),
    numeroPedido,
    data,
    valor,
    pagamento.metodo,
    pagamento.banco,
    pagamento.parcelamento,
    obterStatusEntrega_(pedido),
    status,
    inferirEmpresa_(pedido),
    venda,
    String(
      cliente.uf || ''
    ).trim(),
    String(
      cliente.cidade || ''
    ).trim(),
  ];
}

function montarLinhaPlanilhaResumo_(
  pedido
) {
  const data =
    parseTinyDate_(
      pedido.data_pedido
    );

  const numeroEcommerce =
    String(
      pedido.numero_ecommerce || ''
    ).trim();

  const venda =
    numeroEcommerce
      ? 'NuvemShop'
      : 'Loja Física';

  const valor =
    Number(
      pedido.valor ||
      pedido.total_pedido ||
      0
    );

  const status =
    isCancelado_(pedido.situacao)
      ? 'CANCELADO'
      : 'EFETIVO';

  return [
    formatarMesAno_(data),
    Number(pedido.numero || 0),
    data,
    valor,
    '',
    '',
    '',
    obterStatusEntrega_(pedido),
    status,
    inferirEmpresa_(pedido),
    venda,
    '',
    '',
  ];
}

/**
 * IDENTIFICAÇÃO DO PAGAMENTO
 */

function obterMetodoPagamento_(pedido) {
  return obterCamposPagamento_(pedido).metodo;
}

function obterCamposPagamento_(pedido) {
  return normalizarCamposPagamento_(
    obterTextoPagamento_(pedido)
  );
}

function obterTextoPagamento_(pedido) {
  const pagamentos = [];

  coletarPossivelPagamento_(
    pagamentos,
    pedido.forma_pagamento
  );

  coletarPossivelPagamento_(
    pagamentos,
    pedido.meio_pagamento
  );

  coletarPossivelPagamento_(
    pagamentos,
    pedido.condicao_pagamento
  );

  coletarPossivelPagamento_(
    pagamentos,
    pedido.formaPagamento
  );

  coletarPossivelPagamento_(
    pagamentos,
    pedido.meioPagamento
  );

  coletarPossivelPagamento_(
    pagamentos,
    pedido.condicaoPagamento
  );

  const parcelas =
    normalizarListaTiny_(
      pedido.parcelas
    );

  parcelas.forEach(item => {
    const parcela =
      item && item.parcela
        ? item.parcela
        : item;

    coletarDadosPagamentoObjeto_(
      pagamentos,
      parcela
    );
  });

  const recebimentos =
    normalizarListaTiny_(
      pedido.recebimentos
    );

  recebimentos.forEach(item => {
    const recebimento =
      item && item.recebimento
        ? item.recebimento
        : item;

    coletarDadosPagamentoObjeto_(
      pagamentos,
      recebimento
    );
  });

  const pagamentosPedido =
    normalizarListaTiny_(
      pedido.pagamentos
    );

  pagamentosPedido.forEach(item => {
    const pagamento =
      item && item.pagamento
        ? item.pagamento
        : item;

    coletarDadosPagamentoObjeto_(
      pagamentos,
      pagamento
    );
  });

  const normalizados =
    pagamentos
      .map(normalizarTextoPagamento_)
      .filter(Boolean)
      .filter(valor =>
        valor !== 'SEM DADOS'
      );

  const unicos =
    [...new Set(normalizados)];

  return unicos.length > 0
    ? unicos.join(' + ')
    : 'SEM DADOS';
}

function coletarDadosPagamentoObjeto_(
  destino,
  objeto
) {
  if (!objeto) {
    return;
  }

  if (
    typeof objeto !== 'object'
  ) {
    coletarPossivelPagamento_(
      destino,
      objeto
    );

    return;
  }

  const campos = [
    'forma_pagamento',
    'meio_pagamento',
    'condicao_pagamento',
    'formaPagamento',
    'meioPagamento',
    'condicaoPagamento',
    'descricao',
    'nome',
    'nome_forma_pagamento',
    'descricao_forma_pagamento',
    'nome_meio_pagamento',
    'descricao_meio_pagamento',
  ];

  campos.forEach(campo => {
    coletarPossivelPagamento_(
      destino,
      objeto[campo]
    );
  });
}

function coletarPossivelPagamento_(
  destino,
  valor
) {
  if (
    valor === undefined ||
    valor === null ||
    valor === ''
  ) {
    return;
  }

  if (Array.isArray(valor)) {
    valor.forEach(item => {
      coletarPossivelPagamento_(
        destino,
        item
      );
    });

    return;
  }

  if (
    typeof valor === 'object'
  ) {
    coletarDadosPagamentoObjeto_(
      destino,
      valor
    );

    return;
  }

  const texto =
    normalizarTextoPagamento_(
      valor
    );

  if (texto) {
    destino.push(texto);
  }
}

function normalizarTextoPagamento_(valor) {
  return String(valor || '')
    .replace(/\s+/g, ' ')
    .trim();
}

function normalizarCamposPagamento_(
  valor
) {
  const texto =
    normalizarTextoPagamento_(valor);

  if (!texto) {
    return {
      metodo: '',
      banco: '',
      parcelamento: '',
    };
  }

  const textoLower =
    texto.toLowerCase();

  if (
    textoLower === 'sem dados'
  ) {
    return {
      metodo: '',
      banco: '',
      parcelamento: '',
    };
  }

  const metodos = [];

  if (
    textoLower.includes('pix')
  ) {
    metodos.push('PIX');
  }

  if (
    textoLower.includes('credito') ||
    textoLower.includes('crédito')
  ) {
    metodos.push('CRÉDITO');
  }

  if (
    textoLower.includes('debito') ||
    textoLower.includes('débito')
  ) {
    metodos.push('DÉBITO');
  }

  if (
    textoLower.includes('dinheiro')
  ) {
    metodos.push('DINHEIRO');
  }

  if (
    textoLower.includes(
      'link de pagamento'
    )
  ) {
    metodos.push(
      'LINK DE PAGAMENTO'
    );
  }

  const bancos = [];

  if (
    textoLower.includes('itau') ||
    textoLower.includes('itaú')
  ) {
    bancos.push('ITAU');
  }

  if (
    textoLower.includes('btg')
  ) {
    bancos.push('BTG');
  }

  if (
    textoLower.includes('stone')
  ) {
    bancos.push('STONE');
  }

  const parcelas =
    obterQuantidadeParcelasCredito_(
      textoLower
    );

  return {
    metodo:
      [...new Set(metodos)]
        .join(' + '),
    banco:
      [...new Set(bancos)]
        .join(' + '),
    parcelamento:
      parcelas > 0
        ? `${parcelas}X`
        : '',
  };
}

function normalizarCamposPagamentoDaLinha_(
  metodo,
  banco,
  parcelamento
) {
  const metodoTexto =
    normalizarTextoPagamento_(metodo);

  const bancoTexto =
    normalizarTextoPagamento_(banco);

  const parcelamentoTexto =
    normalizarTextoPagamento_(
      parcelamento
    ).toUpperCase();

  const textoCompleto =
    [
      metodoTexto,
      bancoTexto,
      parcelamentoTexto,
    ]
      .filter(Boolean)
      .join(' ');

  const campos =
    normalizarCamposPagamento_(
      textoCompleto
    );

  return {
    metodo:
      campos.metodo,
    banco:
      campos.banco ||
      bancoTexto.toUpperCase(),
    parcelamento:
      campos.parcelamento ||
      parcelamentoTexto,
  };
}

function normalizarDescricaoMetodoPagamento_(
  valor
) {
  const texto =
    normalizarTextoPagamento_(valor);

  if (!texto) {
    return '';
  }

  const textoLower =
    texto.toLowerCase();

  if (
    textoLower === 'sem dados'
  ) {
    return 'SEM DADOS';
  }

  const multiplos =
    montarMetodoPagamentoMultiplo_(
      textoLower
    );

  if (multiplos) {
    return multiplos;
  }

  if (
    textoLower.includes(
      'link de pagamento'
    )
  ) {
    const linkNormalizado =
      textoLower.match(
        /link de pagamento\s+(\d{1,2})x/
      );

    if (linkNormalizado) {
      return montarDescricaoComBanco_(
        `LINK DE PAGAMENTO ${linkNormalizado[1]}X`,
        textoLower
      );
    }

    const parcelas =
      obterQuantidadeParcelasCredito_(
        textoLower
      );

    return parcelas > 0
      ? montarDescricaoComBanco_(
          `LINK DE PAGAMENTO ${parcelas}X`,
          textoLower
        )
      : montarDescricaoComBanco_(
          'LINK DE PAGAMENTO',
          textoLower
        );
  }

  if (textoLower.includes('pix')) {
    if (
      /pix\s*\+\s*(itau|itaú)/.test(
        textoLower
      )
    ) {
      return 'PIX ITAU';
    }

    if (
      /pix\s*\+\s*stone/.test(
        textoLower
      )
    ) {
      return 'PIX STONE';
    }

    if (
      /pix\s*\+\s*btg/.test(
        textoLower
      )
    ) {
      return 'PIX BTG';
    }

    if (
      textoLower.includes('stone')
    ) {
      return 'PIX STONE';
    }

    if (
      textoLower.includes('itau') ||
      textoLower.includes('itaú')
    ) {
      return 'PIX ITAU';
    }

    if (
      textoLower.includes('btg')
    ) {
      return 'PIX BTG';
    }

    return 'PIX';
  }

  if (
    textoLower.includes('credito') ||
    textoLower.includes('crédito')
  ) {
    const creditoNormalizado =
      textoLower.match(
        /cr[eé]dito\s+(\d{1,2})x/
      );

    if (creditoNormalizado) {
      return montarDescricaoComBanco_(
        `CRÉDITO ${creditoNormalizado[1]}X`,
        textoLower
      );
    }

    const parcelas =
      obterQuantidadeParcelasCredito_(
        textoLower
      );

    return parcelas > 0
      ? montarDescricaoComBanco_(
          `CRÉDITO ${parcelas}X`,
          textoLower
        )
      : montarDescricaoComBanco_(
          'CRÉDITO',
          textoLower
        );
  }

  if (
    textoLower.includes('debito') ||
    textoLower.includes('débito')
  ) {
    return obterDescricaoDebito_(
      textoLower
    );
  }

  if (
    textoLower.includes('stone')
  ) {
    return 'STONE';
  }

  if (
    textoLower.includes('itau') ||
    textoLower.includes('itaú')
  ) {
    return 'ITAU';
  }

  if (
    textoLower.includes('btg')
  ) {
    return 'BTG';
  }

  if (
    textoLower.includes('cielo')
  ) {
    return 'CIELO';
  }

  if (
    textoLower.includes('dinheiro')
  ) {
    return 'DINHEIRO';
  }

  if (
    textoLower.includes('multiplas') ||
    textoLower.includes('múltiplas')
  ) {
    return 'MÚLTIPLAS';
  }

  return texto.toUpperCase();
}

function montarMetodoPagamentoMultiplo_(
  textoLower
) {
  const partes = [];
  const temPix =
    textoLower.includes('pix');
  const temCredito =
    textoLower.includes('credito') ||
    textoLower.includes('crédito');
  const temLink =
    textoLower.includes(
      'link de pagamento'
    );
  const temDebito =
    textoLower.includes('debito') ||
    textoLower.includes('débito');
  const temDinheiro =
    textoLower.includes('dinheiro');

  const quantidadeTipos =
    [
      temPix,
      temCredito,
      temLink,
      temDebito,
      temDinheiro,
    ].filter(Boolean).length;

  if (quantidadeTipos < 2) {
    return '';
  }

  if (temPix) {
    partes.push(
      obterDescricaoPix_(textoLower)
    );
  }

  if (temCredito) {
    partes.push(
      obterDescricaoCredito_(textoLower)
    );
  }

  if (temLink) {
    partes.push(
      obterDescricaoLinkPagamento_(
        textoLower
      )
    );
  }

  if (temDebito) {
    partes.push(
      obterDescricaoDebito_(
        textoLower
      )
    );
  }

  if (temDinheiro) {
    partes.push('DINHEIRO');
  }

  return [...new Set(partes)]
    .filter(Boolean)
    .join(' + ');
}

function obterDescricaoPix_(
  textoLower
) {
  if (
    /pix\s*\+\s*(itau|itaú)/.test(
      textoLower
    )
  ) {
    return 'PIX ITAU';
  }

  if (
    /pix\s*\+\s*stone/.test(
      textoLower
    )
  ) {
    return 'PIX STONE';
  }

  if (
    /pix\s*\+\s*btg/.test(
      textoLower
    )
  ) {
    return 'PIX BTG';
  }

  if (
    textoLower.includes('itau') ||
    textoLower.includes('itaú')
  ) {
    return 'PIX ITAU';
  }

  if (
    textoLower.includes('stone')
  ) {
    return 'PIX STONE';
  }

  if (
    textoLower.includes('btg')
  ) {
    return 'PIX BTG';
  }

  return 'PIX';
}

function obterDescricaoCredito_(
  textoLower
) {
  const creditoNormalizado =
    textoLower.match(
      /cr[eé]dito\s+(\d{1,2})x/
    );

  if (creditoNormalizado) {
    return `CRÉDITO ${creditoNormalizado[1]}X`;
  }

  const parcelas =
    obterQuantidadeParcelasCredito_(
      textoLower
    );

  return parcelas > 0
    ? montarDescricaoComBanco_(
        `CRÉDITO ${parcelas}X`,
        textoLower
      )
    : montarDescricaoComBanco_(
        'CRÉDITO',
        textoLower
      );
}

function obterDescricaoLinkPagamento_(
  textoLower
) {
  const linkNormalizado =
    textoLower.match(
      /link de pagamento\s+(\d{1,2})x/
    );

  if (linkNormalizado) {
    return montarDescricaoComBanco_(
      `LINK DE PAGAMENTO ${linkNormalizado[1]}X`,
      textoLower
    );
  }

  const parcelas =
    obterQuantidadeParcelasCredito_(
      textoLower
    );

  return parcelas > 0
    ? montarDescricaoComBanco_(
        `LINK DE PAGAMENTO ${parcelas}X`,
        textoLower
      )
    : montarDescricaoComBanco_(
        'LINK DE PAGAMENTO',
        textoLower
      );
}

function obterDescricaoDebito_(
  textoLower
) {
  return montarDescricaoComBanco_(
    'DÉBITO',
    textoLower
  );
}

function montarDescricaoComBanco_(
  descricao,
  textoLower
) {
  const banco =
    obterBancoPagamento_(
      textoLower
    );

  return banco
    ? `${descricao} ${banco}`
    : descricao;
}

function obterBancoPagamento_(
  textoLower
) {
  if (
    textoLower.includes('stone')
  ) {
    return 'STONE';
  }

  if (
    textoLower.includes('cielo')
  ) {
    return 'CIELO';
  }

  if (
    textoLower.includes('btg')
  ) {
    return 'BTG';
  }

  if (
    textoLower.includes('itau') ||
    textoLower.includes('itaú')
  ) {
    return 'ITAU';
  }

  return '';
}

function obterQuantidadeParcelasCredito_(
  textoLower
) {
  const parcelamentoDireto =
    textoLower.match(
      /\b(\d{1,2})x\b/
    );

  if (parcelamentoDireto) {
    return Number(
      parcelamentoDireto[1]
    );
  }

  const numeros =
    textoLower.match(/\b\d{1,3}\b/g) || [];

  const parcelas =
    numeros
      .map(numero => Number(numero))
      .filter(numero =>
        Number.isFinite(numero) &&
        numero > 0 &&
        numero <= 360
      );

  if (parcelas.length === 0) {
    return 0;
  }

  return parcelas.length;
}

function montarChaveDataValor_(
  data,
  valor
) {
  const dataChave =
    normalizarDataChave_(data);

  const valorChave =
    normalizarValorChave_(valor);

  if (
    !dataChave ||
    valorChave === ''
  ) {
    return '';
  }

  return `${dataChave}|${valorChave}`;
}

function normalizarDataChave_(value) {
  const data =
    parseTinyDateOrNull_(value);

  if (!data) {
    return '';
  }

  return Utilities.formatDate(
    data,
    Session.getScriptTimeZone(),
    'yyyy-MM-dd'
  );
}

function normalizarValorChave_(value) {
  if (
    value === undefined ||
    value === null ||
    value === ''
  ) {
    return '';
  }

  let numero;

  if (typeof value === 'number') {
    numero = value;
  } else {
    const texto =
      String(value)
        .replace(/[R$\s.]/g, '')
        .replace(',', '.')
        .trim();

    numero = Number(texto);
  }

  if (!Number.isFinite(numero)) {
    return '';
  }

  return String(
    Math.round(numero * 100)
  );
}

function normalizarMetodosPagamentoPlanilha_() {
  const sheet = obterAbaVendas_();

  const lastRow =
    ultimaLinhaDePedidos_(sheet);

  if (lastRow < 2) {
    return {
      status: 'ok',
      linhasNormalizadas: 0,
    };
  }

  const range =
    sheet.getRange(
      2,
      COL_METODO_PAGAMENTO,
      lastRow - 1,
      3
    );

  const valores =
    range.getDisplayValues();

  let alterados = 0;

  const normalizados =
    valores.map(row => {
      const original =
        String(row[0] || '').trim();

      const campos =
        normalizarCamposPagamento_(
          original
        );

      if (
        campos.metodo !== original ||
        campos.banco !==
          String(row[1] || '').trim() ||
        campos.parcelamento !==
          String(row[2] || '').trim()
      ) {
        alterados += 1;
      }

      return [
        campos.metodo,
        campos.banco,
        campos.parcelamento,
      ];
    });

  range.setValues(normalizados);

  SpreadsheetApp.flush();

  return {
    status: 'ok',
    linhasVerificadas:
      valores.length,
    linhasNormalizadas:
      alterados,
  };
}

function juntarAnoMesPlanilha_() {
  const sheet = obterAbaVendas_();

  const headers =
    sheet
      .getRange(1, 1, 1, 2)
      .getDisplayValues()[0]
      .map(value =>
        String(value || '').trim()
      );

  const primeiraColuna =
    headers[0];

  const segundaColuna =
    headers[1];

  if (
    primeiraColuna === 'Mês' &&
    segundaColuna ===
      'Numero do Pedido'
  ) {
    const normalizacao =
      normalizarColunaMesAno_(
        sheet
      );

    garantirCabecalhos_(sheet);

    return {
      status: 'ok',
      mensagem:
        'Ano e Mês já estavam juntos.',
      migrado: false,
      normalizacao,
    };
  }

  if (
    primeiraColuna !== 'Ano' ||
    segundaColuna !== 'Mês'
  ) {
    throw new Error(
      'Estrutura inesperada. Esperado A=Ano e B=Mês.'
    );
  }

  const lastRow =
    Math.max(
      sheet.getLastRow(),
      1
    );

  if (lastRow > 1) {
    sheet
      .getRange(
        2,
        1,
        lastRow - 1,
        1
      )
      .setNumberFormat('@');

    const valores =
      sheet
        .getRange(
          2,
          1,
          lastRow - 1,
          2
        )
        .getDisplayValues();

    const mesAno =
      valores.map(row => [
        formatarMesAnoDeTexto_(
          row[0],
          row[1]
        ),
      ]);

    sheet
      .getRange(
        2,
        1,
        mesAno.length,
        1
      )
      .setValues(mesAno);
  }

  sheet
    .getRange(1, 1)
    .setValue('Mês');

  sheet.deleteColumn(2);

  normalizarColunaMesAno_(sheet);

  garantirCabecalhos_(sheet);

  SpreadsheetApp.flush();

  return {
    status: 'ok',
    mensagem:
      'Colunas Ano e Mês unificadas.',
    migrado: true,
    linhasAtualizadas:
      Math.max(lastRow - 1, 0),
  };
}

function ordenarVendasPorData_(sheet) {
  const lastRow =
    sheet.getLastRow();

  if (lastRow < 3) {
    return {
      status: 'ok',
      linhasOrdenadas: 0,
    };
  }

  garantirCabecalhos_(sheet);
  recalcularMesAnoPelaData_(
    sheet,
    lastRow
  );

  const range =
    sheet.getRange(
      2,
      1,
      lastRow - 1,
      TOTAL_COLUNAS_VENDAS
    );

  range.sort([
    {
      column: COL_DATA,
      ascending: true,
    },
  ]);

  SpreadsheetApp.flush();

  return {
    status: 'ok',
    linhasOrdenadas:
      lastRow - 1,
  };
}

function recalcularMesAnoPelaData_(
  sheet,
  lastRow
) {
  if (lastRow < 2) {
    return {
      linhasVerificadas: 0,
      linhasAlteradas: 0,
    };
  }

  const datas =
    sheet
      .getRange(
        2,
        COL_DATA,
        lastRow - 1,
        1
      )
      .getValues();

  const rangeMes =
    sheet.getRange(
      2,
      COL_MES_ANO,
      lastRow - 1,
      1
    );

  const mesesAtuais =
    rangeMes.getDisplayValues();

  let alteradas = 0;

  const meses =
    datas.map((row, index) => {
      const data =
        row[0];

      const mesAno =
        formatarMesAno_(data);

      const atual =
        normalizarMesAnoTexto_(
          mesesAtuais[index][0]
        );

      if (mesAno && mesAno !== atual) {
        alteradas += 1;
      }

      return [
        mesAno || atual,
      ];
    });

  rangeMes
    .setNumberFormat('@')
    .setValues(meses);

  return {
    linhasVerificadas:
      datas.length,
    linhasAlteradas:
      alteradas,
  };
}

function normalizarColunaMesAno_(
  sheet
) {
  const lastRow =
    ultimaLinhaDePedidos_(sheet);

  if (lastRow < 2) {
    return {
      linhasVerificadas: 0,
      linhasAlteradas: 0,
    };
  }

  const range =
    sheet.getRange(
      2,
      COL_MES_ANO,
      lastRow - 1,
      1
    );

  range.setNumberFormat('@');

  const valores =
    range.getDisplayValues();

  let alteradas = 0;

  const normalizados =
    valores.map(row => {
      const atual =
        String(row[0] || '').trim();

      const novo =
        normalizarMesAnoTexto_(atual);

      if (novo !== atual) {
        alteradas += 1;
      }

      return [novo];
    });

  range.setValues(normalizados);

  return {
    linhasVerificadas:
      valores.length,
    linhasAlteradas:
      alteradas,
  };
}

function normalizarMesAnoTexto_(
  value
) {
  const texto =
    String(value || '').trim();

  if (!texto) {
    return '';
  }

  const match =
    texto.match(
      /^([A-Za-zÀ-ÿ.]+)\/(\d{2,4})$/
    );

  if (!match) {
    return texto;
  }

  const mes =
    match[1]
      .replace('.', '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

  const meses = {
    jan: 'Jan',
    janeiro: 'Jan',
    fev: 'Fev',
    fevereiro: 'Fev',
    mar: 'Mar',
    marco: 'Mar',
    abr: 'Abr',
    abril: 'Abr',
    mai: 'Mai',
    maio: 'Mai',
    jun: 'Jun',
    junho: 'Jun',
    jul: 'Jul',
    julho: 'Jul',
    ago: 'Ago',
    agosto: 'Ago',
    set: 'Set',
    setembro: 'Set',
    out: 'Out',
    outubro: 'Out',
    nov: 'Nov',
    novembro: 'Nov',
    dez: 'Dez',
    dezembro: 'Dez',
  };

  const ano =
    match[2].slice(-2);

  return `${meses[mes] || match[1]}/${ano}`;
}

/**
 * DADOS DA PLANILHA
 */

function obterAbaVendas_() {
  const spreadsheet =
    SpreadsheetApp.openById(
      SPREADSHEET_ID
    );

  const sheet =
    spreadsheet.getSheetByName(
      SHEET_NAME
    );

  if (!sheet) {
    throw new Error(
      `Aba não encontrada: ${SHEET_NAME}`
    );
  }

  return sheet;
}

function garantirCabecalhos_(sheet) {
  const cabecalhos = [
    'Mês',
    'Numero do Pedido',
    'Data',
    'Valor',
    'Método de Pagamento',
    'Banco',
    'Parcelamento',
    'Entregas',
    'Status',
    'Empresa',
    'Venda',
    'Estado',
    'Cidade',
  ];

  sheet
    .getRange(
      1,
      1,
      1,
      cabecalhos.length
    )
    .setValues([cabecalhos]);

  sheet.setFrozenRows(1);
}

function encontrarProximaLinhaVendas_(sheet) {
  const lastRow =
    Math.max(
      sheet.getLastRow(),
      2
    );

  const values =
    sheet
      .getRange(
        2,
        COL_NUMERO_PEDIDO,
        lastRow - 1,
        1
      )
      .getValues();

  for (
    let index =
      values.length - 1;
    index >= 0;
    index -= 1
  ) {
    if (
      String(
        values[index][0] || ''
      ).trim()
    ) {
      return index + 3;
    }
  }

  return 2;
}

function carregarPedidosExistentes_(sheet) {
  const lastRow =
    sheet.getLastRow();

  const existing = {};

  if (lastRow < 2) {
    return existing;
  }

  const values =
    sheet
      .getRange(
        2,
        COL_NUMERO_PEDIDO,
        lastRow - 1,
        1
      )
      .getValues();

  values.forEach(
    (row, index) => {
      const numero =
        String(
          row[0] || ''
        ).trim();

      if (numero) {
        existing[numero] =
          index + 2;
      }
    }
  );

  return existing;
}

function maiorNumeroPedidoExistente_(sheet) {
  const lastRow =
    sheet.getLastRow();

  if (lastRow < 2) {
    return 0;
  }

  const values =
    sheet
      .getRange(
        2,
        COL_NUMERO_PEDIDO,
        lastRow - 1,
        1
      )
      .getValues();

  return values.reduce(
    (max, row) => {
      const numero =
        Number(row[0] || 0);

      return Number.isFinite(numero)
        ? Math.max(max, numero)
        : max;
    },
    0
  );
}

function maiorDataPedidoExistente_(sheet) {
  const lastRow =
    sheet.getLastRow();

  if (lastRow < 2) {
    return null;
  }

  const values =
    sheet
      .getRange(
        2,
        COL_DATA,
        lastRow - 1,
        1
      )
      .getValues();

  return values.reduce(
    (max, row) => {
      const data =
        row[0] instanceof Date
          ? row[0]
          : parseTinyDateOrNull_(
              row[0]
            );

      if (
        !data ||
        Number.isNaN(
          data.getTime()
        )
      ) {
        return max;
      }

      if (
        !max ||
        data.getTime() >
        max.getTime()
      ) {
        return data;
      }

      return max;
    },
    null
  );
}

function ultimaLinhaDePedidos_(sheet) {
  const lastRow =
    Math.max(
      sheet.getLastRow(),
      2
    );

  const numeros =
    sheet
      .getRange(
        2,
        COL_NUMERO_PEDIDO,
        lastRow - 1,
        1
      )
      .getDisplayValues();

  for (
    let index =
      numeros.length - 1;
    index >= 0;
    index -= 1
  ) {
    if (
      String(
        numeros[index][0] || ''
      ).trim()
    ) {
      return index + 2;
    }
  }

  return 1;
}

/**
 * REGRAS DE IMPORTAÇÃO
 */

function deveImportarPedidoNovo_(
  numero,
  dataPedido,
  maiorNumeroExistente,
  maiorDataExistente
) {
  const numeroPedido =
    Number(numero || 0);

  if (
    Number.isFinite(numeroPedido) &&
    numeroPedido >
    maiorNumeroExistente
  ) {
    return true;
  }

  if (
    !maiorDataExistente ||
    !dataPedido ||
    Number.isNaN(
      dataPedido.getTime()
    )
  ) {
    return false;
  }

  const margemMs =
    7 *
    24 *
    60 *
    60 *
    1000;

  return (
    dataPedido.getTime() >=
    maiorDataExistente.getTime() -
    margemMs
  );
}

/**
 * DATAS
 */

function parseTinyDate_(value) {
  if (value instanceof Date) {
    return value;
  }

  const texto =
    String(value || '').trim();

  const parts =
    texto.split('/');

  if (parts.length !== 3) {
    return new Date();
  }

  const data =
    new Date(
      Number(parts[2]),
      Number(parts[1]) - 1,
      Number(parts[0])
    );

  return Number.isNaN(
    data.getTime()
  )
    ? new Date()
    : data;
}

function parseTinyDateOrNull_(value) {
  if (value instanceof Date) {
    return value;
  }

  const parts =
    String(value || '')
      .trim()
      .split('/');

  if (parts.length !== 3) {
    return null;
  }

  const data =
    new Date(
      Number(parts[2]),
      Number(parts[1]) - 1,
      Number(parts[0])
    );

  return Number.isNaN(
    data.getTime()
  )
    ? null
    : data;
}

function formatarMesAno_(data) {
  if (
    !(data instanceof Date) ||
    Number.isNaN(data.getTime())
  ) {
    return '';
  }

  const meses = [
    'Jan',
    'Fev',
    'Mar',
    'Abr',
    'Mai',
    'Jun',
    'Jul',
    'Ago',
    'Set',
    'Out',
    'Nov',
    'Dez',
  ];

  return (
    meses[data.getMonth()] +
    '/' +
    String(data.getFullYear()).slice(-2)
  );
}

function formatarMesAnoDeTexto_(
  ano,
  mes
) {
  const anoTexto =
    String(ano || '').trim();

  const mesTexto =
    String(mes || '').trim();

  if (
    !anoTexto ||
    !mesTexto
  ) {
    return '';
  }

  const meses = {
    janeiro: 'Jan',
    fevereiro: 'Fev',
    março: 'Mar',
    marco: 'Mar',
    abril: 'Abr',
    maio: 'Mai',
    junho: 'Jun',
    julho: 'Jul',
    agosto: 'Ago',
    setembro: 'Set',
    outubro: 'Out',
    novembro: 'Nov',
    dezembro: 'Dez',
  };

  const chave =
    mesTexto
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

  const abreviado =
    meses[chave] ||
    mesTexto.slice(0, 3);

  return (
    abreviado +
    '/' +
    anoTexto.slice(-2)
  );
}

/**
 * STATUS E EMPRESA
 */

function isCancelado_(situacao) {
  return String(
    situacao || ''
  )
    .toLowerCase()
    .includes('cancel');
}

function isEntregue_(value) {
  const text =
    String(value || '')
      .toLowerCase();

  return (
    text.includes('entregue')
  );
}

function obterStatusEntrega_(pedido) {
  if (
    isCancelado_(
      pedido && pedido.situacao
    )
  ) {
    return 'Cancelado';
  }

  return isEntregue_(
    pedido && pedido.situacao
  )
    ? 'Entregue'
    : 'Falta Entregar';
}

function inferirEmpresa_(pedido) {
  const situacao =
    String(
      pedido && pedido.situacao
        ? pedido.situacao
        : ''
    )
      .trim()
      .toLowerCase();

  if (situacao === 'em aberto') {
    return 'Marmoraria';
  }

  const text = [
    pedido.obs,
    pedido.obs_interna,
    pedido.deposito,
    pedido.descricao_lista_preco,
    JSON.stringify(
      pedido.marcadores || []
    ),
    JSON.stringify(
      pedido.itens || []
    ),
  ]
    .join(' ')
    .toLowerCase();

  if (
    text.includes('marmoraria')
  ) {
    return 'Marmoraria';
  }

  return 'Saldão';
}

/**
 * CORREÇÕES HISTÓRICAS DOS CANCELADOS
 */

function corrigirValoresCanceladosHistoricos() {
  const sheet =
    obterAbaVendas_();

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

  Object
    .keys(valoresPorLinha)
    .forEach(row => {
      sheet
        .getRange(
          Number(row),
          COL_VALOR
        )
        .setValue(
          valoresPorLinha[row]
        );
    });

  return {
    status: 'ok',
    linhasCorrigidas:
      Object.keys(
        valoresPorLinha
      ).length,
  };
}

/**
 * UTILITÁRIOS
 */

function removerGatilhosDaFuncao_(
  nomeFuncao
) {
  ScriptApp
    .getProjectTriggers()
    .filter(trigger =>
      trigger.getHandlerFunction() ===
      nomeFuncao
    )
    .forEach(trigger =>
      ScriptApp.deleteTrigger(
        trigger
      )
    );
}

function normalizarListaTiny_(value) {
  if (!value) {
    return [];
  }

  return Array.isArray(value)
    ? value
    : [value];
}

function obterMensagemErro_(error) {
  if (!error) {
    return 'Erro desconhecido';
  }

  return String(
    error.message || error
  );
}
