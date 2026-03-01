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
            header="O quanto essa música de fundo gerada se encaixa nessa cena de videogame?",
            options=["Muito mal", "Mal", "Razoávelmente", "Bem", "Muito bem"]
        ),
        # Inspired by OSSL -> Equivalent to Genre Classifier
        LikertQuestion(
            header="O quanto essa música de fundo gerada se encaixa no gênero (PICK_ONE_KEY_NAME) deste jogo?", # In our case the pick_one key name is the game genre
            options=["Muito mal", "Mal", "Razoávelmente", "Bem", "Muito bem"],
            replace="PICK_ONE_KEY_NAME"
        ),
        # Got from GVMGen -> Equivalent to FAD
        LikertQuestion(
            header="Qual a qualidade do áudio dessa música de fundo gerada?",
            options=["Muito ruim", "Ruim", "Razoável", "Boa", "Muito boa"]
        ),
        # Got from GVMGen -> Equivalent to KLD
        LikertQuestion(
            header="O quanto esta música soa como uma composição profissional de videogame?",
            options=["Nada profissional<br>(confusa/aleatória)", "Pouco profissional", "Razoável", "Profissional", "Muito profissional<br>(soa como trilhas clássicas)"]
        ),
        LikertQuestion(
            header="Essa música de fundo gerada soa como música de videogame do Super Nintendo (SNES)?",
            options=["Discordo totalmente", "Discordo", "Neutro", "Concordo", "Concordo totalmente"]
        )
    ]

    gt_questions:tp.List[Question] = [
        BinaryQuestion(
            header="Você conhece esse jogo?",
            options=["Sim", "Não"]
        ),
        LikertQuestion(
            header="Você já jogou esse jogo antes?",
            options=["Nunca joguei", "Joguei algumas vezes", "Joguei várias vezes"]
        ),
        BinaryQuestion(
            header="Você conhece a música de fundo original que acabou de ouvir?",
            options=["Sim", "Não"]
        )
    ]

    koji_gen = StudyTemplate(
        name="Avaliando Modelos de Geração de Música para Videogames",
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
