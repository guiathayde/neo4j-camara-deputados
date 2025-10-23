## Google Colab

https://colab.research.google.com/drive/17Cnqr6ztRZsKwyipFVyQ7INCbIP3_UHI?usp=sharing

## Como rodar

### Pré-requisitos

- Python 3.8 ou superior
- Neo4j Aura (conta gratuita) ou Neo4j Desktop
- Bibliotecas Python: `neo4j`, `python-dotenv`

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto com as credenciais do Neo4j:

```env
NEO4J_URI=neo4j+s://seu-id.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=sua-senha-aqui
NEO4J_DATABASE=neo4j
```

### 3. Coletar os dados (opcional)

Os dados já estão disponíveis na pasta `datasets/`, mas se quiser coletá-los novamente:

```bash
cd datasets
curl -s -H "Content-Type: application/json" https://dadosabertos.camara.leg.br/api/v2/deputados | jq '.' > deputados.json
curl -s -H "Content-Type: application/json" https://dadosabertos.camara.leg.br/api/v2/proposicoes | jq '.' > proposicoes.json
curl -s -H "Content-Type: application/json" https://dadosabertos.camara.leg.br/api/v2/votacoes | jq '.' > votacoes.json
curl -s -H "Content-Type: application/json" https://dadosabertos.camara.leg.br/api/v2/orgaos | jq '.' > orgaos.json
curl -s -H "Content-Type: application/json" https://dadosabertos.camara.leg.br/api/v2/partidos | jq '.' > partidos.json
curl -s -H "Content-Type: application/json" https://dadosabertos.camara.leg.br/api/v2/frentes | jq '.' > frentes.json
cd ..
```

### 4. Importar dados para o Neo4j

```bash
python import_neo4j.py
```

Este script irá:

- Criar constraints de unicidade
- Importar todos os dados JSON
- Criar relacionamentos entre nós

### 5. Executar consultas

Você pode executar as consultas de duas formas:

**Opção 1: Via Python**

```bash
python main.py
```

**Opção 2: Via Jupyter Notebook**

```bash
jupyter notebook main.ipynb
```
