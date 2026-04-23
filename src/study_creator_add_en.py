import typing as tp

from pymongo import MongoClient

from study_template import StudyTemplate, LevelType, Level, Question, LikertQuestion, BinaryQuestion

# Connect with database
database_url = "localhost:27017"
client = MongoClient(database_url)
db = client["user_study_test"]

# Create database
questions_col_en = db["questions_en"]
gt_questions_col_en = db["gt_questions_en"]
xp_meta_col_en = db["xp_meta_en"] # metadata like template's n_models and n_experiments

def register_study(t:StudyTemplate):
    # Register questions
    for idx, question in enumerate(t.questions):
        quesntion_dict = {
            '_id': idx,
            'header': question.header,
            'options': question.options,
            'len': len(question),
            'replace': question.replace
        }

        questions_col_en.insert_one(quesntion_dict)

    print(f"Registered {idx+1} questions.\n\tThe last one is {quesntion_dict}\n")

    for idx, question in enumerate(t.gt_questions):
        quesntion_dict = {
            '_id': idx,
            'header': question.header,
            'options': question.options,
            'len': len(question),
            'replace': question.replace
        }

        gt_questions_col_en.insert_one(quesntion_dict)

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
    xp_meta_col_en.insert_one(xp_meta_dict)

def main():
    questions:tp.List[Question] = [
        # Inspired by GVMGen -> Equivalent to ImageBind
        LikertQuestion(
            header="How much does this generated background music fit this video game scene?",
            options=["Very poorly", "Poorly", "Reasonably", "Well", "Very well"]
        ),
        # Inspired by OSSL -> Equivalent to Genre Classifier
        LikertQuestion(
            header="How much does this generated background music fit the (PICK_ONE_KEY_NAME) genre of this game?", # In our case the pick_one key name is the game genre
            options=["Very poorly", "Poorly", "Reasonably", "Well", "Very well"],
            replace="PICK_ONE_KEY_NAME"
        ),
        # Got from GVMGen -> Equivalent to FAD
        LikertQuestion(
            header="How good is the audio quality of this generated background music?",
            options=["Very poor", "Poor", "Reasonable", "Good", "Very good"]
        ),
        # Got from GVMGen -> Equivalent to KLD
        LikertQuestion(
            header="How much does this music sound like a professional video game composition?",
            options=["Not professional<br>(confusing/random)", "Slightly professional", "Reasonable", "Professional", "Very professional<br>(sounds like classic soundtracks)"]
        ),
        LikertQuestion(
            header="Does this generated background music sound like a Super Nintendo (SNES) video game music?",
            options=["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"]
        )
    ]

    gt_questions:tp.List[Question] = [
        BinaryQuestion(
            header="Do you know this game?",
            options=["Yes", "No"]
        ),
        LikertQuestion(
            header="Have you played this game before?",
            options=["Never played", "Played a few times", "Played many times"]
        ),
        BinaryQuestion(
            header="Do you know the original background music you just heard?",
            options=["Yes", "No"]
        )
    ]

    koji_gen = StudyTemplate(
        name="Evaluating Music Generation Models for Video Games",
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
        exclude = [
            'kamaitachi-no-yoru_00845_gen.mp4',
            'zenkoku-koukou-soccer-senshuken-96_00325_gen.mp4',
            'dig-spike-volleyball_02097_gen.mp4',
            'hat-trick-hero-2_00523_gen.mp4',
            'populous-ii-trials-of-the-olympian-gods_01301_gen.mp4'
        ],
        questions = questions,
        gt_questions = gt_questions
    )

    register_study(koji_gen)

if __name__ == "__main__":
    main()
