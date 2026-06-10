"""Evaluador del catálogo de patrones (FASE 3).

Flujo por patrón, en este orden estricto:
  1. DISPARADOR   — ¿se cumplen las condiciones medibles?  no → fuera (silencio)
  2. CONTRAEVIDENCIA — ¿algo lo anula?  sí → DESCARTADO (se registra y se muestra)
  3. CONFIANZA    — 0-1 calculada por caso
  4. UMBRAL       — publica solo si confianza × severidad > SENAL_UMBRAL;
                    si no llega, también queda registrado como descartado.

Todo determinista: mismos hechos + misma versión de catálogo = misma evaluación.
"""
from app.catalog import CATALOG_VERSION, PATRONES
from app.core.config import settings


def aplanar(hechos: dict) -> dict:
    """Dict PLANO con las claves que usan disparadores y plantillas.

    Claves disponibles en plantillas_es:
      puesto, nivel_final, oro_al_morir, ultima_ronda, ronda_eliminacion,
      densidad_2mas, densidad_3, dano_a_jugadores, rasgos_2mas,
      carry_id, carry_items_n, carry_items_dano, carry_completa,
      unidades_con_item_dano, max_rivales, unidades_contestadas_2mas,
      unidad_mas_contestada, podio_nivel_medio, podio_densidad_media,
      podio_densidad3_media, podio_oro_medio, pct_nivel, pct_densidad, pct_dano
    """
    yo = hechos["jugador"]
    podio = hechos["lobby"]["podio"]
    cont = hechos["contestacion"]
    pct = hechos["percentiles"]
    carry = yo.get("carry") or {}
    clave = cont.get("unidades_clave") or []
    return {
        "puesto": yo["puesto"],
        "nivel_final": yo["nivel_final"],
        "oro_al_morir": yo["oro_al_morir"],
        "ultima_ronda": yo["ultima_ronda"],
        "ronda_eliminacion": yo["ronda_eliminacion"],
        "densidad_2mas": yo["densidad_2mas"],
        "densidad_3": yo["densidad_3"],
        "dano_a_jugadores": yo["dano_a_jugadores"],
        "rasgos_2mas": sum(1 for r in yo["rasgos"] if r["nivel"] >= 2),
        "carry_id": carry.get("id", "—"),
        "carry_items_n": len(carry.get("items", [])),
        "carry_items_dano": carry.get("items_de_dano", 0),
        "carry_completa": bool(carry.get("itemizada_completa")),
        "unidades_con_item_dano": sum(1 for u in yo["unidades"] if u["items_de_dano"] >= 1),
        "max_rivales": cont["max_rivales_compartiendo"],
        "unidades_contestadas_2mas": cont["unidades_contestadas_2mas"],
        "unidad_mas_contestada": clave[0]["unidad"] if clave else "—",
        "podio_nivel_medio": podio["nivel_medio"],
        "podio_densidad_media": podio["densidad_2mas_media"],
        "podio_densidad3_media": podio["densidad_3_media"],
        "podio_oro_medio": podio["oro_al_morir_medio"],
        "pct_nivel": pct["nivel"],
        "pct_densidad": pct["densidad_2mas"],
        "pct_dano": pct["dano_a_jugadores"],
    }


def evaluar(hechos: dict) -> dict:
    """Evalúa el catálogo completo sobre unos hechos.

    Devuelve:
      {"senales": [...], "descartadas": [...], "catalogo_version": "x.y.z"}
    Las señales van ordenadas por impacto (severidad × confianza, desc).
    """
    h = aplanar(hechos)
    senales, descartadas = [], []

    for p in PATRONES:
        if not p.disparador(h):
            continue
        motivo = p.contraevidencia(h)
        if motivo:
            descartadas.append({"patron_id": p.id, "nombre": p.nombre, "motivo": motivo})
            continue
        conf = p.confianza(h)
        if conf * p.severidad <= settings.senal_umbral:
            descartadas.append({
                "patron_id": p.id, "nombre": p.nombre,
                "motivo": f"confianza insuficiente ({conf:.2f} × SEV {p.severidad} ≤ umbral {settings.senal_umbral})",
            })
            continue
        senales.append({
            "patron_id": p.id,
            "nombre": p.nombre,
            "severidad": p.severidad,
            "confianza": conf,
            "texto": p.plantilla_es.format(**h),
            "pregunta": p.pregunta_es,
            "hipotesis": p.hipotesis_es,
            "titulo": p.titulo_es,
        })

    senales.sort(key=lambda s: (-s["severidad"] * s["confianza"], s["patron_id"]))
    return {"senales": senales, "descartadas": descartadas, "catalogo_version": CATALOG_VERSION}
