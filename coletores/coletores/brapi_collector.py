import requests
import logging
from datetime import datetime, date
from typing import Optional, Dict, List
import time

from coletores.db import DatabaseConnection

logger = logging.getLogger(__name__)


class BrapiAPIError(Exception):
    pass


class BrapiCollector:
    """Coletor de dados da API Brapi (Ações B3, FIIs, BDRs)"""

    BASE_URL = "https://brapi.dev/api/v2/stocks/quote?symbols="
    TIMEOUT = 30
    MAX_RETRIES = 3

    def __init__(self, api_token: str, db_connection: Optional[DatabaseConnection]):
        if not api_token:
            raise ValueError("API token não pode ser vazio")

        self.api_token = api_token
        self.db = db_connection
        logger.info("BrapiCollector inicializado")

    def get_tipos_for_tickers(self, tickers: List[str]) -> Dict[str, str]:
        """
        Determina tipo de cada ticker:
        - Termina com "11" → FII
        - Contém "34" → BDR
        - Senão → ação
        """
        tipos = {}
        for ticker in tickers:
            if ticker.endswith('11'):
                tipos[ticker] = 'fii'
            elif '34' in ticker:
                tipos[ticker] = 'bdr'
            else:
                tipos[ticker] = 'acao'

        logger.debug(f"Tipos determinados: {tipos}")
        return tipos

    def fetch_quotes(self, tickers: List[str]) -> Dict:
        """Busca cotações da API Brapi com retry automático"""
        tickers_str = "".join(tickers)
        url = f"{self.BASE_URL}{tickers_str}"
        logger.info(f"{url}")
        logger.info(f"{self.TIMEOUT}")
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logger.debug(f"[Tentativa {attempt}/{self.MAX_RETRIES}] GET {url}")

                response = requests.get(
                    url,
                    params={'token': self.api_token},
                    timeout=self.TIMEOUT
                )

                # Rate limit (429)
                if response.status_code == 429:
                    wait_time = 60
                    logger.warning(f"Rate limit. Aguardando {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                # Outros erros HTTP
                if response.status_code != 200:
                    raise BrapiAPIError(f"Status {response.status_code}: {response.text}")

                # Parse JSON
                try:
                    data = response.json()
                except ValueError as e:
                    raise BrapiAPIError(f"Resposta não é JSON: {e}")

                # Validar resposta
                if 'results' not in data:
                    raise BrapiAPIError(f"Resposta inesperada: {data}")

                logger.info(f"Sucesso: {len(data.get('results', []))} resultados")
                return data

            except requests.Timeout:
                logger.warning(f"Timeout na tentativa {attempt}")
                if attempt < self.MAX_RETRIES:
                    backoff = 2 ** (attempt - 1)
                    time.sleep(backoff)

            except BrapiAPIError as e:
                logger.error(f"Erro na API (tentativa {attempt}): {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(2 ** (attempt - 1))

        raise BrapiAPIError(f"Falhou após {self.MAX_RETRIES} tentativas")

    def insert_or_update_ativos(self, results: List[Dict]) -> Dict[str, Dict]:
        """Insere ou atualiza ativos na tabela"""
        if not self.db:
            raise RuntimeError("Database connection não configurada")

        tipos = self.get_tipos_for_tickers([r['symbol'] for r in results])
        ativo_map = {}

        for result in results:
            ticker = result['symbol']
            data_obj = result.get('data', {})
            nome = data_obj.get('longName', '')
            tipo = tipos[ticker]
            setor = data_obj.get('sector')

            # Verificar se existe
            existing = self.db.fetch_one(
                "SELECT id FROM ativos WHERE ticker = %s",
                (ticker,)
            )

            if existing:
                # UPDATE
                self.db.execute(
                    "UPDATE ativos SET nome = %s, setor = %s WHERE ticker = %s",
                    (nome, setor, ticker)
                )
                ativo_map[ticker] = {'id': existing['id'], 'acao': 'update'}
                logger.debug(f"Ativo {ticker} atualizado")
            else:
                # INSERT
                self.db.execute(
                    "INSERT INTO ativos (ticker, nome, tipo, setor, moeda) VALUES (%s, %s, %s, %s, 'BRL')",
                    (ticker, nome, tipo, setor)
                )
                novo_ativo = self.db.fetch_one(
                    "SELECT id FROM ativos WHERE ticker = %s",
                    (ticker,)
                )
                ativo_map[ticker] = {'id': novo_ativo['id'], 'acao': 'insert'}
                logger.debug(f"Ativo {ticker} inserido (ID: {novo_ativo['id']})")

        return ativo_map

    def insert_or_update_precos(self, results: List[Dict], ativo_map: Dict[str, Dict]) -> int:
        """Insere ou atualiza preços históricos"""
        if not self.db:
            raise RuntimeError("Database connection não configurada")

        count = 0

        for result in results:
            ticker = result['symbol']
            ativo_id = ativo_map[ticker]['id']

            # Parse data - usar regularMarketTime do objeto data
            data_obj = result.get('data', {})
            priced_at = data_obj.get('regularMarketTime')
            try:
                data = datetime.strptime(priced_at, '%Y-%m-%dT%H:%M:%S.%fZ').date()
            except (ValueError, TypeError):
                logger.warning(f"Data inválida para {ticker}: {priced_at}")
                continue

            abertura = data_obj.get('regularMarketOpen')
            fechamento = data_obj.get('regularMarketPrice')
            maxima = data_obj.get('regularMarketDayHigh')
            minima = data_obj.get('regularMarketDayLow')
            volume = data_obj.get('regularMarketVolume')

            try:
                # INSERT
                self.db.execute(
                    "INSERT INTO precos_historicos (ativo_id, data, abertura, fechamento, maxima, minima, volume, fonte) VALUES (%s, %s, %s, %s, %s, %s, %s, 'brapi')",
                    (ativo_id, data, abertura, fechamento, maxima, minima, volume)
                )
                count += 1
                logger.debug(f"Preço inserido: {ticker} em {data}")

            except Exception as e:
                # UPDATE se já existe
                if 'duplicate' in str(e).lower() or 'unique' in str(e).lower():
                    try:
                        self.db.execute(
                            "UPDATE precos_historicos SET abertura=%s, fechamento=%s, maxima=%s, minima=%s, volume=%s WHERE ativo_id=%s AND data=%s",
                            (abertura, fechamento, maxima, minima, volume, ativo_id, data)
                        )
                        count += 1
                        logger.debug(f"Preço atualizado: {ticker} em {data}")
                    except Exception as update_error:
                        logger.error(f"Erro ao atualizar {ticker}: {update_error}")
                else:
                    logger.error(f"Erro ao inserir preço {ticker}: {e}")

        return count

    def run(self, tickers: List[str]) -> Dict:
        """Executa a coleta completa"""
        data_inicio = datetime.utcnow().isoformat() + 'Z'

        try:
            logger.info(f"Iniciando coleta de {len(tickers)} tickers")

            # Buscar dados da API
            api_response = self.fetch_quotes(tickers)
            results = api_response.get('results', [])

            if not results:
                return {
                    'status': 'erro',
                    'data_execucao': data_inicio,
                    'mensagem': 'API retornou lista vazia'
                }

            logger.info(f"API retornou {len(results)} resultados")

            # Inserir/atualizar ativos
            ativo_map = self.insert_or_update_ativos(results)
            ativos_novos = sum(1 for v in ativo_map.values() if v['acao'] == 'insert')
            ativos_atualizados = sum(1 for v in ativo_map.values() if v['acao'] == 'update')

            logger.info(f"Ativos: {ativos_novos} novos, {ativos_atualizados} atualizados")

            # Inserir/atualizar preços
            precos_inseridos = self.insert_or_update_precos(results, ativo_map)
            logger.info(f"Preços: {precos_inseridos} inseridos/atualizados")

            return {
                'status': 'sucesso',
                'data_execucao': data_inicio,
                'ativos_novos': ativos_novos,
                'ativos_atualizados': ativos_atualizados,
                'precos_inseridos': precos_inseridos
            }

        except Exception as e:
            logger.error(f"Erro durante execução: {e}", exc_info=True)
            return {
                'status': 'erro',
                'data_execucao': data_inicio,
                'mensagem': str(e)
            }