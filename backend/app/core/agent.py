import os
from functools import lru_cache
from typing import Dict, Any, List

import openai
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore

from ..config import settings


class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, client=None, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, client=client, config=config)


class DBAgent:
    """
    DBAgent is a class that integrates with Vanna to provide database agent functionalities.
    It uses the MyVanna class to interact with the Vanna framework, which combines OpenAI's chat capabilities with ChromaDB for vector storage.
    """

    def __init__(self, dbname: str):
        """
        Initializes the DBAgent with a specific database name.

        Args:
            dbname (str): The name of the database to connect to.
        """
        self.dbname = dbname
        self.is_trained = False
        client = openai.Client(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE
        )
        # Set cache path for this specific database
        cache_path = os.path.join("databases", dbname, "cache")
        os.makedirs(cache_path, exist_ok=True)
        
        self.vn = MyVanna(
            client=client,
            config={
                'model': settings.LLM_MODEL,
                'temperature': settings.LLM_TEMPERATURE,
                'max_tokens': settings.LLM_MAX_TOKENS,
                'path': cache_path
            }
        )
        self.vn.connect_to_sqlite(os.path.join("databases", dbname, f"{dbname}.db"))
        self.train()
        self.last_generated_sql = None

    def train(self):
        """
        Trains the DBAgent using schema information and optional training data.
        """
        import json
        
        # Load schema.json for DDL training
        schema_path = os.path.join("databases", self.dbname, "schema.json")
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
            
            # Train with DDL statements from schema.json
            for table_name, create_sql in schema_data.get("tables", {}).items():
                self.vn.train(ddl=create_sql)

            for item in schema_data.get("sql", []):
                self.vn.train(sql = item.get("sql", ""), question = item.get("question", ""))
            print(f"✅ Loaded DDL training data from schema.json for {len(schema_data.get('tables', {}))} tables.")
        
        print("✅ DBAgent training completed successfully.")
        self.is_trained = True

    def suggest_question(self) -> list[str]:
        """ Suggests questions based on the trained data."""
        return  self.vn.generate_questions()

    def ask(self, question: str) -> dict:
        """
        Asks a question to the DBAgent and returns the response.

        Args:
            question (str): The question to ask the DBAgent.

        Returns:
            dict: The response from the DBAgent.
        """
        if not self.is_trained:
            raise RuntimeError("DBAgent is not trained yet. Please call train() method first.")

        sql = self.vn.generate_sql(question, allow_llm_to_see_data = True)
        self.last_generated_sql = sql
        data = self.vn.run_sql(sql)
        return {
            "sql": sql,
            "data": data
        }



@lru_cache(maxsize = 100)
def get_dbagent(dbname: str) -> DBAgent:
    """
    Returns a DBAgent instance for the specified database name.

    Args:
        dbname (str): The name of the database.

    Returns:
        DBAgent: An instance of DBAgent for the specified database.
    """
    return DBAgent(dbname)