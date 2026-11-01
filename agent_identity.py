"""Gestión de autenticación AgentID (OAuth 2.0 client_credentials) para proxies MCP en WSO2 Agent Manager."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator

import httpx

from config import Config

log = logging.getLogger("ayuntamiento-agent-identity")


class AgentIdentityNotProvisionedError(Exception):
    """Indica que AgentID aún no está disponible en este entorno."""


class AgentIdentityAuth(httpx.Auth):
    """Adjunta un token Bearer generado con las credenciales de AgentID inyectadas por WSO2 Agent Manager."""

    def __init__(self, cfg: Config, resource: str) -> None:
        self._cfg = cfg
        self._resource = resource
        self._token: str | None = None
        self._expiry = 0.0
        self._lock = asyncio.Lock()

    async def async_auth_flow(
        self, request: httpx.Request
    ) -> AsyncGenerator[httpx.Request, httpx.Response]:
        request.headers["Authorization"] = f"Bearer {await self._get_token()}"
        yield request

    async def _get_token(self) -> str:
        async with self._lock:
            now = time.time()
            if self._token is not None and now < self._expiry - 60:
                return self._token

            if not self._cfg.agentid_ready:
                raise AgentIdentityNotProvisionedError(
                    "Credenciales AMP_AGENTID_* no configuradas en el entorno."
                )

            data: dict[str, str] = {
                "grant_type": "client_credentials",
                "client_id": self._cfg.agentid_client_id,
                "client_secret": self._cfg.agentid_client_secret,
            }
            if self._resource:
                data["resource"] = self._resource
            if self._cfg.agentid_scopes:
                data["scope"] = self._cfg.agentid_scopes

            async with httpx.AsyncClient() as client:
                resp = await client.post(self._cfg.agentid_token_endpoint, data=data)
                resp.raise_for_status()
                payload = resp.json()

            token = payload.get("access_token")
            expires_in = payload.get("expires_in", 3600)
            if not token:
                raise RuntimeError("La respuesta de ThunderID no incluyó access_token")

            self._token = str(token)
            self._expiry = now + float(expires_in)
            log.info("Token AgentID obtenido/renovado para el recurso: %s", self._resource)
            return self._token

