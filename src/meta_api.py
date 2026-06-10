"""
Integração com Meta Marketing API
"""
import os
from pathlib import Path
from typing import List, Optional
from loguru import logger

from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.campaign import Campaign
from facebook_business.adobjects.adset import AdSet
from facebook_business.adobjects.ad import Ad
from facebook_business.adobjects.adimage import AdImage
from facebook_business.adobjects.adcreative import AdCreative
from facebook_business.adobjects.advideo import AdVideo

from config.settings import META_CONFIG, SUPPORTED_IMAGES, SUPPORTED_VIDEOS


class MetaAdsAPI:
    """Gerencia conexão e operações com Meta Ads API."""

    def __init__(self):
        self._init_api()
        self.account = AdAccount(f"act_{META_CONFIG['ad_account_id']}")
        logger.info(f"Conectado à conta: act_{META_CONFIG['ad_account_id']}")

    def _init_api(self):
        """Inicializa a API do Facebook."""
        FacebookAdsApi.init(
            app_id=META_CONFIG["app_id"],
            app_secret=META_CONFIG["app_secret"],
            access_token=META_CONFIG["access_token"],
        )

    # ==================== UPLOAD DE CRIATIVOS ====================

    def upload_imagem(self, caminho: str) -> dict:
        """
        Faz upload de uma imagem para a conta.

        Args:
            caminho: Caminho do arquivo de imagem

        Returns:
            Dict com hash e url da imagem
        """
        caminho = Path(caminho)
        if not caminho.exists():
            raise FileNotFoundError(f"Imagem não encontrada: {caminho}")

        if caminho.suffix.lower() not in SUPPORTED_IMAGES:
            raise ValueError(f"Formato não suportado: {caminho.suffix}")

        image = AdImage(parent_id=self.account.get_id())
        image[AdImage.Field.filename] = str(caminho)
        image.remote_create()

        result = {
            "hash": image[AdImage.Field.hash],
            "url": image.get(AdImage.Field.url, ""),
            "nome": caminho.name,
        }

        logger.success(f"Imagem enviada: {caminho.name} -> {result['hash']}")
        return result

    def upload_pasta_criativos(self, pasta: str) -> List[dict]:
        """
        Faz upload de todos os criativos de uma pasta.

        Args:
            pasta: Caminho da pasta com imagens

        Returns:
            Lista de dicts com info de cada imagem
        """
        pasta = Path(pasta)
        if not pasta.exists():
            raise FileNotFoundError(f"Pasta não encontrada: {pasta}")

        resultados = []
        arquivos = list(pasta.iterdir())
        imagens = [f for f in arquivos if f.suffix.lower() in SUPPORTED_IMAGES]

        logger.info(f"Encontradas {len(imagens)} imagens em {pasta}")

        for img in imagens:
            try:
                resultado = self.upload_imagem(str(img))
                resultados.append(resultado)
            except Exception as e:
                logger.error(f"Erro ao enviar {img.name}: {e}")

        logger.success(f"Upload completo: {len(resultados)}/{len(imagens)} imagens")
        return resultados

    def upload_video(self, caminho: str) -> dict:
        """
        Faz upload de um vídeo para a conta.
        """
        caminho = Path(caminho)
        if not caminho.exists():
            raise FileNotFoundError(f"Vídeo não encontrado: {caminho}")

        video = AdVideo(parent_id=self.account.get_id())
        video[AdVideo.Field.source] = str(caminho)
        video.remote_create()

        result = {
            "id": video.get_id(),
            "nome": caminho.name,
        }

        logger.success(f"Vídeo enviado: {caminho.name} -> {result['id']}")
        return result

    # ==================== CAMPANHAS ====================

    def criar_campanha(
        self,
        nome: str,
        objetivo: str = "OUTCOME_SALES",
        status: str = "PAUSED",
        budget_diario: Optional[int] = None,
    ) -> Campaign:
        """
        Cria uma nova campanha.

        Args:
            nome: Nome da campanha
            objetivo: OUTCOME_SALES, OUTCOME_LEADS, OUTCOME_AWARENESS, etc.
            status: ACTIVE ou PAUSED
            budget_diario: Budget diário em centavos (opcional, pode ser no AdSet)

        Returns:
            Objeto Campaign
        """
        params = {
            Campaign.Field.name: nome,
            Campaign.Field.objective: objetivo,
            Campaign.Field.status: status,
            Campaign.Field.special_ad_categories: [],
        }

        if budget_diario:
            params[Campaign.Field.daily_budget] = budget_diario

        campaign = self.account.create_campaign(params=params)
        logger.success(f"Campanha criada: {nome} (ID: {campaign.get_id()})")
        return campaign

    def listar_campanhas(self, status: Optional[str] = None) -> List[dict]:
        """Lista campanhas da conta."""
        fields = [
            Campaign.Field.id,
            Campaign.Field.name,
            Campaign.Field.status,
            Campaign.Field.objective,
            Campaign.Field.daily_budget,
        ]

        params = {}
        if status:
            params["filtering"] = [{"field": "status", "operator": "EQUAL", "value": status}]

        campanhas = self.account.get_campaigns(fields=fields, params=params)
        return [dict(c) for c in campanhas]

    def pausar_campanha(self, campaign_id: str):
        """Pausa uma campanha."""
        campaign = Campaign(campaign_id)
        campaign.api_update(params={Campaign.Field.status: "PAUSED"})
        logger.info(f"Campanha pausada: {campaign_id}")

    def ativar_campanha(self, campaign_id: str):
        """Ativa uma campanha."""
        campaign = Campaign(campaign_id)
        campaign.api_update(params={Campaign.Field.status: "ACTIVE"})
        logger.info(f"Campanha ativada: {campaign_id}")

    # ==================== AD SETS ====================

    def criar_adset(
        self,
        campaign_id: str,
        nome: str,
        budget_diario: int,
        targeting: dict,
        optimization_goal: str = "OFFSITE_CONVERSIONS",
        billing_event: str = "IMPRESSIONS",
        bid_strategy: str = "LOWEST_COST_WITHOUT_CAP",
        status: str = "PAUSED",
    ) -> AdSet:
        """
        Cria um Ad Set dentro de uma campanha.

        Args:
            campaign_id: ID da campanha
            nome: Nome do ad set
            budget_diario: Budget em centavos
            targeting: Dict de segmentação
            optimization_goal: Objetivo de otimização
            billing_event: Evento de cobrança
            bid_strategy: Estratégia de lance
            status: ACTIVE ou PAUSED
        """
        params = {
            AdSet.Field.name: nome,
            AdSet.Field.campaign_id: campaign_id,
            AdSet.Field.daily_budget: budget_diario,
            AdSet.Field.targeting: targeting,
            AdSet.Field.optimization_goal: optimization_goal,
            AdSet.Field.billing_event: billing_event,
            AdSet.Field.bid_strategy: bid_strategy,
            AdSet.Field.status: status,
        }

        adset = self.account.create_ad_set(params=params)
        logger.success(f"AdSet criado: {nome} (ID: {adset.get_id()})")
        return adset

    def listar_adsets(self, campaign_id: str) -> List[dict]:
        """Lista ad sets de uma campanha."""
        campaign = Campaign(campaign_id)
        fields = [
            AdSet.Field.id,
            AdSet.Field.name,
            AdSet.Field.status,
            AdSet.Field.daily_budget,
        ]
        adsets = campaign.get_ad_sets(fields=fields)
        return [dict(a) for a in adsets]

    # ==================== CRIATIVOS E ADS ====================

    def criar_creative(
        self,
        nome: str,
        image_hash: str,
        headline: str,
        texto: str,
        descricao: str,
        link_url: str,
        cta: str = "LEARN_MORE",
    ) -> AdCreative:
        """
        Cria um criativo de anúncio.

        Args:
            nome: Nome do criativo
            image_hash: Hash da imagem (do upload)
            headline: Título do anúncio
            texto: Texto principal
            descricao: Descrição do link
            link_url: URL de destino
            cta: Call to action
        """
        params = {
            AdCreative.Field.name: nome,
            AdCreative.Field.object_story_spec: {
                "page_id": META_CONFIG["page_id"],
                "link_data": {
                    "image_hash": image_hash,
                    "link": link_url,
                    "message": texto,
                    "name": headline,
                    "description": descricao,
                    "call_to_action": {"type": cta},
                },
            },
        }

        creative = self.account.create_ad_creative(params=params)
        logger.success(f"Creative criado: {nome} (ID: {creative.get_id()})")
        return creative

    def criar_ad(
        self,
        nome: str,
        adset_id: str,
        creative_id: str,
        status: str = "PAUSED",
    ) -> Ad:
        """
        Cria um anúncio.

        Args:
            nome: Nome do anúncio
            adset_id: ID do ad set
            creative_id: ID do criativo
            status: ACTIVE ou PAUSED
        """
        params = {
            Ad.Field.name: nome,
            Ad.Field.adset_id: adset_id,
            Ad.Field.creative: {"creative_id": creative_id},
            Ad.Field.status: status,
        }

        ad = self.account.create_ad(params=params)
        logger.success(f"Anúncio criado: {nome} (ID: {ad.get_id()})")
        return ad

    # ==================== MÉTRICAS ====================

    def obter_insights(
        self,
        object_id: str,
        object_type: str = "campaign",
        date_preset: str = "last_7d",
    ) -> dict:
        """
        Obtém métricas de performance.

        Args:
            object_id: ID da campanha, adset ou ad
            object_type: 'campaign', 'adset' ou 'ad'
            date_preset: last_7d, last_30d, today, yesterday, etc.
        """
        if object_type == "campaign":
            obj = Campaign(object_id)
        elif object_type == "adset":
            obj = AdSet(object_id)
        else:
            obj = Ad(object_id)

        fields = [
            "impressions",
            "clicks",
            "ctr",
            "cpc",
            "spend",
            "actions",
            "cost_per_action_type",
            "purchase_roas",
        ]

        insights = obj.get_insights(
            fields=fields,
            params={"date_preset": date_preset}
        )

        if not insights:
            return {}

        data = dict(insights[0])

        # Processar conversões e CPA
        conversoes = 0
        cpa = 0
        if "actions" in data:
            for action in data["actions"]:
                if action["action_type"] in ["purchase", "lead", "complete_registration"]:
                    conversoes += int(action["value"])

        if "cost_per_action_type" in data:
            for cost in data["cost_per_action_type"]:
                if cost["action_type"] in ["purchase", "lead"]:
                    cpa = float(cost["value"])
                    break

        return {
            "impressoes": int(data.get("impressions", 0)),
            "cliques": int(data.get("clicks", 0)),
            "ctr": float(data.get("ctr", 0)),
            "cpc": float(data.get("cpc", 0)),
            "gasto": float(data.get("spend", 0)),
            "conversoes": conversoes,
            "cpa": cpa,
            "roas": float(data.get("purchase_roas", [{}])[0].get("value", 0)) if data.get("purchase_roas") else 0,
        }


# Singleton
_api = None


def get_api() -> MetaAdsAPI:
    """Retorna instância da API."""
    global _api
    if _api is None:
        _api = MetaAdsAPI()
    return _api


if __name__ == "__main__":
    # Teste de conexão
    from config.settings import validate_config
    validate_config()
    api = MetaAdsAPI()
    print("Conexão OK!")
    print("Campanhas:", api.listar_campanhas())
