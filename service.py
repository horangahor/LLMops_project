"""
=========================================================
PaperDraft AI Service
Business Logic

SW Research Notes (문서 A)
       ↓
Proposal Agent
       ↓
Empirical Validation Report (문서 B)
       ↓
Validation Agent
       ↓
Evaluation_Input.pdf (합성 대조표 문서)
       ↓
Paper Draft Agent (Classify + Extract)
       ↓
Matching Result (논문 4장/5장 초안 및 정합성 평가)
=========================================================
"""

import json
from pathlib import Path

from app import (
    process_document,
    build_matching_pdf,
    process_matching
)

from config import (
    PROPOSAL_JSON,
    VALIDATION_JSON,
    PAPER_DRAFT_RESULT
)

from proposal_agent import analyze_proposal
from validation_agent import analyze_validation

##################################################
# Proposal Analysis (Document A)
##################################################

def analyze_proposal_document(proposal_path: str):
    """
    SW 연구/설계 노트 분석
    """
    return process_document(
        step="Step 1. Proposal Analysis (Document A)",
        document_name="Proposal",
        input_file=proposal_path,
        analyzer=analyze_proposal,
        output_json=PROPOSAL_JSON
    )

# Alias for backward compatibility
analyze_resume_document = analyze_proposal_document

##################################################
# Validation Analysis (Document B)
##################################################

def analyze_validation_document(validation_path: str):
    """
    실증 검증 리포트 분석
    """
    return process_document(
        step="Step 2. Validation Analysis (Document B)",
        document_name="Validation",
        input_file=validation_path,
        analyzer=analyze_validation,
        output_json=VALIDATION_JSON
    )

# Alias for backward compatibility
analyze_jd_document = analyze_validation_document

##################################################
# Evaluation PDF Builder
##################################################

def build_matching_document():
    """
    Evaluation_Input.pdf (합성 문서) 생성
    """
    return build_matching_pdf()

##################################################
# Paper Draft & Coherence Analysis
##################################################

def analyze_matching(matching_pdf):
    """
    Paper Draft Agent 실행
    """
    return process_matching(matching_pdf)

##################################################
# Load Result
##################################################

def load_matching_result():
    """
    matching_result.json 읽기
    """
    with open(PAPER_DRAFT_RESULT, "r", encoding="utf-8") as file:
        return json.load(file)

##################################################
# Main Service Runner
##################################################

def run_paper_draft_service(
    proposal_path: str,
    validation_path: str
) -> dict:
    """
    PaperDraft AI Service Pipeline
    """
    print()
    print("=" * 60)
    print("PaperDraft AI Service Execution")
    print("=" * 60)
    print()

    # Step 1. Proposal
    print("Step 1. Proposal Analysis")
    analyze_proposal_document(proposal_path)

    # Step 2. Validation
    print()
    print("Step 2. Validation Analysis")
    analyze_validation_document(validation_path)

    # Step 3. Build Evaluation PDF
    print()
    print("Step 3. Build Evaluation Document")
    eval_pdf = build_matching_document()

    # Step 4. Paper Draft Analysis
    print()
    print("Step 4. Paper Draft Analysis & Evaluation")
    result = analyze_matching(eval_pdf)

    # Step 5. Load Result
    print()
    print("Step 5. Load Final Result")
    if result is None:
        result = load_matching_result()

    print()
    print("=" * 60)
    print("PaperDraft Pipeline Completed Successfully")
    print("=" * 60)
    print()

    return result

# Alias for backward compatibility
run_matching_service = run_paper_draft_service