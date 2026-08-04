import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Gerencia conexão com PostgreSQL"""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn = None

    def connect(self):
        try:
            self.conn = psycopg2.connect(self.database_url)
            logger.debug("Conectado ao banco de dados")
        except psycopg2.OperationalError as e:
            logger.error(f"Falha ao conectar ao banco: {e}")
            raise RuntimeError(f"Falha ao conectar ao banco: {e}")

    def execute(self, query: str, params: tuple = None) -> int:
        """Executa INSERT, UPDATE, DELETE. Retorna número de linhas afetadas."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            self.conn.commit()
            rows_affected = cursor.rowcount
            cursor.close()
            return rows_affected
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            logger.warning(f"Violação de constraint: {e}")
            raise
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Erro ao executar query: {e}")
            raise

    def fetch_one(self, query: str, params: tuple = None) -> dict:
        """Retorna um resultado como dicionário, ou None."""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            cursor.close()
            return result
        except psycopg2.Error as e:
            logger.error(f"Erro ao buscar registro: {e}")
            raise

    def fetch_all(self, query: str, params: tuple = None) -> list:
        """Retorna todos os resultados como lista de dicionários."""
        try:
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params or ())
            results = cursor.fetchall()
            cursor.close()
            return results
        except psycopg2.Error as e:
            logger.error(f"Erro ao buscar registros: {e}")
            raise

    def close(self):
        if self.conn:
            self.conn.close()
            logger.debug("Conexão fechada")

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()