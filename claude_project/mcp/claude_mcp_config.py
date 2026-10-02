import json
import os
from collections import defaultdict
from pathlib import Path
from string import Template

from dotenv import load_dotenv


load_dotenv()


_CONFIG_PATH = Path(__file__).parent.parent / "claude_mcp_servers.json"


def load_mcp_configs(project_path: str | Path | None = None) -> dict:
    """Return mcp_servers from claude_mcp_servers.json with env vars resolved.


    ${CWD} resolves to the selected project, including when it was supplied with
    --project, rather than to the package installation directory.
    """
    environment = defaultdict(str, os.environ)
    environment["CWD"] = str(Path(project_path or Path.cwd()).resolve())
    raw = json.loads(_CONFIG_PATH.read_text(encoding="utf-8"))

    def resolve(value):
        if isinstance(value, dict):
            return {key: resolve(item) for key, item in value.items()}
        if isinstance(value, list):
            return [resolve(item) for item in value]
        if isinstance(value, str):
            return Template(value).safe_substitute(environment)
        return value

    return resolve(raw).get("mcp_servers", {})
