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
    def create_schema_json(db_name: str, table_creation_sql: Dict[str, str],tables:List[TableInfo],conn:sqlite3.Connection) -> str:
        """Create schema.json file for a database
        
        Args:
            db_name (str): Database name
            table_creation_sql (Dict[str, str]): Table name to CREATE SQL mapping
            tables: List of table information
            conn:database connection (used for generating SQL statements)
        Returns:
            str: Path to created schema.json file
        """

        # 生成sql语句
        sql_entries = DatabaseManager.generate_sql_statements(table_creation_sql, conn)

        # 生成文档
        documents = DatabaseManager.generate_documents(db_name, tables)

        #构建schema数据

        schema_data = {
            "database_name": db_name,
            "tables": table_creation_sql,
            "sql": sql_entries,
            "documents": documents,
            "created_at": datetime.datetime.now().isoformat()
        }

        # 保存文件
        db_folder = os.path.join(settings.DATABASES_DIR, db_name)
        schema_file = os.path.join(db_folder, "schema.json")
        
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        
        return schema_file

    @staticmethod
    def generate_sql_statements(table_creation_sql: Dict[str, str], conn: sqlite3.Connection) -> List[str]:
        """
        生成有价值的SQL语句集合

        返回格式: [{"question": "...", "sql": "...", "added_at": "..."}, ...]
        """
        sql_entries = []
        current_time = datetime.datetime.now().isoformat()

        for table_name, _ in table_creation_sql.items():
            #基础查询 - 获取样本数据
            sql = f"SELECT * FROM \"{table_name}\" LIMIT 10;"
            question = f"获取表 '{table_name}' 的前10条样本数据"
            sql_entries.append({
                "question": question,
                "sql": sql,
                "added_at": current_time
            })

            #基础查询 - 统计总行数
            sql = f"SELECT COUNT(*) AS total_rows FROM \"{table_name}\";"
            question = f"统计表 '{table_name}' 的总行数"
            sql_entries.append({
                "question": question,
                "sql": sql,
                "added_at": current_time
            })

            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
                    columns = cursor.fetchall()

                    for col in columns:
                        col_name = col[1]
                        col_type = col[2].upper()

                        if "INT" in col_type or "REAL" in col_type:
                            #数值型分析 - 分组统计
                            sql = (
                                f"SELECT \"{col_name}\", COUNT(*) AS count FROM \"{table_name}\" "
                                f"GROUP BY \"{col_name}\" ORDER BY count DESC;"
                            )
                            question = f"按列 '{col_name}' 分组统计表 '{table_name}' 中的记录分布"
                            sql_entries.append({
                                "question": question,
                                "sql": sql,
                                "added_at": current_time
                            })

                            #数值型分析 - 基本统计量
                            sql = (
                                f"SELECT AVG(\"{col_name}\") AS avg_value, "
                                f"MIN(\"{col_name}\") AS min_value, "
                                f"MAX(\"{col_name}\") AS max_value "
                                f"FROM \"{table_name}\";"
                            )
                            question = f"计算表 '{table_name}' 中列 '{col_name}' 的平均值、最小值和最大值"
                            sql_entries.append({
                                "question": question,
                                "sql": sql,
                                "added_at": current_time
                            })

                        elif "TEXT" in col_type:
                            #文本型分析 - TOP 10 值
                            sql = (
                                f"SELECT \"{col_name}\", COUNT(*) AS count FROM \"{table_name}\" "
                                f"GROUP BY \"{col_name}\" ORDER BY count DESC LIMIT 10;"
                            )
                            question = f"找出表 '{table_name}' 中列 '{col_name}' 最常见的10个值"
                            sql_entries.append({
                                "question": question,
                                "sql": sql,
                                "added_at": current_time
                            })

                            #文本型分析 - 长度分布
                            sql = (
                                f"SELECT LENGTH(\"{col_name}\") AS length, COUNT(*) AS count "
                                f"FROM \"{table_name}\" GROUP BY length;"
                            )
                            question = f"分析表 '{table_name}' 中列 '{col_name}' 的文本长度分布"
                            sql_entries.append({
                                "question": question,
                                "sql": sql,
                                "added_at": current_time
                            })

                except sqlite3.Error:
                    # 如果获取列信息失败，继续下一张表
                    continue

        return sql_entries

    @staticmethod
    def generate_documents(db_name: str, tables: List[TableInfo]) -> List[Dict]:
        """生成数据库文档"""
        documents = []

        # 数据库概览
        documents.append({
            "type": "database_overview",
            "title": f"{db_name} 数据库概览",
            "content": f"""
               ## {db_name} 数据库

               **创建时间**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}
               **包含表数**: {len(tables)}

               ### 主要数据表:
               {', '.join([t.table_name for t in tables])}
               """
        })

        # 每表文档
        for table in tables:
            # 列描述
            columns_desc = "\n".join([
                f"- **{col}**: 数据类型待检测，建议分析方向..."
                for col in table.columns
            ])

            documents.append({
                "type": "table_schema",
                "table": table.table_name,
                "title": f"{table.table_name} 表结构",
                "content": f"""
                   ## {table.table_name}

                   **来源文件**: {table.filename}
                   **行数**: {table.rows:,}
                   **列数**: {len(table.columns)}

                   ### 字段列表:
                   {columns_desc}

                   ### 数据分析建议:
                   1. 探索各字段的分布情况
                   2. 识别关键字段之间的关系
                   3. 分析时间趋势（如果存在时间字段）
                   """
            })

        # 分析指南
        documents.append({
            "type": "analysis_guide",
            "title": "数据分析指南",
            "content": """
               ## 推荐分析方向

               ### 1. 趋势分析
               - 随时间变化的指标趋势
               - 不同分类下的指标对比

               ### 2. 分布分析
               - 关键指标的分布情况
               - 地理分布（如果包含位置数据）

               ### 3. 相关性分析
               - 不同字段间的相关性
               - 影响因素分析
               """
        })

        return documents

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
            # Create schema.json file using separate method
            DatabaseManager.create_schema_json(db_name, table_creation_sql, created_tables, conn)  ##

        except Exception as e:
            conn.close()
            raise e
        
        conn.close()
        
        
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
