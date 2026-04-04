"""
ALLERGY GUARDIAN — Real-time allergen detection and recipe safety checker.
=========================================================================
Runs on EVERY recipe before it reaches the user. Non-negotiable.
This is YOUR (backend dev) full implementation — no stub.
"""

from typing import List, Dict


# ============ ALLERGEN DATABASE ============

ALLERGEN_DATABASE = {
    "peanuts": {
        "aliases": ["groundnuts", "peanut butter", "peanut oil", "arachis oil",
                     "groundnut oil", "peanut flour", "peanut sauce", "satay sauce"],
        "cross_reactive": ["tree nuts", "lupin"],
        "safe_substitutes": ["sunflower seed butter", "tahini", "soy butter",
                              "almond butter (if no tree nut allergy)"],
    },
    "tree_nuts": {
        "aliases": ["almonds", "cashews", "walnuts", "pistachios", "pecans",
                     "macadamia", "hazelnuts", "brazil nuts", "pine nuts",
                     "praline", "marzipan", "nougat", "badam"],
        "cross_reactive": ["peanuts", "coconut (rarely)"],
        "safe_substitutes": ["sunflower seeds", "pumpkin seeds",
                              "roasted chickpeas", "watermelon seeds"],
    },
    "shellfish": {
        "aliases": ["shrimp", "prawns", "crab", "lobster", "crayfish", "oyster",
                     "clam", "mussel", "scallop", "squid", "octopus", "prawn crackers"],
        "cross_reactive": ["mollusks", "crustaceans"],
        "safe_substitutes": ["chicken", "tofu", "paneer", "mushrooms", "jackfruit"],
    },
    "fish": {
        "aliases": ["salmon", "tuna", "cod", "sardine", "anchovy", "mackerel",
                     "tilapia", "fish sauce", "worcestershire sauce", "surimi",
                     "pomfret", "rohu", "hilsa"],
        "cross_reactive": ["shellfish (sometimes)"],
        "safe_substitutes": ["chicken", "tofu", "tempeh", "seitan"],
    },
    "lactose": {
        "aliases": ["milk", "cheese", "butter", "cream", "yogurt", "curd",
                     "paneer", "ghee", "whey", "casein", "buttermilk", "khoya",
                     "mawa", "condensed milk", "ice cream", "cottage cheese", "ricotta"],
        "cross_reactive": [],
        "safe_substitutes": ["oat milk", "coconut milk", "coconut cream",
                              "almond milk", "soy milk", "vegan cheese",
                              "tofu paneer", "coconut yogurt", "vegan butter"],
    },
    "gluten": {
        "aliases": ["wheat", "barley", "rye", "semolina", "maida", "atta",
                     "bread", "pasta", "noodles", "couscous", "bulgur", "seitan",
                     "soy sauce", "beer", "flour tortilla", "chapati", "naan",
                     "roti", "puri"],
        "cross_reactive": ["spelt", "kamut", "triticale"],
        "safe_substitutes": ["rice flour", "almond flour", "coconut flour",
                              "chickpea flour (besan)", "rice noodles",
                              "gluten-free bread", "corn tortilla",
                              "tamari (GF soy sauce)", "rice", "quinoa",
                              "millet (bajra)", "sorghum (jowar)"],
    },
    "eggs": {
        "aliases": ["egg white", "egg yolk", "mayonnaise", "meringue", "aioli",
                     "hollandaise", "egg noodles", "french toast", "omelette",
                     "quiche", "custard", "eggnog"],
        "cross_reactive": [],
        "safe_substitutes": ["flax egg (1 tbsp flax + 3 tbsp water)", "chia egg",
                              "applesauce (in baking)", "mashed banana (in baking)",
                              "aquafaba", "silken tofu"],
    },
    "soy": {
        "aliases": ["soy sauce", "tofu", "tempeh", "edamame", "soy milk",
                     "miso", "soy protein", "soy lecithin", "soybean oil", "tamari"],
        "cross_reactive": ["lupin"],
        "safe_substitutes": ["coconut aminos", "chickpeas", "coconut milk",
                              "lentils", "other legumes"],
    },
    "sesame": {
        "aliases": ["sesame seeds", "tahini", "sesame oil", "halvah", "hummus", "til"],
        "cross_reactive": [],
        "safe_substitutes": ["sunflower seed butter", "poppy seeds", "hemp seeds"],
    },
    "mustard": {
        "aliases": ["mustard seeds", "mustard oil", "mustard powder", "rai",
                     "sarson", "dijon", "yellow mustard"],
        "cross_reactive": ["rapeseed", "canola"],
        "safe_substitutes": ["horseradish", "wasabi", "turmeric (for color)"],
    },
    "celery": {
        "aliases": ["celery seed", "celery salt", "celeriac"],
        "cross_reactive": ["carrot", "parsley", "fennel"],
        "safe_substitutes": ["cucumber (for crunch)", "fennel", "jicama"],
    },
    "sulfites": {
        "aliases": ["wine", "dried fruits", "vinegar", "pickles", "jam",
                     "molasses", "grape juice"],
        "cross_reactive": [],
        "safe_substitutes": ["fresh fruits", "lemon juice",
                              "apple cider vinegar (check label)"],
    },
}


async def allergy_check(recipe: dict, user_allergies: list) -> dict:
    """
    Scans every ingredient in a recipe against the user's allergy profile.
    Returns safety status with warnings and substitutions.

    Args:
        recipe: dict with "ingredients" key — list of {"name": ..., "quantity": ...}
        user_allergies: list of {"allergen": "peanuts", "severity": "severe"} or
                        objects with .allergen / .severity attrs

    Returns:
        {
            "safe": bool,
            "warnings": [{"ingredient": str, "allergen": str, "severity": str, "message": str}],
            "substitutions": [{"replace": str, "with_options": [str], "note": str}],
            "checked_against": [str]
        }
    """
    if not user_allergies:
        return {"safe": True, "warnings": [], "substitutions": [], "checked_against": []}

    warnings: List[Dict] = []
    substitutions: List[Dict] = []
    is_safe = True

    for ingredient in recipe.get("ingredients", []):
        ing_name = (
            ingredient.get("name", "")
            if isinstance(ingredient, dict)
            else getattr(ingredient, "name", "")
        )
        ingredient_lower = ing_name.lower().strip()

        for allergy in user_allergies:
            if isinstance(allergy, dict):
                allergen = allergy.get("allergen", "")
                severity = allergy.get("severity", "moderate")
            else:
                allergen = getattr(allergy, "allergen", "")
                severity = getattr(allergy, "severity", "moderate")

            allergen_lower = allergen.lower().strip()
            allergen_data = ALLERGEN_DATABASE.get(allergen_lower, {})

            # Build full list of terms to match
            all_terms = [allergen_lower] + [
                a.lower() for a in allergen_data.get("aliases", [])
            ]

            matched = False
            for term in all_terms:
                if term in ingredient_lower or ingredient_lower in term:
                    matched = True
                    break

            # Check cross-reactive substances
            if not matched:
                cross_terms = [c.lower() for c in allergen_data.get("cross_reactive", [])]
                for term in cross_terms:
                    if term in ingredient_lower or ingredient_lower in term:
                        matched = True
                        break

            if matched:
                is_safe = False
                warnings.append({
                    "ingredient": ing_name,
                    "allergen": allergen,
                    "severity": severity,
                    "message": (
                        f"WARNING: {ing_name} contains/is related to "
                        f"{allergen} — {severity} allergy flagged"
                    ),
                })
                subs = allergen_data.get("safe_substitutes", [])
                if subs:
                    substitutions.append({
                        "replace": ing_name,
                        "with_options": subs,
                        "note": f"Substitute to avoid {allergen}",
                    })

    checked = []
    for a in user_allergies:
        if isinstance(a, dict):
            checked.append(a.get("allergen", ""))
        else:
            checked.append(getattr(a, "allergen", ""))

    return {
        "safe": is_safe,
        "warnings": warnings,
        "substitutions": substitutions,
        "checked_against": checked,
    }
