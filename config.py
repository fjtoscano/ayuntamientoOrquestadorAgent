from __future__ import annotations

import os
from dataclasses import dataclass


def _env(name: str, default: str | None = None) -> str:
    val = os.environ.get(name, default)
    if val is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


@dataclass(frozen=True)
class Config:
    company_name: str
    tone: str
    additional_guidance: str
    agent_version: str
    llm_model: str
    embedding_model: str
    vector_db_url: str
    use_llm_provider: bool
    llm_provider_url: str
    llm_provider_key: str
    use_mcp: bool
    mcp_url: str
    mcp_api_key: str
    mcp_oauth: bool
    agentid_client_id: str
    agentid_client_secret: str
    agentid_token_endpoint: str
    agentid_scopes: str

    @property
    def agentid_ready(self) -> bool:
        return bool(
            self.agentid_client_id
            and self.agentid_client_secret
            and self.agentid_token_endpoint
        )

    @classmethod
    def from_env(cls) -> "Config":
        use_llm_provider = _env("USE_LLM_PROVIDER", "false").lower() == "true"
        llm_provider_url = _env("LLM_PROVIDER_URL", "")
        llm_provider_key = _env("LLM_PROVIDER_KEY", "")

        if use_llm_provider:
            if not llm_provider_url:
                raise RuntimeError("USE_LLM_PROVIDER is true but LLM_PROVIDER_URL is not set")
            if not llm_provider_key:
                raise RuntimeError("USE_LLM_PROVIDER is true but LLM_PROVIDER_KEY is not set")

        use_mcp = _env("USE_MCP", "false").lower() == "true"
        mcp_url = _env("MCP_URL", "")
        mcp_api_key = _env("MCP_API_KEY", "")
        mcp_oauth = _env("MCP_OAUTH", "false").lower() == "true"

        # Default Vector DB URL connects to local cluster postgres-vector (localhost:5432 from host or postgres-vector-service:5432 in cluster)
        default_vector_url = os.environ.get(
            "VECTOR_DB_URL",
            "postgresql://postgres:postgres@localhost:5432/agent_memory_db",
        )

        return cls(
            company_name=_env("COMPANY_NAME", "Ayuntamiento - Servicio de Atención Ciudadana"),
            tone=_env("TONE", "servicial, claro, institucional, empático y estructurado"),
            additional_guidance=_env("ADDITIONAL_GUIDANCE", ""),
            agent_version=_env("AGENT_VERSION", "1.0.0"),
            llm_model=_env("LLM_MODEL", "gpt-4o-mini"),
            embedding_model=_env("EMBEDDING_MODEL", "text-embedding-3-small"),
            vector_db_url=default_vector_url,
            use_llm_provider=use_llm_provider,
            llm_provider_url=llm_provider_url,
            llm_provider_key=llm_provider_key,
            use_mcp=use_mcp,
            mcp_url=mcp_url,
            mcp_api_key=mcp_api_key,
            mcp_oauth=mcp_oauth,
            agentid_client_id=_env("AMP_AGENTID_CLIENT_ID", ""),
            agentid_client_secret=_env("AMP_AGENTID_CLIENT_SECRET", ""),
            agentid_token_endpoint=_env("AMP_AGENTID_TOKEN_ENDPOINT", ""),
            agentid_scopes=_env("AMP_AGENTID_SCOPES", ""),
        )

