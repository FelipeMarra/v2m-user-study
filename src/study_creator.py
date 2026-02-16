import random

from pymongo import MongoClient

from study_template import StudyTemplate, LevelType, Level

# Connect with database
database_url = "localhost:27017"
database = MongoClient(database_url)

# Create database
experiments_col = database["user_study_test"]["experiments"]

def retrieve_study(t:StudyTemplate, seed:int):
    study = {}
    for model in t.models:
        print(model.path)

        study[model.name] = {
            '_id': f'{model.name}_{seed}',
            'pieces': [str(content) for content in model.contents]
        }

    return study

def main():
    seed = 42
    random.seed(42)

    kojiGen = StudyTemplate(
        name="KojiGen",
        ends_with="_gen.mp4",
        levels = [
            Level("Model", LevelType.MODEL),
            Level("Inference", LevelType.FOLDER, force_folder="inference"),
            Level("Game Genre", LevelType.PICK_ONE)
        ]
    )

    study = retrieve_study(kojiGen, seed)

    for experiment in study:
        experiments_col.insert_one(study[experiment])

if __name__ == "__main__":
    main()
