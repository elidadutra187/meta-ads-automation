"""
Meta Ads Automation - CLI Principal
Sistema gratuito de automação com IA local (Ollama)
"""
import sys
import json
from pathlib import Path

# Adicionar diretório pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from loguru import logger

from config.settings import validate_config, PATHS, META_CONFIG

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    Meta Ads Automation - Automação gratuita com IA local

    Sistema completo para gerenciar campanhas do Meta Ads
    usando Ollama para geração de copy (100% gratuito).
    """
    pass


@cli.command()
def status():
    """Verifica status da conexão com Meta e Ollama."""
    console.print(Panel("Verificando conexões...", style="blue"))

    # Verificar configurações
    try:
        validate_config()
        console.print("[green]✓[/green] Configurações .env OK")
    except ValueError as e:
        console.print(f"[red]✗[/red] Erro nas configurações: {e}")
        return

    # Verificar Meta API
    try:
        from src.meta_api import MetaAdsAPI
        api = MetaAdsAPI()
        campanhas = api.listar_campanhas()
        console.print(f"[green]✓[/green] Meta API conectada ({len(campanhas)} campanhas)")
    except Exception as e:
        console.print(f"[red]✗[/red] Erro Meta API: {e}")

    # Verificar Ollama
    try:
        from src.ollama_copy import OllamaCopyGenerator
        gen = OllamaCopyGenerator()
        console.print(f"[green]✓[/green] Ollama conectado (modelo: {gen.model})")
    except Exception as e:
        console.print(f"[red]✗[/red] Ollama não disponível: {e}")
        console.print("    Execute: ollama serve")


@cli.command()
@click.argument("pasta", type=click.Path(exists=True), required=False)
def upload(pasta):
    """Faz upload de criativos de uma pasta."""
    pasta = pasta or str(PATHS["criativos"])

    console.print(f"Enviando criativos de: {pasta}")

    try:
        from src.meta_api import get_api
        api = get_api()
        resultados = api.upload_pasta_criativos(pasta)

        table = Table(title="Imagens Enviadas")
        table.add_column("Arquivo")
        table.add_column("Hash")

        for r in resultados:
            table.add_row(r["nome"], r["hash"][:20] + "...")

        console.print(table)
        console.print(f"[green]Total: {len(resultados)} imagens[/green]")

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


@cli.command()
@click.argument("produto")
@click.option("--publico", "-p", default="Público geral", help="Público-alvo")
@click.option("--objetivo", "-o", default="Vendas", help="Objetivo (Vendas/Leads)")
@click.option("--tom", "-t", default="Profissional", help="Tom de voz")
def gerar_copy(produto, publico, objetivo, tom):
    """Gera copy de anúncio com IA."""
    console.print(f"Gerando copy para: {produto}")

    try:
        from src.ollama_copy import get_generator
        gen = get_generator()

        copy = gen.gerar_copy(
            produto=produto,
            publico=publico,
            objetivo=objetivo,
            tom=tom
        )

        console.print(Panel(
            f"[bold]Headline:[/bold] {copy.get('headline', 'N/A')}\n\n"
            f"[bold]Texto:[/bold] {copy.get('texto_principal', 'N/A')}\n\n"
            f"[bold]Descrição:[/bold] {copy.get('descricao', 'N/A')}\n\n"
            f"[bold]CTA:[/bold] {copy.get('cta', 'N/A')}",
            title="Copy Gerado",
            style="green"
        ))

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


@cli.command()
@click.argument("produto")
@click.argument("link_url")
@click.option("--pasta", "-p", help="Pasta com criativos")
@click.option("--budget", "-b", type=int, default=5000, help="Budget diário (centavos)")
@click.option("--ativar", is_flag=True, help="Ativar campanha imediatamente")
def criar_campanha(produto, link_url, pasta, budget, ativar):
    """Cria uma campanha completa com criativos e copy."""
    console.print(Panel(f"Criando campanha para: {produto}", style="blue"))

    try:
        from src.campaign_manager import get_manager
        manager = get_manager()

        resultado = manager.criar_campanha_completa(
            produto=produto,
            link_url=link_url,
            pasta_criativos=pasta,
            budget_diario=budget,
            ativar=ativar,
        )

        console.print(Panel(
            f"[bold]Campaign ID:[/bold] {resultado['campaign_id']}\n"
            f"[bold]AdSet ID:[/bold] {resultado['adset_id']}\n"
            f"[bold]Ads criados:[/bold] {len(resultado['ad_ids'])}\n"
            f"[bold]Status:[/bold] {'ATIVA' if ativar else 'PAUSADA'}",
            title="Campanha Criada!",
            style="green"
        ))

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")
        logger.exception(e)


@cli.command()
def listar():
    """Lista todas as campanhas."""
    try:
        from src.meta_api import get_api
        api = get_api()
        campanhas = api.listar_campanhas()

        table = Table(title="Campanhas")
        table.add_column("ID")
        table.add_column("Nome")
        table.add_column("Status")
        table.add_column("Objetivo")

        for c in campanhas:
            status_color = "green" if c.get("status") == "ACTIVE" else "yellow"
            table.add_row(
                c["id"],
                c.get("name", "N/A")[:40],
                f"[{status_color}]{c.get('status', 'N/A')}[/{status_color}]",
                c.get("objective", "N/A")
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


@cli.command()
@click.argument("campaign_id")
def insights(campaign_id):
    """Mostra insights de uma campanha."""
    try:
        from src.meta_api import get_api
        api = get_api()
        metricas = api.obter_insights(campaign_id, "campaign", "last_7d")

        if not metricas:
            console.print("[yellow]Sem dados disponíveis[/yellow]")
            return

        table = Table(title=f"Insights - {campaign_id}")
        table.add_column("Métrica")
        table.add_column("Valor")

        table.add_row("Impressões", f"{metricas.get('impressoes', 0):,}")
        table.add_row("Cliques", f"{metricas.get('cliques', 0):,}")
        table.add_row("CTR", f"{metricas.get('ctr', 0):.2f}%")
        table.add_row("CPC", f"R$ {metricas.get('cpc', 0):.2f}")
        table.add_row("Gasto", f"R$ {metricas.get('gasto', 0):.2f}")
        table.add_row("Conversões", f"{metricas.get('conversoes', 0)}")
        table.add_row("CPA", f"R$ {metricas.get('cpa', 0):.2f}")
        table.add_row("ROAS", f"{metricas.get('roas', 0):.2f}")

        console.print(table)

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


@cli.command()
@click.option("--auto", is_flag=True, help="Executar ações automaticamente")
def otimizar(auto):
    """Analisa e otimiza campanhas."""
    console.print("Analisando campanhas...")

    try:
        from src.optimizer import get_optimizer
        optimizer = get_optimizer()
        resultados = optimizer.otimizar_campanhas()

        table = Table(title="Otimização")
        table.add_column("Campanha")
        table.add_column("Diagnóstico")
        table.add_column("Ação")

        for r in resultados:
            diag = r.get("analise", {}).get("diagnostico", {})
            table.add_row(
                r["campaign_id"][:15],
                diag.get("mensagem", "N/A")[:40],
                r.get("acao_tomada", "N/A")
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


@cli.command()
@click.option("--intervalo", "-i", type=int, default=30, help="Intervalo em minutos")
def monitorar(intervalo):
    """Inicia monitoramento contínuo."""
    console.print(Panel(
        f"Iniciando monitoramento a cada {intervalo} minutos\n"
        "Pressione Ctrl+C para parar",
        style="blue"
    ))

    try:
        from src.monitor import get_monitor
        monitor = get_monitor()
        monitor.iniciar_monitoramento(intervalo_minutos=intervalo)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoramento encerrado[/yellow]")
    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


@cli.command()
@click.argument("campaign_id")
@click.option("--acao", type=click.Choice(["pausar", "ativar"]))
def gerenciar(campaign_id, acao):
    """Pausa ou ativa uma campanha."""
    try:
        from src.meta_api import get_api
        api = get_api()

        if acao == "pausar":
            api.pausar_campanha(campaign_id)
            console.print(f"[yellow]Campanha {campaign_id} pausada[/yellow]")
        elif acao == "ativar":
            api.ativar_campanha(campaign_id)
            console.print(f"[green]Campanha {campaign_id} ativada[/green]")

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


@cli.command()
def relatorio():
    """Gera relatório diário."""
    console.print("Gerando relatório...")

    try:
        from src.monitor import get_monitor
        monitor = get_monitor()
        rel = monitor.obter_relatorio_diario()

        console.print(Panel(
            f"[bold]Data:[/bold] {rel['data']}\n"
            f"[bold]Campanhas:[/bold] {rel['total_campanhas']} "
            f"({rel['ativas']} ativas, {rel['pausadas']} pausadas)\n\n"
            f"[bold]Gasto Total:[/bold] R$ {rel['metricas_totais']['gasto']:.2f}\n"
            f"[bold]Impressões:[/bold] {rel['metricas_totais']['impressoes']:,}\n"
            f"[bold]Cliques:[/bold] {rel['metricas_totais']['cliques']:,}\n"
            f"[bold]Conversões:[/bold] {rel['metricas_totais']['conversoes']}",
            title="Relatório Diário",
            style="blue"
        ))

    except Exception as e:
        console.print(f"[red]Erro: {e}[/red]")


if __name__ == "__main__":
    cli()
