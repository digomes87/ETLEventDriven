from pathlib import Path

from dotenv import load_dotenv


def load_dataenv(env_path: str | None = ".env") -> None:
    path = Path(env_path or ".env")
    if path.exists():
        load_dotenv(dotenv_path=path, override=False)
