from llm_scribe.config import settings
from llm_scribe.main.manger import run

if __name__ == "__main__":
    group_id = 123454325
    hours = 23
    print(f"[LLM-Scribe] 独立运行模式启动 (group_id={group_id}, hours={hours})")
    result = run(group_id=group_id, hours=hours)
    print("\n=== 摘要结果 ===\n")
    print(result or "（无输出或模型未配置）")