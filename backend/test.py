from src.dbagent.agents.base import get_dbagent

agent = get_dbagent("bank")
res = agent.ask(
    question = "客户贷款总额"
)
print(res)