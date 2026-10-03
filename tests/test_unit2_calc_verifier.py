import sys
from pathlib import Path
import gc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import EvidenceRecord, ClaimRecord
from evidence_store import EvidenceStore
from calculation_engine import DeterministicCalculationEngine
from verifier import VerificationEngine


def test_unit2():
    test_db = Path("result/test_unit2.db")
    store = EvidenceStore(test_db)
    store.reset_store()

    # 1. Test Deterministic Calculation Engine (FR-06)
    speedup_calc = DeterministicCalculationEngine.calculate_speedup(
        baseline_time=5200.0,
        accelerated_time=580.0,
        baseline_name="CPU",
        accelerated_name="GPU v5",
        evidence_ids=["ev_v5"]
    )
    assert speedup_calc.result_value == 8.97 or speedup_calc.result_value == 8.96
    assert "5200.0ms" in speedup_calc.formula
    assert "580.0ms" in speedup_calc.formula
    store.add_calculation(speedup_calc)
    print(f"[OK] Deterministic Speedup: {speedup_calc.result_value}x | Formula: {speedup_calc.formula}")

    latency_calc = DeterministicCalculationEngine.calculate_latency_reduction(
        initial_latency=353.0,
        optimized_latency=40.0,
        initial_name="초기 커널",
        optimized_name="메모리 풀",
        evidence_ids=["ev_v4"]
    )
    assert latency_calc.result_value == 88.7 or latency_calc.result_value == 88.6
    store.add_calculation(latency_calc)
    print(f"[OK] Latency Reduction: {latency_calc.result_value}% | Formula: {latency_calc.formula}")

    # 2. Add Test Evidences
    ev1 = EvidenceRecord(
        evidence_id="ev_v5",
        source_id="src_doc_b",
        source_hash="hash_b",
        page=2,
        evidence_type="numeric",
        raw_text="대규모 40000차원 가중치 행렬 처리 시 GPU 소요시간 580ms, CPU 5200ms 대비 8.96배 가속 달성",
        value=8.96,
        unit="x"
    )
    store.add_evidence(ev1)

    # 3. Test Verifier (FR-08)
    verifier = VerificationEngine(store)

    # Case A: Valid Grounded & Matching Claim
    valid_claim = ClaimRecord(
        claim_id="clm_valid",
        claim_text="제안된 아키텍처는 40000차원 가중치 행렬 환경에서 580ms를 기록하여 CPU 대비 8.96배의 속도 향상을 입증하였다.",
        paper_section="results_discussion",
        evidence_ids=["ev_v5"],
        calculation_id=speedup_calc.calculation_id
    )
    verified_a = verifier.verify_claim(valid_claim)
    assert verified_a.numeric_check_result == "MATCH", f"Expected MATCH, got {verified_a.numeric_check_result}"
    assert verified_a.groundedness_result == "GROUNDED", f"Expected GROUNDED, got {verified_a.groundedness_result}"
    assert verified_a.scope_check_result == "VALID", f"Expected VALID, got {verified_a.scope_check_result}"
    print("[OK] Case A: Valid Grounded & Matching Claim verified successfully!")

    # Case B: Numeric Mismatch Claim (Hallucinated 15.5x)
    mismatch_claim = ClaimRecord(
        claim_id="clm_mismatch",
        claim_text="제안된 아키텍처는 40000차원 환경에서 CPU 대비 15.5배의 속도 향상을 달성하였다.",
        paper_section="results_discussion",
        evidence_ids=["ev_v5"]
    )
    verified_b = verifier.verify_claim(mismatch_claim)
    assert verified_b.numeric_check_result == "MISMATCH", f"Expected MISMATCH, got {verified_b.numeric_check_result}"
    print("[OK] Case B: Numeric Mismatch (Hallucination) caught successfully!")

    # Case C: Overclaim (Scope violation)
    overclaim = ClaimRecord(
        claim_id="clm_overclaim",
        claim_text="제안 기법은 모든 모델에서 어떠한 환경에서도 완벽하게 무제한으로 8.96배 가속을 보장한다.",
        paper_section="results_discussion",
        evidence_ids=["ev_v5"]
    )
    verified_c = verifier.verify_claim(overclaim)
    assert verified_c.scope_check_result == "OVERCLAIM", f"Expected OVERCLAIM, got {verified_c.scope_check_result}"
    print("[OK] Case C: Overclaim (Scope Violation) caught successfully!")

    # Case D: Ungrounded Claim (No evidence)
    ungrounded = ClaimRecord(
        claim_id="clm_ungrounded",
        claim_text="근거가 전혀 없는 임의의 성능 주장 문장입니다.",
        paper_section="results_discussion",
        evidence_ids=[]
    )
    verified_d = verifier.verify_claim(ungrounded)
    assert verified_d.groundedness_result == "UNGROUNDED", f"Expected UNGROUNDED, got {verified_d.groundedness_result}"
    print("[OK] Case D: Ungrounded Claim without evidence caught successfully!")

    # Cleanup
    del verifier
    del store
    gc.collect()
    try:
        if test_db.exists():
            test_db.unlink()
    except Exception:
        pass

    print(">>> All Unit 2 tests passed successfully!")


if __name__ == "__main__":
    test_unit2()
