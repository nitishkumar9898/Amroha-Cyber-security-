import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


class ToolPermissionError(Exception):
    pass


class ToolTimeoutError(Exception):
    pass


class ToolRateLimitError(Exception):
    pass


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)
    required_clearance: str = "analyst"
    timeout_default: int = 60
    retry_default: int = 3
    rate_limit_per_minute: int = 30
    module_id: str = ""


@dataclass
class ToolCallRecord:
    tool_name: str
    start_time: float
    end_time: float
    success: bool
    error: Optional[str] = None


class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, Callable[..., Awaitable[dict[str, Any]]]] = {}
        self._call_history: list[ToolCallRecord] = []
        self._rate_limiters: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    def register_tool(
        self,
        name: str,
        description: str,
        handler: Callable[..., Awaitable[dict[str, Any]]],
        parameters: Optional[dict[str, Any]] = None,
        required_clearance: str = "analyst",
        timeout_default: int = 60,
        retry_default: int = 3,
        rate_limit_per_minute: int = 30,
        module_id: str = "",
    ) -> ToolDefinition:
        tool_def = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters or {},
            required_clearance=required_clearance,
            timeout_default=timeout_default,
            retry_default=retry_default,
            rate_limit_per_minute=rate_limit_per_minute,
            module_id=module_id,
        )
        self._tools[name] = tool_def
        self._handlers[name] = handler
        self._rate_limiters.setdefault(name, [])
        logger.info("Registered tool: %s (module=%s, clearance=%s)", name, module_id, required_clearance)
        return tool_def

    def unregister_tool(self, name: str) -> None:
        self._tools.pop(name, None)
        self._handlers.pop(name, None)
        self._rate_limiters.pop(name, None)
        logger.info("Unregistered tool: %s", name)

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> dict[str, ToolDefinition]:
        return dict(self._tools)

    def list_tools_by_clearance(self, clearance: str) -> list[ToolDefinition]:
        clearance_levels = {"admin": 4, "senior_analyst": 3, "analyst": 2, "junior": 1}
        required = clearance_levels.get(clearance, 0)
        return [
            t for t in self._tools.values()
            if clearance_levels.get(t.required_clearance, 0) <= required
        ]

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def check_permission(self, tool_name: str, user_clearance: str) -> bool:
        tool = self.get_tool(tool_name)
        if tool is None:
            return False
        clearance_levels = {"admin": 4, "senior_analyst": 3, "analyst": 2, "junior": 1}
        user_level = clearance_levels.get(user_clearance, 0)
        tool_level = clearance_levels.get(tool.required_clearance, 0)
        return user_level >= tool_level

    async def _check_rate_limit(self, tool_name: str) -> None:
        now = time.time()
        window = 60.0
        self._rate_limiters.setdefault(tool_name, [])
        self._rate_limiters[tool_name] = [
            t for t in self._rate_limiters[tool_name] if now - t < window
        ]
        tool = self.get_tool(tool_name)
        if tool and len(self._rate_limiters[tool_name]) >= tool.rate_limit_per_minute:
            raise ToolRateLimitError(
                f"Rate limit exceeded for tool '{tool_name}': "
                f"{tool.rate_limit_per_minute} calls per minute"
            )

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Optional[dict[str, Any]] = None,
        user_clearance: str = "analyst",
        timeout: Optional[int] = None,
        retries: Optional[int] = None,
    ) -> dict[str, Any]:
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Unknown tool: {tool_name}")

        if not self.check_permission(tool_name, user_clearance):
            raise ToolPermissionError(
                f"Clearance '{user_clearance}' insufficient for tool '{tool_name}' "
                f"(requires '{tool.required_clearance}')"
            )

        await self._check_rate_limit(tool_name)

        handler = self._handlers.get(tool_name)
        if handler is None:
            raise ValueError(f"No handler registered for tool: {tool_name}")

        effective_timeout = timeout or tool.timeout_default
        effective_retries = retries or tool.retry_default
        params = parameters or {}

        last_error: Optional[str] = None
        for attempt in range(effective_retries):
            try:
                start = time.monotonic()
                result = await asyncio.wait_for(
                    handler(**params),
                    timeout=effective_timeout,
                )
                elapsed = (time.monotonic() - start) * 1000

                async with self._lock:
                    self._rate_limiters[tool_name].append(time.time())
                    self._call_history.append(ToolCallRecord(
                        tool_name=tool_name,
                        start_time=start,
                        end_time=time.monotonic(),
                        success=True,
                    ))

                return {
                    "success": True,
                    "data": result,
                    "tool_name": tool_name,
                    "execution_time_ms": int(elapsed),
                    "attempt": attempt + 1,
                }

            except asyncio.TimeoutError:
                last_error = f"Timeout after {effective_timeout}s (attempt {attempt + 1}/{effective_retries})"
                logger.warning("Tool %s timeout attempt %d/%d", tool_name, attempt + 1, effective_retries)
                if attempt < effective_retries - 1:
                    await asyncio.sleep(2 ** attempt)
            except ToolPermissionError:
                raise
            except ToolRateLimitError:
                raise
            except Exception as e:
                last_error = str(e)
                logger.warning("Tool %s error attempt %d/%d: %s", tool_name, attempt + 1, effective_retries, e)
                if attempt < effective_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        async with self._lock:
            self._call_history.append(ToolCallRecord(
                tool_name=tool_name,
                start_time=time.time(),
                end_time=time.time(),
                success=False,
                error=last_error,
            ))

        return {
            "success": False,
            "data": {},
            "error": last_error or "Unknown error",
            "tool_name": tool_name,
            "execution_time_ms": 0,
            "attempt": effective_retries,
        }

    def get_call_history(self, tool_name: Optional[str] = None) -> list[ToolCallRecord]:
        if tool_name:
            return [r for r in self._call_history if r.tool_name == tool_name]
        return list(self._call_history)

    def get_statistics(self) -> dict[str, Any]:
        total = len(self._call_history)
        successes = sum(1 for r in self._call_history if r.success)
        failures = total - successes
        tool_stats: dict[str, dict[str, int]] = {}
        for r in self._call_history:
            if r.tool_name not in tool_stats:
                tool_stats[r.tool_name] = {"total": 0, "success": 0, "failure": 0}
            tool_stats[r.tool_name]["total"] += 1
            if r.success:
                tool_stats[r.tool_name]["success"] += 1
            else:
                tool_stats[r.tool_name]["failure"] += 1

        return {
            "total_calls": total,
            "successful": successes,
            "failed": failures,
            "success_rate": successes / total if total > 0 else 0,
            "registered_tools": len(self._tools),
            "tool_stats": tool_stats,
        }

    def discover_from_sentinel(self, modules: list[dict[str, Any]]) -> int:
        discovered = 0
        for mod in modules:
            module_id = mod.get("id", "")
            capabilities = mod.get("capabilities", [])
            for cap in capabilities:
                tool_name = f"{module_id}.{cap}"
                if not self.has_tool(tool_name):

                    async def _passthrough(**kw: Any) -> dict[str, Any]:
                        return {"module": module_id, "capability": cap, "params": kw}

                    self.register_tool(
                        name=tool_name,
                        description=f"{cap} from {module_id}",
                        handler=_passthrough,
                        module_id=module_id,
                    )
                    discovered += 1
        return discovered
