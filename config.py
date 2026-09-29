"""
config.py

PaperDraft AI: SW 연구 및 실증 데이터 기반 논문 초안 생성 서비스
프로젝트 환경설정
"""

import os
from pathlib import Path
from dotenv import load_dotenv

##################################################
# Load Environment
##################################################

load_dotenv()

##################################################
# Upstage API
##################################################

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")

##################################################
# Proposal Agent (Document A)
##################################################

PROPOSAL_AGENT_ID = os.getenv("PROPOSAL_AGENT_ID") or os.getenv("RESUME_AGENT_ID")
PROPOSAL_CONFIG_ID = os.getenv("PROPOSAL_CONFIG_ID") or os.getenv("RESUME_CONFIG_ID", "1")

# Aliases for backward compatibility
RESUME_AGENT_ID = PROPOSAL_AGENT_ID
RESUME_CONFIG_ID = PROPOSAL_CONFIG_ID

##################################################
# Validation Agent (Document B)
##################################################

VALIDATION_AGENT_ID = os.getenv("VALIDATION_AGENT_ID") or os.getenv("JD_AGENT_ID")
VALIDATION_CONFIG_ID = os.getenv("VALIDATION_CONFIG_ID") or os.getenv("JD_CONFIG_ID", "1")

# Aliases for backward compatibility
JD_AGENT_ID = VALIDATION_AGENT_ID
JD_CONFIG_ID = VALIDATION_CONFIG_ID

##################################################
# Paper Draft Agent (Synthesis & Evaluation)
##################################################

PAPER_DRAFT_AGENT_ID = os.getenv("PAPER_DRAFT_AGENT_ID") or os.getenv("MATCHING_AGENT_ID")
PAPER_DRAFT_CONFIG_ID = os.getenv("PAPER_DRAFT_CONFIG_ID") or os.getenv("MATCHING_CONFIG_ID", "1")

# Aliases for backward compatibility
MATCHING_AGENT_ID = PAPER_DRAFT_AGENT_ID
MATCHING_CONFIG_ID = PAPER_DRAFT_CONFIG_ID

##################################################
# Project Directories
##################################################

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
RESULT_DIR = BASE_DIR / "result"

##################################################
# Input Files
##################################################

PROPOSAL_FILE = DATA_DIR / "SW_Design_Notes.pdf"
if not PROPOSAL_FILE.exists() and (DATA_DIR / "Resume.pdf").exists():
    PROPOSAL_FILE = DATA_DIR / "Resume.pdf"

VALIDATION_FILE = DATA_DIR / "Validation_Report.pdf"
if not VALIDATION_FILE.exists() and (DATA_DIR / "JobDescription.pdf").exists():
    VALIDATION_FILE = DATA_DIR / "JobDescription.pdf"

RAW_GPU_FILE = DATA_DIR / "GPU_Programming_CUDA_Parallel_Processing.pdf"

# Aliases for backward compatibility
RESUME_FILE = PROPOSAL_FILE
JD_FILE = VALIDATION_FILE

##################################################
# Output Files
##################################################

PROPOSAL_JSON = OUTPUT_DIR / "proposal.json"
VALIDATION_JSON = OUTPUT_DIR / "validation.json"
EVALUATION_PDF = OUTPUT_DIR / "Evaluation_Input.pdf"
PAPER_DRAFT_RESULT = RESULT_DIR / "matching_result.json"
PAPER_DRAFT_MD = RESULT_DIR / "Paper_Draft_Sections.md"
PAPER_DRAFT_PDF = RESULT_DIR / "Paper_Draft.pdf"

# Aliases for backward compatibility
RESUME_JSON = PROPOSAL_JSON
JD_JSON = VALIDATION_JSON
MATCHING_PDF = EVALUATION_PDF
MATCHING_RESULT = PAPER_DRAFT_RESULT

##################################################
# Fonts
##################################################

FONT_NAME = "Nanum"
FONT_PATH = BASE_DIR / "fonts" / "NanumGothic-Regular.ttf"

##################################################
# Directory Initialization
##################################################

def create_directories():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

##################################################
# Configuration Validation
##################################################

def validate_config():
    required = {
        "UPSTAGE_API_KEY": UPSTAGE_API_KEY,
    }

    missing = [key for key, value in required.items() if not value]

    if missing:
        raise ValueError(
            "다음 환경변수가 설정되지 않았습니다.\n\n"
            + "\n".join(missing)
        )

    create_directories()

##################################################
# Project Information
##################################################

def print_config():
    print("=" * 60)
    print("Project Configuration : PaperDraft AI Service")
    print("=" * 60)
    print(f"Project Directory    : {BASE_DIR}")
    print(f"Data Directory       : {DATA_DIR}")
    print(f"Output Directory     : {OUTPUT_DIR}")
    print(f"Result Directory     : {RESULT_DIR}")
    print()
    print(f"Proposal Agent       : {PROPOSAL_AGENT_ID}")
    print(f"Validation Agent     : {VALIDATION_AGENT_ID}")
    print(f"Paper Draft Agent    : {PAPER_DRAFT_AGENT_ID}")
    print("=" * 60)