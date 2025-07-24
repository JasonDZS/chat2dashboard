import os
import json
import sqlite3
import datetime
from typing import List, Dict, Any, Tuple
from fastapi import UploadFile

try:
    import pandas as pd
    import openpyxl
    XLSX_SUPPORT = True
except ImportError as e:
    XLSX_SUPPORT = False
    IMPORT_ERROR = str(e)

from ..config import settings
from ..models.responses import TableInfo, DatabaseInfo, TableSchema, ColumnInfo, DatabaseSchema
from .exceptions import (
    PandasNotAvailableError, 
    UnsupportedFileTypeError, 
    DatabaseNotFoundError,
    SchemaNotFoundError
)

class DatabaseManager:
    
    @staticmethod
    def create_database_from_files(files: List[UploadFile], db_name: str) -> Tuple[List[TableInfo], str]:
        """Create SQLite database from xlsx or csv files"""
        # Check if we need pandas for any file type
        needs_pandas = any(file.filename.endswith(('.xlsx', '.csv')) for file in files)
        if needs_pandas and not XLSX_SUPPORT:
            raise PandasNotAvailableError(IMPORT_ERROR)
        
        # Create database folder structure
        db_folder = os.path.join(settings.DATABASES_DIR, db_name)
        os.makedirs(db_folder, exist_ok=True)
        
        db_path = os.path.join(db_folder, f"{db_name}.db")
        
        conn = sqlite3.connect(db_path)
        created_tables = []
        table_creation_sql = {}
        
        try:
            for file in files:
                # Read file based on extension
                filename_lower = file.filename.lower()
                if filename_lower.endswith('.xlsx'):
                    df = pd.read_excel(file.file)
                elif filename_lower.endswith('.csv'):
                    df = pd.read_csv(file.file, encoding='utf-8')
                else:
                    raise UnsupportedFileTypeError(file.filename)
                
                # Generate table name from filename
                table_name = os.path.splitext(file.filename)[0].replace(" ", "_").replace("-", "_")
                
                # Generate CREATE TABLE SQL statement
                columns_sql = []
                for col in df.columns:
                    # Determine column type based on data
                    if pd.api.types.is_numeric_dtype(df[col]):
                        if pd.api.types.is_integer_dtype(df[col]):
                            col_type = "INTEGER"
                        else:
                            col_type = "REAL"
                    else:
                        col_type = "TEXT"
                    columns_sql.append(f"    `{col}` {col_type}")
                
                create_sql = f"CREATE TABLE `{table_name}` (\n" + ",\n".join(columns_sql) + "\n);"
                table_creation_sql[table_name] = create_sql
                
                # Create table in database
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                created_tables.append(TableInfo(
                    table_name=table_name,
                    filename=file.filename,
                    rows=len(df),
                    columns=list(df.columns)
                ))
        
        except Exception as e:
            conn.close()
            raise e
        
        conn.close()
        
        # Create JSON file with table creation statements
        schema_file = os.path.join(db_folder, "schema.json")
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump({
                "database_name": db_name,
                "tables": table_creation_sql,
                "sql": [],
                "documents": [],
                "created_at": datetime.datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        return created_tables, db_path
    
    @staticmethod
    def get_database_schema(db_name: str) -> DatabaseSchema:
        """Get database schema by database name"""
        db_path = os.path.join(settings.DATABASES_DIR, db_name, f"{db_name}.db")
        
        if not os.path.exists(db_path):
            raise DatabaseNotFoundError(db_name)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        table_schemas = []
        
        # Get schema for each table
        for table in tables:
            table_name = table[0]
            
            # Get table info
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            row_count = cursor.fetchone()[0]
            
            column_infos = [
                ColumnInfo(
                    name=col[1],
                    type=col[2],
                    not_null=bool(col[3]),
                    default_value=col[4],
                    primary_key=bool(col[5])
                )
                for col in columns
            ]
            
            table_schemas.append(TableSchema(
                table_name=table_name,
                row_count=row_count,
                columns=column_infos
            ))
        
        conn.close()
        
        return DatabaseSchema(
            database_name=db_name,
            database_path=db_path,
            tables=table_schemas
        )
    
    @staticmethod
    def get_schema_json(db_name: str) -> Dict[str, Any]:
        """Get schema.json file content for a specific database"""
        schema_path = os.path.join(settings.DATABASES_DIR, db_name, "schema.json")
        
        if not os.path.exists(schema_path):
            raise SchemaNotFoundError(db_name)
        
        with open(schema_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def update_schema_json(db_name: str, schema_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update schema.json file for a specific database"""
        db_folder = os.path.join(settings.DATABASES_DIR, db_name)
        schema_path = os.path.join(db_folder, "schema.json")
        
        if not os.path.exists(db_folder):
            raise DatabaseNotFoundError(db_name)
        
        # Update timestamp
        schema_data["updated_at"] = datetime.datetime.now().isoformat()
        
        # Write updated schema.json
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        
        return {
            "message": "Schema updated successfully and agent cache cleared",
            "database_name": db_name,
            "updated_at": schema_data["updated_at"]
        }
    
    @staticmethod
    def list_databases() -> List[DatabaseInfo]:
        """List all available databases"""
        databases_dir = settings.DATABASES_DIR
        
        if not os.path.exists(databases_dir):
            return []
        
        databases = []
        for item in os.listdir(databases_dir):
            db_path = os.path.join(databases_dir, item)
            if os.path.isdir(db_path):
                db_file = os.path.join(db_path, f"{item}.db")
                schema_file = os.path.join(db_path, "schema.json")
                
                if os.path.exists(db_file):
                    database_info = DatabaseInfo(
                        name=item,
                        path=db_file,
                        has_schema=os.path.exists(schema_file)
                    )
                    
                    # Try to get additional info from schema.json
                    if os.path.exists(schema_file):
                        try:
                            with open(schema_file, 'r', encoding='utf-8') as f:
                                schema_data = json.load(f)
                                database_info.created_at = schema_data.get("created_at")
                                database_info.table_count = len(schema_data.get("tables", {}))
                        except Exception:
                            pass
                    
                    databases.append(database_info)
        
        return databases