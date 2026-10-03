"""
section_requirements.py
PaperDraft: 논문 섹션별 필수 요구 데이터 명세 및 자료 공백(Gap) 판정기
PRD FR-05: 필수 요구를 충족·부족·제외로 판정하고 부족할 때 구체적인 요청서를 만든다.
"""

from typing import List, Dict, Any, Tuple
from models import SectionRequirement, EvidenceRecord
from evidence_store import EvidenceStore


SECTION_ORDER = [
    ("materials_methods", "제4장 연구 방법론 및 시스템 환경 (Materials & Methods)"),
    ("results_discussion", "제5장 실증 검증 및 결과 고찰 (Results & Discussion)"),
    ("limitations", "제6장 연구의 한계점 및 제약 사항 (Limitations & Future Work)"),
    ("introduction", "제1장 서론 및 연구 배경 (Introduction)"),
    ("conclusion", "제7장 결론 (Conclusion)"),
    ("abstract", "논문 초록 (Abstract)")
]


def get_default_section_requirements() -> List[SectionRequirement]:
    """PRD 기준 각 섹션별 필수 요구 데이터 명세를 정의한다."""
    return [
        # 1. Materials & Methods 필수 데이터
        SectionRequirement(
            section_id="materials_methods",
            section_title="제4장 연구 방법론 및 시스템 환경 (Materials & Methods)",
            required_field="hardware_environment",
            field_description="GPU 디바이스 사양 및 최소 VRAM 요구조건 (예: VRAM 8GB 이상)",
            required_type="environment"
        ),
        SectionRequirement(
            section_id="materials_methods",
            section_title="제4장 연구 방법론 및 시스템 환경 (Materials & Methods)",
            required_field="target_model_assumptions",
            field_description="대상 신경망 구조 (Fully-Connected) 및 런타임 섭동(Epsilon) 제약",
            required_type="environment"
        ),
        SectionRequirement(
            section_id="materials_methods",
            section_title="제4장 연구 방법론 및 시스템 환경 (Materials & Methods)",
            required_field="floating_point_precision",
            field_description="수학적 사운드니스 보장을 위한 연산 정밀도 (IEEE 754 FP64 배정밀도)",
            required_type="environment"
        ),
        SectionRequirement(
            section_id="materials_methods",
            section_title="제4장 연구 방법론 및 시스템 환경 (Materials & Methods)",
            required_field="kernel_separation_design",
            field_description="선형 변환 및 ReLU 활성화 함수 상/하한 기울기 CUDA 커널 분리 설계",
            required_type="methodology"
        ),
        SectionRequirement(
            section_id="materials_methods",
            section_title="제4장 연구 방법론 및 시스템 환경 (Materials & Methods)",
            required_field="hybrid_blas_sparse_pipeline",
            field_description="cuBLAS(cublasDgemm)와 cuSPARSE(spMM) 하이브리드 행렬 연산 명세",
            required_type="methodology"
        ),
        SectionRequirement(
            section_id="materials_methods",
            section_title="제4장 연구 방법론 및 시스템 환경 (Materials & Methods)",
            required_field="memory_pool_management",
            field_description="cudaMalloc 드라이버 오버헤드 차단을 위한 정적 메모리 풀 사전 할당 설계",
            required_type="methodology"
        ),

        # 2. Results & Discussion 필수 데이터
        SectionRequirement(
            section_id="results_discussion",
            section_title="제5장 실증 검증 및 결과 고찰 (Results & Discussion)",
            required_field="v3_cusparse_benchmark",
            field_description="v3 (cuSPARSE spMM) 벤치마크 소요시간(85.0ms) 및 가속비(1.18x)",
            required_type="numeric"
        ),
        SectionRequirement(
            section_id="results_discussion",
            section_title="제5장 실증 검증 및 결과 고찰 (Results & Discussion)",
            required_field="v4_memory_pool_benchmark",
            field_description="v4 (Memory Pool) 벤치마크 소요시간(40.0ms), 가속비(2.52x), 지연시간 감소율(88.6%)",
            required_type="numeric"
        ),
        SectionRequirement(
            section_id="results_discussion",
            section_title="제5장 실증 검증 및 결과 고찰 (Results & Discussion)",
            required_field="v5_large_matrix_benchmark",
            field_description="v5 (40,000차원 대규모 가중치) 소요시간(580ms) 및 CPU 대비 가속비(8.96x)",
            required_type="numeric"
        ),
        SectionRequirement(
            section_id="results_discussion",
            section_title="제5장 실증 검증 및 결과 고찰 (Results & Discussion)",
            required_field="mathematical_soundness_proof",
            field_description="CPU 및 GPU Bound 출력값 간 1e-12 오차 범위 내 수학적 정합성 검증 기록",
            required_type="observation"
        ),

        # 3. Limitations & Future Work 필수 데이터
        SectionRequirement(
            section_id="limitations",
            section_title="제6장 연구의 한계점 및 제약 사항 (Limitations & Future Work)",
            required_field="host_to_device_bottleneck",
            field_description="소규모 신경망에서 cudaMemcpy 오버헤드가 전체 60% 이상 차지하는 병목 분석",
            required_type="limitation"
        ),
        SectionRequirement(
            section_id="limitations",
            section_title="제6장 연구의 한계점 및 제약 사항 (Limitations & Future Work)",
            required_field="cusparse_sparsity_threshold",
            field_description="희소도 70% 미만 레이어에서 cuBLAS가 cuSPARSE보다 우수한 성능 역전 임계점",
            required_type="limitation"
        ),
        SectionRequirement(
            section_id="limitations",
            section_title="제6장 연구의 한계점 및 제약 사항 (Limitations & Future Work)",
            required_field="recommended_followups",
            field_description="Unified Memory 및 커널 융합(Kernel Fusion) 기반 추천 후속 과제",
            required_type="recommendation"
        ),

        # 4. Introduction 필수 데이터
        SectionRequirement(
            section_id="introduction",
            section_title="제1장 서론 및 연구 배경 (Introduction)",
            required_field="research_problem",
            field_description="CROWN 신경망 형식 검증의 CPU 고차원 지연시간 병목 현상 정의",
            required_type="problem"
        ),
        SectionRequirement(
            section_id="introduction",
            section_title="제1장 서론 및 연구 배경 (Introduction)",
            required_field="key_contributions",
            field_description="최초 CUDA 병렬화 및 메모리 오버헤드 최소화 브릿지 등 핵심 기여점",
            required_type="contribution"
        )
    ]


class SectionRequirementEvaluator:
    """
    FR-05: 섹션별 필수 요구 충족도 평가 및 자료 부족(Data Gap) 요청서 생성기
    """

    def __init__(self, store: EvidenceStore):
        self.store = store

    def evaluate_section(
        self,
        section_id: str
    ) -> Dict[str, Any]:
        """
        특정 섹션에 대해 필수 요구 충족 여부를 판정한다.
        - FULFILLED (충족: 모든 필수 항목에 대해 유효한 근거가 연결됨)
        - GAP_DETECTED (자료 부족: 필수 항목 중 근거가 없는 항목 존재 -> 자료 요청서 생성)
        """
        reqs = self.store.list_section_requirements(section_id=section_id)
        if not reqs:
            # Fallback to default requirements for section
            all_defaults = get_default_section_requirements()
            reqs = [r for r in all_defaults if r.section_id == section_id]

        evidences = self.store.list_evidences(section_tag=section_id)
        all_ev_texts = " ".join([f"{e.raw_text} {str(e.value or '')} {str(e.conditions)}" for e in evidences]).lower()

        fulfilled_items = []
        missing_items = []

        field_keywords = {
            "hardware_environment": ["gpu", "vram", "8gb", "cuda", "디바이스"],
            "target_model_assumptions": ["fc", "fully-connected", "epsilon", "섭동", "가정"],
            "floating_point_precision": ["fp64", "배정밀도", "ieee", "사운드니스", "precision"],
            "kernel_separation_design": ["커널 분리", "오프로딩", "kernel", "분리"],
            "hybrid_blas_sparse_pipeline": ["cublas", "cusparse", "하이브리드", "spmm"],
            "memory_pool_management": ["메모리 풀", "memory pool", "cudamalloc", "사전 할당"],
            "v3_cusparse_benchmark": ["v3", "85", "1.18"],
            "v4_memory_pool_benchmark": ["v4", "40", "2.52", "88.6"],
            "v5_large_matrix_benchmark": ["v5", "580", "8.96", "40000", "40,000"],
            "mathematical_soundness_proof": ["1e-12", "오차", "soundness", "동등", "수학적"],
            "host_to_device_bottleneck": ["host-to-device", "cudamemcpy", "60%", "병목", "pcie"],
            "cusparse_sparsity_threshold": ["70%", "희소도", "sparsity", "역전", "임계점"],
            "recommended_followups": ["unified memory", "kernel fusion", "후속", "fusion"],
            "research_problem": ["병목", "지연시간", "lirpa", "crown", "cpu"],
            "key_contributions": ["최초", "기여", "설계", "제안"]
        }

        for req in reqs:
            keywords = field_keywords.get(req.required_field, [req.required_field.lower()])
            matched_ev = None

            for ev in evidences:
                ev_str = f"{ev.raw_text} {str(ev.value or '')} {str(ev.conditions)}".lower()
                if any(kw in ev_str for kw in keywords):
                    matched_ev = ev
                    break

            if matched_ev:
                req.status = "제공됨"
                req.linked_evidence_id = matched_ev.evidence_id
                req.data_gap_reason = None
                fulfilled_items.append(req)
            else:
                req.status = "확인 필요"
                req.linked_evidence_id = None
                req.data_gap_reason = f"[{req.section_title}] 작성에 필수적인 '{req.field_description}' 자료가 업로드된 문서에서 식별되지 않았습니다."
                missing_items.append(req)

        # Update requirements in store
        self.store.set_section_requirements(fulfilled_items + missing_items)

        is_fulfilled = len(missing_items) == 0
        status = "FULFILLED" if is_fulfilled else "GAP_DETECTED"

        return {
            "section_id": section_id,
            "status": status,
            "total_requirements": len(reqs),
            "fulfilled_count": len(fulfilled_items),
            "missing_count": len(missing_items),
            "fulfilled_items": fulfilled_items,
            "missing_items": missing_items,
            "gap_request_form": self._generate_gap_request_form(section_id, missing_items) if missing_items else None
        }

    def _generate_gap_request_form(self, section_id: str, missing_items: List[SectionRequirement]) -> Dict[str, Any]:
        """자료 부족 시 사용자에게 제시할 구체적인 요청서 생성 (FR-05)"""
        return {
            "section_id": section_id,
            "request_title": f"🚨 [{section_id}] 작성을 위한 추가 연구자료 요청서",
            "missing_fields": [
                {
                    "field_name": item.required_field,
                    "description": item.field_description,
                    "required_type": item.required_type,
                    "reason": item.data_gap_reason,
                    "recommended_file": "실험 로그 (.txt), 벤치마크 표 (.pdf, .csv), 또는 환경 설정 노트 (.pdf)"
                }
                for item in missing_items
            ],
            "options": [
                "1. 추가 원본 자료 업로드 후 재검색",
                "2. 해당 주장 범위 축소 후 작성 진행",
                "3. 해당 하위 항목 작성 제외 (사용자 승인 기록)"
            ]
        }
