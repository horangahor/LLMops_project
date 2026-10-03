"""
evidence_store.py
PaperDraft: SQLite 기반 Evidence & Claim Store
PRD FR-01, FR-04, FR-08, FR-09 구현
"""

import os
import json
import hashlib
import sqlite3
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

try:
    import pypdf
except ImportError:
    pypdf = None

from models import (
    SourceDocument,
    EvidenceRecord,
    CalculationRecord,
    ClaimRecord,
    SectionRequirement
)

DEFAULT_DB_PATH = Path(__file__).resolve().parent / "result" / "paperdraft_evidence.db"


def compute_file_sha256(file_path: str | Path) -> str:
    """파일의 SHA-256 해시를 계산한다."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class EvidenceStore:
    """
    SQLite 기반의 연구 근거 및 주장(Claim) 영구 저장소
    """

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """테이블 스키마 생성"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 1. Sources Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                source_id TEXT PRIMARY KEY,
                project_id TEXT,
                file_path TEXT,
                file_name TEXT,
                file_hash TEXT UNIQUE,
                file_format TEXT,
                page_count INTEGER,
                registered_at TEXT
            )
            """)

            # 2. Evidences Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidences (
                evidence_id TEXT PRIMARY KEY,
                source_id TEXT,
                source_hash TEXT,
                page INTEGER,
                element_id TEXT,
                evidence_type TEXT,
                experiment_id TEXT,
                section_tags TEXT,
                raw_text TEXT,
                value TEXT,
                unit TEXT,
                conditions TEXT,
                confidence REAL,
                evidence_status TEXT,
                user_review_status TEXT,
                created_at TEXT,
                FOREIGN KEY (source_id) REFERENCES sources (source_id)
            )
            """)

            # 3. Calculations Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS calculations (
                calculation_id TEXT PRIMARY KEY,
                formula TEXT,
                operation TEXT,
                input_values TEXT,
                result_value REAL,
                unit TEXT,
                evidence_ids TEXT,
                calculated_at TEXT
            )
            """)

            # 4. Claims Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                claim_text TEXT,
                paper_section TEXT,
                evidence_ids TEXT,
                calculation_id TEXT,
                groundedness_result TEXT,
                numeric_check_result TEXT,
                scope_check_result TEXT,
                user_review_status TEXT,
                reviewer_comment TEXT,
                created_at TEXT
            )
            """)

            # 5. Section Requirements Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS section_requirements (
                req_id TEXT PRIMARY KEY,
                section_id TEXT,
                section_title TEXT,
                required_field TEXT,
                field_description TEXT,
                required_type TEXT,
                status TEXT,
                linked_evidence_id TEXT,
                data_gap_reason TEXT
            )
            """)

            conn.commit()

    # ==========================================================
    # FR-01: 자료 등록 및 중복 병합
    # ==========================================================

    def register_source(
        self,
        file_path: str | Path,
        project_id: str = "project_cuda_01",
        custom_source_id: Optional[str] = None
    ) -> SourceDocument:
        """
        자료 등록: source_id, 파일 해시, 형식, 페이지 수, 프로젝트 ID를 저장하고
        동일 해시의 중복 파일은 기존 레코드와 병합 반환한다. (FR-01)
        """
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"등록할 파일이 존재하지 않습니다: {path}")

        file_hash = compute_file_sha256(path)
        file_format = path.suffix.lstrip(".").lower()

        # Check existing by hash
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sources WHERE file_hash = ?", (file_hash,))
            row = cursor.fetchone()
            if row:
                return SourceDocument(
                    source_id=row["source_id"],
                    project_id=row["project_id"],
                    file_path=row["file_path"],
                    file_name=row["file_name"],
                    file_hash=row["file_hash"],
                    file_format=row["file_format"],
                    page_count=row["page_count"],
                    registered_at=row["registered_at"]
                )

        # Count pages if PDF
        page_count = 1
        if file_format == "pdf" and pypdf is not None:
            try:
                reader = pypdf.PdfReader(str(path))
                page_count = len(reader.pages)
            except Exception:
                page_count = 1

        source_id = custom_source_id or f"src_{path.stem[:20]}_{file_hash[:6]}"
        registered_at = datetime.utcnow().isoformat()

        doc = SourceDocument(
            source_id=source_id,
            project_id=project_id,
            file_path=str(path),
            file_name=path.name,
            file_hash=file_hash,
            file_format=file_format,
            page_count=page_count,
            registered_at=registered_at
        )

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sources (
                source_id, project_id, file_path, file_name, file_hash, file_format, page_count, registered_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc.source_id, doc.project_id, doc.file_path, doc.file_name,
                doc.file_hash, doc.file_format, doc.page_count, doc.registered_at
            ))
            conn.commit()

        return doc

    def list_sources(self) -> List[SourceDocument]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sources ORDER BY registered_at DESC")
            return [
                SourceDocument(
                    source_id=r["source_id"],
                    project_id=r["project_id"],
                    file_path=r["file_path"],
                    file_name=r["file_name"],
                    file_hash=r["file_hash"],
                    file_format=r["file_format"],
                    page_count=r["page_count"],
                    registered_at=r["registered_at"]
                )
                for r in cursor.fetchall()
            ]

    # ==========================================================
    # FR-03 / FR-04: Evidence CRUD
    # ==========================================================

    def add_evidence(self, ev: EvidenceRecord) -> EvidenceRecord:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO evidences (
                evidence_id, source_id, source_hash, page, element_id,
                evidence_type, experiment_id, section_tags, raw_text,
                value, unit, conditions, confidence, evidence_status,
                user_review_status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ev.evidence_id,
                ev.source_id,
                ev.source_hash,
                ev.page,
                ev.element_id,
                ev.evidence_type,
                ev.experiment_id,
                json.dumps(ev.section_tags, ensure_ascii=False),
                ev.raw_text,
                json.dumps(ev.value, ensure_ascii=False) if ev.value is not None else None,
                ev.unit,
                json.dumps(ev.conditions, ensure_ascii=False),
                ev.confidence,
                ev.evidence_status,
                ev.user_review_status,
                datetime.utcnow().isoformat()
            ))
            conn.commit()
        return ev

    def add_evidences(self, ev_list: List[EvidenceRecord]):
        for ev in ev_list:
            self.add_evidence(ev)

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM evidences WHERE evidence_id = ?", (evidence_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_evidence(row)

    def list_evidences(
        self,
        source_id: Optional[str] = None,
        section_tag: Optional[str] = None,
        evidence_status: Optional[str] = None
    ) -> List[EvidenceRecord]:
        query = "SELECT * FROM evidences WHERE 1=1"
        params = []
        if source_id:
            query += " AND source_id = ?"
            params.append(source_id)
        if evidence_status:
            query += " AND evidence_status = ?"
            params.append(evidence_status)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            evs = [self._row_to_evidence(r) for r in rows]

        if section_tag:
            evs = [e for e in evs if section_tag in e.section_tags]
        return evs

    def update_evidence_status(
        self,
        evidence_id: str,
        evidence_status: str,
        user_review_status: Optional[str] = None
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_review_status:
                cursor.execute(
                    "UPDATE evidences SET evidence_status = ?, user_review_status = ? WHERE evidence_id = ?",
                    (evidence_status, user_review_status, evidence_id)
                )
            else:
                cursor.execute(
                    "UPDATE evidences SET evidence_status = ? WHERE evidence_id = ?",
                    (evidence_status, evidence_id)
                )
            conn.commit()

    def _row_to_evidence(self, row: sqlite3.Row) -> EvidenceRecord:
        val = None
        if row["value"] is not None:
            try:
                val = json.loads(row["value"])
            except Exception:
                val = row["value"]

        return EvidenceRecord(
            evidence_id=row["evidence_id"],
            source_id=row["source_id"],
            source_hash=row["source_hash"],
            page=row["page"],
            element_id=row["element_id"],
            evidence_type=row["evidence_type"],
            experiment_id=row["experiment_id"],
            section_tags=json.loads(row["section_tags"]) if row["section_tags"] else [],
            raw_text=row["raw_text"],
            value=val,
            unit=row["unit"],
            conditions=json.loads(row["conditions"]) if row["conditions"] else {},
            confidence=row["confidence"],
            evidence_status=row["evidence_status"],
            user_review_status=row["user_review_status"]
        )

    # ==========================================================
    # FR-06: Calculation CRUD
    # ==========================================================

    def add_calculation(self, calc: CalculationRecord) -> CalculationRecord:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO calculations (
                calculation_id, formula, operation, input_values,
                result_value, unit, evidence_ids, calculated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                calc.calculation_id,
                calc.formula,
                calc.operation,
                json.dumps(calc.input_values, ensure_ascii=False),
                calc.result_value,
                calc.unit,
                json.dumps(calc.evidence_ids, ensure_ascii=False),
                calc.calculated_at
            ))
            conn.commit()
        return calc

    def get_calculation(self, calculation_id: str) -> Optional[CalculationRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM calculations WHERE calculation_id = ?", (calculation_id,))
            r = cursor.fetchone()
            if not r:
                return None
            return CalculationRecord(
                calculation_id=r["calculation_id"],
                formula=r["formula"],
                operation=r["operation"],
                input_values=json.loads(r["input_values"]) if r["input_values"] else {},
                result_value=r["result_value"],
                unit=r["unit"],
                evidence_ids=json.loads(r["evidence_ids"]) if r["evidence_ids"] else [],
                calculated_at=r["calculated_at"]
            )

    def list_calculations(self) -> List[CalculationRecord]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM calculations ORDER BY calculated_at DESC")
            return [
                CalculationRecord(
                    calculation_id=r["calculation_id"],
                    formula=r["formula"],
                    operation=r["operation"],
                    input_values=json.loads(r["input_values"]) if r["input_values"] else {},
                    result_value=r["result_value"],
                    unit=r["unit"],
                    evidence_ids=json.loads(r["evidence_ids"]) if r["evidence_ids"] else [],
                    calculated_at=r["calculated_at"]
                )
                for r in cursor.fetchall()
            ]

    # ==========================================================
    # FR-07 / FR-08 / FR-09: Claim CRUD
    # ==========================================================

    def add_claim(self, claim: ClaimRecord) -> ClaimRecord:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO claims (
                claim_id, claim_text, paper_section, evidence_ids,
                calculation_id, groundedness_result, numeric_check_result,
                scope_check_result, user_review_status, reviewer_comment,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                claim.claim_id,
                claim.claim_text,
                claim.paper_section,
                json.dumps(claim.evidence_ids, ensure_ascii=False),
                claim.calculation_id,
                claim.groundedness_result,
                claim.numeric_check_result,
                claim.scope_check_result,
                claim.user_review_status,
                claim.reviewer_comment,
                datetime.utcnow().isoformat()
            ))
            conn.commit()
        return claim

    def add_claims(self, claim_list: List[ClaimRecord]):
        for clm in claim_list:
            self.add_claim(clm)

    def list_claims(self, section: Optional[str] = None) -> List[ClaimRecord]:
        query = "SELECT * FROM claims"
        params = []
        if section:
            query += " WHERE paper_section = ?"
            params.append(section)
        query += " ORDER BY claim_id ASC"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [
                ClaimRecord(
                    claim_id=r["claim_id"],
                    claim_text=r["claim_text"],
                    paper_section=r["paper_section"],
                    evidence_ids=json.loads(r["evidence_ids"]) if r["evidence_ids"] else [],
                    calculation_id=r["calculation_id"],
                    groundedness_result=r["groundedness_result"],
                    numeric_check_result=r["numeric_check_result"],
                    scope_check_result=r["scope_check_result"],
                    user_review_status=r["user_review_status"],
                    reviewer_comment=r["reviewer_comment"]
                )
                for r in cursor.fetchall()
            ]

    def update_claim_review(
        self,
        claim_id: str,
        user_review_status: str,
        reviewer_comment: Optional[str] = None
    ):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE claims SET user_review_status = ?, reviewer_comment = ? WHERE claim_id = ?",
                (user_review_status, reviewer_comment, claim_id)
            )
            conn.commit()

    # ==========================================================
    # Section Requirements
    # ==========================================================

    def set_section_requirements(self, reqs: List[SectionRequirement]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM section_requirements")
            for req in reqs:
                req_id = f"{req.section_id}_{req.required_field}"
                cursor.execute("""
                INSERT INTO section_requirements (
                    req_id, section_id, section_title, required_field,
                    field_description, required_type, status,
                    linked_evidence_id, data_gap_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    req_id, req.section_id, req.section_title, req.required_field,
                    req.field_description, req.required_type, req.status,
                    req.linked_evidence_id, req.data_gap_reason
                ))
            conn.commit()

    def list_section_requirements(self, section_id: Optional[str] = None) -> List[SectionRequirement]:
        query = "SELECT * FROM section_requirements"
        params = []
        if section_id:
            query += " WHERE section_id = ?"
            params.append(section_id)
        query += " ORDER BY section_id, required_field"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [
                SectionRequirement(
                    section_id=r["section_id"],
                    section_title=r["section_title"],
                    required_field=r["required_field"],
                    field_description=r["field_description"],
                    required_type=r["required_type"],
                    status=r["status"],
                    linked_evidence_id=r["linked_evidence_id"],
                    data_gap_reason=r["data_gap_reason"]
                )
                for r in cursor.fetchall()
            ]

    def reset_store(self):
        """저장소 초기화 (테스트용)"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM claims")
            cursor.execute("DELETE FROM calculations")
            cursor.execute("DELETE FROM evidences")
            cursor.execute("DELETE FROM sources")
            cursor.execute("DELETE FROM section_requirements")
            conn.commit()
