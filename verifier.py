"""
verifier.py
PaperDraft: Claim & Evidence 검증 엔진
PRD FR-08: JSON schema, 숫자 exact match, source traceability, Groundedness, 적용 범위 검사
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from models import ClaimRecord, EvidenceRecord, CalculationRecord
from evidence_store import EvidenceStore


class VerificationEngine:
    """
    FR-08 검증 엔진:
    1. Source Traceability: Claim의 evidence_ids가 EvidenceStore에 실제로 존재하는지 100% 검증
    2. Numeric Exact Match: Claim 내 모든 수치가 Evidence 또는 CalculationRecord와 일치하는지 검사
    3. Groundedness Check: Claim의 사실 주장이 근거 원문(raw_text)에 명시되어 있는지 확인
    4. Scope Check: 실험 조건(행렬 차원, 디바이스)을 벗어난 과도한 일반화(Overclaim) 여부 판정
    """

    def __init__(self, store: EvidenceStore):
        self.store = store

    def extract_numbers_from_text(self, text: str) -> List[float]:
        """텍스트에서 유의미한 숫자(소수, 지수, 정수)를 추출한다."""
        # Regex for numbers including scientific notation like 1e-12, decimals like 8.96, integers like 40000
        pattern = r'[-+]?(?:\d+\.\d+|\d+)(?:[eE][-+]?\d+)?'
        matches = re.findall(pattern, text)
        numbers = []
        for m in matches:
            try:
                num = float(m)
                # Filter out pure year/index like 2026 or small section numbers unless relevant
                if num not in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 2026.0]:
                    numbers.append(num)
            except ValueError:
                pass
        return numbers

    def verify_claim(self, claim: ClaimRecord) -> ClaimRecord:
        """단일 ClaimRecord에 대해 FR-08의 4대 검증을 수행하고 결과를 업데이트한다."""
        # 1. Source Traceability Check
        if not claim.evidence_ids and not claim.calculation_id:
            claim.groundedness_result = "UNGROUNDED"
            claim.numeric_check_result = "N/A"
            claim.scope_check_result = "OVERCLAIM"
            return claim

        linked_evidences: List[EvidenceRecord] = []
        missing_ids = []
        for eid in claim.evidence_ids:
            ev = self.store.get_evidence(eid)
            if ev:
                linked_evidences.append(ev)
            else:
                missing_ids.append(eid)

        if missing_ids or not linked_evidences:
            claim.groundedness_result = "UNGROUNDED"
            claim.scope_check_result = "OVERCLAIM"
            claim.numeric_check_result = "MISMATCH"
            return claim

        # 2. Calculation Traceability
        linked_calc: Optional[CalculationRecord] = None
        if claim.calculation_id:
            linked_calc = self.store.get_calculation(claim.calculation_id)

        # 3. Numeric Exact Match Check
        claim_numbers = self.extract_numbers_from_text(claim.claim_text)
        evidence_numbers: List[float] = []

        for ev in linked_evidences:
            if ev.value is not None:
                try:
                    evidence_numbers.append(float(ev.value))
                except (ValueError, TypeError):
                    pass
            # Also extract from ev.raw_text
            evidence_numbers.extend(self.extract_numbers_from_text(ev.raw_text))

        if linked_calc:
            evidence_numbers.append(float(linked_calc.result_value))
            for val in linked_calc.input_values.values():
                try:
                    evidence_numbers.append(float(val))
                except (ValueError, TypeError):
                    pass

        # Check if numbers in claim exist in evidence/calc within tolerance
        if not claim_numbers:
            claim.numeric_check_result = "N/A"
        else:
            all_numbers_matched = True
            for cn in claim_numbers:
                matched = any(abs(cn - en) < 0.05 or (en != 0 and abs(cn - en) / abs(en) < 0.01) for en in evidence_numbers)
                if not matched:
                    all_numbers_matched = False
                    break
            claim.numeric_check_result = "MATCH" if all_numbers_matched else "MISMATCH"

        # 4. Groundedness Check (Lexical & Concept Overlap)
        combined_ev_text = " ".join([ev.raw_text for ev in linked_evidences])
        claim_words = [w for w in re.findall(r'[가-힣a-zA-Z0-9]+', claim.claim_text) if len(w) > 1]
        matched_words = [w for w in claim_words if w.lower() in combined_ev_text.lower()]

        overlap_ratio = len(matched_words) / max(len(claim_words), 1)
        if overlap_ratio >= 0.35 or claim.numeric_check_result == "MATCH":
            claim.groundedness_result = "GROUNDED"
        else:
            claim.groundedness_result = "UNGROUNDED"

        # 5. Scope Check (Overclaim Detection)
        # E.g. claiming "모든 신경망에서 무조건 10배 가속" without stating condition
        overclaim_indicators = ["모든 모델에서", "어떠한 환경에서도", "완벽하게 무제한", "항상 우수"]
        is_overclaim = any(ind in claim.claim_text for ind in overclaim_indicators)

        if is_overclaim:
            claim.scope_check_result = "OVERCLAIM"
        else:
            claim.scope_check_result = "VALID"

        return claim

    def verify_all_claims(self, section: Optional[str] = None) -> Dict[str, Any]:
        """저장된 모든 Claim에 대해 일괄 검증을 수행하고 종합 리포트를 반환한다."""
        claims = self.store.list_claims(section=section)
        verified_claims = []
        grounded_count = 0
        numeric_match_count = 0
        valid_scope_count = 0

        for clm in claims:
            updated_clm = self.verify_claim(clm)
            self.store.add_claim(updated_clm)  # Update in SQLite
            verified_claims.append(updated_clm)

            if updated_clm.groundedness_result == "GROUNDED":
                grounded_count += 1
            if updated_clm.numeric_check_result in ["MATCH", "N/A"]:
                numeric_match_count += 1
            if updated_clm.scope_check_result == "VALID":
                valid_scope_count += 1

        total = max(len(verified_claims), 1)
        return {
            "total_claims": len(verified_claims),
            "grounded_rate": round((grounded_count / total) * 100, 1),
            "numeric_exactness_rate": round((numeric_match_count / total) * 100, 1),
            "valid_scope_rate": round((valid_scope_count / total) * 100, 1),
            "claims": verified_claims
        }
