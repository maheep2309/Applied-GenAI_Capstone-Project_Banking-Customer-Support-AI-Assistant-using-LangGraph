from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).parent.parent

LOG_FILE = (
    PROJECT_ROOT
    / "logs"
    / "banking_assistant_log.log"
)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(message)s"
    )
)

logger = logging.getLogger("banking_assistant")