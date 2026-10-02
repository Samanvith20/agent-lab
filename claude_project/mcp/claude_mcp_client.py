import asyncio
import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from claude_project.mcp.claude_mcp_config import load_mcp_configs
from claude_project.observability.logger import get_logger


logger = get_logger(__name__)


async def get_mcp_tools(project_path: str | None = None) -> list:
    """Load tools from each configured MCP server independently.

    An unavailable optional MCP server should not prevent local codebase search
    and Q&A from starting. Isolating connections also identifies which server
    failed during startup.
    """
    configs = load_mcp_configs(project_path)
    logger.info(f"Connecting to MCP servers: {list(configs.keys())}")

    try:
        timeout = max(1, int(os.getenv("MCP_STARTUP_TIMEOUT_SECONDS", "30")))
    except ValueError:
        timeout = 30
        logger.warning("Invalid MCP_STARTUP_TIMEOUT_SECONDS; using 30 seconds")

    async def load_server(server_name: str, server_config: dict) -> list:
        try:
            client = MultiServerMCPClient({server_name: server_config})
            server_tools = await asyncio.wait_for(client.get_tools(), timeout=timeout)
            logger.info("Loaded %d tools from MCP server %s", len(server_tools), server_name)
            return server_tools
        except Exception:
            logger.exception(
                "MCP server %s failed to start within %d seconds; continuing without its tools",
                server_name, timeout,
            )
            return []

    server_tools = await asyncio.gather(
        *(load_server(name, server_config) for name, server_config in configs.items())
    )
    tools = [tool for tools_for_server in server_tools for tool in tools_for_server]
    if not tools:
        logger.warning("No MCP tools loaded; codebase search will still be available")
    else:
        logger.info("Loaded %d MCP tools total", len(tools))
    return tools
