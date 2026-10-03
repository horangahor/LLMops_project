import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import SourceDocument, EvidenceRecord, ClaimRecord, CalculationRecord
from evidence_store import EvidenceStore

def test_evidence_store():
    test_db = Path("result/test_evidence.db")
    store = EvidenceStore(test_db)
    store.reset_store()

    # 1. Test Source Registration & Hash Deduplication (FR-01)
    sample_pdf = Path("data/SW_Design_Notes.pdf")
    doc1 = store.register_source(sample_pdf, project_id="p1")
    print(f"[OK] Source 1 registered: {doc1.source_id}, hash: {doc1.file_hash[:8]}..., pages: {doc1.page_count}")

    # Register again -> should deduplicate
    doc2 = store.register_source(sample_pdf, project_id="p1")
    assert doc1.source_id == doc2.source_id, "Deduplication failed!"
    print("[OK] Source deduplication verified!")

    # 2. Test Evidence Record Addition & Query (PRD 8절)
    ev1 = EvidenceRecord(
        evidence_id="ev_001",
        source_id=doc1.source_id,
        source_hash=doc1.file_hash,
        page=1,
        element_id="elem_p1_01",
        evidence_type="numeric",
        experiment_id="exp_cuda_01",
        section_tags=["materials_methods", "results_discussion"],
        raw_text="v5 40,000차원 대규모 행렬 벤치마크 결과 580ms 소요, CPU 대비 8.96배 가속",
        value=8.96,
        unit="x",
        conditions={"matrix_dim": 40000, "device": "NVIDIA GPU"}
    )
    store.add_evidence(ev1)
    retrieved_ev = store.get_evidence("ev_001")
    assert retrieved_ev is not None
    assert retrieved_ev.value == 8.96
    print(f"[OK] Evidence ev_001 added and retrieved: value={retrieved_ev.value} {retrieved_ev.unit}")

    # 3. Test Calculation Record (FR-06)
    calc1 = CalculationRecord(
        calculation_id="calc_speedup_01",
        formula="cpu_latency / gpu_latency = 5200ms / 580ms = 8.965x",
        operation="speedup",
        input_values={"cpu_latency_ms": 5200.0, "gpu_latency_ms": 580.0},
        result_value=8.965,
        unit="x",
        evidence_ids=["ev_001"]
    )
    store.add_calculation(calc1)
    retrieved_calc = store.get_calculation("calc_speedup_01")
    assert retrieved_calc is not None
    assert retrieved_calc.result_value == 8.965
    print(f"[OK] Calculation added and retrieved: formula={retrieved_calc.formula}")

    # 4. Test Claim Record (PRD 8절)
    clm1 = ClaimRecord(
        claim_id="clm_001",
        claim_text="제안된 CUDA 가속화 기법은 대규모 가중치 환경에서 CPU 대비 8.96배의 처리 가속을 달성하였다.",
        paper_section="results_discussion",
        evidence_ids=["ev_001"],
        calculation_id="calc_speedup_01",
        groundedness_result="GROUNDED",
        numeric_check_result="MATCH",
        scope_check_result="VALID"
    )
    store.add_claim(clm1)
    claims = store.list_claims(section="results_discussion")
    assert len(claims) == 1
    assert claims[0].claim_id == "clm_001"
    print(f"[OK] Claim clm_001 verified and retrieved: text={claims[0].claim_text[:40]}...")

    # Cleanup test db
    del store
    import gc
    gc.collect()
    try:
        if test_db.exists():
            test_db.unlink()
    except Exception:
        pass
    print(">>> All Unit 1 tests passed successfully!")

if __name__ == "__main__":
    test_evidence_store()
