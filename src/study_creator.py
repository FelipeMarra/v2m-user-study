from itertools import combinations

from pymongo import MongoClient

from study_template import StudyTemplate, LevelType, Level

# Connect with database
database_url = "localhost:27017"
database = MongoClient(database_url)

# Create database
pick_one_col = database["user_study_test"]["control_pick_one"]
models_comb_col = database["user_study_test"]["control_models_combinations"]

def register_study(t:StudyTemplate):
    # Register the pick_one_dict with the pick_one_keys, the list of contents inside each key
    # and a corresponding list to keep track of the amount of times that each content was visited
    for idx, row in enumerate(t._pick_one_dict.items()):
        key, values = row

        pick_one_dict = {
            '_id': idx,
            'name': key,
            'contents': [str(content) for content in values],
            'visits': [0 for _ in values]
        }

        pick_one_col.insert_one(pick_one_dict)

    print(f"Registered {idx+1} pick_one rows.\n\tThe last one is {pick_one_dict}\n")

    # Register model_combintaions with idx, number of times it was visited and the list of models in the combination
    model_combintaions = combinations(t.models, t.models_comb)

    for idx, models in enumerate(model_combintaions):
        models_comb_dict = {
            '_id': idx,
            'visits': 0,
            'names': [model.name for model in models],
            'paths': [str(model.path.relative_to(t.src_dir)) for model in models]
        }

        models_comb_col.insert_one(models_comb_dict)

    print(f"Registered {idx+1} model combinations.\n\tThe last one is {models_comb_dict}\n")

def main():
    koji_gen = StudyTemplate(
        name="KojiGen",
        models_comb=3,
        ends_with="_gen.mp4",
        levels = [
            Level("Model", LevelType.MODEL),
            Level("Inference", LevelType.FOLDER, force_folder="inference"),
            Level("Game Genre", LevelType.PICK_ONE)
        ]
    )

    register_study(koji_gen)

if __name__ == "__main__":
    main()
