"""Gestor RAG con persistencia en PostgreSQL + pgvector.

Maneja el cálculo de embeddings con OpenAI y la búsqueda semántica
por similitud de coseno en la tabla 'rag_knowledge_base'.
Incluye fallback en memoria si la base de datos PostgreSQL no estuviera
disponible durante pruebas locales aisladas.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any

from langchain_openai import OpenAIEmbeddings

log = logging.getLogger("ayuntamiento-rag")

COLLECTION_NAME = "agentes_ayuntamiento"


class VectorRAGManager:
    def __init__(self, vector_db_url: str, embedding_model: str = "text-embedding-3-small") -> None:
        self.vector_db_url = vector_db_url
        self.embedding_model = embedding_model
        self.embeddings = OpenAIEmbeddings(model=embedding_model)
        self._db_available: bool | None = None
        self._local_fallback_docs: list[dict[str, Any]] = []

    def get_connection(self) -> Any:
        import psycopg2

        return psycopg2.connect(self.vector_db_url)

    def is_db_available(self) -> bool:
        if self._db_available is not None:
            return self._db_available
        try:
            conn = self.get_connection()
            conn.close()
            self._db_available = True
            log.info("Conexión con PostgreSQL pgvector verificada con éxito: %s", self.vector_db_url)
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "PostgreSQL no está disponible en '%s' (%s). Se activará el motor de búsqueda local de respaldo.",
                self.vector_db_url,
                exc,
            )
            self._db_available = False
        return self._db_available

    def ensure_tables(self) -> None:
        """Crea la extensión pgvector y la tabla si no existen."""
        if not self.is_db_available():
            return

        init_sql = """
        CREATE EXTENSION IF NOT EXISTS vector;
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

        CREATE TABLE IF NOT EXISTS rag_knowledge_base (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            collection VARCHAR(100) NOT NULL,
            document_id VARCHAR(255),
            chunk_index INT NOT NULL DEFAULT 0,
            chunk_text TEXT NOT NULL,
            embedding vector(1536),
            metadata JSONB DEFAULT '{}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_rag_knowledge_hnsw ON rag_knowledge_base 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);

        CREATE INDEX IF NOT EXISTS idx_rag_collection ON rag_knowledge_base (collection);
        """
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(init_sql)
            conn.commit()
            conn.close()
            log.info("Tablas e índices de pgvector inicializados en PostgreSQL.")
        except Exception as exc:  # noqa: BLE001
            log.exception("Error al verificar/crear tablas en PostgreSQL: %s", exc)

    def seed_from_directory(self, knowledge_dir: Path | str, force_reload: bool = False) -> int:
        """Lee los documentos markdown, genera embeddings con OpenAI y los inserta en pgvector."""
        dir_path = Path(knowledge_dir)
        if not dir_path.exists():
            log.error("El directorio de conocimiento no existe: %s", dir_path)
            return 0

        files = sorted(dir_path.glob("*.md"))
        if not files:
            log.warning("No se encontraron archivos .md en %s", dir_path)
            return 0

        total_chunks = 0
        chunks_to_insert: list[dict[str, Any]] = []

        for f in files:
            content = f.read_text(encoding="utf-8")
            # Segmentar por encabezados secundarios o párrafos clave
            sections = content.split("\n## ")
            doc_title = sections[0].replace("#", "").strip()

            for idx, sec in enumerate(sections[1:], start=1):
                chunk_header = sec.split("\n")[0].strip()
                chunk_body = "\n".join(sec.split("\n")[1:]).strip()
                full_chunk_text = f"Documento: {doc_title}\nSección: {chunk_header}\n\n{chunk_body}"
                
                chunks_to_insert.append({
                    "document_id": f.stem,
                    "chunk_index": idx,
                    "title": doc_title,
                    "section": chunk_header,
                    "text": full_chunk_text,
                })

        # Almacenar siempre en fallback local por seguridad
        self._local_fallback_docs = chunks_to_insert

        if not self.is_db_available():
            log.warning("PostgreSQL no accesible. %d fragmentos guardados en memoria local.", len(chunks_to_insert))
            return len(chunks_to_insert)

        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                # Comprobar si ya existen registros
                cur.execute(
                    "SELECT COUNT(*) FROM rag_knowledge_base WHERE collection = %s",
                    (COLLECTION_NAME,),
                )
                count = cur.fetchone()[0]

                if count > 0 and not force_reload:
                    log.info("La colección '%s' ya contiene %d fragmentos en PostgreSQL. Omitiendo re-seeding.", COLLECTION_NAME, count)
                    conn.close()
                    return count

                if force_reload and count > 0:
                    cur.execute("DELETE FROM rag_knowledge_base WHERE collection = %s", (COLLECTION_NAME,))
                    conn.commit()
                    log.info("Colección anterior '%s' vaciada para recarga forzada.", COLLECTION_NAME)

                # Calcular embeddings en batch con OpenAI
                texts = [item["text"] for item in chunks_to_insert]
                log.info("Generando embeddings OpenAI (%s) para %d fragmentos...", self.embedding_model, len(texts))
                vectors = self.embeddings.embed_documents(texts)

                # Inserción en batch
                insert_sql = """
                INSERT INTO rag_knowledge_base (collection, document_id, chunk_index, chunk_text, embedding, metadata)
                VALUES (%s, %s, %s, %s, %s::vector, %s::jsonb)
                """
                for item, vec in zip(chunks_to_insert, vectors):
                    metadata_json = json.dumps({
                        "document": item["document_id"],
                        "title": item["title"],
                        "section": item["section"],
                    })
                    cur.execute(
                        insert_sql,
                        (COLLECTION_NAME, item["document_id"], item["chunk_index"], item["text"], vec, metadata_json),
                    )

                conn.commit()
                total_chunks = len(chunks_to_insert)
                log.info("Se han indexado con éxito %d fragmentos en PostgreSQL pgvector.", total_chunks)

            conn.close()
        except Exception as exc:  # noqa: BLE001
            log.exception("Error al insertar embeddings en pgvector: %s", exc)

        return total_chunks

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Realiza una búsqueda semántica usando distancia coseno contra pgvector."""
        query_vector = self.embeddings.embed_query(query)

        if self.is_db_available():
            try:
                conn = self.get_connection()
                with conn.cursor() as cur:
                    search_sql = """
                    SELECT 
                        document_id, 
                        chunk_index, 
                        chunk_text, 
                        metadata, 
                        1 - (embedding <=> %s::vector) AS similarity
                    FROM rag_knowledge_base
                    WHERE collection = %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s;
                    """
                    cur.execute(search_sql, (query_vector, COLLECTION_NAME, query_vector, top_k))
                    rows = cur.fetchall()

                    results = []
                    for row in rows:
                        results.append({
                            "document_id": row[0],
                            "chunk_index": row[1],
                            "text": row[2],
                            "metadata": row[3],
                            "similarity": float(row[4]),
                        })
                    conn.close()
                    return results
            except Exception as exc:  # noqa: BLE001
                log.warning("Fallo en búsqueda pgvector, recurriendo a búsqueda local: %s", exc)

        # Fallback local simple si DB no está disponible
        return self._local_fallback_search(query, top_k)

    def _local_fallback_search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        """Fallback que busca palabras clave en los documentos cargados en memoria."""
        q_lower = query.lower()
        scored: list[tuple[float, dict[str, Any]]] = []
        for doc in self._local_fallback_docs:
            text = doc["text"].lower()
            score = 0.0
            for word in q_lower.split():
                if len(word) > 3 and word in text:
                    score += 1.0
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "document_id": d["document_id"],
                "chunk_index": d["chunk_index"],
                "text": d["text"],
                "metadata": {"title": d["title"], "section": d["section"]},
                "similarity": 0.8,
            }
            for _, d in scored[:top_k]
        ]

