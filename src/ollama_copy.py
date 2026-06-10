"""
Gerador de Copy com Ollama (IA Local Gratuita)
"""
import json
import ollama
from loguru import logger
from config.settings import OLLAMA_CONFIG
from templates.prompts import (
    COPY_GENERATOR,
    COPY_VARIATIONS,
    ANALYZE_PERFORMANCE,
    AUDIENCE_GENERATOR,
    CAMPAIGN_NAME,
)


class OllamaCopyGenerator:
    """Gera copies de anúncios usando Ollama (100% gratuito)."""

    def __init__(self):
        self.model = OLLAMA_CONFIG["model"]
        self.host = OLLAMA_CONFIG["host"]
        self._check_ollama()

    def _check_ollama(self):
        """Verifica se Ollama está rodando."""
        try:
            ollama.list()
            logger.info(f"Ollama conectado. Modelo: {self.model}")
        except Exception as e:
            logger.error(f"Ollama não está rodando: {e}")
            logger.info("Execute: ollama serve")
            raise ConnectionError("Inicie o Ollama com: ollama serve")

    def _generate(self, prompt: str) -> str:
        """Gera texto com Ollama."""
        try:
            response = ollama.generate(
                model=self.model,
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "top_p": 0.9,
                }
            )
            return response["response"].strip()
        except Exception as e:
            logger.error(f"Erro ao gerar com Ollama: {e}")
            raise

    def _parse_json(self, text: str) -> dict:
        """Extrai JSON da resposta."""
        try:
            # Tentar encontrar JSON na resposta
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
            raise ValueError("JSON não encontrado")
        except json.JSONDecodeError as e:
            logger.warning(f"Erro ao parsear JSON: {e}")
            logger.debug(f"Resposta: {text}")
            return {}

    def gerar_copy(
        self,
        produto: str,
        publico: str = "Público geral",
        objetivo: str = "Vendas",
        tom: str = "Profissional e persuasivo"
    ) -> dict:
        """
        Gera copy completo para anúncio.

        Args:
            produto: Nome/descrição do produto
            publico: Público-alvo
            objetivo: Objetivo da campanha
            tom: Tom de voz desejado

        Returns:
            dict com headline, texto_principal, descricao, cta
        """
        prompt = COPY_GENERATOR.format(
            produto=produto,
            publico=publico,
            objetivo=objetivo,
            tom=tom
        )

        logger.info(f"Gerando copy para: {produto}")
        response = self._generate(prompt)
        result = self._parse_json(response)

        if not result:
            # Fallback com valores padrão
            logger.warning("Usando copy padrão")
            result = {
                "headline": f"Conheça {produto[:30]}",
                "texto_principal": f"Descubra {produto}. Aproveite agora!",
                "descricao": "Saiba mais",
                "cta": "LEARN_MORE"
            }

        logger.success(f"Copy gerado: {result.get('headline', 'N/A')}")
        return result

    def gerar_variacoes(self, headline: str, texto: str) -> list:
        """
        Gera variações do copy para teste A/B.

        Returns:
            Lista com 3 variações
        """
        prompt = COPY_VARIATIONS.format(headline=headline, texto=texto)
        response = self._generate(prompt)
        result = self._parse_json(response)
        return result.get("variacoes", [])

    def analisar_performance(self, metricas: dict, copy_atual: str) -> dict:
        """
        Analisa performance e sugere melhorias.

        Args:
            metricas: Dict com impressoes, cliques, ctr, cpc, conversoes, cpa, roas, gasto
            copy_atual: Copy sendo usado atualmente

        Returns:
            Dict com diagnóstico e recomendações
        """
        prompt = ANALYZE_PERFORMANCE.format(
            impressoes=metricas.get("impressoes", 0),
            cliques=metricas.get("cliques", 0),
            ctr=metricas.get("ctr", 0),
            cpc=metricas.get("cpc", 0),
            conversoes=metricas.get("conversoes", 0),
            cpa=metricas.get("cpa", 0),
            roas=metricas.get("roas", 0),
            gasto=metricas.get("gasto", 0),
            copy_atual=copy_atual
        )
        response = self._generate(prompt)
        return self._parse_json(response)

    def sugerir_publico(self, produto: str, descricao: str) -> dict:
        """
        Sugere segmentação de público baseado no produto.
        """
        prompt = AUDIENCE_GENERATOR.format(produto=produto, descricao=descricao)
        response = self._generate(prompt)
        return self._parse_json(response)

    def gerar_nome_campanha(self, produto: str, objetivo: str, data: str) -> str:
        """
        Gera nome para a campanha.
        """
        prompt = CAMPAIGN_NAME.format(produto=produto, objetivo=objetivo, data=data)
        return self._generate(prompt)[:50]


# Singleton para uso global
_generator = None


def get_generator() -> OllamaCopyGenerator:
    """Retorna instância do gerador."""
    global _generator
    if _generator is None:
        _generator = OllamaCopyGenerator()
    return _generator


if __name__ == "__main__":
    # Teste rápido
    gen = OllamaCopyGenerator()
    copy = gen.gerar_copy(
        produto="Curso de Marketing Digital",
        publico="Empreendedores 25-45 anos",
        objetivo="Vendas",
        tom="Inspirador e urgente"
    )
    print(json.dumps(copy, indent=2, ensure_ascii=False))
