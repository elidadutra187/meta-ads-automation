# Meta Ads Automation

Sistema **100% gratuito** de automação de anúncios para Facebook e Instagram usando IA local (Ollama).

## Funcionalidades

- **Upload automático** de criativos (imagens/vídeos)
- **Geração de copy** com IA local (Ollama - gratuito)
- **Criação de campanhas** completas via CLI
- **Otimização automática** baseada em CPA/ROAS
- **Monitoramento contínuo** com alertas
- **Teste A/B** de copies gerados por IA
- **Relatórios** de performance

## Custos

| Componente | Custo |
|------------|-------|
| Ollama (IA local) | Gratuito |
| Meta Marketing API | Gratuito |
| Python + Bibliotecas | Gratuito |
| **Total** | **R$ 0** |

> Você só paga pelos anúncios no Meta Ads.

## Requisitos

- Python 3.9+
- [Ollama](https://ollama.com) instalado
- Conta Meta Business
- App no [Meta for Developers](https://developers.facebook.com)

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/meta-ads-automation.git
cd meta-ads-automation
```

### 2. Execute o setup

**Windows:**
```batch
scripts\setup.bat
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 3. Configure as credenciais

Edite o arquivo `.env` com suas credenciais:

```env
META_APP_ID=seu_app_id
META_APP_SECRET=seu_app_secret
META_ACCESS_TOKEN=seu_token
META_AD_ACCOUNT_ID=123456789
FACEBOOK_PAGE_ID=sua_pagina
```

### 4. Instale o modelo Ollama

```bash
ollama pull llama3.2
```

### 5. Inicie o Ollama

```bash
ollama serve
```

Ou no Windows:
```batch
scripts\start_ollama.bat
```

## Como Obter Credenciais Meta

1. Acesse [developers.facebook.com](https://developers.facebook.com)
2. Crie um novo App (tipo: Business)
3. Adicione o produto "Marketing API"
4. Gere um Access Token com permissões:
   - `ads_management`
   - `ads_read`
   - `business_management`
   - `pages_read_engagement`

## Uso

### Verificar conexões

```bash
python -m src.main status
```

### Upload de criativos

Coloque suas imagens na pasta `criativos/` e execute:

```bash
python -m src.main upload
```

Ou especifique uma pasta:

```bash
python -m src.main upload "C:\meus\criativos"
```

### Gerar copy com IA

```bash
python -m src.main gerar-copy "Curso de Marketing Digital" \
  --publico "Empreendedores 25-45 anos" \
  --objetivo "Vendas" \
  --tom "Urgente"
```

### Criar campanha completa

```bash
python -m src.main criar-campanha "Meu Produto" "https://meusite.com/produto" \
  --budget 5000 \
  --ativar
```

Isso vai:
1. Fazer upload de todos os criativos
2. Gerar copy com IA
3. Criar campanha, ad set e ads
4. Ativar (se usar `--ativar`)

### Listar campanhas

```bash
python -m src.main listar
```

### Ver métricas

```bash
python -m src.main insights CAMPAIGN_ID
```

### Otimizar campanhas

```bash
python -m src.main otimizar
```

### Monitoramento contínuo

```bash
python -m src.main monitorar --intervalo 30
```

### Gerar relatório

```bash
python -m src.main relatorio
```

## Estrutura do Projeto

```
meta-ads-automation/
├── config/
│   └── settings.py      # Configurações
├── criativos/           # Suas imagens/vídeos
├── logs/                # Logs do sistema
├── scripts/
│   ├── setup.bat        # Setup Windows
│   ├── run.bat          # Atalho para comandos
│   └── start_ollama.bat # Iniciar Ollama
├── src/
│   ├── main.py          # CLI principal
│   ├── meta_api.py      # Integração Meta
│   ├── ollama_copy.py   # Geração de copy
│   ├── campaign_manager.py # Gerenciador
│   ├── optimizer.py     # Otimização
│   └── monitor.py       # Monitoramento
├── templates/
│   └── prompts.py       # Prompts para IA
├── .env.example         # Exemplo de config
├── requirements.txt     # Dependências
└── README.md
```

## Regras de Otimização

O sistema aplica automaticamente:

| Condição | Ação |
|----------|------|
| CPA > limite | Pausar campanha |
| ROAS < mínimo | Reduzir budget 30% |
| CTR < 0.5% | Sugerir novo criativo |
| Performance boa | Aumentar budget 20% |

Configure os limites no `.env`:

```env
MAX_CPA=5000      # R$ 50,00 em centavos
MIN_ROAS=1.5      # ROAS mínimo
```

## Modelos Ollama Recomendados

| Modelo | RAM | Qualidade | Velocidade |
|--------|-----|-----------|------------|
| `llama3.2:3b` | 4GB | Boa | Rápida |
| `llama3.2` | 8GB | Muito boa | Média |
| `mistral` | 6GB | Boa | Rápida |
| `gemma2:9b` | 10GB | Excelente | Média |

Para trocar o modelo, edite o `.env`:

```env
OLLAMA_MODEL=mistral
```

## Fluxo de Automação

```
Seus Criativos (pasta)
        │
        ▼
   Upload Meta
        │
        ▼
  Ollama gera Copy ──────┐
        │                │
        ▼                │
 Criar Campanha          │
        │                │
        ▼                │
   Monitorar ◄───────────┘
        │
        ▼
   CPA/ROAS OK? ──No──► Pausar/Ajustar
        │
       Yes
        ▼
     Escalar
```

## Contribuindo

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-funcionalidade`)
3. Commit (`git commit -m 'Adiciona nova funcionalidade'`)
4. Push (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## Licença

MIT License - veja [LICENSE](LICENSE) para detalhes.

## Suporte

- Issues: [GitHub Issues](https://github.com/seu-usuario/meta-ads-automation/issues)
- Docs Meta: [Marketing API](https://developers.facebook.com/docs/marketing-apis/)
- Docs Ollama: [ollama.com](https://ollama.com)
