import typing as tp

from pymongo import MongoClient

from study_template import StudyTemplate, LevelType, Level, Question, LikertQuestion, BinaryQuestion

# Connect with database
database_url = "localhost:27017"
client = MongoClient(database_url)
db = client["user_study_test"]

# Create database
pick_one_col = db["pick_one"]
models_col = db["models"]
questions_col = db["questions"]
gt_questions_col = db["gt_questions"]
xp_meta_col = db["xp_meta"] # metadata like template's n_models and n_experiments

def register_study(t:StudyTemplate):
    # Register the pick_one_dict with the pick_one_keys, the list of contents inside each key
    # and a corresponding list to keep track of the amount of times that each content was visited
    for idx, row in enumerate(t._pick_one_dict.items()):
        key, values = row

        pick_one_dict = {
            '_id': idx,
            'name': key,
            'visits': 0,
            'contents': [str(content) for content in values],
            'contents_visits': [0 for _ in values]
        }

        pick_one_col.insert_one(pick_one_dict)

    print(f"Registered {idx+1} pick_one rows.\n\tThe last one is {pick_one_dict}\n")

    # Register model with idx, number of times it was visited
    for idx, model in enumerate(t.models):
        models_dict = {
            '_id': idx,
            'visits': 0,
            'name': model.name,
            'ends_with': model.ends_with,
            'path': str(model.path.relative_to(t.src_dir))
        }

        models_col.insert_one(models_dict)

    print(f"Registered {idx+1} models.\n\tThe last one is {models_dict}\n")

    # Register questions
    for idx, question in enumerate(t.questions):
        quesntion_dict = {
            '_id': idx,
            'header': question.header,
            'options': question.options,
            'len': len(question),
            'replace': question.replace
        }

        questions_col.insert_one(quesntion_dict)

    print(f"Registered {idx+1} questions.\n\tThe last one is {quesntion_dict}\n")

    for idx, question in enumerate(t.gt_questions):
        quesntion_dict = {
            '_id': idx,
            'header': question.header,
            'options': question.options,
            'len': len(question),
            'replace': question.replace
        }

        gt_questions_col.insert_one(quesntion_dict)

    print(f"Registered {idx+1} questions.\n\tThe last one is {quesntion_dict}\n")

    # Register experiments metadata
    xp_meta_dict = {
        '_id': 0,
        'name': t.name,
        'n_experiments': t.n_experiments,
        'n_models': t.n_models,
        'gt': t.gt,
        'gt_ends_with': t.gt_ends_with,
        'gen_ends_with': t.gen_ends_with
    }
    xp_meta_col.insert_one(xp_meta_dict)

    print(f"Registered meta\n\tThe last one is {xp_meta_dict}\n")

def main():
    questions:tp.List[Question] = [
        # Inspired by GVMGen -> Equivalent to ImageBind
        LikertQuestion(
            header="How much this generated background music fits this video game scene?",
            options=["Very Poorly", "Poorly", "Neutral", "Well", "Very Well"]
        ),
        # Inspired by OSSL -> Equivalent to Genre Classifier
        LikertQuestion(
            header="How much this generated background music fits the PICK_ONE_KEY_NAME of this game?", # In our case the pick_one key name is the game genre
            options=["Very Poorly", "Poorly", "Neutral", "Well", "Very Well"],
            replace="PICK_ONE_KEY_NAME"
        ),
        # Got from GVMGen -> Equivalent to FAD
        LikertQuestion(
            header="What is the overall audio quality of this generated background music?",
            options=["Very Poor", "Poor", "Neutral", "Good", "Very Good"]
        ),
        # Got from GVMGen -> Equivalent to KLD
        LikertQuestion(
            header="What is the overall musical quality (rhythm, harmony, melody, form, etc) of this generated background music?",
            options=["Very Poor", "Poor", "Neutral", "Good", "Very Good"]
        ),
        LikertQuestion(
            header="Does this generated background music sound as a SNES video game music?",
            options=["Strongly Disagree", "Disagree", "Neutal", "Agree", "Strongly Agree"]
        )
    ]

    gt_questions:tp.List[Question] = [
        BinaryQuestion(
            header="Do you know this game?",
            options=["Yes", "No"]
        ),
        LikertQuestion(
            header="Have you played this game before?",
            options=["Never Played", "Played a Few Times", "It's one of My Favorite Games"]
        ),
        BinaryQuestion(
            header="Do you know the original background music you just listened?",
            options=["Yes", "No"]
        )
    ]

    koji_gen = StudyTemplate(
        name="Evaluating Generative Music for Videogames",
        n_experiments=2,
        n_models=3,
        gt="Ground_Truth",
        gt_ends_with=".mp4",
        gen_ends_with="_gen.mp4",
        levels = [
            Level("Model", LevelType.MODEL),
            Level("Inference", LevelType.FOLDER, force_folder="inference"),
            Level("Game Genre", LevelType.PICK_ONE)
        ],
        questions = questions,
        gt_questions = gt_questions
    )

    register_study(koji_gen)

if __name__ == "__main__":
    main()
