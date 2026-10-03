import sys
from pathlib import Path
import gc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from service import run_traceable_paper_draft_pipeline
from config import PAPER_DRAFT_MD, PAPER_DRAFT_PDF, PAPER_DRAFT_RESULT


def test_unit4():
    test_db = Path("result/test_unit4.db")
    if test_db.exists():
        test_db.unlink()

    res = run_traceable_paper_draft_pipeline(
        proposal_path="data/SW_Design_Notes.pdf",
        validation_path="data/Validation_Report.pdf",
        db_path=test_db
    )

    # 1. Verify Structure & Metadata
    assert res is not None
    assert res["support_level"] == "Strongly Supported"
    assert res["coherence_score"] == 95
    print(f"[OK] Coherence Score: {res['coherence_score']} | Support: {res['support_level']}")

    # 2. Verify Audit Report (FR-08)
    audit = res["audit_report"]
    print(f"[OK] Audit Report: Total Claims={audit['total_claims']}, Grounded={audit['grounded_rate']}%, Numeric Exactness={audit['numeric_exactness_rate']}%")
    assert audit["total_claims"] >= 10
    assert audit["grounded_rate"] >= 80.0
    assert audit["numeric_exactness_rate"] >= 80.0

    # 3. Verify Deterministic Calculations (FR-06)
    calcs = res["calculations"]
    assert len(calcs) >= 3
    print(f"[OK] Deterministic Calculations Count: {len(calcs)}")
    for c in calcs:
        print(f"  - [{c['calculation_id']}] {c['formula']}")

    # 4. Verify Section Evaluations (FR-05)
    sec_eval = res["section_evaluations"]
    assert "materials_methods" in sec_eval
    assert "results_discussion" in sec_eval
    assert "limitations" in sec_eval
    print("[OK] Section Requirements Evaluated:")
    for s_name, s_data in sec_eval.items():
        print(f"  - {s_name}: {s_data['fulfilled_count']}/{s_data['total_requirements']} fulfilled ({s_data['status']})")

    # 5. Verify Output Artifacts
    assert Path(PAPER_DRAFT_RESULT).exists()
    assert Path(PAPER_DRAFT_MD).exists()
    assert Path(PAPER_DRAFT_PDF).exists()
    print("[OK] All Output Artifacts verified: MD, PDF, JSON!")

    # Cleanup
    del res
    gc.collect()
    try:
        if test_db.exists():
            test_db.unlink()
    except Exception:
        pass

    print(">>> All Unit 4 tests passed successfully!")


if __name__ == "__main__":
    test_unit4()
