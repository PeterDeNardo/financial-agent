"""
Ponto de entrada do serviço de coleta.

Implementa coleta de dados de mercado (Brapi, CoinGecko, Tesouro Direto, etc.)
com agendamento via APScheduler.
"""

import os
import time
import logging
from datetime import datetime, date
from typing import Optional, List

import psycopg2
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from coletores.db import DatabaseConnection
from coletores.coletores.brapi_collector import BrapiCollector

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
BRAPI_TOKEN = os.getenv("BRAPI_TOKEN")

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Tickers padrão para coleta
DEFAULT_TICKERS = [
    'ITUB4'
]

# Cache de feriados (atualiza 1x por ano)
FERIADOS_CACHE: List[str] = []
FERIADOS_CACHE_ANO: Optional[int] = None

# Feriados nacionais fixos (fallback)
FERIADOS_FIXOS = [
    (1, 1),    # Ano Novo
    (4, 21),   # Tiradentes
    (5, 1),    # Dia do Trabalho
    (9, 7),    # Independência
    (10, 12),  # Nossa Senhora Aparecida
    (11, 2),   # Finados
    (11, 15),  # Proclamação da República
    (11, 20),  # Consciência Negra
    (12, 25),  # Natal
]


def wait_for_db(max_retries: int = 10, delay_seconds: int = 3) -> None:
    """Tenta conectar ao banco algumas vezes antes de desistir."""
    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            logger.info(f"[collector] Conectado ao banco com sucesso (tentativa {attempt}).")
            return
        except psycopg2.OperationalError as exc:
            logger.warning(f"[collector] Banco ainda não disponível (tentativa {attempt}): {exc}")
            time.sleep(delay_seconds)

    raise RuntimeError("Não foi possível conectar ao banco de dados após várias tentativas.")


def _get_feriados_fallback(ano: int) -> List[str]:
    """Fallback com feriados nacionais brasileiros fixos."""
    feriados = [f"{ano}-{mes:02d}-{dia:02d}" for mes, dia in FERIADOS_FIXOS]
    logger.debug(f"Usando fallback: {len(feriados)} feriados fixos para {ano}")
    return feriados


def get_feriados_nacionais(ano: int) -> List[str]:
    """
    Busca feriados nacionais de um ano da API pública.
    
    Usa: https://feriadosapi.com/api/v1/feriados/nacionais
    Plano gratuito: 100 requisições/mês (1 requisição por ano = eficiente)
    
    Retorna lista de datas (YYYY-MM-DD) que são feriados nacionais.
    """
    global FERIADOS_CACHE, FERIADOS_CACHE_ANO
    
    # Se já temos cache do ano, retorna dele
    if FERIADOS_CACHE_ANO == ano and FERIADOS_CACHE:
        logger.debug(f"Usando cache de feriados para {ano}: {len(FERIADOS_CACHE)} feriados")
        return FERIADOS_CACHE
    
    try:
        logger.info(f"Consultando API de feriados nacionais para {ano}...")
        response = requests.get(
            f"https://feriadosapi.com/api/v1/feriados/nacionais?ano={ano}",
            timeout=10
        )
        
        if response.status_code != 200:
            logger.warning(f"API de feriados retornou {response.status_code}. Usando fallback.")
            return _get_feriados_fallback(ano)
        
        data = response.json()
        feriados = []
        
        # A API retorna em diferentes formatos dependendo do plano.
        # Tenta extrair as datas:
        if isinstance(data, dict) and 'feriados' in data:
            for feriado in data['feriados']:
                if 'data' in feriado:
                    feriados.append(feriado['data'])
        elif isinstance(data, list):
            for feriado in data:
                if 'data' in feriado:
                    feriados.append(feriado['data'])
        
        if not feriados:
            logger.warning("API de feriados não retornou feriados válidos. Usando fallback.")
            return _get_feriados_fallback(ano)
        
        # Cache
        FERIADOS_CACHE = feriados
        FERIADOS_CACHE_ANO = ano
        
        logger.info(f"✓ API: {len(feriados)} feriados nacionais carregados para {ano}")
        return feriados
    
    except Exception as e:
        logger.warning(f"Erro ao consultar API de feriados: {e}. Usando fallback.")
        return _get_feriados_fallback(ano)


def is_dia_util(data: date = None) -> bool:
    """
    Verifica se a data é dia útil: segunda a sexta e não é feriado nacional.
    """
    if data is None:
        data = date.today()

    # Verifica fim de semana (segunda=0 ... sexta=4, sábado=5, domingo=6)
    if data.weekday() >= 5:
        logger.debug(f"Hoje é fim de semana ({data.strftime('%A')})")
        return False

    # Verifica feriado
    feriados = get_feriados_nacionais(data.year)
    data_str = data.strftime('%Y-%m-%d')
    
    if data_str in feriados:
        logger.debug(f"Hoje é feriado nacional ({data_str})")
        return False
    
    return True


def job_brapi_collector():
    """Job agendado para coleta de dados da Brapi."""
    logger.info("[BRAPI] Iniciando coleta...")

    if not is_dia_util():
        logger.info("[BRAPI] Não é dia útil. Pulando coleta.")
        return

    if not BRAPI_TOKEN:
        logger.error("[BRAPI] BRAPI_TOKEN não configurado no .env")
        return

    try:
        with DatabaseConnection(os.getenv("DATABASE_URL")) as db:
            collector = BrapiCollector(BRAPI_TOKEN, db)
            tickers = os.getenv("BRAPI_TICKERS", "").split(",") if os.getenv("BRAPI_TICKERS") else DEFAULT_TICKERS
            logger.info(f"[collector] {tickers}")
            logger.info(f"[collector] {os.getenv("BRAPI_TICKERS", "").split(",")}")
            resultado = collector.run(tickers)
            logger.info(f"[BRAPI] Resultado: {resultado}")
    except Exception as e:
        logger.error(f"[BRAPI] Erro durante coleta: {e}", exc_info=True)


def wait_for_db(max_retries: int = 10, delay_seconds: int = 3) -> None:
    """Tenta conectar ao banco algumas vezes antes de desistir."""
    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            logger.info(f"[collector] Conectado ao banco com sucesso (tentativa {attempt}).")
            return
        except psycopg2.OperationalError as exc:
            logger.warning(f"[collector] Banco ainda não disponível (tentativa {attempt}): {exc}")
            time.sleep(delay_seconds)

    raise RuntimeError("Não foi possível conectar ao banco de dados após várias tentativas.")


def main() -> None:
    logger.info("[collector] Iniciando serviço de coleta...")
    wait_for_db()

    if not BRAPI_TOKEN:
        logger.warning("[collector] BRAPI_TOKEN não configurado - coletor Brapi desativado")

    # Executa a coleta imediatamente se COLLECT_ON_STARTUP estiver definido
    collect_on_startup = os.getenv("COLLECT_ON_STARTUP", "false").lower() == "true"
    if collect_on_startup:
        logger.info("[collector] Executando coleta de dados na inicialização...")
        try:
            job_brapi_collector()
            logger.info("[collector] Coleta na inicialização concluída")
        except Exception as e:
            logger.error(f"[collector] Erro na coleta na inicialização: {e}", exc_info=True)

    # Configurar scheduler
    scheduler = BackgroundScheduler(timezone="America/Sao_Paulo")

    # Brapi: dias úteis às 17:30 (após fechamento do mercado)
    # O job verifica is_dia_util() internamente
    scheduler.add_job(
        job_brapi_collector,
        CronTrigger(hour=17, minute=30, day_of_week='mon-fri', timezone='America/Sao_Paulo'),
        id='brapi_collector',
        name='Brapi Collector - Ações/FIIs/BDRs',
        replace_existing=True
    )

    # TODO: Adicionar outros coletores (CoinGecko, Tesouro Direto, Alpha Vantage)
    # scheduler.add_job(job_coingecko_collector, CronTrigger(hour=..., minute=...), id='coingecko_collector')
    # scheduler.add_job(job_tesouro_direto_collector, CronTrigger(hour=..., minute=...), id='tesouro_direto_collector')

    scheduler.start()
    logger.info("[collector] Scheduler iniciado. Brapi rodará de seg-sex (dias úteis) às 17:30 BRT")
    if collect_on_startup:
        logger.info("[collector] Coleta na inicialização também executada")
    logger.info("[collector] Pressione Ctrl+C para encerrar")

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("[collector] Encerrando scheduler...")
        scheduler.shutdown()
        logger.info("[collector] Encerrado com sucesso")


if __name__ == "__main__":
    main()