"""
Configuração específica do Saldão Center
Foco: Conversas no WhatsApp para venda de pisos e porcelanatos
"""

# === DADOS DA EMPRESA ===
EMPRESA = {
    "nome": "Saldão Center",
    "segmento": "Pisos, Porcelanatos e Revestimentos",
    "endereco": "Av. Min. Marcos Freire, 4268 - Vila Antártica - Praia Grande/SP",
    "site": "https://saldaocenter.com.br",
    "whatsapp": "5513997258292",  # Formato internacional sem +
    "whatsapp_display": "(13) 99725-8292",
}

# === OBJETIVO PRINCIPAL ===
# NÃO é tráfego, NÃO é engajamento
# É CONVERSA QUALIFICADA NO WHATSAPP
OBJETIVO_CAMPANHA = "OUTCOME_ENGAGEMENT"  # Para mensagens
OPTIMIZATION_GOAL = "CONVERSATIONS"  # Otimizar para conversas
CTA_PADRAO = "WHATSAPP_MESSAGE"

# === TARGETING GEOGRÁFICO ===
# Mercado principal: Baixada Santista
TARGETING_PRINCIPAL = {
    "geo_locations": {
        "cities": [
            {"key": "2511805", "name": "Praia Grande", "region": "São Paulo"},
            {"key": "2511904", "name": "Santos", "region": "São Paulo"},
            {"key": "2512209", "name": "São Vicente", "region": "São Paulo"},
            {"key": "2505709", "name": "Guarujá", "region": "São Paulo"},
            {"key": "2503706", "name": "Cubatão", "region": "São Paulo"},
            {"key": "2509205", "name": "Mongaguá", "region": "São Paulo"},
            {"key": "2507705", "name": "Itanhaém", "region": "São Paulo"},
            {"key": "2510907", "name": "Peruíbe", "region": "São Paulo"},
        ],
        "location_types": ["home", "recent"],
    },
    "age_min": 25,
    "age_max": 65,
    "publisher_platforms": ["facebook", "instagram"],
    "facebook_positions": ["feed", "story", "reels", "marketplace"],
    "instagram_positions": ["stream", "story", "reels"],
}

# Mercado expandido: Grande SP + Interior
TARGETING_EXPANDIDO = {
    "geo_locations": {
        "regions": [
            {"key": "3550308", "name": "São Paulo"},  # Estado de SP
        ],
        "location_types": ["home"],
    },
    "age_min": 25,
    "age_max": 65,
    "publisher_platforms": ["facebook", "instagram"],
}

# === INTERESSES RELEVANTES ===
INTERESSES = [
    # Construção e Reforma
    "Reforma residencial",
    "Construção civil",
    "Decoração de interiores",
    "Arquitetura",
    "Design de interiores",
    # Produtos
    "Pisos",
    "Cerâmica",
    "Porcelanato",
    "Revestimentos",
    # Comportamento
    "Proprietário de imóvel",
    "Casa própria",
    "Faça você mesmo",
    "DIY",
    # Profissionais
    "Pedreiro",
    "Mestre de obras",
    "Construtor",
]

# === PRODUTOS PRINCIPAIS ===
PRODUTOS = [
    "Porcelanato 60x60",
    "Porcelanato 80x80",
    "Piso cerâmico",
    "Revestimento para cozinha",
    "Revestimento para banheiro",
    "Pastilhas para piscina",
    "Piso externo",
    "Piso acetinado",
    "Piso polido",
    "Argamassa",
    "Rejunte",
]

# === DIFERENCIAIS PARA COPY ===
DIFERENCIAIS = [
    "Até 15x sem juros",
    "Até 21x com juros",
    "Frete grátis Baixada Santista",
    "Entrega para todo Brasil",
    "Loja física em Praia Grande",
    "Estoque disponível",
    "Atendimento personalizado",
    "Orçamento sem compromisso",
]

# === GATILHOS DE COPY ===
GATILHOS = {
    "urgencia": [
        "Estoque limitado",
        "Só essa semana",
        "Últimas unidades",
        "Promoção por tempo limitado",
        "Aproveite agora",
    ],
    "economia": [
        "Preço de fábrica",
        "Desconto especial",
        "Economia garantida",
        "Menor preço da região",
        "Saldão de ofertas",
    ],
    "facilidade": [
        "Parcelamos em até 15x",
        "Frete grátis",
        "Entregamos na sua obra",
        "Calculamos a metragem pra você",
        "Atendimento pelo WhatsApp",
    ],
    "confianca": [
        "Loja física consolidada",
        "Anos de experiência",
        "Milhares de clientes satisfeitos",
        "Produto de qualidade",
        "Garantia de fábrica",
    ],
}

# === TOM DE COMUNICAÇÃO ===
TOM_DE_VOZ = """
- Direto e objetivo
- Comercial, focado em conversão
- Popular, acessível
- Sem enrolação
- Com senso de urgência
- Enfatiza economia e condições de pagamento
- Convida para conversa no WhatsApp
"""

# === MÉTRICAS PRIORITÁRIAS ===
METRICAS_PRINCIPAIS = [
    "messaging_conversation_started_7d",  # Conversas iniciadas
    "cost_per_conversation",  # Custo por conversa
    "messaging_first_reply",  # Primeira resposta
]

METRICAS_SECUNDARIAS = [
    "ctr",
    "cpc",
    "cpm",
    "reach",
    "frequency",
]

# === LIMITES DE OTIMIZAÇÃO ===
OTIMIZACAO = {
    "max_custo_por_conversa": 15.00,  # R$ - pausar se passar
    "min_conversas_dia": 5,  # mínimo esperado por campanha
    "max_frequencia": 3.0,  # evitar fadiga
    "min_ctr": 0.8,  # % - abaixo indica problema no criativo
}
