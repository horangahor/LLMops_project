"""
calculation_engine.py
PaperDraft: Python 기반 결정론 계산 엔진
PRD FR-06: Python이 통계, 단위 변환, speedup과 표를 생성하고 계산식을 보존한다.
(LLM에게 평균·speedup·단위 변환 등 수치 계산을 위임하지 않음)
"""

from typing import List, Dict, Any, Optional
import math
from datetime import datetime

from models import CalculationRecord


class DeterministicCalculationEngine:
    """
    수치 계산의 엄밀성과 무결성을 보장하기 위한 결정론 연산 엔진
    모든 연산 결과는 고유 calculation_id와 함께 계산식(formula), 입력값, 근거 ID를 보존한다.
    """

    @staticmethod
    def calculate_speedup(
        baseline_time: float,
        accelerated_time: float,
        time_unit: str = "ms",
        baseline_name: str = "CPU",
        accelerated_name: str = "GPU",
        evidence_ids: Optional[List[str]] = None,
        calc_id: Optional[str] = None
    ) -> CalculationRecord:
        """
        가속비 (Speedup) 계산: Baseline / Accelerated
        예: CPU (5200ms) / GPU (580ms) = 8.965x -> 8.96x
        """
        if accelerated_time <= 0:
            raise ValueError("가속 실행 시간은 0보다 커야 합니다.")

        speedup_raw = baseline_time / accelerated_time
        speedup = round(speedup_raw, 2)

        formula = f"{baseline_name} ({baseline_time}{time_unit}) / {accelerated_name} ({accelerated_time}{time_unit}) = {speedup}x (원시값: {speedup_raw:.4f})"
        cid = calc_id or f"calc_speedup_{accelerated_name.lower()}_{int(speedup * 100)}"

        return CalculationRecord(
            calculation_id=cid,
            formula=formula,
            operation="speedup",
            input_values={
                "baseline_name": baseline_name,
                "baseline_time": baseline_time,
                "accelerated_name": accelerated_name,
                "accelerated_time": accelerated_time,
                "unit": time_unit
            },
            result_value=speedup,
            unit="x",
            evidence_ids=evidence_ids or []
        )

    @staticmethod
    def calculate_latency_reduction(
        initial_latency: float,
        optimized_latency: float,
        time_unit: str = "ms",
        initial_name: str = "초기 GPU",
        optimized_name: str = "메모리 풀 적용",
        evidence_ids: Optional[List[str]] = None,
        calc_id: Optional[str] = None
    ) -> CalculationRecord:
        """
        지연시간 감소율 (%) 계산: ((Initial - Optimized) / Initial) * 100
        예: ((353ms - 40ms) / 353ms) * 100 = 88.67% -> 88.6%
        """
        if initial_latency <= 0:
            raise ValueError("초기 지연시간은 0보다 커야 합니다.")

        reduction_raw = ((initial_latency - optimized_latency) / initial_latency) * 100.0
        reduction = round(reduction_raw, 1)

        formula = f"(({initial_name} {initial_latency}{time_unit} - {optimized_name} {optimized_latency}{time_unit}) / {initial_latency}{time_unit}) * 100 = {reduction}%"
        cid = calc_id or f"calc_reduction_{int(reduction * 10)}"

        return CalculationRecord(
            calculation_id=cid,
            formula=formula,
            operation="latency_reduction",
            input_values={
                "initial_name": initial_name,
                "initial_latency": initial_latency,
                "optimized_name": optimized_name,
                "optimized_latency": optimized_latency,
                "unit": time_unit
            },
            result_value=reduction,
            unit="%",
            evidence_ids=evidence_ids or []
        )

    @staticmethod
    def calculate_throughput_ratio(
        baseline_throughput: float,
        accelerated_throughput: float,
        unit: str = "items/s",
        evidence_ids: Optional[List[str]] = None,
        calc_id: Optional[str] = None
    ) -> CalculationRecord:
        """
        처리량 향상비 (Throughput Ratio) 계산
        """
        if baseline_throughput <= 0:
            raise ValueError("기준 처리량은 0보다 커야 합니다.")

        ratio = round(accelerated_throughput / baseline_throughput, 2)
        formula = f"처리량 비율: {accelerated_throughput} {unit} / {baseline_throughput} {unit} = {ratio}배"
        cid = calc_id or f"calc_throughput_{int(ratio * 10)}"

        return CalculationRecord(
            calculation_id=cid,
            formula=formula,
            operation="throughput_ratio",
            input_values={
                "baseline_throughput": baseline_throughput,
                "accelerated_throughput": accelerated_throughput,
                "unit": unit
            },
            result_value=ratio,
            unit="배",
            evidence_ids=evidence_ids or []
        )

    @staticmethod
    def generate_benchmark_summary_table(
        benchmark_entries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Results & Discussion 섹션에 삽입될 정량적 벤치마크 표 및 계산식을 자동 조립한다.
        """
        table_rows = []
        calculations = []

        for entry in benchmark_entries:
            baseline = entry.get("cpu_ms", 100.0)
            target = entry.get("gpu_ms", 50.0)
            name = entry.get("name", "벤치마크")
            ev_ids = entry.get("evidence_ids", [])

            calc = DeterministicCalculationEngine.calculate_speedup(
                baseline_time=baseline,
                accelerated_time=target,
                time_unit="ms",
                baseline_name="CPU",
                accelerated_name=name,
                evidence_ids=ev_ids
            )
            calculations.append(calc)

            table_rows.append({
                "benchmark_name": name,
                "cpu_latency_ms": baseline,
                "gpu_latency_ms": target,
                "speedup": f"{calc.result_value}x",
                "calculation_id": calc.calculation_id,
                "formula": calc.formula
            })

        return {
            "columns": ["실험 항목", "CPU 소요시간(ms)", "GPU 소요시간(ms)", "가속비", "계산 검증식"],
            "rows": table_rows,
            "calculations": calculations
        }
