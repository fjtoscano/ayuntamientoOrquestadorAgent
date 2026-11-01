"""Punto de entrada principal para el Agente Orquestador del Ayuntamiento.

Compatible con el contrato de ejecución de WSO2 Agent Manager y ejecución local:
  python main.py
"""

from __future__ import annotations

import os
import uvicorn

from app import app


def main() -> None:
    # En Kubernetes (WSO2 Agent Manager), el pod probea y espera el puerto 8000.
    # En local (sin KUBERNETES_SERVICE_HOST), usa 8001 para evitar colisionar con mcpserver (puerto 8000 de k3d).
    # Se puede sobrescribir con la variable de entorno AGENT_PORT.
    if os.environ.get("AGENT_PORT"):
        port = int(os.environ["AGENT_PORT"])
    elif os.environ.get("KUBERNETES_SERVICE_HOST"):
        port = 8000
    else:
        port = int(os.environ.get("PORT", "8001"))

    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()

