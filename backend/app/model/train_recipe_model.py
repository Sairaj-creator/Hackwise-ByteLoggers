"""
Train the TF-IDF recipe retrieval model.

This script ships with a richer seed corpus so the backend can move off the
8-recipe mock immediately. If you have a larger cleaned dataset JSON file,
pass it with `--dataset path/to/recipes.json` and it will be merged in.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Iterable

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer


def recipe(title, cuisine, ingredients, tags, steps):
    return {
        "title": title,
        "cuisine": cuisine,
        "ingredients": ingredients,
        "tags": tags,
        "steps": steps,
    }


SEED_RECIPES = [
    recipe("Paneer Jalfrezi", "Indian", ["paneer", "bell pepper", "onion", "tomato", "garam masala", "ginger", "garlic"], ["vegetarian", "gluten-free", "high-protein"], ["Cut paneer into cubes and slice the vegetables.", "Saute onion, ginger, and garlic until fragrant.", "Add tomato, bell pepper, and spices; cook until glossy.", "Fold in paneer, simmer briefly, and serve hot."]),
    recipe("Chana Masala", "Indian", ["chickpeas", "onion", "tomato", "garlic", "ginger", "cumin", "garam masala"], ["vegan", "gluten-free", "high-protein", "dairy-free"], ["Saute onion with garlic and ginger.", "Add tomato and spices, then cook into a masala base.", "Stir in chickpeas with a splash of water.", "Simmer until thick and finish with coriander."]),
    recipe("Vegetable Pulao", "Indian", ["rice", "carrot", "peas", "onion", "cumin", "ginger", "garam masala"], ["vegetarian", "gluten-free", "nut-free"], ["Wash and soak the rice briefly.", "Saute cumin, onion, and ginger in oil or ghee.", "Add vegetables and spices, then stir in rice.", "Cook with water until fluffy and aromatic."]),
    recipe("Dal Tadka", "Indian", ["lentils", "onion", "tomato", "garlic", "ginger", "turmeric", "cumin"], ["vegan", "gluten-free", "high-protein", "dairy-free"], ["Boil lentils until soft.", "Cook onion, tomato, garlic, ginger, and spices into a tempering.", "Pour the tempering into the cooked lentils.", "Simmer for a few minutes and serve."]),
    recipe("Palak Paneer", "Indian", ["paneer", "spinach", "onion", "garlic", "ginger", "cream", "garam masala"], ["vegetarian", "gluten-free", "high-protein"], ["Blanch spinach and blend into a smooth puree.", "Cook onion, garlic, and ginger until soft.", "Add spinach puree and spices, then simmer.", "Fold in paneer and cream before serving."]),
    recipe("Aloo Gobi", "Indian", ["potato", "cauliflower", "onion", "tomato", "turmeric", "cumin", "garlic"], ["vegan", "gluten-free", "dairy-free", "nut-free"], ["Parboil potato and cauliflower lightly.", "Saute onion and garlic with spices.", "Add tomato and cook into a quick sauce.", "Toss in vegetables and cook until tender."]),

    recipe("Spaghetti Pomodoro", "Italian", ["spaghetti", "tomato", "garlic", "olive oil", "basil", "onion"], ["vegan", "dairy-free", "nut-free"], ["Boil the spaghetti until al dente.", "Saute garlic and onion in olive oil.", "Add tomato and simmer into a light sauce.", "Toss with pasta and basil before serving."]),
    recipe("Mushroom Risotto", "Italian", ["rice", "mushroom", "onion", "garlic", "parmesan", "butter", "vegetable broth"], ["vegetarian", "gluten-free"], ["Saute onion, garlic, and mushroom in butter.", "Toast the rice briefly in the pan.", "Add broth gradually while stirring until creamy.", "Finish with parmesan and black pepper."]),
    recipe("Pesto Pasta", "Italian", ["pasta", "basil", "olive oil", "garlic", "parmesan", "spinach"], ["vegetarian", "nut-free"], ["Cook the pasta until tender.", "Blend basil, spinach, garlic, olive oil, and parmesan into pesto.", "Loosen the pesto with a spoon of pasta water.", "Toss with the pasta and serve immediately."]),
    recipe("Caprese Pasta Bake", "Italian", ["pasta", "tomato", "mozzarella", "basil", "olive oil", "garlic"], ["vegetarian", "nut-free"], ["Cook the pasta until just underdone.", "Mix pasta with tomato, garlic, olive oil, and basil.", "Top with mozzarella in a baking dish.", "Bake until bubbling and lightly golden."]),
    recipe("Minestrone Soup", "Italian", ["beans", "pasta", "tomato", "carrot", "celery", "onion", "garlic"], ["vegan", "dairy-free", "high-protein"], ["Saute onion, carrot, celery, and garlic.", "Add tomato and broth, then simmer.", "Stir in beans and pasta.", "Cook until the pasta is tender and serve hot."]),
    recipe("Creamy Spinach Penne", "Italian", ["pasta", "spinach", "cream", "garlic", "onion", "parmesan"], ["vegetarian"], ["Boil the penne until al dente.", "Cook onion and garlic until soft.", "Add cream, spinach, and parmesan to form a sauce.", "Fold in the pasta and season to taste."]),

    recipe("Vegetable Fried Rice", "Chinese", ["rice", "carrot", "peas", "spring onion", "soy sauce", "ginger", "garlic"], ["vegetarian", "dairy-free", "nut-free"], ["Use chilled cooked rice for best texture.", "Stir-fry garlic, ginger, and vegetables over high heat.", "Add the rice and toss vigorously.", "Season with soy sauce and spring onion."]),
    recipe("Ginger Garlic Tofu Stir Fry", "Chinese", ["tofu", "bell pepper", "broccoli", "soy sauce", "ginger", "garlic", "sesame oil"], ["vegan", "dairy-free", "high-protein"], ["Pan-sear the tofu until lightly crisp.", "Stir-fry ginger, garlic, broccoli, and bell pepper.", "Return tofu to the pan with soy sauce and sesame oil.", "Cook briefly until glossy and serve."]),
    recipe("Sesame Noodles", "Chinese", ["noodles", "soy sauce", "garlic", "ginger", "spring onion", "sesame oil"], ["vegan", "dairy-free"], ["Cook the noodles and rinse lightly.", "Mix soy sauce, sesame oil, garlic, and ginger into a dressing.", "Toss noodles with the dressing and spring onion.", "Serve warm or chilled."]),
    recipe("Chili Paneer", "Chinese", ["paneer", "bell pepper", "onion", "soy sauce", "garlic", "ginger", "chili"], ["vegetarian", "high-protein"], ["Sear the paneer cubes until golden.", "Cook onion, bell pepper, garlic, and ginger on high heat.", "Add soy sauce and chili for the glaze.", "Toss paneer back in and coat well."]),
    recipe("Bok Choy Mushroom Stir Fry", "Chinese", ["bok choy", "mushroom", "garlic", "ginger", "soy sauce", "sesame oil"], ["vegan", "gluten-free", "dairy-free"], ["Heat oil in a wok or skillet.", "Add garlic and ginger followed by mushrooms.", "Stir in bok choy and cook until just wilted.", "Season with soy sauce or tamari and finish with sesame oil."]),
    recipe("Veg Hakka Noodles", "Chinese", ["noodles", "cabbage", "carrot", "bell pepper", "soy sauce", "ginger", "garlic"], ["vegan", "dairy-free"], ["Boil noodles and toss with a little oil.", "Stir-fry garlic, ginger, and sliced vegetables.", "Add noodles and soy sauce.", "Toss on high heat until smoky and well mixed."]),

    recipe("Greek Quinoa Salad", "Mediterranean", ["quinoa", "cucumber", "tomato", "olive", "feta", "lemon", "olive oil"], ["vegetarian", "gluten-free", "nut-free"], ["Cook quinoa and cool slightly.", "Chop cucumber, tomato, and olives.", "Whisk lemon juice with olive oil.", "Combine everything with feta and toss gently."]),
    recipe("Chickpea Cucumber Bowl", "Mediterranean", ["chickpeas", "cucumber", "tomato", "olive oil", "lemon", "parsley"], ["vegan", "gluten-free", "high-protein", "dairy-free"], ["Rinse the chickpeas and drain well.", "Dice cucumber and tomato.", "Toss with olive oil, lemon, and parsley.", "Serve chilled or at room temperature."]),
    recipe("Roasted Vegetable Couscous", "Mediterranean", ["couscous", "bell pepper", "zucchini", "tomato", "olive oil", "garlic"], ["vegan", "dairy-free", "nut-free"], ["Roast the vegetables with olive oil and garlic.", "Steam couscous with hot broth or water.", "Fold roasted vegetables into the couscous.", "Finish with lemon and herbs."]),
    recipe("Hummus Pita Wrap", "Mediterranean", ["hummus", "pita", "cucumber", "tomato", "lettuce", "olive oil"], ["vegan", "dairy-free", "nut-free"], ["Warm the pita briefly.", "Spread hummus over the pita.", "Layer cucumber, tomato, and lettuce.", "Roll tightly and serve."]),
    recipe("Feta Olive Pasta Salad", "Mediterranean", ["pasta", "feta", "olive", "cucumber", "tomato", "olive oil", "oregano"], ["vegetarian", "nut-free"], ["Cook the pasta and cool it slightly.", "Chop the vegetables and olives.", "Whisk olive oil with oregano.", "Combine everything with feta and chill before serving."]),
    recipe("Lemon Herb Lentil Soup", "Mediterranean", ["lentils", "carrot", "celery", "onion", "garlic", "lemon", "olive oil"], ["vegan", "gluten-free", "high-protein", "dairy-free"], ["Saute onion, celery, carrot, and garlic.", "Add lentils with water or broth.", "Simmer until the lentils are tender.", "Finish with lemon juice and herbs."]),

    recipe("Black Bean Tacos", "Mexican", ["beans", "tortilla", "avocado", "tomato", "onion", "cumin", "lime"], ["vegan", "dairy-free", "high-protein"], ["Warm the tortillas.", "Cook beans with onion, tomato, and cumin.", "Slice avocado and prepare the lime garnish.", "Fill tortillas and serve immediately."]),
    recipe("Veggie Quesadilla", "Mexican", ["tortilla", "cheese", "bell pepper", "onion", "tomato", "beans"], ["vegetarian", "high-protein"], ["Saute the bell pepper and onion.", "Spread filling and cheese over a tortilla.", "Top with another tortilla and toast both sides.", "Cut into wedges and serve."]),
    recipe("Burrito Bowl", "Mexican", ["rice", "beans", "avocado", "corn", "tomato", "onion", "lime"], ["vegan", "gluten-free", "high-protein", "dairy-free"], ["Cook the rice and warm the beans.", "Dice tomato, onion, and avocado.", "Layer rice, beans, and vegetables into bowls.", "Finish with lime and seasoning."]),
    recipe("Mexican Rice Skillet", "Mexican", ["rice", "tomato", "beans", "corn", "onion", "bell pepper", "cumin"], ["vegan", "gluten-free", "high-protein", "dairy-free"], ["Saute onion and bell pepper.", "Add rice, tomato, cumin, and water or broth.", "Stir in beans and corn near the end.", "Cook until the rice is tender and fluffy."]),
    recipe("Avocado Bean Salad", "Mexican", ["avocado", "beans", "tomato", "onion", "lime", "cilantro"], ["vegan", "gluten-free", "high-protein", "dairy-free"], ["Rinse and drain the beans.", "Dice avocado, tomato, and onion.", "Toss with lime juice and cilantro.", "Serve immediately while fresh."]),
    recipe("Salsa Pasta", "Mexican", ["pasta", "tomato", "corn", "beans", "jalapeno", "onion", "cheese"], ["vegetarian", "high-protein"], ["Cook the pasta until tender.", "Saute onion and jalapeno lightly.", "Stir in tomato, corn, and beans to create a quick salsa sauce.", "Toss with pasta and finish with cheese."]),

    recipe("Herb Roasted Vegetables", "Continental", ["potato", "carrot", "broccoli", "olive oil", "garlic", "oregano"], ["vegan", "gluten-free", "dairy-free", "nut-free"], ["Cut the vegetables into even pieces.", "Toss with olive oil, garlic, and oregano.", "Roast until browned and tender.", "Serve as a side or light main."]),
    recipe("Creamy Mushroom Toast", "Continental", ["bread", "mushroom", "cream", "garlic", "butter", "parsley"], ["vegetarian", "nut-free"], ["Toast the bread slices.", "Saute mushroom and garlic in butter.", "Add cream and reduce slightly.", "Spoon over toast and garnish with parsley."]),
    recipe("Tomato Basil Soup", "Continental", ["tomato", "onion", "garlic", "basil", "olive oil", "cream"], ["vegetarian", "gluten-free", "nut-free"], ["Cook onion and garlic in olive oil.", "Add tomato and simmer until soft.", "Blend until smooth and return to the pot.", "Finish with basil and a splash of cream."]),
    recipe("Baked Potato Gratin", "Continental", ["potato", "cream", "cheese", "garlic", "onion", "butter"], ["vegetarian", "gluten-free"], ["Slice the potatoes thinly.", "Layer with onion, garlic, cream, and cheese.", "Bake until the potatoes are tender.", "Rest briefly before serving."]),
    recipe("Cheese Omelette", "Continental", ["egg", "cheese", "onion", "bell pepper", "butter"], ["vegetarian", "gluten-free", "high-protein"], ["Beat the eggs with seasoning.", "Cook onion and bell pepper briefly in butter.", "Pour in the eggs and add cheese.", "Fold when set and serve immediately."]),
    recipe("Garlic Butter Rice", "Continental", ["rice", "butter", "garlic", "parsley", "onion"], ["vegetarian", "gluten-free", "nut-free"], ["Cook the rice until fluffy.", "Saute garlic and onion in butter.", "Fold the rice into the pan.", "Finish with parsley and serve warm."]),

    recipe("Tofu Teriyaki Bowl", "Japanese", ["tofu", "rice", "soy sauce", "ginger", "garlic", "sesame", "broccoli"], ["vegan", "dairy-free", "high-protein"], ["Sear tofu until lightly crisp.", "Mix soy sauce with ginger and garlic to form a teriyaki-style glaze.", "Cook broccoli until tender-crisp.", "Serve everything over rice with sesame."]),
    recipe("Miso Vegetable Soup", "Japanese", ["miso", "tofu", "mushroom", "spring onion", "carrot", "spinach"], ["vegan", "dairy-free", "gluten-free"], ["Simmer carrot and mushroom in water or broth.", "Add tofu and cook briefly.", "Stir in miso off the heat so it stays mellow.", "Finish with spinach and spring onion."]),
    recipe("Kimchi Fried Rice", "Korean", ["rice", "kimchi", "spring onion", "garlic", "egg", "sesame oil"], ["vegetarian", "high-protein"], ["Saute kimchi, garlic, and spring onion.", "Add cold rice and stir-fry well.", "Season with a little sesame oil.", "Top with a fried egg if desired."]),
    recipe("Bibimbap Bowl", "Korean", ["rice", "spinach", "carrot", "mushroom", "egg", "gochujang", "sesame"], ["vegetarian", "high-protein", "gluten-free"], ["Cook rice and prepare the vegetables separately.", "Saute spinach, carrot, and mushroom lightly.", "Fry or soft-poach the egg.", "Assemble the bowl and serve with gochujang."]),
    recipe("Ramen Stir Fry", "Japanese", ["ramen", "mushroom", "carrot", "soy sauce", "ginger", "garlic", "spring onion"], ["vegan", "dairy-free"], ["Boil ramen just until loosened and drain.", "Stir-fry vegetables with garlic and ginger.", "Add noodles and soy sauce.", "Toss until coated and garnish with spring onion."]),
    recipe("Quinoa Power Bowl", "Other", ["quinoa", "avocado", "chickpeas", "spinach", "tomato", "olive oil", "lemon"], ["vegan", "gluten-free", "high-protein", "dairy-free"], ["Cook quinoa until fluffy.", "Roast or warm the chickpeas.", "Arrange spinach, tomato, avocado, and quinoa in a bowl.", "Dress with olive oil and lemon before serving."]),
]


def normalize_name(value: str) -> str:
    return str(value).strip().lower().replace(" ", "_")


def processed_ingredients(recipe_record: dict) -> str:
    return " ".join(normalize_name(ingredient) for ingredient in recipe_record["ingredients"])


def load_external_dataset(path: str | None) -> list[dict]:
    if not path:
        return []

    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    with dataset_path.open("r", encoding="utf-8") as handle:
        records = json.load(handle)

    cleaned = []
    for record in records:
        if not isinstance(record, dict):
            continue
        title = str(record.get("title", "")).strip()
        cuisine = str(record.get("cuisine", "Other")).strip() or "Other"
        ingredients = [str(item).strip().lower() for item in record.get("ingredients", []) if str(item).strip()]
        steps = [str(item).strip() for item in record.get("steps", []) if str(item).strip()]
        tags = [str(item).strip().lower() for item in record.get("tags", []) if str(item).strip()]
        if title and len(ingredients) >= 2 and steps:
            cleaned.append(recipe(title, cuisine, ingredients, tags, steps))
    return cleaned


def dedupe_records(records: Iterable[dict]) -> list[dict]:
    unique = {}
    for record in records:
        key = (record["title"].strip().lower(), tuple(sorted(record["ingredients"])))
        unique[key] = record
    return list(unique.values())


def train(records: list[dict], output_path: Path) -> None:
    vectorizer = TfidfVectorizer(max_features=10000, ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform([processed_ingredients(record) for record in records])

    artifacts = {
        "vectorizer": vectorizer,
        "tfidf_matrix": tfidf_matrix,
        "records": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifacts, output_path)

    print(f"Trained recipe model with {len(records)} recipes")
    print(f"Saved artifact to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", help="Optional cleaned recipe JSON to merge into the seed corpus")
    parser.add_argument("--output", help="Output path for recipe_model.joblib")
    args = parser.parse_args()

    output_path = Path(args.output or Path(__file__).with_name("recipe_model.joblib"))
    records = dedupe_records([*SEED_RECIPES, *load_external_dataset(args.dataset)])
    train(records, output_path)


if __name__ == "__main__":
    main()
