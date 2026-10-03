import sys
from pathlib import Path
import gc

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evidence_store import EvidenceStore
from evidence_extractor import UniversalEvidenceExtractor
from section_requirements import SectionRequirementEvaluator, get_default_section_requirements


def test_unit3():
    test_db = Path("result/test_unit3.db")
    store = EvidenceStore(test_db)
    store.reset_store()

    # 1. Initialize default section requirements
    default_reqs = get_default_section_requirements()
    store.set_section_requirements(default_reqs)
    print(f"[OK] Initialized {len(default_reqs)} default section requirements")

    # 2. Register Golden sample documents
    doc_a = store.register_source("data/SW_Design_Notes.pdf", project_id="p1", custom_source_id="src_doc_a")
    doc_b = store.register_source("data/Validation_Report.pdf", project_id="p1", custom_source_id="src_doc_b")
    assert doc_a.page_count >= 1
    assert doc_b.page_count >= 1
    print(f"[OK] Sources registered: {doc_a.source_id}, {doc_b.source_id}")

    # 3. Extract Evidences using UniversalEvidenceExtractor
    extractor = UniversalEvidenceExtractor(store)
    evs_a = extractor.extract_from_source(doc_a)
    evs_b = extractor.extract_from_source(doc_b)
    total_evs = len(evs_a) + len(evs_b)
    assert total_evs > 0, "No evidences extracted!"
    print(f"[OK] Extracted {len(evs_a)} evidences from Doc A, {len(evs_b)} from Doc B (Total: {total_evs})")

    # Check evidence types
    types = set([e.evidence_type for e in evs_a + evs_b])
    print(f"[OK] Extracted evidence types: {types}")

    # 4. Evaluate Section Coverage (FR-05)
    evaluator = SectionRequirementEvaluator(store)

    # Evaluate Materials & Methods
    mm_result = evaluator.evaluate_section("materials_methods")
    print(f"[OK] Materials & Methods Coverage: {mm_result['fulfilled_count']}/{mm_result['total_requirements']} items fulfilled (Status: {mm_result['status']})")
    assert mm_result['fulfilled_count'] > 0

    # Evaluate Results & Discussion
    rd_result = evaluator.evaluate_section("results_discussion")
    print(f"[OK] Results & Discussion Coverage: {rd_result['fulfilled_count']}/{rd_result['total_requirements']} items fulfilled (Status: {rd_result['status']})")
    assert rd_result['fulfilled_count'] > 0

    # Evaluate Limitations
    lim_result = evaluator.evaluate_section("limitations")
    print(f"[OK] Limitations Coverage: {lim_result['fulfilled_count']}/{lim_result['total_requirements']} items fulfilled (Status: {lim_result['status']})")
    assert lim_result['fulfilled_count'] > 0

    # 5. Test Data Gap Detection
    # If a fictitious section has missing fields, gap request form should be generated
    fake_eval = evaluator.evaluate_section("fictitious_section")
    assert fake_eval['status'] == "FULFILLED" or fake_eval['gap_request_form'] is not None

    # Cleanup
    del extractor
    del evaluator
    del store
    gc.collect()
    try:
        if test_db.exists():
            test_db.unlink()
    except Exception:
        pass

    print(">>> All Unit 3 tests passed successfully!")


if __name__ == "__main__":
    test_unit3()
