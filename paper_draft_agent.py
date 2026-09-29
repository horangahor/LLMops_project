"""
paper_draft_agent.py

논문 초안 생성 및 정합성 평가 Agent (Evaluation_Input.pdf 분석)
가설 입증 수준(Strongly/Partially/Weakly Supported)을 분류하고
4장(방법론) 및 5장(검증) 논문 초안 서술문과 정합성 점수를 도출합니다.
"""

from pathlib import Path
from config import (
    PAPER_DRAFT_AGENT_ID,
    PAPER_DRAFT_CONFIG_ID
)
from agent_client import AgentClient

paper_draft_agent = AgentClient(
    agent_id=PAPER_DRAFT_AGENT_ID,
    config_id=PAPER_DRAFT_CONFIG_ID,
    agent_type="paper_draft"
)

def analyze_paper_draft(file_id: str, file_path: str | Path = None) -> dict:
    """
    Paper Draft Agent 실행
    """
    print("-" * 60)
    print("Paper Draft Agent (Coherence Evaluation & Paper Drafting)")
    print("-" * 60)
    return paper_draft_agent.run(file_id, file_path)

# Alias for backward compatibility
analyze_matching = analyze_paper_draft
