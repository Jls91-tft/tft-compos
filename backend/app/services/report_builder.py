"""CAPA 3 — Generador de informes template-first (FASE 3).

Composición DETERMINISTA en castellano a partir de hechos (CAPA 1) y señales
ya evaluadas (CAPA 2). Sin LLM en el pipeline (acción prohibida n.º 1):
misma partida + misma versión de catálogo = mismo informe, siempre.

Estructura de salida (la que pinta la app v3):
  titulo · hipotesis · vs_podio · senales (con pregunta y feedback) · bien ·
  hechos_verificados (incluye DESCARTADOS) · catalogo_version · engine_version
"""
from app.catalog import CATALOG_VERSION
from app.services.pattern_evaluator import aplanar


def _media(valores: list[float]) -> float:
    return round(sum(valores) / len(valores), 1) if valores else 0.0


def _vs_podio(hechos: dict, h: dict) -> list[dict]:
    """Comparativa VS la MEDIA del top 4 del lobby (decisión cerrada n.º 4)."""
    podio = [j for j in hechos["lobby"]["jugadores"] if 1 <= j["puesto"] <= 4]
    items_carry_podio = _media([len((j.get("carry") or {}).get("items", [])) for j in podio])
    return [
        {"l": "NIVEL", "tu": h["nivel_final"], "podio": h["podio_nivel_medio"]},
        {"l": "UNID. 2★+", "tu": h["densidad_2mas"], "podio": h["podio_densidad_media"]},
        {"l": "ÍTEMS CARRY", "tu": h["carry_items_n"], "podio": items_carry_podio},
    ]


def _aciertos(h: dict) -> list[str]:
    """Lo que hiciste bien — hechos positivos medibles, máximo 2, orden fijo."""
    out = []
    if h["puesto"] == 1:
        out.append("Top 1 con ejecución limpia: esta partida entra en tu referencia para próximos análisis.")
    if h["carry_completa"]:
        out.append(f"Tu carry ({h['carry_id']}) cerró <b>itemizada al completo</b>.")
    if h["densidad_2mas"] >= h["podio_densidad_media"]:
        out.append(f"Densidad de tablero al nivel del podio: <b>{h['densidad_2mas']} unidades 2★+</b>.")
    if h["max_rivales"] == 0 and h["puesto"] <= 4:
        out.append("Línea libre bien elegida: ningún rival compartía tus unidades clave.")
    if h["pct_dano"] >= 75:
        out.append(f"Tu tablero presionó de verdad: percentil <b>{h['pct_dano']}</b> de daño del lobby.")
    if h["nivel_final"] >= h["podio_nivel_medio"] and h["puesto"] <= 4:
        out.append("Tempo de nivel al ritmo del podio.")
    return out[:2]


def _titulo_e_hipotesis(h: dict, senales: list[dict]) -> tuple[str, str]:
    if senales:
        dominante = senales[0]   # ya ordenadas por severidad × confianza
        return dominante["titulo"], dominante["hipotesis"]
    if h["puesto"] == 1:
        return "Partida de referencia", ("top 1 con ejecución limpia. Esta partida entra en tu "
                                         "biblioteca de referencia para comparar próximos análisis.")
    if h["puesto"] <= 4:
        return "Cierre sólido", ("partida bien ejecutada: ninguna señal superó el umbral. "
                                 "Las posiciones por encima se decidieron por detalles que el end-state no captura.")
    return "Sin señales por encima del umbral", ("ningún patrón del catálogo superó el umbral de confianza. "
                                                 "Derrota probablemente decidida por factores que no vemos "
                                                 "(tiendas, posicionamiento): no fabricamos causas.")


def _hechos_verificados(h: dict, descartadas: list[dict]) -> list[str]:
    """Líneas crudas del inspector (monoespaciada en la UI), descartados incluidos."""
    lineas = [
        f"nivel_final=<b>{h['nivel_final']}</b> · oro_al_morir=<b>{h['oro_al_morir']}</b> · "
        f"eliminado en <b>{h['ronda_eliminacion'] or '—'}</b> · puesto <b>{h['puesto']}</b>",
        f"contestación: <b>{h['max_rivales']}</b> rival(es) comparten tus unidades clave "
        f"({h['unidad_mas_contestada']} la más disputada)",
        f"densidad 2★+: <b>{h['densidad_2mas']}</b> · media del podio: <b>{h['podio_densidad_media']}</b>",
        f"carry: {h['carry_id']} · ítems de daño: <b>{h['carry_items_dano']}</b>/{h['carry_items_n']} totales",
        f"daño a jugadores: percentil <b>{h['pct_dano']}</b> del lobby",
    ]
    for d in descartadas:
        lineas.append(f"[DESCARTADO] {d['patron_id']} {d['nombre']} → {d['motivo']}")
    return lineas


def construir(hechos: dict, evaluacion: dict) -> dict:
    """Informe completo y determinista a partir de hechos + evaluación."""
    h = aplanar(hechos)
    senales = evaluacion["senales"]
    descartadas = evaluacion["descartadas"]
    titulo, hipotesis = _titulo_e_hipotesis(h, senales)

    return {
        "match_id": hechos.get("match_id", ""),
        "puesto": h["puesto"],
        "titulo": titulo,
        "hipotesis": hipotesis,
        "vs_podio": _vs_podio(hechos, h),
        "senales": [
            {"patron_id": s["patron_id"], "severidad": s["severidad"], "confianza": s["confianza"],
             "texto": s["texto"], "pregunta": s["pregunta"]}
            for s in senales
        ],
        "bien": _aciertos(h),
        "hechos_verificados": _hechos_verificados(h, descartadas),
        "descartados": descartadas,
        "catalogo_version": CATALOG_VERSION,
        "engine_version": hechos.get("engine_version", ""),
        "fuente": "Generado sobre hechos verificados · API oficial de Riot",
    }
