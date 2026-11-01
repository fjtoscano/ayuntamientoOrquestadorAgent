from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from agent import build_agent, load_mcp_tools
from config import Config
from rag import VectorRAGManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("ayuntamiento-app")

CONFIG = Config.from_env()

# Inicialización de la base de conocimiento vectorial RAG
RAG_MGR = VectorRAGManager(
    vector_db_url=CONFIG.vector_db_url,
    embedding_model=CONFIG.embedding_model,
)

# Cargar conocimiento local en memoria y/o PostgreSQL si está disponible
knowledge_dir = Path(__file__).parent / "knowledge"
try:
    RAG_MGR.ensure_tables()
    RAG_MGR.seed_from_directory(knowledge_dir, force_reload=False)
except Exception as exc:  # noqa: BLE001
    log.warning("Aviso durante la inicialización del RAG: %s", exc)

# Carga de herramientas MCP opcionales de WSO2 Agent Manager
MCP_TOOLS = asyncio.run(load_mcp_tools(CONFIG))

# Construcción del agente orquestador ReAct con memoria de sesión
AGENT = build_agent(CONFIG, RAG_MGR, MCP_TOOLS)

log.info(
    "Agente Orquestador del Ayuntamiento listo (versión=%s, llm=%s, pgvector=%s, mcp_tools=%d)",
    CONFIG.agent_version,
    "agent-manager-provider" if CONFIG.use_llm_provider else f"openai-direct ({CONFIG.llm_model})",
    "conectado" if RAG_MGR.is_db_available() else "fallback-local",
    len(MCP_TOOLS),
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    context: dict[str, Any] | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str | None = None
    agent_version: str | None = None


app = FastAPI(
    title="Agente Orquestador del Ayuntamiento",
    description="Agente conversacional para enrutamiento y derivación inteligente de trámites municipales con RAG en pgvector",
    version=CONFIG.agent_version,
)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "agent": "ayuntamiento-orquestador",
        "version": CONFIG.agent_version,
        "company": CONFIG.company_name,
        "llm_provider": "agent-manager" if CONFIG.use_llm_provider else "openai-direct",
        "llm_model": CONFIG.llm_model,
        "rag_pgvector_connected": RAG_MGR.is_db_available(),
        "vector_db_url": CONFIG.vector_db_url,
        "mcp_tools_count": len(MCP_TOOLS),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    # El checkpointer de LangGraph mantiene el hilo conversacional multi-turno por thread_id
    session_id = req.session_id or str(uuid.uuid4())

    try:
        result = await AGENT.ainvoke(
            {"messages": [HumanMessage(content=req.message)]},
            config={"configurable": {"thread_id": session_id}},
        )
    except Exception as exc:  # noqa: BLE001
        log.exception("Error durante la invocación del agente orquestador: %s", exc)
        raise HTTPException(status_code=500, detail=f"Error en la ejecución del agente: {exc}") from exc

    final_content: Any = None
    for msg in reversed(result.get("messages", [])):
        if isinstance(msg, AIMessage):
            final_content = msg.content
            break

    if final_content is None:
        final_content = "Disculpe, no he podido procesar su solicitud en este momento. Por favor, vuelva a intentarlo."

    if isinstance(final_content, list):
        final_content = "\n".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in final_content
        )

    return ChatResponse(
        response=str(final_content),
        session_id=session_id,
        agent_version=CONFIG.agent_version,
    )

