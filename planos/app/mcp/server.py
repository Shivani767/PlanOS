"""MCP server: same Tool Layer as REST, exposed over JSON-RPC/stdio (Phase 7).

Transport: newline-delimited JSON-RPC 2.0 on stdio.
AuthN/Z: caller passes user context per request (service layer enforces it).
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from planos.app.core.permissions import get_role_permissions
from planos.app.db.session import async_session_factory
from planos.app.tools.bootstrap import register_tools
from planos.app.tools.registry import registry

METHOD_TO_TOOL = {
    "planos_get_plan": "get_plan",
    "planos_get_metrics": "get_metrics",
    "planos_create_scenario": "create_scenario",
    "planos_run_scenario": "run_scenario",
    "planos_compare_scenarios": "compare_scenarios",
    "planos_create_change_request": "create_change_request",
    "planos_get_job_status": "get_job_status",
    "planos_search_knowledge": "search_knowledge",
}


async def dispatch(method: str, params: dict[str, Any]) -> dict[str, Any]:
    register_tools()
    if method == "planos_list_tools":
        return {"tools": [t.name for t in registry.list_definitions()]}
    if method == "planos_get_job_status":
        from planos.app.services.jobs import JobService

        async with async_session_factory() as session:
            job = await JobService(session).get(params["job_id"], params["organization_id"])
            return {"job_id": job.id, "status": job.status, "result": job.result}
    tool_name = METHOD_TO_TOOL.get(method)
    if tool_name is None:
        raise ValueError(f"Unknown method '{method}'")
    role = params.pop("role", "VIEWER")
    async with async_session_factory() as session:
        return await registry.execute(
            tool_name,
            params.get("arguments", params),
            session=session,
            organization_id=params["organization_id"],
            user_id=params.get("user_id", ""),
            role=role,
            user_permissions=get_role_permissions(role),
            run_id=params.get("run_id"),
        )


async def serve_stdio() -> None:
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    while True:
        line = await reader.readline()
        if not line:
            break
        try:
            req = json.loads(line)
            result = await dispatch(req["method"], req.get("params", {}))
            resp = {"jsonrpc": "2.0", "id": req.get("id"), "result": result}
        except Exception as exc:  # never leak internals beyond message
            resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(exc)}}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(serve_stdio())
