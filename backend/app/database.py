"""
Database Connections & Sessions
Initializes mock connections for PostgreSQL (via SQLAlchemy SQLite fallback), Neo4j (Graph), and Elasticsearch.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Default fallback to sqlite local for simple deployment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cyberthreatforge.db")

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Optional Neo4j import – fallback if not installed
try:
    from neo4j import GraphDatabase
except ImportError:
    GraphDatabase = None  # type: ignore
# Optional ChromaDB import – fallback if not installed
try:
    import chromadb
except ImportError:
    chromadb = None  # type: ignore

# Real Neo4j Integration
class GraphDB:
    def __init__(self):
        if GraphDatabase is None:
            # Neo4j driver not available; use mock fallback
            self.driver = None
            return
        uri = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "cyberthreatforge2026")
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            print(f"GraphDB Connection Warning: {e}. Falling back to mock data.")
            self.driver = None

    def get_threat_actor_network(self, actor_name: str):
        if not self.driver:
            # Fallback mock for local development without docker
            return {
                "actor": actor_name,
                "nodes": [{"id": "Actor", "label": actor_name, "type": "actor"}],
                "links": []
            }
        
        with self.driver.session() as session:
            # Stub for real query execution once data is seeded
            return {
                "actor": actor_name,
                "nodes": [{"id": "Actor", "label": actor_name, "type": "actor"}],
                "links": []
            }

    def close(self):
        if self.driver:
            self.driver.close()

# ChromaDB Integration (Replacing Elasticsearch for Vector Search)
class VectorDBClient:
    def __init__(self):
        if chromadb is None:
            # ChromaDB library not available; use mock client
            self.client = None
            return
        try:
            # Attempt to connect to ChromaDB container
            chroma_host = os.getenv("CHROMA_HOST", "chromadb")
            self.client = chromadb.HttpClient(host=chroma_host, port=8000)
            self.collection = self.client.get_or_create_collection(name="threat_intel")
        except Exception as e:
            print(f"VectorDB Connection Warning: {e}. Falling back to mock data.")
            self.client = None

    def search_threat_intel(self, query: str):
        if not self.client:
            return [{"id": "doc_102", "source": "threat_intel_feed", "content": f"Threat actor groups targeting government institutes using compromised certificate markers matching '{query}'.", "relevance": 0.94}]
        
        results = self.collection.query(
            query_texts=[query],
            n_results=1
        )
        # Mocking format matching the original Elasticsearch structure
        if results and results['documents'] and len(results['documents'][0]) > 0:
            return [{"id": results['ids'][0][0], "source": "vector_db", "content": results['documents'][0][0], "relevance": 1.0 - results['distances'][0][0]}]
        return []

graph_db = GraphDB()
elasticsearch_client = VectorDBClient()  # Kept variable name for backward compatibility with routes
