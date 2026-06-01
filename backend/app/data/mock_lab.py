"""Datos de EJEMPLO del Lab (centro de entrenamiento) y del Perfil (GPI).

# AQUÍ saldrán de agregaciones de meta + Riot API en producción.
Replican los del prototipo (synapse-prototipo/lab.html, perfil.html, lol-campeon.html).
Arquetipos/ítems/runas genéricos, sin nombres de Riot.
"""

# ----------------------------- Exploradores -----------------------------
LAB = {
    "tft": {
        "units": [
            {"n": "Místico", "cost": 4, "wr": 58, "use": 24, "sub": "Portador mágico", "chips": ["Báculo Arcano", "Velo Espectral", "Reloj de Arena"]},
            {"n": "Centinela", "cost": 5, "wr": 56, "use": 18, "sub": "Tanque", "chips": ["Égida del Guardián", "Manto Rúnico"]},
            {"n": "Francotirador", "cost": 4, "wr": 54, "use": 21, "sub": "Carry físico", "chips": ["Filo Voraz", "Guante Letal"]},
            {"n": "Vanguardia", "cost": 1, "wr": 52, "use": 40, "sub": "Frontline reroll", "chips": ["Cota Reforzada"]},
            {"n": "Invocador", "cost": 5, "wr": 51, "use": 12, "sub": "Escalado tardío", "chips": ["Tomo Arcano"]},
            {"n": "Pistolero", "cost": 2, "wr": 48, "use": 27, "sub": "Carry reroll", "chips": ["Filo Voraz", "Guante Letal"]},
            {"n": "Hechicero", "cost": 3, "wr": 55, "use": 19, "sub": "Daño mágico", "chips": ["Vara Letal", "Reloj de Arena"]},
            {"n": "Guardián", "cost": 2, "wr": 53, "use": 22, "sub": "Tanque reroll", "chips": ["Égida del Guardián"]},
            {"n": "Berserker", "cost": 2, "wr": 50, "use": 17, "sub": "Luchador", "chips": ["Filo Voraz"]},
            {"n": "Vidente", "cost": 3, "wr": 49, "use": 15, "sub": "Control", "chips": ["Reloj de Arena"]},
            {"n": "Curandera", "cost": 1, "wr": 47, "use": 20, "sub": "Sostén", "chips": ["Lágrima Eterna"]},
            {"n": "Mago", "cost": 4, "wr": 53, "use": 14, "sub": "Portador mágico", "chips": ["Báculo Arcano"]},
        ],
        "items": [
            {"n": "Báculo Arcano", "wr": 60, "use": 19, "sub": "Poder mágico", "chips": ["Místico", "Hechicero"]},
            {"n": "Filo Voraz", "wr": 57, "use": 23, "sub": "Robo de vida", "chips": ["Francotirador", "Pistolero"]},
            {"n": "Égida del Guardián", "wr": 55, "use": 15, "sub": "Aguante", "chips": ["Centinela", "Guardián"]},
            {"n": "Reloj de Arena", "wr": 53, "use": 11, "sub": "Utilidad", "chips": ["Místico"]},
            {"n": "Guante Letal", "wr": 50, "use": 21, "sub": "Crítico", "chips": ["Francotirador"]},
            {"n": "Manto Rúnico", "wr": 47, "use": 14, "sub": "Resist. mágica", "chips": ["Centinela"]},
            {"n": "Velo Espectral", "wr": 54, "use": 12, "sub": "Anti-mágico", "chips": ["Centinela", "Guardián"]},
            {"n": "Lágrima Eterna", "wr": 49, "use": 18, "sub": "Maná", "chips": ["Hechicero", "Mago"]},
            {"n": "Vara Letal", "wr": 52, "use": 13, "sub": "Daño mágico", "chips": ["Hechicero"]},
            {"n": "Corona Solar", "wr": 46, "use": 9, "sub": "Daño en área", "chips": ["Mago"]},
        ],
        "augments": [
            {"n": "Convergencia Mística", "tier": "S", "wr": 61, "use": 9, "sub": "Refuerza Místicos", "chips": ["Flex Místicos"]},
            {"n": "Corazón de Cristal", "tier": "S", "wr": 58, "use": 14, "sub": "Económico-poder", "chips": ["Flex Místicos", "Hiperscaling Magos"]},
            {"n": "Mente Táctica", "tier": "A", "wr": 55, "use": 12, "sub": "Tempo", "chips": ["Reroll Vanguardias"]},
            {"n": "Botín de Guerra", "tier": "A", "wr": 53, "use": 10, "sub": "Oro por combate", "chips": ["Fast 8 Francotiradores"]},
            {"n": "Tempo Perfecto", "tier": "A", "wr": 54, "use": 11, "sub": "Tempo de nivel", "chips": ["Reroll Vanguardias"]},
            {"n": "Reserva de Oro", "tier": "B", "wr": 50, "use": 13, "sub": "Económico", "chips": ["Hiperscaling Magos"]},
            {"n": "Eco Resonante", "tier": "B", "wr": 49, "use": 8, "sub": "Situacional", "chips": ["Hiperscaling Magos"]},
            {"n": "Doble Problema", "tier": "C", "wr": 47, "use": 7, "sub": "Reroll agresivo", "chips": ["Reroll Pistoleros"]},
        ],
    },
    "lol": {
        "units": [
            {"n": "Mago de control", "cost": 4, "wr": 54, "use": 14, "sub": "Mid", "chips": ["Tomo Arcano", "Cetro Abisal"]},
            {"n": "Tirador hipercarry", "cost": 4, "wr": 52, "use": 16, "sub": "ADC", "chips": ["Filo Voraz", "Botas Veloces"]},
            {"n": "Luchador de línea", "cost": 3, "wr": 52, "use": 11, "sub": "Top", "chips": ["Égida de Hierro"]},
            {"n": "Encantador", "cost": 2, "wr": 51, "use": 12, "sub": "Support", "chips": ["Cetro Abisal"]},
            {"n": "Asesino", "cost": 4, "wr": 50, "use": 9, "sub": "Mid", "chips": ["Filo Voraz"]},
            {"n": "Tanque iniciador", "cost": 3, "wr": 49, "use": 8, "sub": "Top", "chips": ["Égida de Hierro"]},
            {"n": "Asesino de acceso", "cost": 4, "wr": 50, "use": 9, "sub": "Mid/Jungla", "chips": ["Filo Voraz"]},
            {"n": "Bruiser de jungla", "cost": 3, "wr": 51, "use": 13, "sub": "Jungla", "chips": ["Lanza Crepuscular"]},
            {"n": "Maga de poke", "cost": 3, "wr": 52, "use": 10, "sub": "Mid", "chips": ["Grimorio Prohibido"]},
            {"n": "Soporte de enganche", "cost": 2, "wr": 49, "use": 11, "sub": "Support", "chips": ["Coraza Vital"]},
        ],
        "items": [
            {"n": "Filo Voraz", "wr": 55, "use": 22, "sub": "Crítico + robo vida", "chips": ["Tirador hipercarry", "Asesino"]},
            {"n": "Tomo Arcano", "wr": 54, "use": 18, "sub": "Poder de habilidad", "chips": ["Mago de control"]},
            {"n": "Égida de Hierro", "wr": 53, "use": 15, "sub": "Aguante", "chips": ["Luchador de línea", "Tanque iniciador"]},
            {"n": "Cetro Abisal", "wr": 51, "use": 13, "sub": "Penetración mágica", "chips": ["Mago de control", "Encantador"]},
            {"n": "Botas Veloces", "wr": 50, "use": 31, "sub": "Movilidad", "chips": ["Todos los roles"]},
            {"n": "Lanza Crepuscular", "wr": 52, "use": 14, "sub": "Bruiser", "chips": ["Bruiser de jungla", "Luchador de línea"]},
            {"n": "Grimorio Prohibido", "wr": 51, "use": 12, "sub": "Poder mágico", "chips": ["Maga de poke", "Mago de control"]},
            {"n": "Coraza Vital", "wr": 50, "use": 16, "sub": "Tanque", "chips": ["Tanque iniciador"]},
            {"n": "Daga Veloz", "wr": 48, "use": 19, "sub": "Vel. ataque", "chips": ["Tirador hipercarry"]},
        ],
        "augments": [  # en LoL = runas
            {"n": "Conquistador", "tier": "S", "wr": 54, "use": 17, "sub": "Combate prolongado", "chips": ["Luchador de línea"]},
            {"n": "Cometa Arcano", "tier": "A", "wr": 52, "use": 14, "sub": "Daño a distancia", "chips": ["Mago de control"]},
            {"n": "Golpe Letal", "tier": "A", "wr": 51, "use": 12, "sub": "Burst", "chips": ["Asesino"]},
            {"n": "Aro de Hielo", "tier": "B", "wr": 49, "use": 9, "sub": "Tanque/utilidad", "chips": ["Tanque iniciador"]},
            {"n": "Tormenta Veloz", "tier": "A", "wr": 52, "use": 13, "sub": "Vel. ataque", "chips": ["Tirador hipercarry"]},
            {"n": "Muro de Hueso", "tier": "B", "wr": 49, "use": 10, "sub": "Defensa", "chips": ["Tanque iniciador"]},
            {"n": "Sed de Sangre", "tier": "B", "wr": 50, "use": 11, "sub": "Sustain", "chips": ["Bruiser de jungla"]},
        ],
    },
}

STYLES = {"tft": ["Standard", "Reroll", "Fast 8"], "lol": ["Top", "Jungla", "Mid", "ADC", "Support"]}

# ----------------------------- Recetas de ítems (TFT) -----------------------------
COMPONENTS = ["Espada", "Arco", "Vara", "Lágrima", "Cota", "Capa", "Cinturón", "Guante", "Pala"]
RECIPES = {
    "0-0": "Filo Doble", "0-1": "Filo Veloz", "0-2": "Hoja Arcana", "0-3": "Filo de Maná", "0-4": "Tajo Templado", "0-5": "Filo Sombrío", "0-6": "Mandoble Vital", "0-7": "Filo Letal", "0-8": "Emblema Guerrero",
    "1-1": "Ráfaga", "1-2": "Arco Rúnico", "1-3": "Arco de Maná", "1-4": "Arco Templado", "1-5": "Arco Espectral", "1-6": "Arco Vital", "1-7": "Arco Letal", "1-8": "Emblema Tirador",
    "2-2": "Núcleo Arcano", "2-3": "Báculo Arcano", "2-4": "Vara Templada", "2-5": "Velo Arcano", "2-6": "Vara Vital", "2-7": "Vara Letal", "2-8": "Emblema Mago",
    "3-3": "Fuente de Maná", "3-4": "Égida de Maná", "3-5": "Velo de Maná", "3-6": "Corazón de Maná", "3-7": "Maná Letal", "3-8": "Emblema Místico",
    "4-4": "Muralla", "4-5": "Bastión", "4-6": "Égida del Guardián", "4-7": "Cota Afilada", "4-8": "Emblema Guardián",
    "5-5": "Velo Espectral", "5-6": "Manto Rúnico", "5-7": "Capa Afilada", "5-8": "Emblema Centinela",
    "6-6": "Corazón Titán", "6-7": "Guante Vital", "6-8": "Emblema Coloso",
    "7-7": "Doble Crítico", "7-8": "Emblema Asesino",
    "8-8": "Corona Cambiante",
}

# ----------------------------- Perfil de habilidades (GPI) -----------------------------
GPI = {
    "tft": {"axes": ["Economía", "Posición", "Nivel", "Augments", "Flexib.", "Consist."], "you": [72, 55, 68, 61, 80, 66], "avg": [62, 58, 61, 59, 57, 63]},
    "lol": {"axes": ["Farmeo", "Lucha", "Visión", "Objetivos", "Supervi.", "Consist."], "you": [74, 63, 48, 52, 58, 67], "avg": [60, 62, 56, 58, 61, 60]},
}

# ----------------------------- Build de campeón (LoL) -----------------------------
CHAMPION = {
    "name": "Mago de control", "role": "Mid", "tier": "S", "difficulty": "Media",
    "stats": {"wr": "53%", "pick": "14%", "ban": "8%", "kda": "3.1"},
    "build": ["Tomo Arcano", "Botas de Hechicero", "Cetro Abisal", "Velo Espectral", "Reloj de Arena"],
    "runes": {"primary": ["Cometa Arcano", "Maná Veloz", "Trascendencia", "Combustión"], "secondary": ["Galleta Mágica", "Perspicacia Cósmica"]},
    "skills": {"order": "Q > E > W", "ult": "6 / 11 / 16"},
    "spells": ["Parpadeo", "Quemadura"],
    "counters": {"strong": [["Tanque de iniciación", "58%"], ["Luchador de línea", "55%"]], "weak": [["Asesino de acceso", "44%"], ["Tirador móvil", "47%"]]},
    "spikes": {"early": 58, "mid": 88, "late": 74},
}


def explorer(game: str, kind: str):
    return LAB.get(game, {}).get(kind, [])


def recipes():
    return {"components": COMPONENTS, "recipes": RECIPES}


def gpi(game: str):
    return GPI.get(game, {})


def champion(_id: str = ""):
    return CHAMPION
