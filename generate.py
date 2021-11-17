from jsonschema import validate
from json import load as load_json_io
from glob import glob
from yaml import load as load_yaml_io, Loader, Dumper, dump as dump_yaml
from yaml.error import YAMLError
import os
import errno

Shot = dict
ShotWithPath = tuple[str, Shot]


def load_json(path: str) -> dict:
    """
    Loads a JSON file from it's path.

    :param path: The path of the file
    :return: a dictionary representing the JSON
    """
    with open(path, "r") as json_io:
        return load_json_io(json_io)


def load_yaml(path: str) -> dict:
    """
    Loads a YAML file from it's path.

    :param path: The path of the file
    :return: a dictionary representing the YAML
    """
    with open(path, "r") as yaml_io:
        return load_yaml_io(yaml_io, Loader=Loader)


def load_shot_schema() -> dict:
    """
    Loads the JSON-Schema to validate shots definitions.

    :return: a dictionary representing the JSON-Schema
    """
    return load_json("validation/shot.schema.json")


def get_shots_from_files() -> list[ShotWithPath]:
    """
    Loads all shots from the `shots/` directory.

    :return: an array of dictionaries
    """
    shots = []
    for path in glob('shots/*.yml'):
        shot_json = load_yaml(path)
        shots.append((path, shot_json))
    return shots


def find_duplicates(elements_list: list) -> list[tuple[int, int]] or None:
    """
    Finds duplicated elements in the given list.

    :param elements_list: The list of elements
    :return: A list containing tuples of the ids of duplicated elements if found, else None
    """
    duplicates = []
    for left in range(len(elements_list)):
        for right in range(left + 1, len(elements_list)):
            if elements_list[left] == elements_list[right]:
                duplicates.append((left, right))

    return duplicates if len(duplicates) > 0 else None


def find_duplicates_on_ids(shots: list[ShotWithPath]) -> list[tuple[ShotWithPath, ShotWithPath]] or None:
    """
    Find collisions in shots' ids.

    :param shots: The shots' definitions
    :return: Tuples of duplicated shots
    """
    duplicated = find_duplicates([shot["id"] for _, shot in shots])
    if duplicated is None:
        return None
    return [(shots[right], shots[left]) for left, right in duplicated]


def find_duplicates_on_names(shots: list[ShotWithPath]) -> list[tuple[ShotWithPath, ShotWithPath]] or None:
    """
    Find collisions in shots' names.

    :param shots: The shots' definitions
    :return: Tuples
    """
    duplicated = find_duplicates([shot["name"] for _, shot in shots])
    if duplicated is None:
        return None
    return [(shots[right], shots[left]) for left, right in duplicated]


def generate_batched_shots_definition(shots: list[Shot]):
    """
    Transforms the given given list of shots definition to
    a dict containing all definitions indexed by their id.

    :param shots: The shots' definitions
    :return: The generated dict with id indexed shots
    """
    def remove_id(shot: Shot) -> dict:
        del shot["id"]
        return shot

    definition = {
        "drinks": {shot["id"]: remove_id(shot.copy()) for shot in shots}
    }

    return definition


def write_yaml(path: str, data: dict) -> None:
    """
    Writes the given dict into a YAML file to the file
    at the given path.

    :param path: The path to write the YAML file to
    :param data: The data to put in the YAML file
    """
    if not os.path.exists(os.path.dirname(path)):
        try:
            os.makedirs(os.path.dirname(path))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise

    with open(path, "w") as file:
        dump_yaml(data, file, Dumper=Dumper)


def main():
    """
    Loads the shots definitions and validate
    them against the shot's JSON-schema .
    :return:
    """
    schema = load_shot_schema()
    shots = get_shots_from_files()
    for path, shot in shots:
        try:
            validate(schema=schema, instance=shot)
        except YAMLError as error:
            print(f"[ERREUR] Erreur de format dans le fichier {path}.")
            print(error)

    names_duplicates = find_duplicates_on_names(shots)
    if names_duplicates is not None:
        for left, right in names_duplicates:
            file1, shot = left
            file2, _ = right
            print(f"[ATTENTION] Nom dupliqué dans les fichiers {file1} et {file2} ({shot['name']}).")

    ids_duplicates = find_duplicates_on_ids(shots)
    if ids_duplicates is not None:
        for left, right in ids_duplicates:
            file1, shot = left
            file2, _ = right
            print(f"[ERREUR] Identifiants dupliqués dans les fichiers {file1} et {file2} ({shot['id']}).")
        raise ValueError("Duplicated ids")

    batched_data = generate_batched_shots_definition([shot for _, shot in shots])
    write_yaml("output/shots.yml", batched_data)


if __name__ == '__main__':
    main()
