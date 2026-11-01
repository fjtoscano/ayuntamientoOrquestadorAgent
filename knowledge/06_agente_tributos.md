# AGENTE_TRIBUTOS — IMPUESTOS, TASAS, MULTAS Y PAGOS MUNICIPALES

## Ámbito de Actuación
Este agente gestiona la recaudación voluntaria y ejecutiva, así como los tributos del municipio:
- Impuesto sobre Bienes Inmuebles (IBI / contribución urbana y rústica).
- Impuesto sobre Vehículos de Tracción Mecánica (IVTM / impuesto de circulación).
- Impuesto sobre el Incremento de Valor de los Terrenos de Naturaleza Urbana (Plusvalía municipal / IIVTNU).
- Impuesto sobre Actividades Económicas (IAE).
- Tasas municipales: recogida de basuras, vados permanentes, ocupación de vía pública con mesas y sillas/terrazas y tasas por expedición de licencias.
- Modalidades de pago: pago online con tarjeta, emisión de duplicados de cartas de pago y domiciliación bancaria con bonificación.
- Planes de pago personalizados: fraccionamientos, aplazamientos de deudas y expedientes de compensación.
- Devoluciones de ingresos indebidos y aplicación de bonificaciones fiscales (familias numerosas, vehículos ECO/Cero, etc.).
- Procedimientos de recaudación ejecutiva: providencias de apremio y embargos.
- Gestión y recursos contra sanciones y multas de tráfico del término municipal.

## Señales de Enrutamiento
IBI, contribución, recibo municipal, pagar una tasa, multa de tráfico, sanción municipal, impuesto de vehículo, numerito del coche, IVTM, domiciliación bancaria de impuestos, carta de pago, duplicado de recibo, aviso de embargo, deuda tributaria, aplazar pago de impuestos, fraccionar el IBI, solicitar bonificación fiscal, exención del impuesto, devolución de tributos, recurso de reposición contra una sanción.

## No Corresponde a este Agente
- Solicitar una licencia de obra o de apertura de actividad comercial (corresponde a `AGENTE_URBANISMO`).
- Comunicar un cambio de domicilio para empadronarse (corresponde a `AGENTE_PADRON`).
- Notificar una incidencia, avería o desperfecto en la vía pública (corresponde a `AGENTE_INCIDENCIAS_URBANAS`).

## Reglas de Recurso de Multas
Para recurrir una multa de tráfico o sanción municipal, el orquestador **debe enviar la petición a este agente (`AGENTE_TRIBUTOS`)** y conservar explícitamente la intención de recurso manifestada por el ciudadano; el agente especialista solicitará el número de expediente sancionador / boletín de denuncia y verificará el plazo legal aplicable (plazo ordinario o potestativo de reposición).

