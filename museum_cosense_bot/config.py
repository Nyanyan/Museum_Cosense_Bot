from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ENV_PATH = PROJECT_ROOT / "museum_cosense_bot" / ".env"
LEGACY_ENV_PATH = PROJECT_ROOT / "cosense-sample" / ".env"


def load_environment() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(PACKAGE_ENV_PATH, override=False)
    load_dotenv(LEGACY_ENV_PATH, override=False)


def project_root() -> Path:
    return PROJECT_ROOT