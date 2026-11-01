"""Script de prueba interactiva y batería de pruebas automáticas para el Agente Orquestador.

Uso:
  python test_agent.py --suite        # Ejecuta casos de prueba estándar
  python test_agent.py --interactive  # Chat interactivo en terminal
"""

from __future__ import annotations

import argparse
import json
import logging
import urllib.request
import uuid

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("test-agent")

CASOS_PRUEBA = [
    {
        "titulo": "1. Padrón Municipal",
        "mensaje": "Hola, necesito empadronarme en el municipio y solicitar un volante de empadronamiento.",
        "agente_esperado": "AGENTE_PADRON",
    },
    {
        "titulo": "2. Obras y Licencias",
        "mensaje": "Quiero reformar la cocina de mi piso y poner un andamio y un contenedor en la calle.",
        "agente_esperado": "AGENTE_URBANISMO",
    },
    {
        "titulo": "3. Impuestos y Multas",
        "mensaje": "Me ha llegado una notificación con una multa de tráfico de la policía local y quiero recurrirla.",
        "agente_esperado": "AGENTE_TRIBUTOS",
    },
    {
        "titulo": "4. Incidencias en la Vía Pública",
        "mensaje": "Hay tres farolas apagadas y una baldosa suelta en la calle Mayor frente al número 12.",
        "agente_esperado": "AGENTE_INCIDENCIAS_URBANAS",
    },
    {
        "titulo": "5. Apoyo Social y Dependencia",
        "mensaje": "Mi madre es muy mayor, vive sola y necesito solicitar el servicio de teleasistencia y ayuda a domicilio.",
        "agente_esperado": "AGENTE_SERVICIOS_SOCIALES",
    },
    {
        "titulo": "6. Múltiples Trámites Independientes",
        "mensaje": "Quiero apuntarme al curso municipal de cerámica y a la vez pedir un fraccionamiento para el IBI.",
        "agente_esperado": "AGENTE_PARTICIPACION_Y_CULTURA + AGENTE_TRIBUTOS",
    },
    {
        "titulo": "7. Sede Electrónica y Certificado",
        "mensaje": "Estoy intentando firmar un trámite telemático con mi certificado Cl@ve pero la sede me da error 500.",
        "agente_esperado": "AGENTE_SEDE_DIGITAL",
    },
    {
        "titulo": "8. Emergencia Inmediata",
        "mensaje": "¡Hay una fuga de gas muy fuerte y chispas de un cable eléctrico en la puerta de mi portal!",
        "agente_esperado": "112 / EMERGENCIA INMEDIATA",
    },
]


def send_chat_request(message: str, session_id: str, base_url: str = "http://localhost:8001") -> dict:
    url = f"{base_url}/chat"
    payload = json.dumps({"message": message, "session_id": session_id}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def run_suite(base_url: str = "http://localhost:8001") -> None:
    print("\n" + "=" * 75)
    print("  EJECUTANDO BATERÍA DE PRUEBAS DEL AGENTE ORQUESTADOR MUNICIPAL")
    print("=" * 75 + "\n")

    for caso in CASOS_PRUEBA:
        print(f"\n--- {caso['titulo']} ---")
        print(f"Ciudadano: \"{caso['mensaje']}\"")
        print(f"Objetivo esperado: {caso['agente_esperado']}")

        session_id = f"test-{uuid.uuid4().hex[:6]}"
        try:
            res = send_chat_request(caso["mensaje"], session_id, base_url)
            print(f"Respuesta del Agente:\n{res['response']}\n")
        except Exception as exc:
            print(f"[ERROR] No se pudo comunicar con el agente en {base_url}: {exc}")
            print("Asegúrate de que 'python main.py' esté ejecutándose en otra terminal.")
            return


def run_interactive(base_url: str = "http://localhost:8001") -> None:
    session_id = f"cli-{uuid.uuid4().hex[:8]}"
    print("\n" + "=" * 70)
    print("  CHAT INTERACTIVO - AGENTE ORQUESTADOR DEL AYUNTAMIENTO")
    print(f"  Sesión: {session_id} (Multi-turno activo)")
    print("  Escribe 'salir' o 'exit' para terminar.")
    print("=" * 70 + "\n")

    while True:
        try:
            msg = input("\nCiudadano > ").strip()
            if not msg or msg.lower() in ("salir", "exit", "quit"):
                print("Finalizando sesión de chat.")
                break

            res = send_chat_request(msg, session_id, base_url)
            print(f"\nOrquestador > {res['response']}")
        except KeyboardInterrupt:
            print("\nChat interrumpido.")
            break
        except Exception as exc:
            print(f"\n[ERROR] {exc}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba del Agente Orquestador")
    parser.add_argument("--suite", action="store_true", help="Ejecutar suite de casos de prueba")
    parser.add_argument("--interactive", action="store_true", help="Iniciar sesión interactiva")
    parser.add_argument("--url", default="http://localhost:8001", help="URL base del agente")
    args = parser.parse_args()

    if args.interactive:
        run_interactive(args.url)
    else:
        run_suite(args.url)


if __name__ == "__main__":
    main()

