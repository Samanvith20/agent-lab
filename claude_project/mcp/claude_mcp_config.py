import json
import os
from collections import defaultdict
from pathlib import Path
from string import Template

from dotenv import load_dotenv
from claude_project.observability.logger import get_logger


_CONFIG_PATH = Path(__file__).parent.parent / "claude_mcp_servers.json"
logger = get_logger(__name__)

# Always load the CLI's own credentials, regardless of the directory from which
# the global command was launched.
load_dotenv(Path(__file__).resolve().parents[2] / ".env")


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

    servers = resolve(raw).get("mcp_servers", {})
    github = servers.get("github")
    if github is not None:
        token = (
            os.getenv("GITHUB_TOKEN", "").strip()
            or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "").strip()
        )
        if not token:
            logger.warning(
                "GitHub MCP disabled: set GITHUB_TOKEN in the Agent Lab .env file "
                "to enable authenticated GitHub tools"
            )
            servers.pop("github")
        else:
            github.setdefault("env", {})["GITHUB_PERSONAL_ACCESS_TOKEN"] = token
    return servers
