"""Punto de entrada principal para el Agente Orquestador del Ayuntamiento.

Compatible con el contrato de ejecución de WSO2 Agent Manager y ejecución local:
  python main.py
"""

from __future__ import annotations

import os
import uvicorn

from app import app


def main() -> None:
    # Si PORT está definido en el entorno se respeta (ej. 8000 en WSO2 AMP).
    # Por defecto en local se usa 8001 para no colisionar con mcpserver (puerto 8000 en k3d).
    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

