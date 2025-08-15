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
from .logging import get_logger

logger = get_logger()

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

        #构建schema数据
        schema_data = {
            "database_name": db_name,
            "tables": table_creation_sql,
            "sql": [],
            "documents": [],
            "created_at": datetime.datetime.now().isoformat()
        }
        try:
            # 生成sql语句
            logger.info("开始生成SQL语句")
            sql_entries = DatabaseManager.generate_sql_statements(table_creation_sql, conn)
            logger.info(f"生成了{len(sql_entries)}条SQL语句")
        except Exception as e:
            logger.error(f"生成SQL语句失败: {str(e)}")
            sql_entries = []

        # 生成文档
        try:
            logger.info("开始生成数据库文档")
            documents = DatabaseManager.generate_documents(db_name, tables, conn)
            logger.info(f"生成了{len(documents)}条文档")
        except:
            logger.error("生成数据库文档失败，使用默认文档")
            documents = []

        schema_data["sql"] = sql_entries
        schema_data["documents"] = documents
        # 保存文件
        db_folder = os.path.join(settings.DATABASES_DIR, db_name)
        schema_file = os.path.join(db_folder, "schema.json")
        
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Schema文件已保存: {schema_file}")
        return schema_file

    @staticmethod
    def generate_sql_statements(table_creation_sql: Dict[str, str],
                                 conn: sqlite3.Connection) -> List[Dict]:
        """
        使用AI同时生成自然语言问题和对应的SQL语句
        确保问题表达自然且SQL准确
        """
        sql_entries = []
        current_time = datetime.datetime.now().isoformat()

        # 收集表结构信息用于AI提示
        table_descriptions = []
        for table_name, create_sql in table_creation_sql.items():
            columns = []
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(f"PRAGMA table_info(\"{table_name}\")")
                    columns_info = cursor.fetchall()
                    columns = [{"name": col[1], "type": col[2].upper()} for col in columns_info]
                except sqlite3.Error:
                    pass

            table_descriptions.append({
                "table_name": table_name,
                "columns": columns,
                "create_sql": create_sql
            })

        # 使用API同时生成问题和SQL
        ai_questions_sql = DatabaseManager._generate_questions_and_sql_with_ai(table_descriptions)

        # 创建OpenAI客户端实例
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE
        )

        # 验证并存储生成的SQL
        for entry in ai_questions_sql:
            # 验证SQL是否可执行
            try:
                if conn:
                    cursor = conn.cursor()
                    # 使用EXPLAIN验证SQL语法
                    cursor.execute(f"EXPLAIN QUERY PLAN {entry['sql']}")
                    explain_result = cursor.fetchall()

                    # 如果EXPLAIN返回结果，说明SQL有效
                    if explain_result:
                        #AI语义一致性验证
                        validation_prompt = f"""
                        请检查SQL是否准确解决了用户问题。只回答"是"或"否"。

                        数据库表结构:
                        {table_descriptions}

                        用户问题: {entry['question']}

                        生成的SQL: {entry['sql']}

                        验证标准:
                        1. SQL是否包含问题中提到的所有关键元素?
                        2. 过滤条件是否完整?
                        3. 聚合函数使用是否正确?
                        4. 表连接是否合理?

                        你的判断（只回答是/否）：
                        """

                        validation_response = client.chat.completions.create(
                            model=settings.LLM_MODEL,
                            messages=[
                                {"role": "system", "content": "你是一个SQL专家，擅长验证SQL查询的准确性。"},
                                {"role": "user", "content": validation_prompt}
                            ],
                            temperature=0.1,  # 更低的温度确保确定性
                            max_tokens=10
                        )

                        # 解析AI响应
                        ai_answer = validation_response.choices[0].message.content.strip().lower()
                        is_semantically_valid = "是" in ai_answer or "yes" in ai_answer

                        if is_semantically_valid:
                            # 语义验证通过
                            sql_entries.append({
                                "question": entry["question"],
                                "sql": entry["sql"],
                                "added_at": current_time,
                                "validation": "ai_verified"  # 添加验证标记
                            })
                        else:
                            # 语义验证失败，使用默认SQL
                            print(f"⚠️ SQL语义不匹配: {entry['question']}")
                            default_sql = DatabaseManager._generate_default_sql(entry["question"], table_descriptions)
                            sql_entries.append({
                                "question": entry["question"],
                                "sql": default_sql,
                                "added_at": current_time,
                                "validation": "default_sql"  # 标记为默认SQL
                            })
                    else:
                        # 如果语法验证失败，使用默认SQL
                        print(f"SQL语法验证失败: {entry['sql']}")
                        sql_entries.append({
                            "question": entry["question"],
                            "sql": DatabaseManager._generate_default_sql(entry["question"], table_descriptions),
                            "added_at": current_time,
                            "validation": "syntax_failed"
                        })
                else:
                    # 没有数据库连接
                    print(f"⚠️ 无数据库连接，使用默认SQL: {entry['question']}")
                    default_sql = DatabaseManager._generate_default_sql(entry["question"], table_descriptions)
                    sql_entries.append({
                        "question": entry["question"],
                        "sql": default_sql,
                        "added_at": current_time,
                        "validation": "no_connection"
                    })

            except sqlite3.Error as e:
                print(f"SQL执行错误: {str(e)}")
                # 生成默认SQL
                sql_entries.append({
                    "question": entry["question"],
                    "sql": DatabaseManager._generate_default_sql(entry["question"], table_descriptions),
                    "added_at": current_time,
                    "validation": "error_recovery"
                })
            except Exception as e:
                print(f"AI验证异常: {str(e)}")
                # 异常时使用原始SQL
                sql_entries.append({
                    "question": entry["question"],
                    "sql": entry["sql"],
                    "added_at": current_time,
                    "validation": "ai_failed"
                })

        return sql_entries

    @staticmethod
    def _generate_questions_and_sql_with_ai(table_descriptions: List[Dict],num_questions: int = 50) -> List[Dict]:
        """

        使用API同时生成自然语言问题和对应的SQL语句
        返回格式: [{"question": "...", "sql": "..."}, ...]

        """
        # 构建表结构信息文本
        schema_parts = []
        for desc in table_descriptions:
            columns_text = ', '.join([f"{col['name']} ({col['type']})" for col in desc['columns']])
            schema_parts.append(f"表名: {desc['table_name']}\n包含列: {columns_text}")
        schema_text = "\n\n".join(schema_parts)

        prompt = f"""
    基于以下数据库表结构，生成{num_questions}个具体的自然语言查询问题及其对应的SQL查询语句。要求：
    1. 自然语言问题使用流畅的中文表达，避免直接引用表名和列名
    2. SQL语句使用SQLite语法，确保正确性
    3. 问题应该具有实际业务意义
    4. 问题可以通过SQL查询得到明确答案
    5. 结果适合用图表展示

    输出格式要求：
    每个问题及其SQL占一行，格式为：
    问题: [自然语言问题]
    SQL: [对应的SQL语句]

    数据库表结构：
    {schema_text}

    请严格按照上述格式输出，不要包含任何其他内容。
    """

        try:
            # 使用OpenAI API生成问题和SQL
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_API_BASE)

            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个SQL专家，擅长将自然语言问题转换为准确的SQL查询语句。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # 确保准确性
                max_tokens=1024
            )

            # 解析返回的问题和SQL
            content = response.choices[0].message.content.strip()
            entries = []
            current_question = None
            current_sql = None

            for line in content.split('\n'):
                if line.startswith("问题:"):
                    if current_question and current_sql:
                        entries.append({"question": current_question, "sql": current_sql})
                    current_question = line.replace("问题:", "").strip()
                    current_sql = None
                elif line.startswith("SQL:"):
                    current_sql = line.replace("SQL:", "").strip()

            # 添加最后一个条目
            if current_question and current_sql:
                entries.append({"question": current_question, "sql": current_sql})

            return entries

        except Exception as e:
            print(f"AI问题生成失败: {str(e)}")
            # 备选方案：基于表结构生成简单问题和SQL
            return DatabaseManager._generate_fallback_questions_and_sql(table_descriptions)

    @staticmethod
    def _generate_fallback_questions_and_sql(table_descriptions: List[Dict]) -> List[Dict]:
        """备选方案：生成简单问题和SQL"""
        entries = []

        for desc in table_descriptions:
            table_name = desc["table_name"]
            readable_table_name = table_name.replace('_', ' ')

            # 样本数据查询
            entries.append({
                "question": f"查看{readable_table_name}的前10条记录",
                "sql": f"SELECT * FROM \"{table_name}\" LIMIT 10;"
            })

            # 行数统计
            entries.append({
                "question": f"统计{readable_table_name}的总数量",
                "sql": f"SELECT COUNT(*) AS total_count FROM \"{table_name}\";"
            })

            # 为每个列生成分析问题
            for col in desc["columns"]:
                col_name = col["name"]
                readable_col_name = col_name.replace('_', ' ')
                col_type = col["type"]

                if "INT" in col_type or "REAL" in col_type:
                    # 数值分析
                    entries.append({
                        "question": f"分析{readable_table_name}中{readable_col_name}的分布情况",
                        "sql": f"SELECT \"{col_name}\", COUNT(*) AS count FROM \"{table_name}\" GROUP BY \"{col_name}\" ORDER BY count DESC;"
                    })

                    entries.append({
                        "question": f"计算{readable_table_name}中{readable_col_name}的平均值",
                        "sql": f"SELECT AVG(\"{col_name}\") AS average_value FROM \"{table_name}\";"
                    })

                elif "TEXT" in col_type:
                    # 文本分析
                    entries.append({
                        "question": f"找出{readable_table_name}中最常见的{readable_col_name}",
                        "sql": f"SELECT \"{col_name}\", COUNT(*) AS count FROM \"{table_name}\" GROUP BY \"{col_name}\" ORDER BY count DESC LIMIT 10;"
                    })

                elif "DATE" in col_type or "TIME" in col_type:
                    # 时间分析
                    entries.append({
                        "question": f"分析{readable_table_name}中{readable_col_name}的月度趋势",
                        "sql": f"SELECT strftime('%Y-%m', \"{col_name}\") AS month, COUNT(*) AS count FROM \"{table_name}\" GROUP BY month ORDER BY month;"
                    })

        return entries

    @staticmethod
    def _generate_default_sql(question: str, table_descriptions: List[Dict]) -> str:
        """根据问题生成默认SQL"""
        # 目前简单返回一个基础查询

        for desc in table_descriptions:
            if desc["table_name"] in question:
                return f"SELECT * FROM \"{desc['table_name']}\" LIMIT 10;"

        # 默认返回第一个表的查询
        if table_descriptions:
            return f"SELECT * FROM \"{table_descriptions[0]['table_name']}\" LIMIT 10;"

        return "SELECT 1;"
        
   @staticmethod
    def generate_documents(db_name: str, tables: List[TableInfo], conn: sqlite3.Connection) -> List[Dict]:
        """生成有价值的数据库文档，使用AI生成有意义的业务描述"""
        documents = []

        # 数据库概览文档（AI生成业务背景描述）
        overview_doc = DatabaseManager._generate_database_overview(db_name, tables)
        documents.append(overview_doc)

        # 表文档（AI生成每表业务含义）
        for table in tables:
            table_doc = DatabaseManager._generate_table_document(table, conn)
            documents.append(table_doc)

        # 分析指南（基于实际数据的AI分析建议）
        analysis_guide = DatabaseManager._generate_analysis_guide(db_name, tables, conn)
        documents.append(analysis_guide)

        return documents

    @staticmethod
    def _generate_database_overview(db_name: str, tables: List[TableInfo]) -> Dict:
        """生成数据库概览文档（业务背景描述）"""
        # 收集基本信息
        table_names = [table.table_name for table in tables]

        # AI生成有意义的概述
        prompt = f"""
    请为名为 "{db_name}" 的数据库撰写一个有价值的业务概述文档。该数据库包含以下表：{", ".join(table_names)}。

    请从业务角度描述：
    1. 这个数据库可能服务于什么类型的业务场景？
    2. 这些数据能解决哪些业务问题？
    3. 数据可能来自哪些业务系统？
    4. 主要分析价值是什么？

    请使用专业的业务语言，避免技术术语。
            """

        content = DatabaseManager._call_ai_for_document(prompt)

        return {
            "type": "database_overview",
            "title": f"{db_name} 数据库业务概述",
            "content": content
        }

    @staticmethod
    def _generate_table_document(table: TableInfo, conn: sqlite3.Connection) -> Dict:
        """生成单表文档（业务含义+分析建议）"""
        # 获取表的前10行样本数据
        sample_data = []
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM \"{table.table_name}\" LIMIT 10")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                sample_data = [dict(zip(columns, row)) for row in rows]
            except sqlite3.Error:
                pass

        # AI生成表描述
        prompt = f"""
    请为数据表 "{table.table_name}" 撰写详细的业务文档。该表来自文件 {table.filename}，包含 {table.rows} 行和 {len(table.columns)} 列。

    表结构：
    {", ".join(table.columns)}

    样本数据（前3行）：
    {json.dumps(sample_data, indent=2, ensure_ascii=False) if sample_data else "无样本数据"}

    请包含以下内容：
    1. 这张表在业务中代表什么？（例如：客户交易记录、用户行为日志等）
    2. 主要字段的业务含义解释
    3. 基于样本数据的具体分析建议
    4. 可能的业务应用场景

    请使用专业、易懂的业务语言，避免技术术语。
            """

        content = DatabaseManager._call_ai_for_document(prompt)

        return {
            "type": "table_schema",
            "table_name": table.table_name,
            "title": f"{table.table_name} 表业务文档",
            "content": content
        }

    @staticmethod
    def _generate_analysis_guide(db_name: str, tables: List[TableInfo], conn: sqlite3.Connection) -> Dict:
        """生成分析指南（基于实际数据的建议）"""
        # 收集表信息
        table_info = []
        for table in tables:
            # 获取每表的数据摘要
            summary = {}
            if conn:
                try:
                    cursor = conn.cursor()
                    for col in table.columns:
                        cursor.execute(f"SELECT COUNT(DISTINCT \"{col}\") FROM \"{table.table_name}\"")
                        distinct_count = cursor.fetchone()[0]
                        summary[col] = {
                            "distinct_values": distinct_count,
                            "suggestion": "高基数字段" if distinct_count > 100 else "低基数字段"
                        }
                except sqlite3.Error:
                    pass
            table_info.append({
                "table_name": table.table_name,
                "columns": table.columns,
                "summary": summary
            })

        # AI生成分析指南
        prompt = f"""
    基于数据库 "{db_name}" 的结构和初步分析，请创建一份有价值的数据分析指南。

    数据库包含以下表：
    {json.dumps(table_info, indent=2, ensure_ascii=False)}

    请提供：
    1. 3-5个最值得关注的分析方向（基于数据结构）
    2. 每个方向的具体分析方法和预期价值
    3. 推荐的可视化方式
    4. 潜在的数据质量问题和检查建议

    请使用专业的数据分析语言。
            """

        content = DatabaseManager._call_ai_for_document(prompt)

        return {
            "type": "analysis_guide",
            "title": "数据分析与洞察指南",
            "content": content
        }

    @staticmethod
    def _call_ai_for_document(prompt: str) -> str:
        """调用AI生成文档内容"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_API_BASE)

            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个资深数据分析师，擅长撰写清晰、专业的数据文档。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=2048
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"AI文档生成失败: {str(e)}")
            # 返回备选内容
            return "## 文档生成失败\n请手动补充文档内容。"

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
                logger.info(f"Created table {table_name} with {len(df)} rows and {len(df.columns)} columns.")
                created_tables.append(TableInfo(
                    table_name=table_name,
                    filename=file.filename,
                    rows=len(df),
                    columns=list(df.columns)
                ))
            # Create schema.json file
            logger.info(f"Creating schema.json for database {db_name} with {len(created_tables)} tables.")
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
