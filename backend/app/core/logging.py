import logging
from pathlib import Path


def configure_rusprofile_logging() -> None:
    log_dir = Path("tmp/rusprofile")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "rusprofile.log"

    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.INFO)

    if any(getattr(handler, "baseFilename", None) == str(log_path.resolve()) for handler in app_logger.handlers):
        return

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    app_logger.addHandler(file_handler)
