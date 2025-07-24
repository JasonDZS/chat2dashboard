from ..core.sql_generator import create_sql_generator

class SQLService:
    def create_sql_generator(self, db_name: str):
        """Create SQL generator for a database"""
        return create_sql_generator(db_name)