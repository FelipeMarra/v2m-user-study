from itertools import combinations

from pymongo import MongoClient

from study_template import StudyTemplate, LevelType, Level, LikertQuestion

# Connect with database
database_url = "localhost:27017"
database = MongoClient(database_url)

# Create database
pick_one_col = database["user_study_test"]["control_pick_one"]
models_comb_col = database["user_study_test"]["control_models_combinations"]
questions_col = database["user_study_test"]["questions"]

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

    # Register questions
    for idx, question in enumerate(t.questions):
        quesntion_dict = {
            '_id': idx,
            'header': question.header,
            'options': question.options
        }

        questions_col.insert_one(quesntion_dict)

    print(f"Registered {idx+1} questions.\n\tThe last one is {quesntion_dict}\n")

def main():
    questions_headers = [
        # TODO This music sounds as a retro videogame piece - e.g., SNES
        # TODO How much this piece sounds as a retro videogame music - e.g., SNES
        # Strongly Disagree ---- Strongly Agree

        # Got from GVMGen -> Equivalent to ImageBind
        "What is the overall (semantic, emotional and rhythmic) correspondence between this soundtrack and the video?",
        # Inspired by OSSL -> Equivalent to Genre Classifier
        "What is the overall correspondence between this soundtrack and the genre of the game in the video?",
        # Got from GVMGen -> Equivalent to FAD
        "What is the overall audio quality of this piece?",
        # Got from GVMGen -> Equivalent to KLD
        "What is the overall musical quality (rhythm, harmony, melody, form, etc) of this piece?"
    ]

    koji_gen = StudyTemplate(
        name="Evaluating Generative Music for Videogames",
        models_comb=3, # Fazer cada modelo separado. Permutar modelos. Pegar uma música aleatória pra cada modelo. Precisa que cada modelo tenha X avaliações e não cada música. Atribuir músicas diferentes é mais pra eliminar o viés da música
                       # Fazer original, shufle no modelo -> original, shufle no modelo
                       # Fixar 2 | 1 original + 3 modelos | original 2 + 3 modelos | demográfico
                       # 
                       # Title: Evaluating generative music for videogames
        ends_with="_gen.mp4",
        levels = [
            Level("Model", LevelType.MODEL),
            Level("Inference", LevelType.FOLDER, force_folder="inference"),
            Level("Game Genre", LevelType.PICK_ONE)
        ],
        questions = [
            LikertQuestion(
                header=question_header,
                options=["Very Poor", "Poor", "Neutral", "Good", "Very Good"]
            )
            for question_header in questions_headers
        ]
    )

    register_study(koji_gen)

if __name__ == "__main__":
    main()
