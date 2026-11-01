# Agente Orquestador del Ayuntamiento

Agente conversacional inteligente para la atención ciudadana y el enrutamiento especializado de trámites municipales, desarrollado con **LangGraph**, **LangChain**, **FastAPI** y **PostgreSQL con pgvector** para recuperación semántica (RAG).

Diseñado específicamente para ser probado en local y posteriormente desplegado de forma nativa en **WSO2 Agent Management Platform (AMP)** cumpliendo con su contrato de servicio (`POST /chat` y `GET /health` en el puerto `8000`).

---

## 🏛️ Propósito y Comportamiento del Agente

El agente recibe las solicitudes de la ciudadanía en lenguaje natural, analiza su intención real y deriva el caso al agente municipal competente basándose en la base de conocimiento vectorial indexada en PostgreSQL con `pgvector`.

### Catálogo de Agentes Especialistas:
1. **`AGENTE_PADRON`**: Altas, bajas, cambios de domicilio, volantes, certificados de empadronamiento, convivencia e histórico de residencia.
2. **`AGENTE_URBANISMO`**: Licencias de obra mayor y menor, declaraciones responsables, andamios, vados, contenedores en vía pública, licencias de apertura de negocios y terrazas.
3. **`AGENTE_TRIBUTOS`**: IBI, impuesto de vehículos (IVTM), tasa de basuras, plusvalía, fraccionamientos, bonificaciones y recursos contra multas de tráfico.
4. **`AGENTE_SERVICIOS_SOCIALES`**: Ayudas de emergencia social, alquiler, vulnerabilidad, Ley de Dependencia, teleasistencia domiciliaria y ayuda a domicilio (SAD).
5. **`AGENTE_PARTICIPACION_Y_CULTURA`**: Cursos, talleres culturales, actividades deportivas, piscinas, biblioteca, centros cívicos, asociaciones vecinales y eventos no lucrativos.
6. **`AGENTE_INCIDENCIAS_URBANAS`**: Avisos y quejas sobre baches, aceras rotas, farolas apagadas, limpieza viaria, contenedores, parques, mobiliario urbano, fugas de agua y ruidos.
7. **`AGENTE_REGISTRO_Y_EXPEDIENTES`**: Presentación de instancias generales, justificación con número de asiento y consulta de estado de expedientes sin área definida.
8. **`AGENTE_SEDE_DIGITAL`**: Soporte para certificados digitales (FNMT), sistema Cl@ve, autofirma, resolución de errores técnicos y notificaciones electrónicas.
9. **`AGENTE_EDUCACION`**: Escuelas infantiles municipales (0-3 años), becas de comedor escolar y ayudas para material o libros.
10. **`AGENTE_ATENCION_GENERAL`**: Información institucional básica (horarios, teléfonos, ubicaciones) o casos que no encajen tras desambiguación.

### Reglas Esenciales de Orquestación:
- **Múltiples Trámites**: Si el ciudadano solicita dos o más trámites independientes (ej. *"empadronarme y pagar una multa"*), el agente invoca una derivación por cada trámite y explica con claridad la división al ciudadano.
- **Aclaración Breve**: Si faltan datos para distinguir dos destinos posibles, formula una pregunta breve antes de derivar.
- **Sin Promesas de Concesión**: No promete plazos exactos, concesiones ni importes de tasas; el agente especialista destino valida requisitos y confirma condiciones.
- **Protocolo de Emergencias**: Si se detecta un peligro inminente (incendio, fuga grave de gas, cable expuesto, riesgo para la vida), instruye de inmediato llamar al **112 / 092** antes de tramitaciones ordinarias.

---

## 📁 Estructura del Proyecto

```
ayuntamientoOrquestadorAgent/
├── knowledge/                     # Base de conocimiento oficial dividida por materias
│   ├── 01_base_orquestador.md
│   ├── 02_agente_incidencias_urbanas.md
│   ├── 03_agente_padron.md
│   ├── 04_agente_participacion_cultura.md
│   ├── 05_agente_servicios_sociales.md
│   ├── 06_agente_tributos.md
│   ├── 07_agente_urbanismo.md
│   └── 08_agentes_transversales_registro_sede_atencion.md
├── agent.py                       # Grafo ReAct de LangGraph, prompts y checkpointer multi-turno
├── app.py                         # Servidor FastAPI con los endpoints /chat y /health
├── config.py                      # Configuración por variables de entorno
├── main.py                        # Punto de entrada de ejecución (uvicorn port 8000)
├── rag.py                         # Conector PostgreSQL + pgvector con HNSW y embeddings OpenAI
├── seed_rag.py                    # Script para poblar la base vectorial pgvector
├── tools.py                       # Herramientas de consulta RAG, catálogo y derivación
├── test_agent.py                  # Suite de pruebas automatizadas y chat interactivo en consola
├── Dockerfile                     # Imagen de contenedor lista para producción
├── requirements.txt               # Dependencias fijadas del ecosistema LangChain y FastAPI
└── .gitignore                     # Filtros para Git
```

---

## 🛠️ Requisitos Previos

- **Python 3.11 o 3.12** instalado.
- **Clave de API de OpenAI** (`OPENAI_API_KEY`).
- *(Opcional para persistencia completa)*: PostgreSQL con extensión `pgvector` en ejecución (si el clúster k3d del proyecto está levantado, ya está disponible en `localhost:5432`). Si no está encendido, el agente cuenta con un fallback local automático en memoria.

---

## 🚀 Paso 1: Pruebas en Local

### 1.1. Crear y Activar el Entorno Virtual
Abre una terminal en la carpeta `ayuntamientoOrquestadorAgent`:

```powershell
cd c:\Desarrollo\workspaces\proyectosIA\wso2IAPlatformAdaptative\ayuntamientoOrquestadorAgent

# Crear entorno virtual
python -m venv venv

# Activar en Windows PowerShell
.\venv\Scripts\Activate.ps1

# O en Windows CMD:
# .\venv\Scripts\activate.bat
```

### 1.2. Instalar Dependencias
```powershell
pip install -r requirements.txt
```

### 1.3. Configurar Variables de Entorno
```powershell
# En PowerShell:
$env:OPENAI_API_KEY = "sk-proj-tu-clave-aqui"

# Opcional (si deseas apuntar a otra URL de PostgreSQL):
# $env:VECTOR_DB_URL = "postgresql://postgres:postgres@localhost:5432/agent_memory_db"
```

### 1.4. Poblar la Base de Conocimiento RAG en pgvector
Si tienes el PostgreSQL del clúster corriendo en el puerto `5432`:
```powershell
python seed_rag.py --force
```
*Generará los embeddings con `text-embedding-3-small` e indexará todos los documentos con índices HNSW de distancia coseno.*

### 1.5. Iniciar el Agente Localmente
```powershell
python main.py
```
> **Nota de Puerto Local**: En local arranca por defecto en el puerto `8001` (`http://localhost:8001`) para evitar colisiones con `mcpserver` (que ya ocupa el puerto 8000 en el clúster k3d). Cuando se despliega en WSO2 Agent Manager o Docker, utiliza el puerto estándar `8000`.

---

## 🧪 Paso 2: Probar los Endpoints

Abre otra terminal (dejando `python main.py` corriendo):

### Verificar Salud (`/health`):
```powershell
curl.exe -s http://localhost:8001/health
```
O con PowerShell nativo:
```powershell
Invoke-RestMethod http://localhost:8001/health
```
Respuesta esperada:
```json
{
  "status": "ok",
  "agent": "ayuntamiento-orquestador",
  "version": "1.0.0",
  "company": "Ayuntamiento - Servicio de Atención Ciudadana",
  "llm_provider": "openai-direct",
  "rag_pgvector_connected": true,
  "vector_db_url": "postgresql://postgres:postgres@localhost:5432/agent_memory_db"
}
```

### Probar Conversación (`/chat`):

#### Opción 1: Con `curl.exe`
```powershell
curl.exe -X POST http://localhost:8001/chat -H "Content-Type: application/json" -d "{\"message\": \"Hola, necesito cambiar de domicilio y pedir un volante de empadronamiento\", \"session_id\": \"sesion-demo-01\"}"
```

#### Opción 2: Con PowerShell (`Invoke-RestMethod`)
```powershell
$body = @{
    message = "Hola, necesito cambiar de domicilio y pedir un volante de empadronamiento"
    session_id = "sesion-demo-01"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8001/chat -Method POST -ContentType "application/json" -Body $body
```

#### Opción 3: Trámites Múltiples (División de trámites)
```powershell
$body = @{
    message = "Quiero apuntarme a las clases de natación municipal y también pagar la tasa de basuras."
    session_id = "sesion-demo-02"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8001/chat -Method POST -ContentType "application/json" -Body $body
```

#### Opción 4: Alerta de Peligro / Emergencia
```powershell
$body = @{
    message = "¡Hay una fuga muy fuerte de gas en la esquina de la plaza!"
    session_id = "sesion-demo-03"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8001/chat -Method POST -ContentType "application/json" -Body $body
```

### Ejecutar Batería de Pruebas Automáticas:
```powershell
python test_agent.py --suite
```

### Modo Chat Interactivo en Terminal:
```powershell
python test_agent.py --interactive
```

---

## 📤 Paso 3: Subir a un Repositorio GitHub

Para desplegar este agente en **WSO2 Agent Management Platform (AMP)**, puedes subir esta carpeta a un nuevo repositorio de GitHub:

```bash
cd c:\Desarrollo\workspaces\proyectosIA\wso2IAPlatformAdaptative\ayuntamientoOrquestadorAgent

# Inicializar repositorio Git local
git init
git add .
git commit -m "feat: Agente Orquestador del Ayuntamiento con LangGraph y RAG pgvector"

# Crear rama principal y vincular con tu repositorio remoto en GitHub
git branch -M main
git remote add origin https://github.com/TU_USUARIO/ayuntamiento-orquestador-agent.git

# Subir cambios
git push -u origin main
```

---

## 🌐 Paso 4: Despliegue en WSO2 Agent Manager (AMP)

Una vez subido el código a GitHub:

1. **Abrir la Consola de WSO2 AMP**:
   - Entra en tu navegador a: [http://console.amp.localhost:8080](http://console.amp.localhost:8080)
   - Inicia sesión con `admin` / `admin`.

2. **Crear Nuevo Agente**:
   - Ve a la sección **Agents** y haz clic en **Create Agent**.
   - Nombre: `ayuntamiento-orquestador`.
   - Tipo de origen: **Git Repository**.
   - URL del Repositorio: `https://github.com/TU_USUARIO/ayuntamiento-orquestador-agent.git`
   - Rama: `main`.

3. **Configuración de Ejecución**:
   - **Build Command**: `pip install -r requirements.txt` (o dejar autodetección Python).
   - **Run Command**: `python main.py`
   - **Port**: `8000`

4. **Variables de Entorno del Agente**:
   En la pestaña de **Configuration / Environment Variables**, añade:
   - `OPENAI_API_KEY`: Tu clave de OpenAI (`sk-...`).
   - `VECTOR_DB_URL`: `postgresql://postgres:postgres@postgres-vector-service.wso2-dev.svc.cluster.local:5432/agent_memory_db`
     *(Permite que el agente resuelva la base vectorial interna del clúster a través del DNS cross-namespace).*
   - `COMPANY_NAME`: `Ayuntamiento - Atención Ciudadana`
   - `AGENT_VERSION`: `1.0.0`

5. **(Opcional) Gobernanza de Modelo**:
   - Si deseas usar el **LLM Service Provider** de WSO2 AMP en lugar de llamar directo a OpenAI, activa `USE_LLM_PROVIDER=true` en la consola de AMP; la plataforma inyectará automáticamente `LLM_PROVIDER_URL` y `LLM_PROVIDER_KEY` aplicando guardrails y observabilidad corporativa.

6. **Despliegue y Validación**:
   - Haz clic en **Deploy**.
   - Una vez el pod esté en estado `Ready`, podrás interactuar directamente con el Agente desde el panel de pruebas de la consola de AMP o integrarlo a través del **OpenChoreo Agent Gateway** (`http://openchoreoapis.localhost:19080`).

