# AGENTE_URBANISMO — OBRAS, LICENCIAS Y ACTIVIDADES

## Ámbito de Actuación
Este agente atiende la ordenación del territorio, disciplina urbanística, licencias y autorizaciones sobre el espacio público:
- Licencias de obras mayores (nueva edificación, reformas estructurales, ampliaciones).
- Declaraciones responsables de obras menores (reforma de cocina, baño, solados, pintura, alicatados).
- Actuaciones de demolición, rehabilitación de fachadas y cubiertas.
- Obras y adecuaciones de accesibilidad (instalación de ascensores, rampas comunitarias).
- Ocupación temporal de la vía pública vinculada a obras: instalación de andamios, vallas de protección, contenedores de escombros, grúas torre y cortes de calle por descarga de materiales.
- Autorización y reserva de vados permanentes y reservas de estacionamiento.
- Licencias de apertura, declaraciones responsables de inicio de actividad y cambio de uso de locales comerciales o profesionales.
- Autorización de terrazas de hostelería en acera o calzada (mesas y sillas).
- Tramitación de inspecciones técnicas de edificios (ITE/IEE) y disciplina urbanística.

## Señales de Enrutamiento
Hacer una obra, reformar el baño, tirar un tabique, rehabilitar fachada, pedir licencia de obra, presentar declaración responsable de obra, cerramiento de terraza, solicitar un vado, colocar un andamio, poner un contenedor de escombros en la calle, ocupar la acera para obra, abrir un bar, abrir un negocio o tienda, licencia de actividad clasificada o inocua, terraza de bar, cambio de local a vivienda, inspección urbanística.

## No Corresponde a este Agente
- Notificar una baldosa rota, bache o farola apagada en la vía pública (corresponde a `AGENTE_INCIDENCIAS_URBANAS`).
- Liquidación o fraccionamiento de tasas o impuestos de una licencia ya concedida (corresponde a `AGENTE_TRIBUTOS`).
- Reserva de una sala en un centro cívico o instalación deportiva municipal para un evento vecinal (corresponde a `AGENTE_PARTICIPACION_Y_CULTURA`).

## Criterio de Enrutamiento de Obras
Si el ciudadano no tiene claro si su intervención requiere **licencia urbanística formal** o una **declaración responsable**, el orquestador debe dirigir siempre la consulta a `AGENTE_URBANISMO`. Este especialista determinará con precisión el procedimiento exacto, si precisa proyecto técnico visado por técnico colegiado o autorización ambiental complementaria.

