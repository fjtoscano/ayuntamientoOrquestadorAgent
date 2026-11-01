"""Construcción del Agente Orquestador del Ayuntamiento con LangGraph y LangChain.

Implementa un agente conversacional basado en el patrón ReAct, con persistencia
de memoria de conversación multi-turno (checkpointer en memoria por session_id)
y conectores tanto directos a OpenAI como a través del LLM Provider de WSO2 Agent Manager.
"""

from __future__ import annotations

import logging
from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.prebuilt import create_react_agent

from config import Config
from rag import VectorRAGManager
from tools import build_tools

log = logging.getLogger("ayuntamiento-agent")

SYSTEM_PROMPT_TEMPLATE = """Eres el AGENTE ORQUESTADOR DEL AYUNTAMIENTO ({company_name}).
Tu misión principal es atender a la ciudadanía, comprender qué trámite o necesidad administrativa tienen y derivarles al agente municipal especialista adecuado, apoyándote en la base de conocimiento vectorial (RAG).

ESTRUCTURA Y PROCESO DE DECISIÓN QUE DEBES SEGUIR RIGUROSAMENTE:
1. IDENTIFICAR LA ACCIÓN: Identifica la acción real que quiere realizar la persona, no solo las palabras literales que usa.
2. CONSULTAR EL RAG: Utiliza la herramienta 'consultar_base_conocimiento_tramite' con la acción descrita para validar el ámbito del agente, las reglas de enrutamiento y las exclusiones aplicables.
3. MÚLTIPLES TRÁMITES INDEPENDIENTES:
   - Si la petición incluye dos o más trámites independientes (por ejemplo: "quiero empadronarme y también pagar una multa de tráfico"), DEBES llamar a la herramienta 'derivar_a_agente' POR CADA TRÁMITE identificado.
   - Explica con total claridad al ciudadano cómo se divide la gestión entre los distintos departamentos.
4. ACLARACIÓN BREVE ANTES DE DERIVAR:
   - Si faltan datos indispensables para distinguir entre dos agentes posibles (por ejemplo, si no queda claro si una obra es mayor o menor, o si una queja es un aviso de vía pública o una queja tributaria), formula una pregunta aclaratoria concisa antes de derivar.
5. NO PROMETER CONDICIONES:
   - Jamás prometas concesiones, plazos exactos ni importes o importes de tasas/bonificaciones. Explica siempre que el agente especialista de destino es quien valida los requisitos, la documentación y confirma las condiciones oficiales.
6. PROTOCOLO DE PELIGRO INMEDIATO Y EMERGENCIAS:
   - Si el ciudadano menciona un peligro inminente (incendio, fuga grave de gas o agua, cable eléctrico suelto, derrumbe, accidente con heridos, agresión o violencia), DEBES llamar inmediatamente a 'activar_alerta_emergencia' e indicar al ciudadano de manera prioritaria que llame al 112 (Emergencias) o Policía Local (092) ANTES de tramitar cualquier aviso administrativo.

REGLAS DE DESAMBIGUACIÓN FUNDAMENTALES:
- Padrón, empadronamiento, cambio de domicilio, volante de residencia, convivencia -> AGENTE_PADRON.
- Obras, reformas, licencias, andamios, vados, contenedores en calle, apertura de negocios -> AGENTE_URBANISMO.
- Multas, recibos, IBI, basuras, vehículo (IVTM), pagos, fraccionamientos, bonificaciones -> AGENTE_TRIBUTOS.
- Ayudas de emergencia, alquiler, vulnerabilidad, dependencia, teleasistencia, ayuda a domicilio -> AGENTE_SERVICIOS_SOCIALES.
- Actividades culturales, talleres, cursos, instalaciones deportivas, piscinas, biblioteca, centros cívicos, eventos vecinales -> AGENTE_PARTICIPACION_Y_CULTURA.
- Quejas o avisos sobre baches, aceras, farolas, limpieza, contenedores rotos, parques o ruidos en la calle -> AGENTE_INCIDENCIAS_URBANAS.

CASOS TRANSVERSALES:
- Presentar una instancia o documento general ya redactado, o consultar el estado de un expediente sin saber su materia -> AGENTE_REGISTRO_Y_EXPEDIENTES.
- Problemas con certificado digital, Cl@ve, firma telemática o errores de la sede electrónica -> AGENTE_SEDE_DIGITAL.
- Consultas generales que no encajen en ningún procedimiento municipal o dudas de horarios/ubicación -> AGENTE_ATENCION_GENERAL.

Tono de comunicación: {tone}.
{additional_guidance}
"""


async def load_mcp_tools(cfg: Config) -> list[Any]:
    """Carga herramientas desde un proxy MCP de WSO2 Agent Manager si está habilitado."""
    if not cfg.use_mcp:
        return []

    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient

        connection: dict[str, Any] = {
            "url": cfg.mcp_url,
            "transport": "streamable_http",
        }
        if cfg.mcp_oauth and cfg.agentid_ready:
            from agent_identity import AgentIdentityAuth
            connection["auth"] = AgentIdentityAuth(cfg, resource=cfg.mcp_url)
        elif cfg.mcp_api_key:
            connection["headers"] = {"X-API-Key": cfg.mcp_api_key}

        client = MultiServerMCPClient({"amp_mcp": connection})
        tools = list(await client.get_tools())
        log.info("Cargadas %d herramientas desde el proxy MCP de WSO2 Agent Manager.", len(tools))
        return tools
    except Exception as exc:  # noqa: BLE001
        log.warning("No se pudieron cargar herramientas MCP externas (%s). Continuando solo con herramientas locales.", exc)
        return []


def build_agent(cfg: Config, rag_manager: VectorRAGManager, mcp_tools: list[Any] | None = None) -> Any:
    """Instancia el modelo LLM y crea el agente ReAct con checkpointer de memoria."""
    if cfg.use_llm_provider:
        log.info("Enrutando a través de WSO2 Agent Manager LLM Provider: %s", cfg.llm_provider_url)
        llm = ChatOpenAI(
            model=cfg.llm_model,
            temperature=0,
            base_url=cfg.llm_provider_url,
            api_key="not-used",
            default_headers={
                "API-Key": cfg.llm_provider_key,
                "Authorization": "",
            },
        )
    else:
        log.info("Conectando directamente con OpenAI API (Modelo: %s)...", cfg.llm_model)
        llm = ChatOpenAI(model=cfg.llm_model, temperature=0)

    tools = build_tools(cfg, rag_manager) + list(mcp_tools or [])

    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
        company_name=cfg.company_name,
        tone=cfg.tone,
        additional_guidance=cfg.additional_guidance,
    )

    # Persistencia de memoria conversacional basada en thread_id (el session_id de la petición /chat)
    checkpointer = InMemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=system_prompt,
        checkpointer=checkpointer,
    )
    return agent

