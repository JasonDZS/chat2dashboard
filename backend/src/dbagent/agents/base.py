import os
from functools import lru_cache
from typing import Dict, Any, List

import pandas as pd
import openai
from vanna.openai import OpenAI_Chat
from vanna.chromadb import ChromaDB_VectorStore

from ..html_generator.models import ProcessedData, DataPoint, ChartType

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
            api_key = "sk-MZH2vaMPWT5HKQNcATFM", base_url = "http://litellm.5gunicom.cn:5002/v1"
        )
        # Set cache path for this specific database
        cache_path = os.path.join("databases", dbname, "cache")
        os.makedirs(cache_path, exist_ok=True)
        
        self.vn = MyVanna(
            client=client,
            config = {
                'model': 'Qwen/Qwen2.5-72B-Instruct',
                'temperature': 0.0,
                'max_tokens': 2048,
                'path': cache_path
            }
        )
        self.vn.connect_to_sqlite(os.path.join("databases", dbname, f"{dbname}.db"))
        self.train()

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
        data = self.vn.run_sql(sql)
        return {
            "sql": sql,
            "data": data
        }

    def to_processed_data(self, question: str, chart_type: str = "bar") -> ProcessedData:
        """
        Converts DBAgent query result to ProcessedData format for HTML generation.

        Args:
            question (str): The question to ask the DBAgent.
            chart_type (str): The chart type to use ("bar", "line", "pie", "scatter", "area").

        Returns:
            ProcessedData: Formatted data ready for HTML generation.
        """
        result = self.ask(question)
        df = result["data"]
        
        # Convert DataFrame to DataPoint list
        sample_data = []
        
        if isinstance(df, pd.DataFrame) and not df.empty:
            # Get column names
            columns = df.columns.tolist()
            
            if len(columns) >= 2:
                # Use first column as name/x and second as value/y
                name_col, value_col = columns[0], columns[1]
                
                for _, row in df.iterrows():
                    sample_data.append(DataPoint(
                        name=str(row[name_col]),
                        value=float(row[value_col]) if pd.notna(row[value_col]) else 0.0
                    ))
            elif len(columns) == 1:
                # Single column - use index as name and column as value
                value_col = columns[0]
                for idx, row in df.iterrows():
                    sample_data.append(DataPoint(
                        name=str(idx),
                        value=float(row[value_col]) if pd.notna(row[value_col]) else 0.0
                    ))
        
        # Validate chart_type
        try:
            chart_type_enum = ChartType(chart_type.lower())
        except ValueError:
            chart_type_enum = ChartType.BAR
        print(chart_type_enum, sample_data, question)
        return ProcessedData(
            chart_type=chart_type_enum,
            sample_data=sample_data,
            original_query=question
        )


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