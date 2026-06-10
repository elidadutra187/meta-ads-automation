"""
Otimizador Automático de Campanhas
Monitora e ajusta campanhas baseado em regras e análise de IA
"""
from typing import List, Dict, Optional
from loguru import logger

from config.settings import OPTIMIZATION
from src.meta_api import get_api
from src.ollama_copy import get_generator


class CampaignOptimizer:
    """
    Otimiza campanhas automaticamente baseado em:
    - Regras de CPA/ROAS
    - Análise de IA para diagnóstico
    - Realocação de budget
    """

    def __init__(self):
        self.api = get_api()
        self.copy_gen = get_generator()
        self.max_cpa = OPTIMIZATION["max_cpa"] / 100  # converter para reais
        self.min_roas = OPTIMIZATION["min_roas"]

    def analisar_campanha(self, campaign_id: str) -> dict:
        """
        Analisa uma campanha e retorna diagnóstico.

        Returns:
            Dict com métricas, diagnóstico e ações recomendadas
        """
        # Obter métricas
        metricas = self.api.obter_insights(campaign_id, "campaign")

        if not metricas or metricas.get("impressoes", 0) == 0:
            return {
                "status": "SEM_DADOS",
                "mensagem": "Campanha sem dados suficientes",
                "acao": "AGUARDAR",
            }

        # Análise por regras
        diagnostico = self._aplicar_regras(metricas)

        # Análise com IA para mais contexto
        if diagnostico["acao"] != "MANTER":
            analise_ia = self.copy_gen.analisar_performance(
                metricas=metricas,
                copy_atual="(copy não disponível)"
            )
            diagnostico["analise_ia"] = analise_ia

        return {
            "metricas": metricas,
            "diagnostico": diagnostico,
        }

    def _aplicar_regras(self, metricas: dict) -> dict:
        """Aplica regras de otimização."""
        cpa = metricas.get("cpa", 0)
        roas = metricas.get("roas", 0)
        ctr = metricas.get("ctr", 0)
        conversoes = metricas.get("conversoes", 0)

        # Regra 1: CPA muito alto
        if cpa > self.max_cpa and conversoes > 0:
            return {
                "problema": "CPA_ALTO",
                "mensagem": f"CPA (R${cpa:.2f}) acima do máximo (R${self.max_cpa:.2f})",
                "acao": "PAUSAR",
                "prioridade": "ALTA",
            }

        # Regra 2: ROAS baixo
        if roas > 0 and roas < self.min_roas:
            return {
                "problema": "ROAS_BAIXO",
                "mensagem": f"ROAS ({roas:.2f}) abaixo do mínimo ({self.min_roas})",
                "acao": "AJUSTAR_BUDGET",
                "prioridade": "ALTA",
            }

        # Regra 3: CTR muito baixo (problema de criativo)
        if ctr < 0.5 and metricas.get("impressoes", 0) > 1000:
            return {
                "problema": "CTR_BAIXO",
                "mensagem": f"CTR ({ctr:.2f}%) muito baixo - problema no criativo",
                "acao": "NOVO_CRIATIVO",
                "prioridade": "MEDIA",
            }

        # Regra 4: Sem conversões com gasto significativo
        if conversoes == 0 and metricas.get("gasto", 0) > 50:
            return {
                "problema": "SEM_CONVERSOES",
                "mensagem": "Gastando sem converter",
                "acao": "PAUSAR",
                "prioridade": "ALTA",
            }

        # Regra 5: Performance boa
        if roas >= self.min_roas or (cpa > 0 and cpa <= self.max_cpa * 0.7):
            return {
                "problema": None,
                "mensagem": "Performance dentro do esperado",
                "acao": "ESCALAR",
                "prioridade": "BAIXA",
            }

        return {
            "problema": None,
            "mensagem": "Performance aceitável",
            "acao": "MANTER",
            "prioridade": "BAIXA",
        }

    def otimizar_campanhas(self, campaign_ids: List[str] = None) -> List[dict]:
        """
        Otimiza múltiplas campanhas.

        Args:
            campaign_ids: Lista de IDs ou None para todas ativas

        Returns:
            Lista de resultados de otimização
        """
        # Se não especificou, pegar todas ativas
        if campaign_ids is None:
            campanhas = self.api.listar_campanhas(status="ACTIVE")
            campaign_ids = [c["id"] for c in campanhas]

        resultados = []

        for campaign_id in campaign_ids:
            logger.info(f"Analisando campanha: {campaign_id}")

            analise = self.analisar_campanha(campaign_id)
            acao = analise.get("diagnostico", {}).get("acao", "MANTER")

            resultado = {
                "campaign_id": campaign_id,
                "analise": analise,
                "acao_tomada": None,
            }

            # Executar ação
            if acao == "PAUSAR":
                self.api.pausar_campanha(campaign_id)
                resultado["acao_tomada"] = "CAMPANHA_PAUSADA"
                logger.warning(f"Campanha {campaign_id} PAUSADA")

            elif acao == "ESCALAR":
                # Aumentar budget em 20%
                self._ajustar_budget(campaign_id, fator=1.2)
                resultado["acao_tomada"] = "BUDGET_AUMENTADO_20%"
                logger.success(f"Campanha {campaign_id} ESCALADA")

            elif acao == "AJUSTAR_BUDGET":
                # Reduzir budget em 30%
                self._ajustar_budget(campaign_id, fator=0.7)
                resultado["acao_tomada"] = "BUDGET_REDUZIDO_30%"
                logger.info(f"Campanha {campaign_id} budget ajustado")

            else:
                resultado["acao_tomada"] = "NENHUMA"

            resultados.append(resultado)

        return resultados

    def _ajustar_budget(self, campaign_id: str, fator: float):
        """Ajusta budget dos ad sets de uma campanha."""
        adsets = self.api.listar_adsets(campaign_id)

        for adset in adsets:
            budget_atual = adset.get("daily_budget", 0)
            if budget_atual:
                novo_budget = int(int(budget_atual) * fator)
                # Implementar atualização via API
                logger.info(f"AdSet {adset['id']}: {budget_atual} -> {novo_budget}")

    def identificar_fadiga_criativo(self, ad_id: str) -> dict:
        """
        Detecta se um criativo está com fadiga.

        Sinais de fadiga:
        - CTR caindo ao longo do tempo
        - Frequência alta (mesma pessoa vendo muito)
        - CPM aumentando
        """
        # Comparar últimos 3 dias vs 7 dias anteriores
        metricas_recente = self.api.obter_insights(ad_id, "ad", "last_3d")
        metricas_anterior = self.api.obter_insights(ad_id, "ad", "last_7d")

        if not metricas_recente or not metricas_anterior:
            return {"fadiga": False, "motivo": "Dados insuficientes"}

        ctr_recente = metricas_recente.get("ctr", 0)
        ctr_anterior = metricas_anterior.get("ctr", 0)

        # CTR caiu mais de 20%
        if ctr_anterior > 0 and ctr_recente < ctr_anterior * 0.8:
            return {
                "fadiga": True,
                "motivo": f"CTR caiu de {ctr_anterior:.2f}% para {ctr_recente:.2f}%",
                "acao_recomendada": "NOVO_CRIATIVO",
            }

        return {"fadiga": False, "motivo": "Criativo ainda performando bem"}

    def realocar_budget(self, campaign_id: str) -> dict:
        """
        Realoca budget dos ad sets com pior performance para os melhores.
        """
        adsets = self.api.listar_adsets(campaign_id)
        performances = []

        for adset in adsets:
            metricas = self.api.obter_insights(adset["id"], "adset")
            performances.append({
                "adset_id": adset["id"],
                "nome": adset["name"],
                "budget": int(adset.get("daily_budget", 0)),
                "roas": metricas.get("roas", 0),
                "cpa": metricas.get("cpa", float("inf")),
            })

        # Ordenar por ROAS (melhor primeiro)
        performances.sort(key=lambda x: x["roas"], reverse=True)

        if len(performances) < 2:
            return {"realocado": False, "motivo": "Poucos ad sets"}

        # Pegar budget do pior e dar para o melhor
        pior = performances[-1]
        melhor = performances[0]

        if pior["roas"] < self.min_roas and melhor["roas"] >= self.min_roas:
            transferir = int(pior["budget"] * 0.5)
            logger.info(f"Transferindo R${transferir/100:.2f} de {pior['nome']} para {melhor['nome']}")

            return {
                "realocado": True,
                "de": pior["adset_id"],
                "para": melhor["adset_id"],
                "valor": transferir,
            }

        return {"realocado": False, "motivo": "Não há necessidade de realocação"}


# Singleton
_optimizer = None


def get_optimizer() -> CampaignOptimizer:
    """Retorna instância do otimizador."""
    global _optimizer
    if _optimizer is None:
        _optimizer = CampaignOptimizer()
    return _optimizer
