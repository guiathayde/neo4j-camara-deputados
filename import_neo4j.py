"""Script de importação dos arquivos JSON da pasta datasets para Neo4j.

Etapas:
1. Carrega variáveis de ambiente (.env) para URI, usuário e senha.
2. Lê cada arquivo JSON em datasets/.
3. Cria constraints (uniqueness) conforme modelo.
4. Faz MERGE dos nós (Partido, Legislatura, Deputado, Frente, Orgao, Proposicao, Votacao).
5. Cria relacionamentos conforme schema.

Uso:
    python import_neo4j.py --database neo4j --datasets-dir datasets

Requisitos:
    pip install neo4j python-dotenv

Observações:
 - Legislatura: inferida de idLegislatura presente em Deputado e Frente; será criada uma vez por ID.
 - Votacao: cria relação com Orgao via sigla (preferência) e também pode manter uri como propriedade adicional.
 - Relação Proposicao-Votacao é criada apenas quando uriProposicaoObjeto não é nula.
 - Atributos nulos são ignorados (não setados) para evitar poluição.
"""

from __future__ import annotations
import json
import argparse
from pathlib import Path
from typing import Any, Dict, List
from neo4j import GraphDatabase, Driver
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


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def create_constraints(driver: Driver, database: str):
    queries = [
        # Uniqueness constraints
        "CREATE CONSTRAINT partido_sigla IF NOT EXISTS FOR (p:Partido) REQUIRE p.sigla IS UNIQUE",
        "CREATE CONSTRAINT partido_id IF NOT EXISTS FOR (p:Partido) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT deputado_id IF NOT EXISTS FOR (d:Deputado) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT frente_id IF NOT EXISTS FOR (f:Frente) REQUIRE f.id IS UNIQUE",
        "CREATE CONSTRAINT legislatura_id IF NOT EXISTS FOR (l:Legislatura) REQUIRE l.id IS UNIQUE",
        "CREATE CONSTRAINT orgao_id IF NOT EXISTS FOR (o:Orgao) REQUIRE o.id IS UNIQUE",
        "CREATE CONSTRAINT orgao_sigla IF NOT EXISTS FOR (o:Orgao) REQUIRE o.sigla IS UNIQUE",
        "CREATE CONSTRAINT proposicao_id IF NOT EXISTS FOR (p:Proposicao) REQUIRE p.id IS UNIQUE",
        "CREATE CONSTRAINT votacao_id IF NOT EXISTS FOR (v:Votacao) REQUIRE v.id IS UNIQUE",
    ]
    for q in queries:
        driver.execute_query(q, database_=database)


def merge_partidos(driver: Driver, database: str, partidos: List[Dict[str, Any]]):
    query = """
    UNWIND $rows AS row
    MERGE (p:Partido {sigla: row.sigla})
      ON CREATE SET p.id = row.id, p.nome = row.nome, p.uri = row.uri
      ON MATCH SET p.id = row.id, p.nome = row.nome, p.uri = row.uri
    """
    driver.execute_query(query, rows=partidos, database_=database)


def merge_legislaturas(driver: Driver, database: str, legislatura_ids: List[int]):
    query = """
    UNWIND $ids AS lid
    MERGE (l:Legislatura {id: lid})
    """
    driver.execute_query(query, ids=legislatura_ids, database_=database)


def merge_deputados(driver: Driver, database: str, deputados: List[Dict[str, Any]]):
    query = """
    UNWIND $rows AS row
    MERGE (d:Deputado {id: row.id})
      ON CREATE SET d.nome = row.nome,
                    d.siglaPartido = row.siglaPartido,
                    d.uriPartido = row.uriPartido,
                    d.siglaUf = row.siglaUf,
                    d.idLegislatura = row.idLegislatura,
                    d.email = row.email,
                    d.urlFoto = row.urlFoto,
                    d.uri = row.uri
      ON MATCH SET  d.nome = row.nome,
                    d.siglaPartido = row.siglaPartido,
                    d.uriPartido = row.uriPartido,
                    d.siglaUf = row.siglaUf,
                    d.idLegislatura = row.idLegislatura,
                    d.email = row.email,
                    d.urlFoto = row.urlFoto,
                    d.uri = row.uri
    WITH d, row
    MATCH (p:Partido {sigla: row.siglaPartido})
    MERGE (p)<-[:PERTENCE_A]-(d)
    WITH d, row
    MATCH (l:Legislatura {id: row.idLegislatura})
    MERGE (d)-[:ATUA_NA_LEGISLATURA]->(l)
    """
    driver.execute_query(query, rows=deputados, database_=database)


def merge_frentes(driver: Driver, database: str, frentes: List[Dict[str, Any]]):
    query = """
    UNWIND $rows AS row
    MERGE (f:Frente {id: row.id})
      ON CREATE SET f.titulo = row.titulo, f.idLegislatura = row.idLegislatura, f.uri = row.uri
      ON MATCH SET  f.titulo = row.titulo, f.idLegislatura = row.idLegislatura, f.uri = row.uri
    WITH f, row
    MATCH (l:Legislatura {id: row.idLegislatura})
    MERGE (f)-[:DA_LEGISLATURA]->(l)
    """
    driver.execute_query(query, rows=frentes, database_=database)


def merge_orgaos(driver: Driver, database: str, orgaos: List[Dict[str, Any]]):
    query = """
    UNWIND $rows AS row
    MERGE (o:Orgao {sigla: row.sigla})
      ON CREATE SET o.id = row.id, o.nome = row.nome, o.apelido = row.apelido,
                    o.codTipoOrgao = row.codTipoOrgao, o.tipoOrgao = row.tipoOrgao,
                    o.nomePublicacao = row.nomePublicacao,
                    o.nomeResumido = row.nomeResumido, o.uri = row.uri
      ON MATCH SET  o.id = row.id, o.nome = row.nome, o.apelido = row.apelido,
                    o.codTipoOrgao = row.codTipoOrgao, o.tipoOrgao = row.tipoOrgao,
                    o.nomePublicacao = row.nomePublicacao,
                    o.nomeResumido = row.nomeResumido, o.uri = row.uri
    """
    driver.execute_query(query, rows=orgaos, database_=database)


def merge_proposicoes(driver: Driver, database: str, proposicoes: List[Dict[str, Any]]):
    query = """
    UNWIND $rows AS row
    MERGE (p:Proposicao {id: row.id})
      ON CREATE SET p.siglaTipo = row.siglaTipo, p.codTipo = row.codTipo,
                    p.numero = row.numero, p.ano = row.ano,
                    p.ementa = row.ementa, p.uri = row.uri
      ON MATCH SET  p.siglaTipo = row.siglaTipo, p.codTipo = row.codTipo,
                    p.numero = row.numero, p.ano = row.ano,
                    p.ementa = row.ementa, p.uri = row.uri
    """
    driver.execute_query(query, rows=proposicoes, database_=database)


def merge_votacoes(driver: Driver, database: str, votacoes: List[Dict[str, Any]]):
    # Filtra props nulas para não sobrescrever com None
    cleaned = []
    for v in votacoes:
        cleaned.append({k: v[k] for k in v.keys()})
    query = """
    UNWIND $rows AS row
    MERGE (v:Votacao {id: row.id})
      ON CREATE SET v.data = row.data,
                    v.dataHoraRegistro = row.dataHoraRegistro,
                    v.siglaOrgao = row.siglaOrgao,
                    v.uriOrgao = row.uriOrgao,
                    v.uriEvento = row.uriEvento,
                    v.proposicaoObjeto = row.proposicaoObjeto,
                    v.uriProposicaoObjeto = row.uriProposicaoObjeto,
                    v.descricao = row.descricao,
                    v.aprovacao = row.aprovacao,
                    v.uri = row.uri
      ON MATCH SET  v.data = row.data,
                    v.dataHoraRegistro = row.dataHoraRegistro,
                    v.siglaOrgao = row.siglaOrgao,
                    v.uriOrgao = row.uriOrgao,
                    v.uriEvento = row.uriEvento,
                    v.proposicaoObjeto = row.proposicaoObjeto,
                    v.uriProposicaoObjeto = row.uriProposicaoObjeto,
                    v.descricao = row.descricao,
                    v.aprovacao = row.aprovacao,
                    v.uri = row.uri
    WITH v, row
    MATCH (o:Orgao {sigla: row.siglaOrgao})
    MERGE (o)-[:REALIZA]->(v)
    WITH v, row
    OPTIONAL MATCH (p:Proposicao {uri: row.uriProposicaoObjeto})
    WITH v, p, row
    WHERE p IS NOT NULL AND row.uriProposicaoObjeto IS NOT NULL
    MERGE (p)-[:REFERENCIADA_EM]->(v)
    RETURN count(v) AS votacoes_processadas
    """
    driver.execute_query(query, rows=cleaned, database_=database)


def parse_args():
    ap = argparse.ArgumentParser(description="Importa datasets JSON para Neo4j")
    ap.add_argument("--datasets-dir", default="datasets", help="Diretório dos arquivos JSON")
    ap.add_argument("--database", default="neo4j", help="Nome do database Neo4j")
    return ap.parse_args()


def main():
    args = parse_args()
    env = load_env()
    datasets_path = Path(args.datasets_dir)
    if not datasets_path.exists():
        raise FileNotFoundError(f"Diretório {datasets_path} não encontrado")

    # Lê arquivos
    deputados = read_json(datasets_path / "deputados.json")['dados']
    frentes = read_json(datasets_path / "frentes.json")['dados']
    orgaos = read_json(datasets_path / "orgaos.json")['dados']
    partidos = read_json(datasets_path / "partidos.json")['dados']
    proposicoes = read_json(datasets_path / "proposicoes.json")['dados']
    votacoes = read_json(datasets_path / "votacoes.json")['dados']

    legislatura_ids = sorted({d['idLegislatura'] for d in deputados} | {f['idLegislatura'] for f in frentes})

    print(f"Deputados: {len(deputados)} | Frentes: {len(frentes)} | Orgaos: {len(orgaos)} | Partidos: {len(partidos)} | Proposicoes: {len(proposicoes)} | Votacoes: {len(votacoes)} | Legislaturas: {len(legislatura_ids)}")

    auth = (env['user'], env['password'])
    with GraphDatabase.driver(env['uri'], auth=auth) as driver:
        driver.verify_connectivity()
        print("Conectado ao Neo4j. Criando constraints...")
        create_constraints(driver, args.database)
        print("Importando Partidos...")
        merge_partidos(driver, args.database, partidos)
        print("Importando Legislaturas...")
        merge_legislaturas(driver, args.database, legislatura_ids)
        print("Importando Deputados...")
        merge_deputados(driver, args.database, deputados)
        print("Importando Frentes...")
        merge_frentes(driver, args.database, frentes)
        print("Importando Órgãos...")
        merge_orgaos(driver, args.database, orgaos)
        print("Importando Proposições...")
        merge_proposicoes(driver, args.database, proposicoes)
        print("Importando Votações...")
        merge_votacoes(driver, args.database, votacoes)
        print("Importação concluída.")


if __name__ == "__main__":
    main()
