from neo4j import GraphDatabase
from typing import Dict
from dotenv import load_dotenv
import os


def load_env() -> Dict[str, str]:
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    if not all([uri, user, password]):
        raise RuntimeError("Variáveis de ambiente NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD são obrigatórias.")
    return {"uri": uri, "user": user, "password": password}

driver = None  # Inicializa a variável do driver

try:
    env = load_env()
    driver = GraphDatabase.driver(env['uri'], auth=(env['user'], env['password']))
    # Verifica se a conexão foi bem-sucedida
    driver.verify_connectivity()
    print("Conexão com o Neo4j Aura bem-sucedida!")

    query = """
    OPTIONAL MATCH (n)-[r]->(m)
    RETURN n, r, m
    """

    print("\nBuscando todos os dados no banco...")
    records, summary, keys = driver.execute_query(query, database_="neo4j")

    if not records:
        print("O banco de dados parece estar vazio.")
    else:
        print("\n--- Dados Encontrados ---")
        for i, record in enumerate(records):
            node_n = record["n"]
            relationship_r = record["r"]
            node_m = record["m"]

            print(f"\nRegistro {i+1}:")

            if node_n:
                # Mostra o tipo do nó (label) e suas propriedades
                print(f"  Nó de Origem (n): Labels={list(node_n.labels)}, Propriedades={dict(node_n)}")

            if relationship_r:
                # Mostra o tipo da relação e suas propriedades
                print(f"  Relação (r): Tipo='{relationship_r.type}', Propriedades={dict(relationship_r)}")

            if node_m:
                 # Mostra o tipo do nó e suas propriedades
                print(f"  Nó de Destino (m): Labels={list(node_m.labels)}, Propriedades={dict(node_m)}")
        print("\n--- Fim dos Dados ---")


except Exception as e:
    print(f"Ocorreu um erro: {e}")

finally:
    if driver is not None:
        driver.close()
        print("\nConexão fechada.")
