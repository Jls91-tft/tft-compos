"""CAPA 2 — Catálogo de patrones versionado (FASE 3).

Cada patrón tiene SEIS piezas (arquitectura aprobada):
  id, nombre, disparador (condiciones medibles sobre hechos), contraevidencia
  (condiciones que ANULAN el disparo), confianza (0-1 calculada por caso),
  severidad (1-4), plantilla_es (con huecos {hecho} y pregunta de coach
  opcional) y telemetría (votos ✓/✗, acumulados en la tabla feedback).

REGLAS DE DISEÑO (no negociables):
- SOLO señales derivables del END-STATE: no vemos tiendas, rolls, posiciones
  ni la línea temporal. Por eso el texto plantea hipótesis y preguntas, nunca
  sentencias (decisión cerrada n.º 2).
- Las comparaciones son contra la MEDIA DEL PODIO (top 4), nunca contra el
  Top 1 individual (decisión n.º 4).
- Terminar con POCO oro es normal (cerrar/rolear lo consume): los patrones de
  economía miran el oro SOBRANTE, jamás castigan el oro bajo.
- Una señal solo se publica si confianza × severidad > SENAL_UMBRAL
  (configurable). Lo descartado por contraevidencia SE REGISTRA y se muestra
  en el inspector de hechos (decisión n.º 5).

Los huecos de las plantillas se rellenan con el dict PLANO de hechos que
construye ``pattern_evaluator.aplanar`` (claves documentadas allí).
"""
from dataclasses import dataclass, field
from typing import Callable

CATALOG_VERSION = "1.0.0"


@dataclass(frozen=True)
class Patron:
    id: str
    nombre: str
    severidad: int                                  # 1-4 (impacto estimado en puestos)
    disparador: Callable[[dict], bool]              # sobre hechos planos
    contraevidencia: Callable[[dict], str | None]   # motivo si ANULA; None si no
    confianza: Callable[[dict], float]              # 0-1, calculada por caso
    plantilla_es: str                               # texto de la señal (admite <b>)
    pregunta_es: str | None                         # pregunta de coach (cursiva en UI)
    hipotesis_es: str                               # si es la señal dominante del informe
    titulo_es: str                                  # titular del informe si domina
    objetivo_es: str                                # regla entrenable (objetivo semanal)
    telemetria: dict = field(default_factory=lambda: {"acierta": 0, "falla": 0})


def _conf(v: float) -> float:
    """Redondeo determinista y acotado de la confianza."""
    return round(max(0.0, min(0.95, v)), 2)


PATRONES: list[Patron] = [

    Patron(
        id="P-001", nombre="Contestación sin densidad", severidad=4,
        # Línea compartida por 2+ rivales Y densidad claramente bajo el podio.
        disparador=lambda h: (h["max_rivales"] >= 2
                              and h["densidad_2mas"] <= h["podio_densidad_media"] - 2
                              and h["puesto"] >= 5),
        # Un reroll consolidado (2+ unidades a 3★) no se mide por densidad 2★.
        contraevidencia=lambda h: ("reroll consolidado: 2+ unidades a 3★, la densidad 2★ no es su métrica"
                                   if h["densidad_3"] >= 2 else None),
        confianza=lambda h: _conf(0.6 + 0.15 * (h["max_rivales"] - 2) + 0.05 * h["unidades_contestadas_2mas"]),
        plantilla_es=("Tu línea principal estaba contestada por <b>{max_rivales} rivales</b> "
                      "({unidad_mas_contestada} incluida) y cerraste con <b>{densidad_2mas} unidades 2★+</b> "
                      "frente a {podio_densidad_media} de media del podio: poca densidad para sostener una línea compartida."),
        pregunta_es="¿Qué alternativa te ofrecía la tienda en la etapa 4?",
        hipotesis_es="mantuviste una línea contestada sin la densidad para ganarla, y el tablero llegó corto al cierre.",
        titulo_es="Línea contestada",
        objetivo_es="Si en 4-1 tu línea está contestada por 2 o más rivales y no llevas ventaja, pivota.",
    ),

    Patron(
        id="P-002", nombre="Oro sin usar al cierre", severidad=2,
        # Murió del 2.º al 8.º con 25+ de oro sin convertir en tablero.
        disparador=lambda h: h["oro_al_morir"] >= 25 and h["puesto"] >= 2,
        # Si la muerte fue temprana, el oro sobrante apunta a P-006, no a este.
        contraevidencia=lambda h: ("muerte temprana: el oro sin usar se evalúa en el patrón de economía/vida"
                                   if h["ultima_ronda"] <= 22 else None),
        confianza=lambda h: _conf(h["oro_al_morir"] / 50),
        plantilla_es=("Cerraste con <b>{oro_al_morir} de oro sin usar</b>: a esa altura de la partida era "
                      "un roll o una subida de nivel que no llegaste a jugar."),
        pregunta_es="¿Qué te frenó a gastarlo antes del último combate?",
        hipotesis_es="te sobró recurso al cierre: el oro sin convertir en tablero costó posiciones.",
        titulo_es="Oro sin usar al cierre",
        objetivo_es="En tus dos últimas rondas con vida, baja de 10 de oro: conviértelo en tablero.",
    ),

    Patron(
        id="P-003", nombre="Pico de poder tardío", severidad=3,
        # Nivel al ritmo del podio pero tablero sin consolidar → roll/subida tarde.
        disparador=lambda h: (h["puesto"] >= 5
                              and h["nivel_final"] >= h["podio_nivel_medio"] - 0.5
                              and h["densidad_2mas"] <= h["podio_densidad_media"] - 3),
        contraevidencia=lambda h: (
            "la causa primaria es la contestación (ver P-001)" if h["max_rivales"] >= 2
            else "reroll consolidado: su poder va por estrellas, no por densidad 2★" if h["densidad_3"] >= 2
            else None),
        confianza=lambda h: _conf(0.55 + 0.07 * (h["podio_densidad_media"] - h["densidad_2mas"])),
        plantilla_es=("Llegaste a nivel <b>{nivel_final}</b> (podio: {podio_nivel_medio}) pero con "
                      "<b>{densidad_2mas} unidades 2★+</b> por {podio_densidad_media} del podio: "
                      "el tablero no acompañó al nivel."),
        pregunta_es=None,
        hipotesis_es="llegaste tarde a tu pico de poder y el tablero no aguantó la transición a late.",
        titulo_es="Pico de poder tardío",
        objetivo_es="Antes de subir a 8, asegura 6+ unidades a 2★: nivel sin tablero es vida regalada.",
    ),

    Patron(
        id="P-004", nombre="Carry sin itemizar", severidad=3,
        # Ninguna unidad concentra el daño (0-1 ítems de daño en la que más lleva).
        disparador=lambda h: h["puesto"] >= 5 and h["carry_items_dano"] <= 1,
        contraevidencia=lambda h: (
            "el poder venía de estrellas (2+ unidades a 3★), no de ítems" if h["densidad_3"] >= 2
            else "los ítems de daño existen pero repartidos: ver el patrón de daño diluido"
            if h["unidades_con_item_dano"] >= 3 else None),
        confianza=lambda h: _conf(0.7 if h["carry_items_dano"] == 0 else 0.55),
        plantilla_es=("Tu unidad con más daño cerró con <b>{carry_items_dano} ítem(s) de daño</b>: "
                      "sin una carry itemizada, el tablero pierde la carrera de daño del late."),
        pregunta_es="¿Había componentes en banco esperando un ítem 'perfecto' que no llegó?",
        hipotesis_es="el daño nunca se concentró en una carry: la partida se decidió en peleas que tu tablero no podía ganar.",
        titulo_es="Carry sin itemizar",
        objetivo_es="Completa 2 ítems de daño en UNA unidad antes del 4-1, aunque no sean los óptimos.",
    ),

    Patron(
        id="P-005", nombre="Nivel por debajo del podio", severidad=2,
        disparador=lambda h: (h["puesto"] >= 5
                              and h["nivel_final"] <= h["podio_nivel_medio"] - 1.5),
        contraevidencia=lambda h: ("reroll legítimo: 2+ unidades a 3★ justifican el nivel bajo"
                                   if h["densidad_3"] >= 2 else None),
        confianza=lambda h: _conf(0.5 + 0.15 * (h["podio_nivel_medio"] - h["nivel_final"] - 1.5)),
        plantilla_es=("Cerraste a nivel <b>{nivel_final}</b> con un podio de media {podio_nivel_medio}: "
                      "uno o dos cuerpos menos que tus rivales en cada pelea del late."),
        pregunta_es="¿Hubo rondas donde el interés ya no compensaba frente a subir?",
        hipotesis_es="el lobby cerró por encima de tu nivel y el late se jugó con desventaja estructural.",
        titulo_es="Nivel por debajo del podio",
        objetivo_es="Marca el 4-2 como tu chequeo de nivel: si vas 1+ por debajo de la mesa, prioriza XP.",
    ),

    Patron(
        id="P-006", nombre="Economía por delante de la vida", severidad=3,
        # Eliminado pronto (antes del ~4-5) con 30+ de oro guardado.
        disparador=lambda h: h["ultima_ronda"] <= 22 and h["oro_al_morir"] >= 30,
        contraevidencia=lambda h: None,   # del end-state no se puede anular: la pregunta es obligada
        confianza=lambda h: _conf(0.6 + (0.1 if h["oro_al_morir"] >= 50 else 0.0)),
        plantilla_es=("Caíste en <b>{ronda_eliminacion}</b> con <b>{oro_al_morir} de oro</b> en el banco: "
                      "el interés no se cobra desde fuera de la partida."),
        pregunta_es="¿Estabas alargando una racha de derrotas a propósito o se fue la vida sin verlo?",
        hipotesis_es="la economía fue por delante de la vida: el oro guardado no llegó a convertirse en tablero.",
        titulo_es="Economía por delante de la vida",
        objetivo_es="Por debajo de 40 de vida, el interés deja de mandar: gasta para estabilizar.",
    ),

    Patron(
        id="P-007", nombre="Tablero sin sinergias", severidad=2,
        disparador=lambda h: h["puesto"] >= 5 and h["rasgos_2mas"] <= 1,
        contraevidencia=lambda h: ("reroll de unidades sueltas a 3★: las sinergias no eran el plan"
                                   if h["densidad_3"] >= 2 else None),
        confianza=lambda h: _conf(0.6),
        plantilla_es=("Cerraste con <b>{rasgos_2mas} rasgo(s) en plata o más</b>: el tablero compitió "
                      "sin los multiplicadores de sinergia que sí tenía el resto del lobby."),
        pregunta_es=None,
        hipotesis_es="el tablero final quedó sin sinergias consolidadas y compitió con estadísticas base.",
        titulo_es="Tablero sin sinergias",
        objetivo_es="En cada transición, conserva al menos dos rasgos en plata: vende después de activar, no antes.",
    ),

    Patron(
        id="P-008", nombre="Tablero sin presión", severidad=1,
        # Daño a jugadores en el cuartil bajo del lobby (hecho duro → confianza alta).
        disparador=lambda h: h["puesto"] >= 5 and h["pct_dano"] <= 25,
        contraevidencia=lambda h: ("muerte temprana: el daño bajo es consecuencia de jugar menos rondas, no causa"
                                   if h["ultima_ronda"] <= 18 else None),
        confianza=lambda h: _conf(0.95),
        plantilla_es=("Tu daño a jugadores quedó en el <b>percentil {pct_dano}</b> del lobby: "
                      "el tablero aguantó, pero nunca llegó a presionar."),
        pregunta_es=None,
        hipotesis_es="el tablero nunca presionó: se llegó lejos por gestión de vida, no por fuerza.",
        titulo_es="Tablero sin presión",
        objetivo_es="Busca un tablero que GANE rondas, no que las pierda por poco: el daño también es vida.",
    ),

    Patron(
        id="P-009", nombre="Daño diluido", severidad=2,
        # Ítems de daño repartidos en 3+ unidades sin completar ninguna carry.
        disparador=lambda h: (h["puesto"] >= 5
                              and h["carry_items_dano"] <= 2
                              and h["unidades_con_item_dano"] >= 3),
        contraevidencia=lambda h: None,
        confianza=lambda h: _conf(0.55),
        plantilla_es=("Repartiste los ítems de daño entre <b>{unidades_con_item_dano} unidades</b> sin "
                      "completar ninguna ({carry_items_dano} en la que más llevaba): el daño diluido "
                      "no gana las peleas del late."),
        pregunta_es="¿Era un plan de doble carry o componentes sin decidir destino?",
        hipotesis_es="los ítems de daño quedaron repartidos y ninguna unidad llegó a carry real.",
        titulo_es="Daño diluido",
        objetivo_es="Primera regla de ítems: completa la carry ANTES de repartir nada al resto.",
    ),

    Patron(
        id="P-010", nombre="Top 4 asegurado, margen sin usar", severidad=1,
        # Señal de matiz para buenos resultados: cerró 2.º-4.º con recursos sin jugar.
        disparador=lambda h: 2 <= h["puesto"] <= 4 and h["oro_al_morir"] >= 30,
        contraevidencia=lambda h: None,
        confianza=lambda h: _conf(0.6 + h["oro_al_morir"] / 100),
        plantilla_es=("Aseguraste el top {puesto} con <b>{oro_al_morir} de oro sin usar</b>: "
                      "había recursos para pelear posiciones más arriba."),
        pregunta_es="¿Qué te frenó a gastarlo en la última tienda?",
        hipotesis_es="cerraste conservador: el top 4 estaba asegurado y sobraron recursos para pelear el 1.º.",
        titulo_es="Top 4 asegurado, margen sin usar",
        objetivo_es="Con el top 4 asegurado, juega el oro restante: el 1.º paga el doble de LP.",
    ),
]

POR_ID: dict[str, Patron] = {p.id: p for p in PATRONES}
