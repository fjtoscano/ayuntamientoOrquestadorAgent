"""Script independiente para cargar la base de conocimiento en PostgreSQL con pgvector.

Uso:
  python seed_rag.py [--force]
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

from config import Config
from rag import VectorRAGManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("seed-rag")


def main() -> None:
    parser = argparse.ArgumentParser(description="Poblar el RAG de PostgreSQL con los trámites municipales.")
    parser.add_argument("--force", action="store_true", help="Sobrescribir datos existentes en la colección")
    args = parser.parse_args()

    cfg = Config.from_env()

    if not os.environ.get("OPENAI_API_KEY"):
        log.error("Falta la variable de entorno OPENAI_API_KEY. Requerida para generar embeddings.")
        sys.exit(1)

    log.info("Conectando a base vectorial en: %s", cfg.vector_db_url)
    rag_mgr = VectorRAGManager(
        vector_db_url=cfg.vector_db_url,
        embedding_model=cfg.embedding_model,
    )

    if not rag_mgr.is_db_available():
        log.error(
            "No se pudo conectar a PostgreSQL en '%s'. Asegúrate de que el contenedor de PostgreSQL esté iniciado.",
            cfg.vector_db_url,
        )
        sys.exit(1)

    log.info("Asegurando tablas e índices HNSW en PostgreSQL...")
    rag_mgr.ensure_tables()

    knowledge_dir = Path(__file__).parent / "knowledge"
    log.info("Cargando documentos desde: %s", knowledge_dir)
    total = rag_mgr.seed_from_directory(knowledge_dir, force_reload=args.force)

    log.info("Población completada. Total de fragmentos indexados: %d", total)

    # Realizar consulta de prueba
    test_query = "Quiero empadronar a mi hijo y cambiar de casa"
    log.info("Ejecutando consulta de prueba: '%s'...", test_query)
    results = rag_mgr.search(test_query, top_k=2)
    for idx, r in enumerate(results, start=1):
        log.info(
            "Resultado %d (Similitud: %.3f) - Doc: %s, Sec: %s",
            idx,
            r["similarity"],
            r["document_id"],
            r.get("metadata", {}).get("section", "N/A"),
        )
        log.info("Fragmento: %s...", r["text"][:150].replace("\n", " "))

    log.info("¡Base de conocimiento RAG en pgvector lista para el agente orquestador!")


if __name__ == "__main__":
    main()

