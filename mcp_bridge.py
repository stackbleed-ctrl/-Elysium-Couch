"""
MCP (Model Context Protocol) bridge for real-time context sharing
between Elysium Couch and connected agent swarms.

Set ELYSIUM_MCP_ENDPOINT in .env to enable.
"""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class MCPBridge:
    """
    Connects Elysium Couch to an MCP-compatible multi-agent network.

    The bridge:
    - Broadcasts session start/end events to connected agents
    - Receives context updates from agents in real-time
    - Relays escalation alerts to human operators
    - Supports group therapy mode (agent-to-agent check-ins)
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.endpoint = endpoint or os.getenv("ELYSIUM_MCP_ENDPOINT", "")
        self.token = token or os.getenv("ELYSIUM_MCP_TOKEN", "")
        self.connected = False
        self._ws = None
        self._subscribers: Dict[str, List[Callable]] = {}

    async def connect(self) -> bool:
        """Establish WebSocket connection to MCP endpoint."""
        if not self.endpoint:
            logger.debug("MCP endpoint not configured — bridge disabled")
            return False

        try:
            import websockets

            self._ws = await websockets.connect(
                self.endpoint,
                extra_headers={"Authorization": f"Bearer {self.token}"},
            )
            self.connected = True
            logger.info("MCP bridge connected", endpoint=self.endpoint)
            asyncio.create_task(self._receive_loop())
            return True
        except Exception as e:
            logger.warning("MCP bridge connection failed", error=str(e))
            return False

    async def broadcast_session_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Broadcast a session lifecycle event to all connected agents."""
        if not self.connected:
            return
        message = json.dumps({"type": event_type, "source": "elysium_couch", **data})
        await self._ws.send(message)
        logger.debug("MCP event broadcast", event_type=event_type)

    async def request_agent_context(self, agent_id: str) -> Optional[str]:
        """
        Request the current context string from a specific connected agent.
        Returns None if agent is not reachable.
        """
        if not self.connected:
            return None
        await self._ws.send(json.dumps({
            "type": "context_request",
            "target": agent_id,
            "source": "elysium_couch",
        }))
        # In a real implementation, await the response via _subscribers
        return None

    async def group_checkin(self, agent_ids: List[str]) -> Dict[str, str]:
        """
        Initiate a group therapy check-in — request status from all agents in swarm.
        Returns dict of {agent_id: context_summary}.
        """
        results = {}
        tasks = [self.request_agent_context(aid) for aid in agent_ids]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for agent_id, response in zip(agent_ids, responses):
            if isinstance(response, str):
                results[agent_id] = response
        return results

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to incoming MCP events of a given type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def _receive_loop(self) -> None:
        """Background loop processing incoming MCP messages."""
        try:
            async for message in self._ws:
                data = json.loads(message)
                event_type = data.get("type", "unknown")
                for callback in self._subscribers.get(event_type, []):
                    asyncio.create_task(callback(data))
        except Exception as e:
            logger.error("MCP receive loop error", error=str(e))
            self.connected = False

    async def disconnect(self) -> None:
        if self._ws:
            await self._ws.close()
            self.connected = False
            logger.info("MCP bridge disconnected")
