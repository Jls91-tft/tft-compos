"""Datos de EJEMPLO (mock) — replican el prototipo de la Etapa 1.

# AQUÍ se sustituye por Riot API + IA + agregaciones reales en las Fases 1-3.
Centralizar los mocks aquí permite que el frontend se integre contra la API ya
mismo; cambiar a datos reales no altera la forma de la respuesta.
"""

# ----------------------------- Partidas -----------------------------
_MATCHES = {
    "tft": [
        {"id": "TFT_0002", "game": "tft", "result": "4", "title": "Flex Místicos",
         "meta": {"nivel": 9, "duracion": "32:45", "nota": "Top 4 cómodo"}},
        {"id": "TFT_0001", "game": "tft", "result": "1", "title": "Reroll Vanguardias",
         "meta": {"nivel": 8, "duracion": "38:12", "nota": "Eco fuerte"}},
        {"id": "TFT_0003", "game": "tft", "result": "8", "title": "Fast 8 Francotiradores",
         "meta": {"nivel": 8, "duracion": "24:10", "nota": "Sin frontline"}},
        {"id": "TFT_0004", "game": "tft", "result": "2", "title": "Hiperscaling Magos",
         "meta": {"nivel": 9, "duracion": "36:00", "nota": "Casi 1º"}},
    ],
    "lol": [
        {"id": "LOL_0002", "game": "lol", "result": "loss", "title": "Jungla · Luchador",
         "meta": {"kda": "4/7/6", "cs": 168, "duracion": "28:40"}},
        {"id": "LOL_0001", "game": "lol", "result": "win", "title": "Mid · Mago de control",
         "meta": {"kda": "8/2/11", "cs": 224, "duracion": "31:05"}},
        {"id": "LOL_0003", "game": "lol", "result": "win", "title": "ADC · Tirador",
         "meta": {"kda": "12/4/8", "cs": 256, "duracion": "34:20"}},
        {"id": "LOL_0004", "game": "lol", "result": "loss", "title": "Top · Tanque",
         "meta": {"kda": "2/5/9", "cs": 198, "duracion": "29:55"}},
    ],
}

# ----------------------------- Informes de coaching -----------------------------
_REPORTS = {
    "tft": {
        "game": "tft", "match_id": "TFT_0002",
        "verdict": "Buen pilotaje, pero perdiste el Top 2 por una economía conservadora "
                   "en la etapa media y un error de posicionamiento que te costó tu mejor combate.",
        "focus": "Antes de cada combate, revisa dónde está la amenaza enemiga y protege a tu portador.",
        "metrics": [
            {"value": "4.º", "label": "Colocación final", "status": "good", "benchmark": "Top 4 conseguido"},
            {"value": "142", "label": "Daño infligido", "status": "good", "benchmark": "Media Diamante: 128"},
            {"value": "18", "label": "Oro de interés perdido", "status": "warn", "benchmark": "Objetivo: < 8"},
            {"value": "4-1", "label": "Llegada a Nivel 8", "status": "warn", "benchmark": "Media top: 3-5"},
        ],
        "did_well": [
            "Transición limpia a tu composición final sin forzar unidades.",
            "Priorizaste los ítems correctos en tu portador desde la etapa 2.",
            "Buen manejo de las rachas: cortaste la perdedora a tiempo.",
        ],
        "errors": [
            {"title": "Subida de nivel tardía en la etapa 3", "severity": "major",
             "what": "Mantuviste el oro por encima de 50 entre 3-2 y 3-5 sin subir a nivel 8.",
             "why": "Llegaste tarde a tus unidades clave y perdiste 3 rondas seguidas (de 78 a 41 de vida).",
             "fix": "Con ≥ 50 de oro y > 50 de vida en 3-2, sube a 8 esa misma ronda y rollea después.",
             "when": "Etapa 3-2 → 3-5"},
            {"title": "Portador expuesto al Asesino enemigo", "severity": "major",
             "what": "Dejaste a tu Francotirador en el borde, al alcance del Asesino, sin cobertura.",
             "why": "Cayó en los primeros 2 segundos; tu mayor fuente de daño apenas disparó.",
             "fix": "Coloca al portador en la esquina opuesta a la amenaza, detrás de tu frontline.",
             "when": "Etapa 4-1"},
        ],
        "corrective": "Ganabas las peleas por estadísticas; las perdías por dos decisiones de criterio "
                      "(subir tarde y posicionar mal el portador). Corrige esas dos y este 4.º es un Top 2.",
        "action_plan": [
            "Revisa el board rival y reposiciona a tu portador antes de cada ronda.",
            "Con vida > 50 en la etapa 3, prioriza subir de nivel sobre acumular oro.",
            "Elige augments que refuercen tu línea de juego, no solo valor económico.",
            "Rollea en ventanas: a nivel estable y con 2-3 unidades concretas como objetivo.",
        ],
    },
    "lol": {
        "game": "lol", "match_id": "LOL_0002",
        "verdict": "La derrota no se decidió en los duelos, sino en el mapa: cediste el control de "
                   "cuatro objetivos mayores en ventanas en las que tenías prioridad.",
        "focus": "Juega alrededor de los timers: prioriza drake y heraldo por encima de los campamentos.",
        "metrics": [
            {"value": "Derrota", "label": "Resultado", "status": "bad", "benchmark": "Racha: 2 derrotas"},
            {"value": "1.4", "label": "KDA (4/7/6)", "status": "warn", "benchmark": "Objetivo: > 2.5"},
            {"value": "5.9", "label": "CS por minuto", "status": "warn", "benchmark": "Jungla Plata: ~6.5"},
            {"value": "2/6", "label": "Objetivos asegurados", "status": "bad", "benchmark": "Drakes + heraldo"},
        ],
        "did_well": [
            "Ruta inicial eficiente: clear rápido y nivel 3 con prioridad.",
            "Ganaste tus enfrentamientos 1 contra 1 dentro de la jungla.",
            "Buen daño total a campeones para tu rol.",
        ],
        "errors": [
            {"title": "Objetivos cedidos con prioridad a favor", "severity": "major",
             "what": "Entre los minutos 8 y 14 se fueron dos drakes estando vivo y cerca.",
             "why": "Regalaste alma y tempo; el rival escaló sin oposición.",
             "fix": "A 30 s del spawn, deja el campamento y colócate cerca del foso con visión previa.",
             "when": "Min. 8:00 y 14:00"},
            {"title": "Sobre-extensión sin visión", "severity": "major",
             "what": "4 de tus 7 muertes fueron en jungla enemiga, sin guardianes y con oleadas en contra.",
             "why": "Cada muerte dio oro, prioridad y un objetivo gratis al rival.",
             "fix": "No entres a la jungla rival sin un guardián de control y sin ver a 3 enemigos.",
             "when": "Min. 12 → 24"},
        ],
        "corrective": "Tu mecánica está bien (farm y duelos ganados). Lo que te frena es la macro: "
                      "ancla tu ruta a los timers de objetivos y deja visión previa.",
        "action_plan": [
            "A 30 s de un drake, abandona el farm y agrúpate cerca del objetivo.",
            "No entres a la jungla enemiga sin un guardián de control si vas por detrás.",
            "Resetea DESPUÉS de asegurar el objetivo, nunca justo antes.",
            "Pinga el objetivo a tu equipo 30 s antes para coordinar.",
        ],
    },
}

# ----------------------------- Estadísticas -----------------------------
_STATS = {
    "tft": {
        "kpis": [
            {"v": "4.2", "k": "Colocación media", "cls": "good", "bench": "Top 200 EUW"},
            {"v": "58%", "k": "Top 4", "cls": "good", "bench": "Media: 50%"},
            {"v": "14%", "k": "Top 1", "cls": "good", "bench": "Media: 12.5%"},
            {"v": "312", "k": "Partidas (Set)", "cls": "", "bench": "Últimos 30 días"},
        ],
        "evol": {"label": "Colocación media por semana (menor es mejor)", "min": 1, "max": 8,
                 "invert": True, "suffix": "", "points": [
                     {"label": "S1", "value": 4.8}, {"label": "S2", "value": 4.6}, {"label": "S3", "value": 4.9},
                     {"label": "S4", "value": 4.3}, {"label": "S5", "value": 4.4}, {"label": "S6", "value": 4.1},
                     {"label": "S7", "value": 4.0}, {"label": "S8", "value": 4.2}]},
        "dist": {"label": "Distribución de colocaciones", "bars": [
            {"label": "1.º", "value": 44, "color": "gold"}, {"label": "2.º", "value": 38, "color": "good"},
            {"label": "3.º", "value": 40, "color": "good"}, {"label": "4.º", "value": 59, "color": "good"},
            {"label": "5.º", "value": 41, "color": "warn"}, {"label": "6.º", "value": 34, "color": "warn"},
            {"label": "7.º", "value": 30, "color": "bad"}, {"label": "8.º", "value": 26, "color": "bad"}]},
        "tableA": {"title": "Comps más jugadas", "cols": ["Comp", "Partidas", "Coloc.", "Top 4"], "rows": [
            ["Flex Místicos", "86", "3.8", "64%"], ["Reroll Vanguardias", "64", "4.1", "58%"],
            ["Fast 8 Francotiradores", "48", "4.6", "48%"], ["Hiperscaling Magos", "39", "4.0", "60%"]]},
        "tableB": {"title": "Augments destacados", "cols": ["Augment", "Veces", "Coloc."], "rows": [
            ["Corazón de Cristal", "41", "3.6"], ["Mente Táctica", "33", "3.9"], ["Botín de Guerra", "28", "4.2"]]},
        "insights": [
            {"cls": "bad", "ic": "📉", "t": "El 68% de tus Top 2 fallidos son por subir tarde a nivel 8",
             "d": "Si llegas a 8 antes de 4-2, tu colocación media es 3.1; si tarde, 4.7."},
            {"cls": "warn", "ic": "🎯", "t": "Fast 8 es tu mayor fuga de LP",
             "d": "Colocación con Fast 8: 4.6 · con Standard: 3.8."},
        ],
    },
    "lol": {
        "kpis": [
            {"v": "54%", "k": "Winrate", "cls": "good", "bench": "Media: 50%"},
            {"v": "2.8", "k": "KDA medio", "cls": "good", "bench": "Objetivo: 2.5"},
            {"v": "6.4", "k": "CS por minuto", "cls": "warn", "bench": "Objetivo: 6.5"},
            {"v": "204", "k": "Partidas", "cls": "", "bench": "Últimos 30 días"},
        ],
        "evol": {"label": "Winrate por semana", "min": 30, "max": 70, "invert": False, "suffix": "%", "points": [
            {"label": "S1", "value": 48}, {"label": "S2", "value": 50}, {"label": "S3", "value": 47},
            {"label": "S4", "value": 53}, {"label": "S5", "value": 55}, {"label": "S6", "value": 52},
            {"label": "S7", "value": 58}, {"label": "S8", "value": 54}]},
        "dist": {"label": "Partidas por rol", "bars": [
            {"label": "Mid", "value": 124, "color": "accent"}, {"label": "Jungla", "value": 38, "color": "good"},
            {"label": "ADC", "value": 22, "color": "warn"}, {"label": "Top", "value": 12, "color": "bad"},
            {"label": "Sup", "value": 8, "color": "muted"}]},
        "tableA": {"title": "Arquetipos más jugados", "cols": ["Arquetipo", "Partidas", "Winrate"], "rows": [
            ["Mago de control", "78", "57%"], ["Asesino", "31", "52%"], ["Tirador", "22", "50%"]]},
        "tableB": {"title": "Rendimiento por rol", "cols": ["Rol", "Partidas", "Winrate"], "rows": [
            ["Mid", "124", "57%"], ["Jungla", "38", "47%"], ["ADC", "22", "55%"]]},
        "insights": [
            {"cls": "bad", "ic": "📉", "t": "Tu winrate cae al 42% fuera de Mid",
             "d": "En Mid ganas el 57%. En autofill rindes peor."},
            {"cls": "warn", "ic": "🐉", "t": "Cedes el primer drake en el 60% de tus derrotas",
             "d": "El control de objetivos tempranos marca la diferencia."},
        ],
    },
}

# ----------------------------- Meta -----------------------------
_META = {
    "tft": {
        "patch": "14.7", "rank": "Diamante +", "guide": True,
        "styles": ["Todos", "Standard", "Reroll", "Fast 8"],
        "metricCols": [{"k": "avg", "label": "Coloc."}, {"k": "top4", "label": "Top 4"},
                       {"k": "win", "label": "1.º"}, {"k": "pick", "label": "Pick"}],
        "comps": [
            {"tier": "S", "name": "Flex Místicos", "style": "Standard", "difficulty": "Media",
             "metrics": {"avg": "3.9", "top4": "64%", "win": "16%", "pick": "12.4%"},
             "units": [{"n": "Místico", "c": 4}, {"n": "Hechicero", "c": 3}, {"n": "Curandera", "c": 2}]},
            {"tier": "S", "name": "Reroll Vanguardias", "style": "Reroll", "difficulty": "Fácil",
             "metrics": {"avg": "4.0", "top4": "62%", "win": "14%", "pick": "9.8%"},
             "units": [{"n": "Vanguardia", "c": 1}, {"n": "Berserker", "c": 2}, {"n": "Guardián", "c": 2}]},
            {"tier": "A", "name": "Fast 8 Francotiradores", "style": "Fast 8", "difficulty": "Difícil",
             "metrics": {"avg": "4.3", "top4": "55%", "win": "13%", "pick": "8.1%"},
             "units": [{"n": "Francotir.", "c": 4}, {"n": "Magista", "c": 5}, {"n": "Vidente", "c": 3}]},
        ],
    },
    "lol": {
        "patch": "14.7", "rank": "Esmeralda +", "guide": False,
        "styles": ["Todos", "Top", "Jungla", "Mid", "ADC", "Support"],
        "metricCols": [{"k": "win", "label": "Winrate"}, {"k": "pick", "label": "Pick"},
                       {"k": "ban", "label": "Ban"}, {"k": "kda", "label": "KDA"}],
        "comps": [
            {"tier": "S", "name": "Mago de control", "style": "Mid", "difficulty": "Media",
             "metrics": {"win": "53%", "pick": "14%", "ban": "8%", "kda": "3.1"}, "units": []},
            {"tier": "A", "name": "Tirador de hipercarry", "style": "ADC", "difficulty": "Media",
             "metrics": {"win": "51%", "pick": "16%", "ban": "4%", "kda": "2.9"}, "units": []},
        ],
    },
}

# ----------------------------- Chat (coach) -----------------------------
_CHAT = {
    "tft": {
        "4-1": "La perdiste por posicionamiento, no por poder de tablero: tu Francotirador estaba al "
               "alcance del Asesino y cayó enseguida. En la esquina opuesta, ese combate era tuyo.",
        "augment": "En 4-2 ya liderabas en economía, así que el augment de oro rindió poco. Uno de "
                   "combate o de tu rasgo Místico te habría dado más tablero para pelear el Top 2.",
        "economia": "Tu problema no fue tener poco oro, sino acumular de más: te quedaste sobre 50 sin "
                    "subir a 8 a tiempo. La economía es un medio; gástala para llegar antes a tus unidades.",
    },
    "lol": {
        "objetivos": "No jugaste alrededor de los timers: a los 8' y 14' estabas en el campamento opuesto "
                     "cuando salía el drake. Llegando 30 s antes, esos dos drakes son tuyos.",
        "jungla": "4 de tus 7 muertes fueron en jungla rival sin visión y con oleadas en contra. No entres "
                  "sin un guardián de control puesto y sin ver a 3 enemigos.",
        "subir": "Tu mecánica está bien; lo que te frena es el mapa. Prioriza drake y heraldo sobre los "
                 "campamentos: es el ajuste que más LP te dará.",
    },
}

_FALLBACK = ("Buena pregunta. En la versión real podré responderte con los datos exactos de esta "
             "partida. De momento tengo respuestas de ejemplo para las preguntas sugeridas. 🙂")


def matches(game: str):
    return _MATCHES.get(game, [])


def report(game: str, match_id: str):
    # En mock ignoramos match_id y devolvemos el informe de ejemplo del juego.
    return _REPORTS.get(game)


def stats(game: str):
    return _STATS.get(game, {})


def meta(game: str):
    return _META.get(game, {})


def chat_answer(game: str, question: str) -> str:
    q = question.lower()
    table = _CHAT.get(game, {})
    for key, answer in table.items():
        if key in q:
            return answer
    return _FALLBACK
