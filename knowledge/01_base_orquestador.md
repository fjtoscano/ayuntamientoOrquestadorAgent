# BASE DE CONOCIMIENTO PARA EL AGENTE ORQUESTADOR DEL AYUNTAMIENTO

## Objetivo
Identificar el trámite principal solicitado por la ciudadanía y llamar o indicar el agente especialista adecuado. Esta base sirve exclusivamente para decidir el enrutamiento; cada agente especializado valida requisitos, plazos, tasas y documentación vigente antes de completar un expediente.

## Proceso de Decisión
1. **Identificar la acción** que quiere realizar la persona, no solo las palabras literales que usa.
2. **Recuperar el agente** cuyo ámbito contenga esa acción.
3. **Múltiples trámites**: Si una petición incluye varios trámites independientes, llamar o indicar a un agente por cada trámite y explicar claramente la división al ciudadano.
4. **Desambiguación**: Si faltan datos necesarios para distinguir dos rutas posibles, pedir una aclaración breve y directa antes de derivar a un agente.
5. **Neutralidad de condiciones**: No prometer concesiones, plazos ni importes económicos: el agente de destino es quien confirma y evalúa esas condiciones.

## Reglas de Desambiguación Rápidas
- **Padrón**, **empadronamiento**, **domicilio habitual** y **convivientes** -> `AGENTE_PADRON`.
- **Obra**, **reforma**, **licencia**, **andamio**, **ocupación de vía** y **apertura de local** -> `AGENTE_URBANISMO`.
- **Multa**, **recibo**, **IBI**, **basura**, **vehículo**, **pago**, **bonificación** y **fraccionamiento** -> `AGENTE_TRIBUTOS`.
- **Ayuda**, **subvención**, **dependencia**, **vulnerabilidad**, **alquiler**, **emergencia social** y **teleasistencia** -> `AGENTE_SERVICIOS_SOCIALES`.
- **Actividad cultural**, **instalación deportiva**, **curso**, **biblioteca**, **evento municipal** y **asociación** -> `AGENTE_PARTICIPACION_Y_CULTURA`.
- **Queja** o **aviso** sobre limpieza, alumbrado, parques, ruido, agua, aceras o mobiliario urbano -> `AGENTE_INCIDENCIAS_URBANAS`.

## Casos Transversales
- **AGENTE_REGISTRO_Y_EXPEDIENTES**: Para presentar una solicitud ya preparada, registrar documentación de entrada o consultar el estado de un expediente sin saber su materia concreta.
- **AGENTE_SEDE_DIGITAL**: Para identidad digital, certificado electrónico, Cl@ve, problemas técnicos de tramitación o notificaciones electrónicas.
- **AGENTE_ATENCION_GENERAL**: Si el asunto no coincide de forma razonable con ningún ámbito o cuando tras una pregunta aclaratoria no sea posible determinar la materia.

## Ejemplos de Enrutamiento
- *"Necesito cambiar mi domicilio y pedir un volante"* -> Corresponde a `AGENTE_PADRON`.
- *"Voy a reformar mi vivienda y colocar un contenedor"* -> Corresponde a `AGENTE_URBANISMO`.
- *"Quiero recurrir una multa de tráfico"* -> Corresponde a `AGENTE_TRIBUTOS`.
- *"Quiero empadronarme y también pagar una multa de la grúa"* -> División de trámites: derivar simultáneamente a `AGENTE_PADRON` y a `AGENTE_TRIBUTOS`.

