"""
Monitor de Campanhas
Executa verificações periódicas e envia alertas
"""
import time
import schedule
from datetime import datetime
from typing import Callable, Optional
from loguru import logger

from src.meta_api import get_api
from src.optimizer import get_optimizer
from config.settings import OPTIMIZATION, PATHS


class CampaignMonitor:
    """
    Monitora campanhas em tempo real e executa ações automáticas.
    """

    def __init__(self):
        self.api = get_api()
        self.optimizer = get_optimizer()
        self.running = False
        self.alertas = []

        # Configurar log
        log_file = PATHS["logs"] / "monitor_{time}.log"
        logger.add(str(log_file), rotation="1 day", retention="7 days")

    def verificar_todas_campanhas(self):
        """Verifica status de todas as campanhas ativas."""
        logger.info("=" * 40)
        logger.info(f"Verificação: {datetime.now().strftime('%H:%M:%S')}")
        logger.info("=" * 40)

        campanhas = self.api.listar_campanhas(status="ACTIVE")

        for campanha in campanhas:
            self._verificar_campanha(campanha)

    def _verificar_campanha(self, campanha: dict):
        """Verifica uma campanha específica."""
        campaign_id = campanha["id"]
        nome = campanha.get("name", "Sem nome")

        logger.info(f"Verificando: {nome}")

        # Obter métricas
        metricas = self.api.obter_insights(campaign_id, "campaign", "today")

        if not metricas:
            logger.debug(f"Sem dados para: {nome}")
            return

        # Verificar limites
        cpa = metricas.get("cpa", 0)
        roas = metricas.get("roas", 0)
        gasto = metricas.get("gasto", 0)

        # Alerta CPA
        max_cpa = OPTIMIZATION["max_cpa"] / 100
        if cpa > max_cpa:
            self._criar_alerta(
                tipo="CPA_ALTO",
                campanha=nome,
                mensagem=f"CPA R${cpa:.2f} > Limite R${max_cpa:.2f}",
                prioridade="ALTA"
            )

        # Alerta ROAS
        if roas > 0 and roas < OPTIMIZATION["min_roas"]:
            self._criar_alerta(
                tipo="ROAS_BAIXO",
                campanha=nome,
                mensagem=f"ROAS {roas:.2f} < Mínimo {OPTIMIZATION['min_roas']}",
                prioridade="MEDIA"
            )

        # Log de status
        logger.info(
            f"  Gasto: R${gasto:.2f} | CPA: R${cpa:.2f} | ROAS: {roas:.2f}"
        )

    def _criar_alerta(
        self,
        tipo: str,
        campanha: str,
        mensagem: str,
        prioridade: str = "MEDIA"
    ):
        """Cria um alerta."""
        alerta = {
            "timestamp": datetime.now().isoformat(),
            "tipo": tipo,
            "campanha": campanha,
            "mensagem": mensagem,
            "prioridade": prioridade,
        }

        self.alertas.append(alerta)

        if prioridade == "ALTA":
            logger.warning(f"ALERTA: {mensagem}")
        else:
            logger.info(f"Aviso: {mensagem}")

    def executar_otimizacao_automatica(self):
        """Executa otimização em todas campanhas ativas."""
        logger.info("Executando otimização automática...")
        resultados = self.optimizer.otimizar_campanhas()

        for r in resultados:
            if r["acao_tomada"] != "NENHUMA":
                logger.info(f"Campanha {r['campaign_id']}: {r['acao_tomada']}")

    def verificar_fadiga_criativos(self):
        """Verifica fadiga de criativos em todos os ads ativos."""
        logger.info("Verificando fadiga de criativos...")

        campanhas = self.api.listar_campanhas(status="ACTIVE")

        for campanha in campanhas:
            adsets = self.api.listar_adsets(campanha["id"])

            for adset in adsets:
                # Aqui você obteria os ads do adset
                # e verificaria fadiga de cada um
                pass

    def obter_relatorio_diario(self) -> dict:
        """Gera relatório diário de todas as campanhas."""
        campanhas = self.api.listar_campanhas()
        relatorio = {
            "data": datetime.now().strftime("%Y-%m-%d"),
            "total_campanhas": len(campanhas),
            "ativas": 0,
            "pausadas": 0,
            "metricas_totais": {
                "gasto": 0,
                "impressoes": 0,
                "cliques": 0,
                "conversoes": 0,
            },
            "campanhas": [],
        }

        for campanha in campanhas:
            status = campanha.get("status", "UNKNOWN")
            if status == "ACTIVE":
                relatorio["ativas"] += 1
            else:
                relatorio["pausadas"] += 1

            metricas = self.api.obter_insights(campanha["id"], "campaign", "today")

            if metricas:
                relatorio["metricas_totais"]["gasto"] += metricas.get("gasto", 0)
                relatorio["metricas_totais"]["impressoes"] += metricas.get("impressoes", 0)
                relatorio["metricas_totais"]["cliques"] += metricas.get("cliques", 0)
                relatorio["metricas_totais"]["conversoes"] += metricas.get("conversoes", 0)

            relatorio["campanhas"].append({
                "id": campanha["id"],
                "nome": campanha.get("name"),
                "status": status,
                "metricas": metricas or {},
            })

        return relatorio

    def iniciar_monitoramento(
        self,
        intervalo_minutos: int = 30,
        otimizar_automaticamente: bool = True
    ):
        """
        Inicia loop de monitoramento.

        Args:
            intervalo_minutos: Intervalo entre verificações
            otimizar_automaticamente: Se True, executa otimização após verificação
        """
        logger.info(f"Iniciando monitoramento a cada {intervalo_minutos} minutos")

        # Agendar verificação
        schedule.every(intervalo_minutos).minutes.do(self.verificar_todas_campanhas)

        # Agendar otimização
        if otimizar_automaticamente:
            schedule.every(intervalo_minutos * 2).minutes.do(
                self.executar_otimizacao_automatica
            )

        # Agendar verificação de fadiga (1x por dia)
        schedule.every().day.at("10:00").do(self.verificar_fadiga_criativos)

        # Executar primeira verificação
        self.verificar_todas_campanhas()

        self.running = True
        logger.info("Monitoramento ativo. Pressione Ctrl+C para parar.")

        try:
            while self.running:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Monitoramento encerrado.")
            self.running = False

    def parar(self):
        """Para o monitoramento."""
        self.running = False


# Singleton
_monitor = None


def get_monitor() -> CampaignMonitor:
    """Retorna instância do monitor."""
    global _monitor
    if _monitor is None:
        _monitor = CampaignMonitor()
    return _monitor
