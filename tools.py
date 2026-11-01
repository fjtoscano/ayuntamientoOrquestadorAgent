"""Herramientas del Agente Orquestador Municipal.

Incluye la consulta al RAG vectorial (PostgreSQL + pgvector), el catálogo de agentes
y la función formal de derivación / enrutamiento de trámites.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_core.tools import tool

from config import Config
from rag import VectorRAGManager

log = logging.getLogger("ayuntamiento-tools")

CATALOGO_AGENTES = {
    "AGENTE_PADRON": "Gestión del padrón municipal: altas, bajas, traslados, volantes, certificados de empadronamiento, convivencia e histórico de residencia.",
    "AGENTE_URBANISMO": "Obras mayores y menores, reformas, licencias, declaraciones responsables, andamios, vados, contenedores, ocupación de vía pública y aperturas de local.",
    "AGENTE_TRIBUTOS": "Impuestos y tasas municipales (IBI, IVTM/vehículos, basuras, plusvalía), fraccionamientos, aplazamientos, bonificaciones y recursos contra multas de tráfico.",
    "AGENTE_SERVICIOS_SOCIALES": "Ayudas de emergencia social, alquiler, vulnerabilidad, Ley de Dependencia, teleasistencia, ayuda a domicilio (SAD) e inclusión social.",
    "AGENTE_PARTICIPACION_Y_CULTURA": "Cursos, talleres culturales, actividades deportivas, piscinas, biblioteca, cesión de salas, centros cívicos, asociaciones y eventos no lucrativos.",
    "AGENTE_INCIDENCIAS_URBANAS": "Avisos sobre desperfectos en el espacio público: aceras, baches, farolas apagadas, limpieza, contenedores, parques, bancos, fugas de agua y ruidos.",
    "AGENTE_REGISTRO_Y_EXPEDIENTES": "Punto de entrada de instancias genéricas, registro oficial con número de justificante y consulta del estado de expedientes sin área gestora definida.",
    "AGENTE_SEDE_DIGITAL": "Soporte para la sede electrónica: certificados digitales (FNMT), sistema Cl@ve, firma electrónica, errores técnicos y notificaciones electrónicas.",
    "AGENTE_EDUCACION": "Escolarización en escuelas infantiles públicas municipales (0-3 años), becas de comedor escolar y ayudas para material o libros.",
    "AGENTE_ATENCION_GENERAL": "Canal de orientación final para información básica (horarios, teléfonos, sedes) cuando no coincide con ningún trámite procedimental específico.",
}


def build_tools(cfg: Config, rag_manager: VectorRAGManager) -> list[Any]:
    @tool
    def consultar_base_conocimiento_tramite(consulta: str) -> str:
        """Consulta la base de conocimiento vectorial (RAG) para determinar qué agente municipal
        es competente según el trámite, verificar reglas de desambiguación, exclusiones y advertencias.
        Usa la descripción o palabras clave de la acción que el ciudadano desea realizar.
        """
        log.info("RAG search query: %s", consulta)
        try:
            results = rag_manager.search(consulta, top_k=3)
            if not results:
                return "No se encontraron coincidencias directas en la base de conocimiento. Recomienda consultar el catálogo general de agentes o solicitar aclaración al ciudadano."

            formatted = []
            for idx, r in enumerate(results, start=1):
                doc_id = r.get("document_id", "doc")
                sec = r.get("metadata", {}).get("section", "")
                text = r.get("text", "")
                sim = r.get("similarity", 0.0)
                formatted.append(f"--- Coincidencia {idx} (Similitud: {sim:.2f}) [Doc: {doc_id} | Sección: {sec}] ---\n{text}")

            return "\n\n".join(formatted)
        except Exception as exc:  # noqa: BLE001
            log.exception("Error al consultar RAG: %s", exc)
            return f"Error al consultar el RAG: {exc}"

    @tool
    def obtener_catalogo_agentes() -> str:
        """Devuelve el catálogo oficial completo de agentes municipales especializados y transversales
        con su ámbito de competencia principal para contrastar enrutamientos.
        """
        lines = ["CATÁLOGO OFICIAL DE AGENTES MUNICIPALES:"]
        for name, desc in CATALOGO_AGENTES.items():
            lines.append(f"- {name}: {desc}")
        return "\n".join(lines)

    @tool
    def derivar_a_agente(agente_destino: str, motivo_enrutamiento: str, datos_tramite: str = "") -> str:
        """Ejecuta la derivación o llamada formal al agente especialista seleccionado.
        Si la petición del ciudadano contiene múltiples trámites independientes, esta herramienta
        debe ser llamada una vez por cada trámite identificado.

        Parámetros:
        - agente_destino: Nombre exacto del agente (ej. 'AGENTE_PADRON', 'AGENTE_URBANISMO', etc.).
        - motivo_enrutamiento: Justificación breve y fundamentada de la derivación según la materia.
        - datos_tramite: Información o contexto aportado por el ciudadano relevante para el especialista.
        """
        agente_upper = agente_destino.strip().upper()
        if agente_upper not in CATALOGO_AGENTES:
            return (
                f"ERROR: El agente '{agente_destino}' no existe en el catálogo municipal. "
                f"Los agentes válidos son: {', '.join(CATALOGO_AGENTES.keys())}"
            )

        log.info("Derivación efectuada hacia: %s (Motivo: %s)", agente_upper, motivo_enrutamiento)
        resultado = {
            "estado": "DERIVADO_CON_EXITO",
            "agente_asignado": agente_upper,
            "descripcion_agente": CATALOGO_AGENTES[agente_upper],
            "motivo": motivo_enrutamiento,
            "datos_aportados": datos_tramite or "Ninguno especificado",
            "mensaje_al_ciudadano": f"El trámite ha sido canalizado correctamente hacia {agente_upper}."
        }
        return json.dumps(resultado, ensure_ascii=False, indent=2)

    @tool
    def activar_alerta_emergencia(tipo_emergencia: str, motivo: str) -> str:
        """Activa una alerta prioritaria cuando el ciudadano menciona un peligro inminente
        (incendio, fuga grave de gas, derrumbe, cable eléctrico suelto, agresión, accidente con heridos).
        Instruye la llamada inmediata al 112 o servicios de emergencia antes de cualquier gestión administrativa.
        """
        log.warning("ALERTA DE EMERGENCIA ACTIVADA: %s - %s", tipo_emergencia, motivo)
        alerta = {
            "protocolo": "EMERGENCIA_INMEDIATA",
            "telefono_prioritario": "112 (Emergencias) / 092 (Policía Local)",
            "tipo": tipo_emergencia,
            "motivo": motivo,
            "instruccion": "Priorizar taxativamente que el ciudadano llame de inmediato al 112 antes de realizar trámites ordinarios."
        }
        return json.dumps(alerta, ensure_ascii=False, indent=2)

    return [
        consultar_base_conocimiento_tramite,
        obtener_catalogo_agentes,
        derivar_a_agente,
        activar_alerta_emergencia,
    ]

