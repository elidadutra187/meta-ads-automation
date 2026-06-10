"""
Prompts específicos para Saldão Center
Foco: Gerar conversas no WhatsApp para venda de pisos e porcelanatos
"""

# Prompt principal para copy de anúncio Saldão Center
COPY_SALDAO = """Você é um copywriter especialista em anúncios para lojas de materiais de construção.

EMPRESA: Saldão Center - Pisos, Porcelanatos e Revestimentos
LOCALIZAÇÃO: Praia Grande/SP - Atende Baixada Santista e todo Brasil
WHATSAPP: (13) 99725-8292

PRODUTO/OFERTA: {produto}
DIFERENCIAL: {diferencial}
PÚBLICO: {publico}

REGRAS IMPORTANTES:
1. O objetivo é fazer a pessoa CHAMAR NO WHATSAPP
2. Tom direto, comercial, popular - sem enrolação
3. Enfatizar economia, parcelamento, frete grátis quando aplicável
4. Criar senso de urgência (estoque limitado, promoção por tempo limitado)
5. NÃO usar emojis em excesso (máximo 2)
6. Terminar com CTA claro para WhatsApp

Crie um anúncio com:

1. HEADLINE (máximo 40 caracteres): Chamada forte e direta
2. TEXTO PRINCIPAL (máximo 125 caracteres): Benefício + urgência + CTA WhatsApp
3. DESCRIÇÃO (máximo 30 caracteres): Reforço da oferta

Responda APENAS no formato JSON:
{{
    "headline": "seu headline aqui",
    "texto_principal": "seu texto aqui",
    "descricao": "descrição aqui"
}}
"""

# Variações para teste A/B
VARIACOES_SALDAO = """Você é um copywriter do Saldão Center (pisos e porcelanatos).

COPY ORIGINAL:
Headline: {headline}
Texto: {texto}

Crie 3 variações diferentes testando abordagens:

1. URGÊNCIA: Foco em escassez/tempo limitado
2. ECONOMIA: Foco em preço/parcelamento/desconto
3. FACILIDADE: Foco em entrega/atendimento/praticidade

Todas devem terminar com chamada para WhatsApp.

Responda APENAS no formato JSON:
{{
    "variacoes": [
        {{"headline": "...", "texto": "...", "tipo": "urgencia"}},
        {{"headline": "...", "texto": "...", "tipo": "economia"}},
        {{"headline": "...", "texto": "...", "tipo": "facilidade"}}
    ]
}}
"""

# Prompt para análise de performance focada em conversas
ANALISE_CONVERSAS = """Você é um analista de Meta Ads especialista em campanhas de mensagens.

EMPRESA: Saldão Center (pisos e porcelanatos)
OBJETIVO: Gerar conversas qualificadas no WhatsApp

MÉTRICAS DA CAMPANHA:
- Conversas iniciadas: {conversas}
- Custo por conversa: R$ {custo_conversa}
- Impressões: {impressoes}
- Cliques: {cliques}
- CTR: {ctr}%
- Gasto total: R$ {gasto}

LIMITES ACEITÁVEIS:
- Custo máximo por conversa: R$ 15,00
- CTR mínimo: 0,8%

COPY ATUAL:
{copy_atual}

Analise e responda no formato JSON:
{{
    "diagnostico": "resumo do problema ou sucesso",
    "custo_conversa_ok": true ou false,
    "ctr_ok": true ou false,
    "acao_recomendada": "PAUSAR|AJUSTAR_BUDGET|ESCALAR|NOVO_CRIATIVO|MANTER",
    "sugestao": "o que fazer especificamente",
    "prioridade": "ALTA|MEDIA|BAIXA"
}}
"""

# Prompt para criar copy baseado em imagem/vídeo
COPY_POR_CRIATIVO = """Você é copywriter do Saldão Center.

O criativo mostra: {descricao_criativo}

CONTEXTO:
- Loja de pisos, porcelanatos e revestimentos
- Baixada Santista/SP
- Objetivo: conversa no WhatsApp
- Tom: direto, comercial, urgente

Crie um copy que:
1. Conecte com o que aparece no criativo
2. Destaque o benefício principal
3. Termine com CTA para WhatsApp

Responda no formato JSON:
{{
    "headline": "máximo 40 caracteres",
    "texto_principal": "máximo 125 caracteres",
    "descricao": "máximo 30 caracteres"
}}
"""

# Headlines prontos para usar
HEADLINES_PRONTOS = [
    "Porcelanato em 15x Sem Juros",
    "Piso Barato? Temos!",
    "Reforma? Chama no Zap",
    "Saldão de Porcelanato",
    "Frete Grátis Baixada",
    "Estoque Limitado!",
    "Preço de Fábrica",
    "Só Essa Semana!",
    "Porcelanato 60x60 Barato",
    "Piso pra Toda Obra",
]

# Textos principais prontos
TEXTOS_PRONTOS = [
    "Porcelanato a partir de R$39,90/m². Parcelamos em até 15x. Chama no WhatsApp!",
    "Reformando? A gente tem o piso que você procura. Frete grátis pra Baixada!",
    "Estoque limitado de porcelanato 60x60. Chama agora e garanta o seu!",
    "Pisos e porcelanatos com os melhores preços da região. Orçamento pelo WhatsApp!",
    "Últimas unidades! Porcelanato polido com desconto especial. Chama no Zap!",
]

# Descrições prontas
DESCRICOES_PRONTAS = [
    "Chama no WhatsApp",
    "Orçamento grátis",
    "Frete grátis",
    "15x sem juros",
    "Estoque limitado",
    "Loja em Praia Grande",
]
