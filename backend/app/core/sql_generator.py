"""SQL 生成器"""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import openai
from .agent import DBAgent
from ..config import settings


class SQLGenerator:
    """
    SQL生成器，使用AI生成问题，通过DBAgent验证SQL准确性，并将验证通过的SQL添加到schema.json中
    """
    
    def __init__(self, dbagent: DBAgent):
        """
        初始化SQL生成器
        
        Args:
            dbagent (DBAgent): 数据库代理实例
        """
        self.dbagent = dbagent
        self.dbname = dbagent.dbname
        self.schema_path = os.path.join("databases", self.dbname, "schema.json")
        
        # 初始化AI客户端
        self.client = openai.Client(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
        )
    
    def load_schema(self) -> Dict[str, Any]:
        """
        加载schema.json文件
        
        Returns:
            Dict[str, Any]: schema数据
        """
        if os.path.exists(self.schema_path):
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "database_name": self.dbname,
            "tables": {},
            "sql": [],
            "documents": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
    
    def save_schema(self, schema_data: Dict[str, Any]) -> None:
        """
        保存schema.json文件
        
        Args:
            schema_data (Dict[str, Any]): schema数据
        """
        schema_data["updated_at"] = datetime.now().isoformat()
        with open(self.schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, ensure_ascii=False, indent=2)
    
    def generate_questions_with_ai(self, num_questions: int = 10) -> List[str]:
        """
        使用AI基于数据库schema生成问题
        
        Args:
            num_questions (int): 要生成的问题数量
            
        Returns:
            List[str]: 生成的问题列表
        """
        schema_data = self.load_schema()
        tables_info = schema_data.get("tables", {})
        
        # 构建表结构信息
        table_descriptions = []
        for table_name, create_sql in tables_info.items():
            table_descriptions.append(f"表名: {table_name}\n创建语句: {create_sql}")
        
        schema_text = "\n\n".join(table_descriptions)
        
        prompt = f"""
基于以下数据库表结构，生成{num_questions}个具体的查询问题。这些问题应该：
1. 涵盖不同类型的查询（统计、分组、排序、时间范围等）
2. 具有实际业务意义
3. 可以通过SQL查询得到明确答案
4. 适合用图表展示结果

数据库表结构:
{schema_text}

请只返回问题列表，每行一个问题，不要包含其他内容。
"""
        
        try:
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Use slightly higher temperature for question generation
                max_tokens=1024
            )
            
            questions_text = response.choices[0].message.content.strip()
            questions = [q.strip() for q in questions_text.split('\n') if q.strip()]
            
            return questions[:num_questions]
            
        except Exception as e:
            print(f"❌ AI问题生成失败: {str(e)}")
            # 使用DBAgent的suggest_question作为备选
            return self.dbagent.suggest_question()[:num_questions]
    
    def validate_and_store_sql(self, question: str) -> Optional[Dict[str, Any]]:
        """
        验证问题的SQL生成和执行，如果成功则存储到schema.json
        
        Args:
            question (str): 要验证的问题
            
        Returns:
            Optional[Dict[str, Any]]: 验证成功的SQL记录，失败返回None
        """
        try:
            # 使用DBAgent生成和执行SQL
            result = self.dbagent.ask(question)
            sql = result["sql"]
            data = result["data"]
            
            # 检查是否有数据返回且SQL不为空
            if sql and data is not None and not data.empty:
                sql_record = {
                    "question": question,
                    "sql": sql,
                    "added_at": datetime.now().isoformat()
                }
                
                # 加载现有schema
                schema_data = self.load_schema()
                
                # 检查是否已存在相同的问题
                existing_questions = {item["question"] for item in schema_data.get("sql", [])}
                if question not in existing_questions:
                    # 添加到sql列表
                    if "sql" not in schema_data:
                        schema_data["sql"] = []
                    schema_data["sql"].append(sql_record)
                    
                    # 保存schema
                    self.save_schema(schema_data)
                    
                    print(f"✅ 验证通过并存储SQL: {question}")
                    return sql_record
                else:
                    print(f"⚠️  问题已存在，跳过: {question}")
                    return None
            else:
                print(f"❌ SQL验证失败（无数据返回）: {question}")
                return None
                
        except Exception as e:
            print(f"❌ SQL验证失败: {question} - {str(e)}")
            return None
    
    def batch_generate_and_validate(self, num_questions: int = 10) -> List[Dict[str, Any]]:
        """
        批量生成问题并验证SQL，将验证通过的添加到schema.json
        
        Args:
            num_questions (int): 要生成的问题数量
            
        Returns:
            List[Dict[str, Any]]: 验证通过的SQL记录列表
        """
        print(f"🚀 开始批量生成和验证{num_questions}个问题...")
        
        # 生成问题
        questions = self.generate_questions_with_ai(num_questions)
        print(f"📝 生成了{len(questions)}个问题")
        
        # 验证和存储
        validated_records = []
        for i, question in enumerate(questions, 1):
            print(f"\n进度 {i}/{len(questions)}: 验证问题 - {question}")
            record = self.validate_and_store_sql(question)
            if record:
                validated_records.append(record)
        
        print(f"\n🎉 完成！验证通过并存储了{len(validated_records)}个SQL记录")
        return validated_records
    
    def get_stored_sql_count(self) -> int:
        """
        获取已存储的SQL记录数量
        
        Returns:
            int: SQL记录数量
        """
        schema_data = self.load_schema()
        return len(schema_data.get("sql", []))
    
    def list_stored_questions(self) -> List[str]:
        """
        列出所有已存储的问题
        
        Returns:
            List[str]: 问题列表
        """
        schema_data = self.load_schema()
        return [item["question"] for item in schema_data.get("sql", [])]


def create_sql_generator(dbname: str) -> SQLGenerator:
    """
    创建SQL生成器实例
    
    Args:
        dbname (str): 数据库名称
        
    Returns:
        SQLGenerator: SQL生成器实例
    """
    from .agent import get_dbagent
    dbagent = get_dbagent(dbname)
    return SQLGenerator(dbagent)


if __name__ == "__main__":
    # 示例用法
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python sqlgen.py <database_name> [num_questions]")
        sys.exit(1)
    
    dbname = sys.argv[1]
    num_questions = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    
    # 创建SQL生成器
    generator = create_sql_generator(dbname)
    
    # 显示当前状态
    print(f"数据库: {dbname}")
    print(f"当前已存储SQL记录数: {generator.get_stored_sql_count()}")
    
    # 批量生成和验证
    validated_records = generator.batch_generate_and_validate(num_questions)
    
    # 显示结果
    print(f"\n最终存储SQL记录数: {generator.get_stored_sql_count()}")