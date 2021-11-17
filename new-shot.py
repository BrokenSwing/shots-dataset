import click
from uuid import uuid4
from slugify import slugify
from yaml import dump, Dumper


@click.command()
@click.option("--name", prompt="Nom du shot", help="Nom du shot")
def create_shot(name: str):
    ingredients = []
    new_ingredient = None

    click.echo("Entrez la liste des ingrédients (ne rien rentrer pour terminer):")

    while new_ingredient != "":
        if new_ingredient is not None:
            ingredients.append(new_ingredient)
        new_ingredient = click.prompt(f"Ingredient {len(ingredients) + 1}", type=str, default="").strip()

    shot = {
        "id": uuid4().hex,
        "name": name.strip(),
        "ingredients": ingredients
    }

    with open(f"shots/{slugify(name.strip())}.yml", "w") as shot_io:
        dump(shot, shot_io, Dumper=Dumper)


if __name__ == "__main__":
    create_shot()

