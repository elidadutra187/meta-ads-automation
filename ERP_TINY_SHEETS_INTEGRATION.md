# Integração Tiny ERP -> Google Sheets

Documentação operacional da automação que sincroniza pedidos do Tiny ERP com a aba `Olist Vendas / Mês` da planilha do Saldão dos Pisos.

Projeto no GitHub: [elidadutra187/meta-ads-automation](https://github.com/elidadutra187/meta-ads-automation)

Arquivo principal:

```text
google_apps_script/sync_olist_vendas_tiny.gs
```

## Objetivo

Manter a planilha financeira e operacional atualizada automaticamente a partir do ERP, reduzindo retrabalho manual e evitando divergência entre pedidos, cancelamentos, entregas e formas de pagamento.

O Apps Script roda dentro do Google Sheets e consulta o Tiny ERP usando um token salvo nas propriedades do projeto. O token não fica exposto no código nem na planilha.

## Fonte e destino

Fonte:

- Tiny ERP.
- Pedidos, status, entregas, valores e informações de pagamento.

Destino:

- Google Sheets.
- Planilha `Planilha Saldão dos Pisos`.
- Aba `Olist Vendas / Mês`.

## Estrutura atual da aba

| Coluna | Campo | Regra |
| --- | --- | --- |
| A | Mês | Gerado a partir da coluna `Data`, no formato `Jan/25`, `Dez/25`, `Jan/26`. |
| B | Numero do Pedido | Número do pedido no ERP. |
| C | Data | Data real da venda. É a coluna usada para ordenar a base. |
| D | Valor | Valor total do pedido. |
| E | Método de Pagamento | Apenas categorias operacionais: `PIX`, `CRÉDITO`, `DÉBITO`, `DINHEIRO`, `LINK DE PAGAMENTO` ou combinações. |
| F | Banco | Banco ou gateway identificado: `ITAU`, `BTG`, `STONE`. Em branco quando não houver dado confiável. |
| G | Parcelamento | Quantidade de parcelas, como `1X`, `4X`, `12X`. Em branco quando não houver parcelamento. |
| H | Entregas | `Entregue`, `Falta Entregar` ou `Cancelado`. |
| I | Status | Status financeiro/operacional do pedido, como `EFETIVO` ou `CANCELADO`. |
| J | Empresa | `Saldão` ou `Marmoraria`. |
| K | Venda | Canal da venda, como `Loja Física` ou `NuvemShop`. |
| L | Estado | UF do cliente. |
| M | Cidade | Cidade do cliente. |

## Regras de negócio

### Mês

O campo `Mês` não deve ser preenchido manualmente. Ele é derivado da coluna `Data`.

Exemplos:

- `02/01/2026` -> `Jan/26`
- `20/12/2025` -> `Dez/25`
- `17/07/2025` -> `Jul/25`

A ordenação correta da base é por `Data`, não por número do pedido. Isso evita gráficos em ordem errada, como `Jul/25` aparecendo depois de meses de 2026.

### Status e cancelamentos

Quando o pedido estiver cancelado no Tiny:

- coluna `Status` recebe `CANCELADO`;
- coluna `Entregas` recebe `Cancelado`;
- o pedido continua na base para manter histórico financeiro e evitar quebra de relatórios.

### Entregas

A coluna `Entregas` segue o status de entrega do Tiny:

- se o pedido estiver entregue: `Entregue`;
- se ainda não estiver entregue: `Falta Entregar`;
- se estiver cancelado: `Cancelado`.

Essa regra evita contar cancelados como pedidos pendentes de entrega.

### Empresa

Regra atual:

- se o status do pedido no ERP for `em aberto`, a empresa é `Marmoraria`;
- nos demais casos, o script usa os sinais disponíveis no pedido e aplica `Saldão` quando não houver indicação contrária.

### Pagamentos

O script separa a forma de pagamento em três campos:

- `Método de Pagamento`;
- `Banco`;
- `Parcelamento`.

Exemplos:

| Entrada do ERP | Método de Pagamento | Banco | Parcelamento |
| --- | --- | --- | --- |
| `pix + Itau` | `PIX` | `ITAU` |  |
| `pix + Stone` | `PIX` | `STONE` |  |
| `Cartão de crédito`, gateway `Stone`, condição `30 60 90 120` | `CRÉDITO` | `STONE` | `4X` |
| `link de pagamento`, condição até `360` | `LINK DE PAGAMENTO` |  | `12X` |
| `multiplas + pix + credito + Stone` | `PIX + CRÉDITO` | `STONE` | conforme parcelas encontradas |

Quando o banco ou o parcelamento não aparecem de forma confiável no Tiny, a coluna fica em branco.

## Funções principais

| Função | Uso |
| --- | --- |
| `aSincronizarAgora` | Sincroniza novos pedidos e atualiza status existentes. |
| `aCriarGatilhoAgora` | Cria o gatilho automático de sincronização. |
| `aAtualizarStatusCanceladosAgora` | Atualiza cancelamentos já existentes na planilha. |
| `aAtualizarEntregasAgora` | Atualiza a coluna `Entregas`. |
| `aReconciliarEntregasComTinyAgora` | Faz varredura para reconciliar entregas com o Tiny. |
| `aReestruturarPagamentosEEntregasAgora` | Reprocessa pagamentos, banco, parcelamento e entregas. |
| `aJuntarAnoMesAgora` | Junta as antigas colunas `Ano` e `Mês` em uma única coluna `Mês`. |
| `aOrdenarVendasPorDataAgora` | Recalcula `Mês` pela `Data` e ordena a base cronologicamente. |

## Execução automática

O fluxo foi preparado para rodar por gatilho de tempo no Apps Script.

Rotina esperada:

1. Buscar novos pedidos no Tiny.
2. Inserir somente pedidos ainda não existentes.
3. Atualizar cancelamentos.
4. Atualizar entregas.
5. Separar método de pagamento, banco e parcelamento.
6. Recalcular `Mês` pela coluna `Data`.
7. Ordenar a aba por `Data`.

## Segurança

O token do Tiny deve ficar nas propriedades do Apps Script, não no código.

Boas práticas:

- nunca colar token em arquivo versionado;
- nunca colocar token em célula da planilha;
- usar `PropertiesService.getScriptProperties()` para ler segredos;
- manter `.env` e arquivos locais de segredo fora do GitHub;
- publicar no GitHub apenas o código e a documentação sem credenciais.

## Validação operacional

Checklist após mudanças:

- Conferir se a coluna A está no formato `Jan/25`, `Fev/25`, `Dez/25`.
- Conferir se a coluna C está em ordem crescente de data.
- Conferir se cancelados aparecem como `Cancelado` em `Entregas`.
- Conferir se `Falta Entregar` não inclui pedidos cancelados.
- Comparar a contagem de entregues, falta entregar e cancelados com o painel do Tiny.
- Verificar se os gráficos usam a coluna `Mês` depois da base estar ordenada por `Data`.

## Observação sobre pedidos antigos

Parte dos pedidos antigos veio de backup de outro sistema e pode ter número diferente do número atual do ERP. Nesses casos, a data da compra é a referência mais confiável para ordenação histórica e análise mensal.

Por isso a base deve ser tratada como uma série temporal ordenada por `Data`, e não como uma série por número de pedido.
