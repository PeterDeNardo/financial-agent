"""
Ponto de entrada do serviço de coleta.

Por enquanto este arquivo só valida que a conexão com o banco de dados
está funcionando. Os coletores de verdade (Brapi, CoinGecko, Tesouro
Direto, etc.) serão adicionados aqui como módulos separados no próximo
passo do projeto.
"""

import os
import time

import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def wait_for_db(max_retries: int = 10, delay_seconds: int = 3) -> None:
    """Tenta conectar ao banco algumas vezes antes de desistir.

    Útil porque o container do Postgres pode ainda estar subindo
    quando este serviço inicia.
    """
    for attempt in range(1, max_retries + 1):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            print(f"[collector] Conectado ao banco com sucesso (tentativa {attempt}).")
            return
        except psycopg2.OperationalError as exc:
            print(f"[collector] Banco ainda não disponível (tentativa {attempt}): {exc}")
            time.sleep(delay_seconds)

    raise RuntimeError("Não foi possível conectar ao banco de dados após várias tentativas.")


def main() -> None:
    print("[collector] Iniciando serviço de coleta...")
    wait_for_db()

    # TODO: registrar aqui os jobs agendados (Brapi, CoinGecko, Tesouro Direto, etc.)
    print("[collector] Serviço pronto. Aguardando implementação dos coletores.")

    # Mantém o container vivo por enquanto.
    while True:
        time.sleep(60)


if __name__ == "__main__":
    main()
