"""
models.py
PaperDraft: 근거 추적형 연구 논문 작성 에이전트
PRD 데이터 및 근거 모델 (Data & Evidence Models)
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class SourceDocument(BaseModel):
    """FR-01: 등록된 원천 연구 자료 메타데이터"""
    source_id: str
    project_id: str = "project_cuda_01"
    file_path: str
    file_name: str
    file_hash: str
    file_format: str = "pdf"
    page_count: int = 1
    registered_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class EvidenceRecord(BaseModel):
    """PRD 8절: Evidence Record 모델"""
    evidence_id: str
    source_id: str
    source_hash: str
    page: int = 1
    element_id: str = "elem_000"
    evidence_type: str = "numeric"  # numeric | environment | observation | table | code
    experiment_id: str = "exp_crown_cuda"
    section_tags: List[str] = Field(default_factory=list)  # ["materials_methods", "results_discussion", etc.]
    raw_text: str
    value: Optional[Any] = None  # e.g., 8.96, 40.0, "8GB"
    unit: Optional[str] = None   # e.g., "x", "ms", "GB", "dimensions"
    conditions: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    evidence_status: str = "candidate"  # candidate | verified | rejected
    user_review_status: str = "pending"  # pending | approved | modified | rejected


class CalculationRecord(BaseModel):
    """FR-06: Python 결정론 계산 기록 모델"""
    calculation_id: str
    formula: str
    operation: str  # speedup | latency_reduction | throughput_ratio | unit_conversion
    input_values: Dict[str, Any]
    result_value: float
    unit: str
    evidence_ids: List[str] = Field(default_factory=list)
    calculated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ClaimRecord(BaseModel):
    """PRD 8절: Claim Record 모델 (초안 문장-근거 간 추적성 링크)"""
    claim_id: str
    claim_text: str
    paper_section: str  # materials_methods | results_discussion | limitations | introduction | conclusion | abstract
    evidence_ids: List[str] = Field(default_factory=list)
    calculation_id: Optional[str] = None
    groundedness_result: str = "PENDING"      # GROUNDED | UNGROUNDED | PENDING
    numeric_check_result: str = "N/A"         # MATCH | MISMATCH | N/A
    scope_check_result: str = "VALID"         # VALID | OVERCLAIM | PENDING
    user_review_status: str = "pending"       # pending | approved | rejected
    reviewer_comment: Optional[str] = None


class SectionRequirement(BaseModel):
    """FR-05: 논문 섹션별 필수 요구 데이터 명세"""
    section_id: str                           # materials_methods, results_discussion, etc.
    section_title: str
    required_field: str                       # e.g. "hardware_gpu_vram", "speedup_benchmark"
    field_description: str
    required_type: str                        # environment | numeric | observation
    status: str = "미확인"                    # 제공됨 | 존재 확인·요청 가능 | 확인 필요 | 현재 미확인
    linked_evidence_id: Optional[str] = None
    data_gap_reason: Optional[str] = None     # 자료 부족 시 요청 사유
