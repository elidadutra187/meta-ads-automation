"""
Templates de prompts para geração de copy com Ollama
"""

# Prompt principal para gerar copy de anúncio
COPY_GENERATOR = """Você é um copywriter especialista em anúncios para Facebook e Instagram.

PRODUTO/SERVIÇO: {produto}
PÚBLICO-ALVO: {publico}
OBJETIVO: {objetivo}
TOM DE VOZ: {tom}

Crie um anúncio com:

1. HEADLINE (máximo 40 caracteres): Título chamativo e direto
2. TEXTO PRINCIPAL (máximo 125 caracteres): Texto persuasivo para o feed
3. DESCRIÇÃO (máximo 30 caracteres): Complemento curto
4. CTA: Escolha o melhor call-to-action entre: SHOP_NOW, LEARN_MORE, SIGN_UP, DOWNLOAD, GET_OFFER, CONTACT_US

Responda APENAS no formato JSON abaixo, sem explicações:
{{
    "headline": "seu headline aqui",
    "texto_principal": "seu texto aqui",
    "descricao": "descrição aqui",
    "cta": "SHOP_NOW"
}}
"""

# Prompt para variações de copy
COPY_VARIATIONS = """Você é um copywriter especialista em testes A/B para Meta Ads.

COPY ORIGINAL:
Headline: {headline}
Texto: {texto}

Crie 3 variações diferentes mantendo a essência mas testando:
- Variação 1: Foco em URGÊNCIA
- Variação 2: Foco em BENEFÍCIO
- Variação 3: Foco em PROVA SOCIAL

Responda APENAS no formato JSON:
{{
    "variacoes": [
        {{"headline": "...", "texto": "...", "tipo": "urgencia"}},
        {{"headline": "...", "texto": "...", "tipo": "beneficio"}},
        {{"headline": "...", "texto": "...", "tipo": "prova_social"}}
    ]
}}
"""

# Prompt para analisar performance e sugerir melhorias
ANALYZE_PERFORMANCE = """Você é um analista de mídia paga especialista em Meta Ads.

MÉTRICAS DA CAMPANHA:
- Impressões: {impressoes}
- Cliques: {cliques}
- CTR: {ctr}%
- CPC: R$ {cpc}
- Conversões: {conversoes}
- CPA: R$ {cpa}
- ROAS: {roas}
- Gasto: R$ {gasto}

COPY ATUAL:
{copy_atual}

Analise e responda no formato JSON:
{{
    "diagnostico": "resumo do problema principal",
    "causa_provavel": "o que pode estar causando",
    "acao_recomendada": "PAUSAR|AJUSTAR_BUDGET|NOVO_CRIATIVO|MANTER",
    "sugestao_copy": "novo copy se aplicável ou null",
    "prioridade": "ALTA|MEDIA|BAIXA"
}}
"""

# Prompt para gerar público-alvo baseado no produto
AUDIENCE_GENERATOR = """Você é um especialista em segmentação de público para Meta Ads.

PRODUTO/SERVIÇO: {produto}
DESCRIÇÃO: {descricao}

Sugira a segmentação ideal. Responda APENAS no formato JSON:
{{
    "idade_min": 18,
    "idade_max": 45,
    "generos": ["male", "female"],
    "interesses": ["interesse1", "interesse2", "interesse3"],
    "comportamentos": ["comportamento1", "comportamento2"],
    "localizacao": "Brasil todo ou estados específicos"
}}
"""

# Prompt para nome de campanha
CAMPAIGN_NAME = """Crie um nome curto e descritivo para uma campanha de Meta Ads.

PRODUTO: {produto}
OBJETIVO: {objetivo}
DATA: {data}

Responda apenas com o nome, sem explicações. Máximo 50 caracteres.
Formato sugerido: [Objetivo]-[Produto]-[Mês/Ano]
"""
