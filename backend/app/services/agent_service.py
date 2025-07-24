from functools import lru_cache
from ..core.agent import get_dbagent, DBAgent

class AgentService:
    def get_agent(self, db_name: str) -> DBAgent:
        """Get database agent instance"""
        return get_dbagent(db_name)

def clear_agent_cache():
    """Clear the agent cache to force retraining"""
    get_dbagent.cache_clear()