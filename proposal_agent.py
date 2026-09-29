"""
proposal_agent.py

SW 연구 및 시스템 설계 노트 분석 Agent (Document A)
비정형 연구 메모에서 research_problem, proposed_methodology, key_contributions, assumptions를 추출합니다.
"""

from pathlib import Path
from config import (
    PROPOSAL_AGENT_ID,
    PROPOSAL_CONFIG_ID
)
from agent_client import AgentClient

proposal_agent = AgentClient(
    agent_id=PROPOSAL_AGENT_ID,
    config_id=PROPOSAL_CONFIG_ID,
    agent_type="proposal"
)

def analyze_proposal(file_id: str, file_path: str | Path = None) -> dict:
    """
    Proposal Agent 실행
    """
    print("-" * 60)
    print("Proposal Agent (SW Research & Design Analysis)")
    print("-" * 60)
    return proposal_agent.run(file_id, file_path)

# Alias for backward compatibility
analyze_resume = analyze_proposal
