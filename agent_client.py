"""
agent_client.py

공통 Agent 실행 모듈
Upstage Studio Agent 호출 및 Solar LLM 백업 파이프라인을 지원합니다.
"""

import json
import time
import os
import requests
from pathlib import Path
from openai import OpenAI
import pypdf

from config import UPSTAGE_API_KEY

##################################################
# OpenAI Client (Upstage v2 for Studio)
##################################################

client = OpenAI(
    api_key=UPSTAGE_API_KEY,
    base_url="https://api.upstage.ai/v2"
)

##################################################
# Agent Client
##################################################

class AgentClient:
    """
    Studio Agent 실행 클래스
    Studio Agent ID가 유효한 경우 v2 Responses API를 호출하며,
    Studio Agent 미생성/미배포 상태인 경우 Upstage Solar API를 통해
    기획서 스키마에 맞춘 고품질 정형 데이터를 추출합니다.
    """

    def __init__(
        self,
        agent_id: str,
        config_id: str = "1",
        agent_type: str = "general"
    ):
        self.agent_id = agent_id or ""
        self.config_id = config_id or "1"
        self.agent_type = agent_type

    ##################################################
    # Job 생성 (Studio v2 API)
    ##################################################

    def create_job(self, file_id: str) -> str:
        input_data = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "file_id": file_id
                    }
                ]
            }
        ]

        response = client.responses.create(
            model=self.agent_id,
            include=["last"],
            input=input_data,
            extra_body={
                "config_id": self.config_id
            }
        )

        return response.id

    ##################################################
    # Polling
    ##################################################

    def wait_until_complete(self, job_id: str, interval: int = 2):
        response = client.responses.retrieve(
            job_id,
            include=["last"]
        )

        print(f"Status : {response.status}")

        while response.status in ("queued", "in_progress"):
            time.sleep(interval)
            response = client.responses.retrieve(
                job_id,
                include=["last"]
            )
            print(f"Status : {response.status}")

        if response.status == "failed":
            raise RuntimeError("Studio Agent 실행 실패")

        if response.status != "completed":
            raise RuntimeError(f"Unknown Status : {response.status}")

        print("Job Complete")
        return response

    ##################################################
    # Result Parsing
    ##################################################

    def parse_result(self, response):
        if not response.output_text:
            raise ValueError("output_text가 존재하지 않습니다.")

        try:
            result = json.loads(response.output_text)
        except json.JSONDecodeError:
            raise ValueError("output_text가 JSON 형식이 아닙니다.")

        return result

    ##################################################
    # Solar LLM Fallback Pipeline
    ##################################################

    def run_solar_fallback(self, file_path: str | Path) -> dict:
        """
        Studio Agent가 설정되지 않은 경우, Upstage Solar LLM을 활용하여
        문서로부터 기획서 스키마에 일치하는 JSON을 정형 추출합니다.
        """
        print(f"[*] Upstage Solar 엔진을 통한 {self.agent_type.upper()} 분석 파이프라인 가동...")

        file_path = Path(file_path)
        extracted_text = ""
        if file_path.exists() and file_path.suffix.lower() == ".pdf":
            try:
                reader = pypdf.PdfReader(str(file_path))
                total_pages = len(reader.pages)
                if total_pages <= 25:
                    pages_to_read = range(total_pages)
                else:
                    # For long documents (e.g. 60+ pages), sample key portions
                    pages_to_read = list(range(0, min(12, total_pages))) + \
                                    list(range(total_pages // 2 - 3, min(total_pages // 2 + 5, total_pages))) + \
                                    list(range(max(0, total_pages - 8), total_pages))
                    pages_to_read = sorted(list(set(pages_to_read)))
                extracted_text = "\n".join([f"[Page {i+1}]\n" + reader.pages[i].extract_text() for i in pages_to_read if i < total_pages])
            except Exception as e:
                print("PDF text extraction warning:", e)

        if not extracted_text:
            extracted_text = f"Document: {file_path.name}"

        headers = {
            "Authorization": f"Bearer {UPSTAGE_API_KEY}",
            "Content-Type": "application/json"
        }

        if self.agent_type == "proposal":
            system_prompt = (
                "You are an expert SW Research Proposal Analyzer agent in Upstage Studio. "
                "Analyze the provided software design document and extract structured JSON with the following exact keys:\n"
                "- research_problem: (string) core research problem and bottleneck being solved\n"
                "- proposed_methodology: (list of strings) proposed algorithm, architecture, and CUDA kernel design\n"
                "- key_contributions: (list of strings) novel technical contributions of the research\n"
                "- assumptions: (list of strings) experimental and theoretical assumptions\n"
                "Respond ONLY with a valid JSON object. No markdown, no backticks."
            )
        elif self.agent_type == "validation":
            system_prompt = (
                "You are an expert Empirical Validation & Artifact Analyzer agent in Upstage Studio. "
                "Analyze the provided validation/experiment document and extract structured JSON with the following exact keys:\n"
                "- validation_type: (string) type of validation (e.g. Quantitative Benchmark, Case Study, Profiling)\n"
                "- empirical_evidence: (list of strings) numerical measurements, benchmark times, speedup metrics, memory logs\n"
                "- verified_properties: (list of strings) verified algorithmic and computational properties\n"
                "- limitations: (list of strings) identified bottlenecks, memory transfer overhead, and constraints\n"
                "Respond ONLY with a valid JSON object. No markdown, no backticks."
            )
        elif self.agent_type == "paper_draft":
            system_prompt = (
                "You are an expert Academic Paper Drafting & Coherence Evaluation Agent in Upstage Studio. "
                "Evaluate the synthesized comparison between SW design proposal and empirical evidence. "
                "Classify the degree of empirical support into one of: 'Strongly Supported', 'Partially Supported', or 'Weakly Supported'. "
                "Then generate a comprehensive, publication-grade academic paper draft as a structured JSON with the following exact keys:\n"
                "- support_level: (string) 'Strongly Supported' | 'Partially Supported' | 'Weakly Supported'\n"
                "- coherence_score: (number) integer score 0 to 100 indicating how well evidence supports the proposal\n"
                "- abstract: (string) A comprehensive academic Abstract in professional Korean summarizing research goal, proposed CUDA acceleration, and empirical performance gains\n"
                "- introduction_draft: (string) Chapter 1 Introduction draft in Korean detailing research background, the need for neural network robustness verification (LiRPA/CROWN), CPU computational bottleneck, and paper roadmap\n"
                "- related_work_draft: (string) Chapter 2 Related Work & Background draft in Korean reviewing formal verification of deep neural networks, GPU parallelism, and technical comparison with existing tools\n"
                "- system_design_draft: (string) Chapter 3 System Architecture & Model draft in Korean explaining the end-to-end acceleration pipeline, backward bound propagation flow, and execution assumptions\n"
                "- methodology_draft: (string) Chapter 4 Methodology & Kernel Optimization draft in Korean covering kernel separation, cuBLAS/cuSPARSE hybrid execution, CUDA memory pool management, and async stream overlapping\n"
                "- validation_draft: (string) Chapter 5 Empirical Evaluation & Discussion draft in Korean covering benchmark configurations (v3, v4, v5), quantitative speedups (up to 8.96x), and mathematical error verification (within 1e-12)\n"
                "- limitations_draft: (string) Chapter 6 Limitations & Discussion draft in Korean explicitly analyzing host-to-device PCIe transfer bottlenecks in smaller networks, sparsity threshold (cuSPARSE performance inversion under 70% sparsity), and hardware constraints\n"
                "- conclusion_draft: (string) Chapter 7 Conclusion & Future Work draft in Korean summarizing core achievements and detailing technical follow-up roadmaps including Unified Memory and Kernel Fusion\n"
                "- supported_contributions: (list of strings) key contributions fully substantiated by empirical data\n"
                "- limitations_list: (list of strings) key identified technical bottlenecks and constraints\n"
                "- recommended_followups: (list of strings) recommended follow-up experiments and architectural optimizations\n"
                "Respond ONLY with a valid JSON object. No markdown, no backticks."
            )
        else:
            system_prompt = "Extract key information as a structured JSON object. Respond only with JSON."

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Document Text:\n{extracted_text[:6000]}"}
        ]

        payload = {
            "model": "solar-pro",
            "messages": messages,
            "temperature": 0.2
        }

        resp = requests.post(
            "https://api.upstage.ai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        if resp.status_code != 200:
            raise RuntimeError(f"Solar LLM API Failed: {resp.status_code} - {resp.text}")

        content = resp.json()["choices"][0]["message"]["content"].strip()
        # Clean markdown codeblocks if any
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        return json.loads(content)

    ##################################################
    # Agent 실행
    ##################################################

    def run(self, file_id: str, file_path: str | Path = None) -> dict:
        print("-" * 60)
        print(f"Run Agent : {self.agent_type.upper()}")
        print("-" * 60)

        # 1. Try Studio v2 API if agent_id looks configured
        if self.agent_id and not self.agent_id.startswith("agt_Draft") and not self.agent_id.startswith("agt_Proposal"):
            try:
                print(f"Agent ID  : {self.agent_id}")
                print(f"Config ID : {self.config_id}")
                print(f"File ID   : {file_id}")
                print()

                job_id = self.create_job(file_id)
                print(f"Job ID : {job_id}")
                print("Waiting...")
                response = self.wait_until_complete(job_id)
                result = self.parse_result(response)
                print("JSON Parsing Complete")
                return result
            except Exception as e:
                print(f"[Notice] Studio Agent ({self.agent_id}) 호출 실패: {e}")
                print("[Notice] Upstage Solar 파이프라인으로 전환합니다.")

        # 2. Solar Fallback
        if file_path is None:
            raise ValueError("Solar 처리를 위해 file_path가 필요합니다.")

        result = self.run_solar_fallback(file_path)
        print("JSON Parsing Complete (via Upstage Solar)")
        return result