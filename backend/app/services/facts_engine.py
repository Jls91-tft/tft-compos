"""CAPA 1 — Motor de hechos (FASE 2). Determinista, SIN IA.

Extrae señales VERIFICABLES del end-state de los 8 jugadores de una partida
de TFT (tft-match-v1). Mismo match + misma versión del motor = mismos hechos,
siempre: nada de aleatoriedad, nada de modelos, solo matemática sobre el JSON.

Qué calcula (spec de la arquitectura aprobada):
  - nivel final, oro al morir, ronda de eliminación (en formato etapa "6-2")
  - tableros y rasgos activos del lobby completo
  - mapa de contestación: cuántos rivales comparten las unidades clave
  - densidad de estrellas (2★+ y 3★)
  - itemización del carry (detectado por ítems de daño)
  - percentiles del jugador respecto al lobby
  - media del PODIO (top 4) — la comparación del producto es VS podio,
    nunca VS el Top 1 individual (decisión cerrada n.º 4)

La salida es un dict estable (claves ordenadas por construcción) que se
persiste como snapshot en la tabla ``hechos`` para reproducibilidad.
"""
import re

ENGINE_VERSION = "0.1.0"

# Ítems de daño/tanque (nombres limpios, minúscula). Los ítems completos base
# son estables entre sets; revisar al cambiar de set.
_DAMAGE_ITEMS = frozenset({
    "infinityedge", "deathblade", "giantslayer", "lastwhisper", "runaanshurricane",
    "rapidfirecannon", "statikkshiv", "guinsoosrageblade", "rabadonsdeathcap",
    "jeweledgauntlet", "hextechgunblade", "spearofshojin", "archangelsstaff",
    "bluebuff", "nashorstooth", "bloodthirster", "morellonomicon", "redbuff",
    "titansresolve", "handofjustice", "voidstaff", "deathfiregrasp", "kraken",
})

# 'TFT11_Ahri' / 'TFT_Item_X' → quita el prefijo del set.
_PREFIJO = re.compile(r"^TFT[^_]*_(?:Item_|Augment_)?")


def _limpiar(crudo: str) -> str:
    """'TFT11_Ahri' → 'Ahri'; 'TFT_Item_InfinityEdge' → 'InfinityEdge'."""
    return _PREFIJO.sub("", crudo or "").strip() or (crudo or "")


def _item_norm(crudo: str) -> str:
    return _limpiar(crudo).replace(" ", "").lower()


def _es_item_de_dano(crudo: str) -> bool:
    return _item_norm(crudo) in _DAMAGE_ITEMS


def ronda_a_etapa(ultima_ronda: int) -> str:
    """Convierte el last_round de la API al formato de etapa del juego ("6-2").

    La etapa 1 tiene 4 rondas (1-1..1-4); de la etapa 2 en adelante, 7 rondas
    por etapa (x-1..x-7).
    """
    if ultima_ronda is None or ultima_ronda <= 0:
        return ""
    if ultima_ronda <= 4:
        return f"1-{ultima_ronda}"
    resto = ultima_ronda - 5
    return f"{2 + resto // 7}-{resto % 7 + 1}"


# --------------------------- resumen por jugador ---------------------------
def _unidades(p: dict) -> list[dict]:
    """Tablero de un participante, ordenado de forma estable (coste desc, nombre)."""
    out = []
    for u in p.get("units", []) or []:
        items = [_limpiar(i) for i in (u.get("itemNames") or [])]
        out.append({
            "id": _limpiar(u.get("character_id", "")),
            "coste": (u.get("rarity", 0) or 0) + 1,
            "estrellas": u.get("tier", 1) or 1,
            "items": items,
            "items_de_dano": sum(1 for i in (u.get("itemNames") or []) if _es_item_de_dano(i)),
        })
    out.sort(key=lambda x: (-x["coste"], -x["estrellas"], x["id"]))
    return out


def _rasgos_activos(p: dict) -> list[dict]:
    out = [
        {"id": _limpiar(t.get("name", "")), "nivel": t.get("style", 0) or 0,
         "unidades": t.get("num_units", 0) or 0}
        for t in (p.get("traits") or []) if (t.get("style", 0) or 0) >= 1
    ]
    out.sort(key=lambda x: (-x["nivel"], -x["unidades"], x["id"]))
    return out


def _carry(unidades: list[dict]) -> dict | None:
    """Unidad con más ítems de daño; desempate por estrellas y nº de ítems.
    Si nadie lleva ítems de daño, no hay carry detectable (None, no se inventa)."""
    if not unidades:
        return None
    mejor = max(unidades, key=lambda u: (u["items_de_dano"], u["estrellas"], len(u["items"])))
    if mejor["items_de_dano"] == 0:
        return None
    return {
        "id": mejor["id"],
        "estrellas": mejor["estrellas"],
        "items": mejor["items"],
        "items_de_dano": mejor["items_de_dano"],
        "itemizada_completa": len(mejor["items"]) >= 3,
    }


def _resumen_jugador(p: dict) -> dict:
    unidades = _unidades(p)
    return {
        "puuid": p.get("puuid", ""),
        "puesto": p.get("placement", 0) or 0,
        "nivel_final": p.get("level", 0) or 0,
        "oro_al_morir": p.get("gold_left", 0) or 0,
        "ultima_ronda": p.get("last_round", 0) or 0,
        "ronda_eliminacion": ronda_a_etapa(p.get("last_round", 0) or 0),
        "dano_a_jugadores": p.get("total_damage_to_players", 0) or 0,
        "jugadores_eliminados": p.get("players_eliminated", 0) or 0,
        "tiempo_vivo_s": round(p.get("time_eliminated", 0) or 0),
        "densidad_2mas": sum(1 for u in unidades if u["estrellas"] >= 2),
        "densidad_3": sum(1 for u in unidades if u["estrellas"] >= 3),
        "unidades": unidades,
        "rasgos": _rasgos_activos(p),
        "carry": _carry(unidades),
    }


# ------------------------------ agregaciones ------------------------------
def _percentil(valor: float, todos: list[float]) -> int:
    """% del lobby con valor <= al del jugador (0-100). Determinista."""
    if not todos:
        return 0
    return round(100 * sum(1 for v in todos if v <= valor) / len(todos))


def _media(valores: list[float]) -> float:
    return round(sum(valores) / len(valores), 2) if valores else 0.0


def _contestacion(yo: dict, rivales: list[dict]) -> dict:
    """Mapa de contestación: para mis unidades CLAVE (coste >= 4, o con 2+ ítems,
    o 3★), cuántos rivales tienen en su tablero esa misma unidad."""
    claves = [u for u in yo["unidades"]
              if u["coste"] >= 4 or len(u["items"]) >= 2 or u["estrellas"] >= 3]
    detalle = []
    for u in claves:
        n = sum(1 for r in rivales if any(ru["id"] == u["id"] for ru in r["unidades"]))
        detalle.append({"unidad": u["id"], "coste": u["coste"], "rivales_con_ella": n})
    detalle.sort(key=lambda x: (-x["rivales_con_ella"], -x["coste"], x["unidad"]))
    max_rivales = max((d["rivales_con_ella"] for d in detalle), default=0)
    return {
        "unidades_clave": detalle,
        "max_rivales_compartiendo": max_rivales,
        "unidades_contestadas_2mas": sum(1 for d in detalle if d["rivales_con_ella"] >= 2),
    }


# -------------------------------- entrada --------------------------------
def extraer(match: dict, puuid: str) -> dict:
    """Hechos verificables de la partida para el jugador `puuid`.

    Lanza ValueError si el jugador no está en la partida.
    """
    info = match.get("info", {}) or {}
    participantes = info.get("participants", []) or []
    resumenes = [_resumen_jugador(p) for p in participantes]
    resumenes.sort(key=lambda r: r["puesto"])

    yo = next((r for r in resumenes if r["puuid"] == puuid), None)
    if yo is None:
        raise ValueError(f"El puuid {puuid[:12]}… no está en la partida")

    rivales = [r for r in resumenes if r["puuid"] != puuid]
    podio = [r for r in resumenes if 1 <= r["puesto"] <= 4]

    niveles = [r["nivel_final"] for r in resumenes]
    densidades = [r["densidad_2mas"] for r in resumenes]
    danos = [r["dano_a_jugadores"] for r in resumenes]

    return {
        "engine_version": ENGINE_VERSION,
        "match_id": match.get("metadata", {}).get("match_id", ""),
        "queue_id": info.get("queue_id"),
        "duracion_s": round(info.get("game_length", 0) or 0),
        "version_juego": info.get("game_version", ""),
        "jugador": yo,
        "lobby": {
            "jugadores": resumenes,           # los 8, ordenados por puesto
            "podio": {                        # media del top 4 (decisión cerrada n.º 4)
                "nivel_medio": _media([r["nivel_final"] for r in podio]),
                "densidad_2mas_media": _media([r["densidad_2mas"] for r in podio]),
                "densidad_3_media": _media([r["densidad_3"] for r in podio]),
                "oro_al_morir_medio": _media([r["oro_al_morir"] for r in podio]),
                "dano_medio": _media([r["dano_a_jugadores"] for r in podio]),
            },
        },
        "contestacion": _contestacion(yo, rivales),
        "percentiles": {                      # % del lobby con valor <= al mío
            "nivel": _percentil(yo["nivel_final"], niveles),
            "densidad_2mas": _percentil(yo["densidad_2mas"], densidades),
            "dano_a_jugadores": _percentil(yo["dano_a_jugadores"], danos),
        },
    }
