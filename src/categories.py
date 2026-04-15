CATEGORIES = {
    "general": {
        "id": "general",
        "name": "General Knowledge",
        "emoji": "🎯",
        "description": "Basic Pokemon knowledge",
        "difficulty": "mixed",
    },
    "gen1": {
        "id": "gen1",
        "name": "Generation I",
        "emoji": "🟢",
        "description": "Pokemon Red/Blue/Yellow (Kanto)",
        "difficulty": "easy",
    },
    "gen2": {
        "id": "gen2",
        "name": "Generation II",
        "emoji": "🟡",
        "description": "Pokemon Gold/Silver/Crystal (Johto)",
        "difficulty": "medium",
    },
    "gen3": {
        "id": "gen3",
        "name": "Generation III",
        "emoji": "🔴",
        "description": "Pokemon Ruby/Sapphire/Emerald (Hoenn)",
        "difficulty": "medium",
    },
    "types": {
        "id": "types",
        "name": "Pokemon Types",
        "emoji": "⚡",
        "description": "Type matchups and weaknesses",
        "difficulty": "medium",
    },
    "moves": {
        "id": "moves",
        "name": "Moves & Attacks",
        "emoji": "💥",
        "description": "Pokemon moves and abilities",
        "difficulty": "hard",
    },
    "pokedex": {
        "id": "pokedex",
        "name": "Pokedex Numbers",
        "emoji": "📖",
        "description": "Pokemon numbers and order",
        "difficulty": "hard",
    },
    "legendary": {
        "id": "legendary",
        "name": "Legendary Pokemon",
        "emoji": "⭐",
        "description": "Mythical and Legendary Pokemon",
        "difficulty": "medium",
    },
    "evolution": {
        "id": "evolution",
        "name": "Evolution",
        "emoji": "🔄",
        "description": "Evolution chains and methods",
        "difficulty": "medium",
    },
    "hardmode": {
        "id": "hardmode",
        "name": "Hard Mode",
        "emoji": "🔥",
        "description": "Tough questions for experts",
        "difficulty": "hard",
    },
}


def get_category_list():
    return list(CATEGORIES.values())


def get_category_by_id(cat_id):
    return CATEGORIES.get(cat_id)


def get_category_name(cat_id):
    cat = CATEGORIES.get(cat_id)
    return cat["name"] if cat else "Mixed"
