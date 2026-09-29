"""
app.py

PaperDraft AI: SW 연구 및 실증 데이터 기반 논문 초안 생성 서비스
전체 Workflow Orchestrator
"""

from pathlib import Path
from config import (
    validate_config,
    print_config,
    PROPOSAL_FILE,
    VALIDATION_FILE,
    PROPOSAL_JSON,
    VALIDATION_JSON,
    EVALUATION_PDF,
    PAPER_DRAFT_RESULT,
    PAPER_DRAFT_MD,
    PAPER_DRAFT_PDF
)

from upload import upload_file
from proposal_agent import analyze_proposal
from validation_agent import analyze_validation
from matching_builder import create_matching_input, create_paper_draft_files
from paper_draft_agent import analyze_paper_draft
from file_manager import save_json

##################################################
# Document Processing Step
##################################################

def process_document(
    step: str,
    document_name: str,
    input_file: str | Path,
    analyzer,
    output_json: str | Path
):
    print()
    print("=" * 60)
    print(step)
    print("=" * 60)

    # 1. Upload to Upstage Files API
    file_id = ""
    try:
        file_id = upload_file(input_file)
        print(f"{document_name} Upload Complete (File ID: {file_id})")
    except Exception as e:
        print(f"[Notice] Files API 업로드 생략 또는 실패: {e}")

    # 2. Agent Analysis
    try:
        result = analyzer(file_id, file_path=input_file)
        save_json(result, output_json)
        print()
        print(f"{document_name} JSON 저장 완료 -> {output_json}")
        return result
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(e)
        return None

##################################################
# Build Evaluation Document
##################################################

def build_matching_pdf():
    print()
    print("=" * 60)
    print("Step 3. Evaluation Builder (Synthesis Document)")
    print("=" * 60)

    try:
        pdf_path = create_matching_input()
        print()
        print("Evaluation_Input.pdf 생성 완료")
        print(pdf_path)
        return pdf_path
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(e)
        return None

##################################################
# Process Paper Draft & Coherence Analysis
##################################################

def process_matching(matching_pdf):
    print()
    print("=" * 60)
    print("Step 4. Paper Draft Analysis & Coherence Evaluation")
    print("=" * 60)

    try:
        file_id = ""
        try:
            file_id = upload_file(matching_pdf)
        except Exception as e:
            print(f"[Notice] Files API 업로드 생략 또는 실패: {e}")

        result = analyze_paper_draft(file_id, file_path=matching_pdf)
        save_json(result, PAPER_DRAFT_RESULT)
        print()
        print("Paper Draft Result 저장 완료")
        print(PAPER_DRAFT_RESULT)

        # Generate formal Paper Draft documents (.md and .pdf)
        create_paper_draft_files(result)

        return result
    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR")
        print("=" * 60)
        print(e)
        return None

##################################################
# Print Results
##################################################

def print_result():
    print()
    print("=" * 60)
    print("Project Complete : PaperDraft AI Pipeline")
    print("=" * 60)
    print()
    print("Generated Files:")
    print("-" * 60)
    print(f"1. Proposal JSON        : {PROPOSAL_JSON}")
    print(f"2. Validation JSON      : {VALIDATION_JSON}")
    print(f"3. Evaluation PDF       : {EVALUATION_PDF}")
    print(f"4. Paper Draft JSON     : {PAPER_DRAFT_RESULT}")
    print(f"5. Paper Draft Markdown : {PAPER_DRAFT_MD}")
    print(f"6. Paper Draft PDF      : {PAPER_DRAFT_PDF}")
    print("-" * 60)

##################################################
# Main Execution
##################################################

def main():
    print()
    print("=" * 60)
    print("PaperDraft AI Service (SW Research to Paper Draft)")
    print("=" * 60)

    validate_config()
    print_config()

    # Step 1. Proposal Analysis
    proposal = process_document(
        step="Step 1. Proposal Analysis (Document A: SW Design Notes)",
        document_name="Proposal",
        input_file=PROPOSAL_FILE,
        analyzer=analyze_proposal,
        output_json=PROPOSAL_JSON
    )
    if proposal is None:
        return

    # Step 2. Validation Analysis
    validation = process_document(
        step="Step 2. Validation Analysis (Document B: Empirical Artifacts)",
        document_name="Validation",
        input_file=VALIDATION_FILE,
        analyzer=analyze_validation,
        output_json=VALIDATION_JSON
    )
    if validation is None:
        return

    # Step 3. Evaluation Builder
    matching_pdf = build_matching_pdf()
    if matching_pdf is None:
        return

    # Step 4. Paper Draft Analysis
    result = process_matching(matching_pdf)
    if result is None:
        return

    # Step 5. Summary
    print_result()

if __name__ == "__main__":
    main()