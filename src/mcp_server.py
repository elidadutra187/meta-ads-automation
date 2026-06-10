"""
MCP Server Local - Saldão Center
Integra Ollama (copy) + Meta Ads + WhatsApp em um único servidor
"""
import json
import asyncio
from typing import Any
import sys

# MCP SDK
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Instalando MCP SDK...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mcp"])
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent

import ollama

# Configurações
from config.saldao_center import (
    EMPRESA,
    PRODUTOS,
    DIFERENCIAIS,
    GATILHOS,
    TARGETING_PRINCIPAL,
)
from templates.prompts_saldao import COPY_SALDAO, HEADLINES_PRONTOS, TEXTOS_PRONTOS

# Criar servidor MCP
server = Server("saldao-center-mcp")


# ==================== FERRAMENTAS ====================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """Lista todas as ferramentas disponíveis."""
    return [
        Tool(
            name="gerar_copy",
            description="Gera copy de anúncio para o Saldão Center usando IA local (Ollama)",
            inputSchema={
                "type": "object",
                "properties": {
                    "produto": {
                        "type": "string",
                        "description": "Produto (ex: Porcelanato 60x60, Piso cerâmico)"
                    },
                    "diferencial": {
                        "type": "string",
                        "description": "Diferencial a destacar (ex: 15x sem juros, frete grátis)"
                    },
                    "publico": {
                        "type": "string",
                        "description": "Público-alvo (ex: pessoas reformando, construtores)"
                    }
                },
                "required": ["produto"]
            }
        ),
        Tool(
            name="gerar_variacoes",
            description="Gera 3 variações de copy para teste A/B",
            inputSchema={
                "type": "object",
                "properties": {
                    "headline": {"type": "string"},
                    "texto": {"type": "string"}
                },
                "required": ["headline", "texto"]
            }
        ),
        Tool(
            name="listar_produtos",
            description="Lista produtos principais do Saldão Center",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="listar_diferenciais",
            description="Lista diferenciais e ofertas disponíveis",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="obter_targeting",
            description="Retorna configuração de targeting para Baixada Santista",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="sugerir_headlines",
            description="Sugere headlines prontos para usar",
            inputSchema={
                "type": "object",
                "properties": {
                    "quantidade": {
                        "type": "integer",
                        "description": "Número de headlines (padrão: 5)"
                    }
                }
            }
        ),
        Tool(
            name="montar_link_whatsapp",
            description="Monta link do WhatsApp com mensagem pré-definida",
            inputSchema={
                "type": "object",
                "properties": {
                    "mensagem": {
                        "type": "string",
                        "description": "Mensagem inicial (ex: Olá, vi o anúncio do porcelanato)"
                    }
                }
            }
        ),
        Tool(
            name="calcular_metragem",
            description="Calcula quantidade de piso necessária",
            inputSchema={
                "type": "object",
                "properties": {
                    "largura": {"type": "number", "description": "Largura em metros"},
                    "comprimento": {"type": "number", "description": "Comprimento em metros"},
                    "margem": {"type": "number", "description": "Margem de segurança % (padrão: 10)"}
                },
                "required": ["largura", "comprimento"]
            }
        ),
        Tool(
            name="info_empresa",
            description="Retorna informações da empresa Saldão Center",
            inputSchema={"type": "object", "properties": {}}
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Executa uma ferramenta."""

    if name == "gerar_copy":
        return await _gerar_copy(arguments)

    elif name == "gerar_variacoes":
        return await _gerar_variacoes(arguments)

    elif name == "listar_produtos":
        return [TextContent(
            type="text",
            text=json.dumps({"produtos": PRODUTOS}, ensure_ascii=False, indent=2)
        )]

    elif name == "listar_diferenciais":
        return [TextContent(
            type="text",
            text=json.dumps({
                "diferenciais": DIFERENCIAIS,
                "gatilhos": GATILHOS
            }, ensure_ascii=False, indent=2)
        )]

    elif name == "obter_targeting":
        return [TextContent(
            type="text",
            text=json.dumps(TARGETING_PRINCIPAL, ensure_ascii=False, indent=2)
        )]

    elif name == "sugerir_headlines":
        qtd = arguments.get("quantidade", 5)
        return [TextContent(
            type="text",
            text=json.dumps({
                "headlines": HEADLINES_PRONTOS[:qtd],
                "textos": TEXTOS_PRONTOS[:qtd]
            }, ensure_ascii=False, indent=2)
        )]

    elif name == "montar_link_whatsapp":
        msg = arguments.get("mensagem", "Olá, vi o anúncio e quero saber mais!")
        msg_encoded = msg.replace(" ", "%20")
        link = f"https://wa.me/{EMPRESA['whatsapp']}?text={msg_encoded}"
        return [TextContent(
            type="text",
            text=json.dumps({
                "link": link,
                "whatsapp": EMPRESA["whatsapp_display"],
                "mensagem": msg
            }, ensure_ascii=False, indent=2)
        )]

    elif name == "calcular_metragem":
        largura = arguments["largura"]
        comprimento = arguments["comprimento"]
        margem = arguments.get("margem", 10) / 100
        area = largura * comprimento
        area_com_margem = area * (1 + margem)
        return [TextContent(
            type="text",
            text=json.dumps({
                "area_m2": round(area, 2),
                "area_com_margem_m2": round(area_com_margem, 2),
                "margem_percentual": arguments.get("margem", 10),
                "dica": "Recomendamos sempre comprar com margem para recortes e reserva"
            }, ensure_ascii=False, indent=2)
        )]

    elif name == "info_empresa":
        return [TextContent(
            type="text",
            text=json.dumps(EMPRESA, ensure_ascii=False, indent=2)
        )]

    else:
        return [TextContent(type="text", text=f"Ferramenta não encontrada: {name}")]


async def _gerar_copy(args: dict) -> list[TextContent]:
    """Gera copy usando Ollama."""
    produto = args.get("produto", "Porcelanato")
    diferencial = args.get("diferencial", "15x sem juros")
    publico = args.get("publico", "pessoas reformando")

    prompt = COPY_SALDAO.format(
        produto=produto,
        diferencial=diferencial,
        publico=publico
    )

    try:
        response = ollama.generate(model="llama3.2", prompt=prompt)
        resultado = response["response"]

        # Tentar parsear JSON
        try:
            start = resultado.find("{")
            end = resultado.rfind("}") + 1
            if start != -1 and end > start:
                copy_json = json.loads(resultado[start:end])
                return [TextContent(
                    type="text",
                    text=json.dumps(copy_json, ensure_ascii=False, indent=2)
                )]
        except:
            pass

        return [TextContent(type="text", text=resultado)]

    except Exception as e:
        return [TextContent(type="text", text=f"Erro ao gerar copy: {str(e)}")]


async def _gerar_variacoes(args: dict) -> list[TextContent]:
    """Gera variações de copy."""
    headline = args.get("headline", "")
    texto = args.get("texto", "")

    prompt = f"""Crie 3 variacoes do copy abaixo para teste A/B.

ORIGINAL:
Headline: {headline}
Texto: {texto}

Variacoes:
1. URGENCIA (foco em escassez)
2. ECONOMIA (foco em preco/desconto)
3. FACILIDADE (foco em entrega/atendimento)

Responda em JSON:
{{"variacoes": [{{"tipo": "urgencia", "headline": "...", "texto": "..."}}, ...]}}
"""

    try:
        response = ollama.generate(model="llama3.2", prompt=prompt)
        return [TextContent(type="text", text=response["response"])]
    except Exception as e:
        return [TextContent(type="text", text=f"Erro: {str(e)}")]


# ==================== MAIN ====================

async def main():
    """Inicia o servidor MCP."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
