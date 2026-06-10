"""
Gerenciador de Campanhas Completo
Orquestra criação de campanhas com criativos e copy gerado por IA
"""
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from loguru import logger

from config.settings import DEFAULT_TARGETING, OPTIMIZATION, PATHS
from src.meta_api import get_api
from src.ollama_copy import get_generator


class CampaignManager:
    """Gerencia criação e configuração de campanhas completas."""

    def __init__(self):
        self.api = get_api()
        self.copy_gen = get_generator()

    def criar_campanha_completa(
        self,
        produto: str,
        link_url: str,
        pasta_criativos: Optional[str] = None,
        publico: str = "Público geral brasileiro",
        objetivo_campanha: str = "OUTCOME_SALES",
        budget_diario: int = None,
        targeting: dict = None,
        ativar: bool = False,
    ) -> dict:
        """
        Cria uma campanha completa com:
        - Upload de criativos da pasta
        - Geração de copy com IA
        - Configuração de targeting
        - Criação de ads

        Args:
            produto: Nome/descrição do produto
            link_url: URL de destino
            pasta_criativos: Pasta com imagens (usa padrão se None)
            publico: Descrição do público-alvo
            objetivo_campanha: Objetivo Meta
            budget_diario: Budget em centavos
            targeting: Segmentação customizada
            ativar: Se True, ativa a campanha imediatamente

        Returns:
            Dict com IDs de tudo criado
        """
        pasta_criativos = pasta_criativos or str(PATHS["criativos"])
        budget_diario = budget_diario or OPTIMIZATION["default_daily_budget"]
        targeting = targeting or DEFAULT_TARGETING
        status = "ACTIVE" if ativar else "PAUSED"
        data_atual = datetime.now().strftime("%m/%Y")

        logger.info("=" * 50)
        logger.info(f"Iniciando criação de campanha para: {produto}")
        logger.info("=" * 50)

        resultado = {
            "produto": produto,
            "campaign_id": None,
            "adset_id": None,
            "creative_ids": [],
            "ad_ids": [],
            "imagens_enviadas": [],
            "copies_gerados": [],
        }

        # 1. Upload de criativos
        logger.info("Etapa 1: Upload de criativos")
        imagens = self.api.upload_pasta_criativos(pasta_criativos)
        resultado["imagens_enviadas"] = imagens

        if not imagens:
            logger.error("Nenhuma imagem encontrada! Abortando.")
            return resultado

        # 2. Gerar copy com IA
        logger.info("Etapa 2: Gerando copy com Ollama")
        copy = self.copy_gen.gerar_copy(
            produto=produto,
            publico=publico,
            objetivo="Vendas" if "SALES" in objetivo_campanha else "Leads",
            tom="Profissional e persuasivo"
        )
        resultado["copies_gerados"].append(copy)

        # Gerar variações para teste A/B
        variacoes = self.copy_gen.gerar_variacoes(
            headline=copy["headline"],
            texto=copy["texto_principal"]
        )
        resultado["copies_gerados"].extend(variacoes)

        # 3. Gerar nome da campanha
        logger.info("Etapa 3: Criando campanha")
        nome_campanha = self.copy_gen.gerar_nome_campanha(
            produto=produto,
            objetivo="Vendas" if "SALES" in objetivo_campanha else "Leads",
            data=data_atual
        )

        campaign = self.api.criar_campanha(
            nome=nome_campanha,
            objetivo=objetivo_campanha,
            status=status,
        )
        resultado["campaign_id"] = campaign.get_id()

        # 4. Criar AdSet
        logger.info("Etapa 4: Criando Ad Set")
        adset = self.api.criar_adset(
            campaign_id=campaign.get_id(),
            nome=f"{nome_campanha} - AdSet Principal",
            budget_diario=budget_diario,
            targeting=targeting,
            status=status,
        )
        resultado["adset_id"] = adset.get_id()

        # 5. Criar Criativos e Ads
        logger.info("Etapa 5: Criando anúncios")

        # Usar o copy principal para cada imagem
        for i, img in enumerate(imagens):
            # Selecionar copy (principal ou variação)
            copy_idx = i % len(resultado["copies_gerados"])
            copy_atual = resultado["copies_gerados"][copy_idx]

            # Se for variação, pegar do formato correto
            if isinstance(copy_atual, dict) and "headline" in copy_atual:
                headline = copy_atual["headline"]
                texto = copy_atual.get("texto_principal", copy_atual.get("texto", ""))
                descricao = copy_atual.get("descricao", "Saiba mais")
                cta = copy_atual.get("cta", "LEARN_MORE")
            else:
                headline = copy["headline"]
                texto = copy["texto_principal"]
                descricao = copy["descricao"]
                cta = copy["cta"]

            # Criar creative
            creative = self.api.criar_creative(
                nome=f"Creative - {img['nome']}",
                image_hash=img["hash"],
                headline=headline,
                texto=texto,
                descricao=descricao,
                link_url=link_url,
                cta=cta,
            )
            resultado["creative_ids"].append(creative.get_id())

            # Criar ad
            ad = self.api.criar_ad(
                nome=f"Ad - {img['nome']}",
                adset_id=adset.get_id(),
                creative_id=creative.get_id(),
                status=status,
            )
            resultado["ad_ids"].append(ad.get_id())

        logger.success("=" * 50)
        logger.success("CAMPANHA CRIADA COM SUCESSO!")
        logger.success(f"Campaign ID: {resultado['campaign_id']}")
        logger.success(f"AdSet ID: {resultado['adset_id']}")
        logger.success(f"Ads criados: {len(resultado['ad_ids'])}")
        logger.success(f"Status: {status}")
        logger.success("=" * 50)

        return resultado

    def criar_teste_ab(
        self,
        campaign_id: str,
        adset_id: str,
        produto: str,
        link_url: str,
        imagens: List[dict],
        num_variacoes: int = 3,
    ) -> List[str]:
        """
        Cria variações de anúncios para teste A/B.

        Args:
            campaign_id: ID da campanha existente
            adset_id: ID do ad set existente
            produto: Descrição do produto
            link_url: URL de destino
            imagens: Lista de imagens já enviadas
            num_variacoes: Número de variações de copy

        Returns:
            Lista de IDs dos ads criados
        """
        logger.info(f"Criando teste A/B com {num_variacoes} variações")

        # Gerar copy base
        copy_base = self.copy_gen.gerar_copy(produto=produto)

        # Gerar variações
        variacoes = self.copy_gen.gerar_variacoes(
            headline=copy_base["headline"],
            texto=copy_base["texto_principal"]
        )

        ad_ids = []

        for i, variacao in enumerate(variacoes[:num_variacoes]):
            # Usar imagem diferente para cada variação
            img = imagens[i % len(imagens)]

            creative = self.api.criar_creative(
                nome=f"AB Test - {variacao.get('tipo', i)}",
                image_hash=img["hash"],
                headline=variacao.get("headline", copy_base["headline"]),
                texto=variacao.get("texto", copy_base["texto_principal"]),
                descricao=copy_base["descricao"],
                link_url=link_url,
                cta=copy_base["cta"],
            )

            ad = self.api.criar_ad(
                nome=f"AB - {variacao.get('tipo', i)}",
                adset_id=adset_id,
                creative_id=creative.get_id(),
                status="PAUSED",
            )
            ad_ids.append(ad.get_id())

        logger.success(f"Teste A/B criado: {len(ad_ids)} variações")
        return ad_ids

    def duplicar_campanha(
        self,
        campaign_id: str,
        novo_nome: str,
        novo_targeting: dict = None,
        novo_budget: int = None,
    ) -> dict:
        """
        Duplica uma campanha existente com novas configurações.
        """
        # Obter info da campanha original
        campanhas = self.api.listar_campanhas()
        original = next((c for c in campanhas if c["id"] == campaign_id), None)

        if not original:
            raise ValueError(f"Campanha não encontrada: {campaign_id}")

        # Criar nova campanha
        nova = self.api.criar_campanha(
            nome=novo_nome,
            objetivo=original.get("objective", "OUTCOME_SALES"),
            status="PAUSED",
        )

        logger.success(f"Campanha duplicada: {novo_nome}")
        return {"campaign_id": nova.get_id()}


# Singleton
_manager = None


def get_manager() -> CampaignManager:
    """Retorna instância do manager."""
    global _manager
    if _manager is None:
        _manager = CampaignManager()
    return _manager
