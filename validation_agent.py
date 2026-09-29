"""
validation_agent.py

실증 검증 및 아티팩트 리포트 분석 Agent (Document B)
실증 데이터에서 validation_type, empirical_evidence, verified_properties, limitations를 추출합니다.
"""

from pathlib import Path
from config import (
    VALIDATION_AGENT_ID,
    VALIDATION_CONFIG_ID
)
from agent_client import AgentClient

validation_agent = AgentClient(
    agent_id=VALIDATION_AGENT_ID,
    config_id=VALIDATION_CONFIG_ID,
    agent_type="validation"
)

def analyze_validation(file_id: str, file_path: str | Path = None) -> dict:
    """
    Validation Agent 실행
    """
    print("-" * 60)
    print("Validation Agent (Empirical Artifacts Analysis)")
    print("-" * 60)
    return validation_agent.run(file_id, file_path)

# Alias for backward compatibility
analyze_jd = analyze_validation
