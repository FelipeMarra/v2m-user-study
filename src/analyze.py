import pandas as pd
from pymongo import MongoClient

# Connect with database
database_url = "localhost:27017"
client = MongoClient(database_url)
db = client["user_study_test"]

models_col = db["models"]
questions_col = db["questions"]
gt_questions_col = db["gt_questions"]
xp_meta_col = db["xp_meta"]
results_col = db["results"]

def get_gen_questions() -> dict[int, str]:
    gen_qustions:dict[int, str] = {}
    for question in questions_col.find({}):
        gen_qustions[int(question['_id'])] = question['header']

    return gen_qustions

def get_model(model_id:int):
    model = models_col.find_one({'_id': model_id})

    return model

def get_answers_per_model() -> dict[str, dict[int, list[int]]]:
    results = results_col.find({})

    id_and_profile = ['_id', 'year', 'xp', 'gender', 'comments', 'play_freq', 'snes_familiarity']
    non_question = ['model_key', 'pick_one_key', 'content_key']

    # {
    #     model_name: {
    #         question_idx: [question_value_1, question_value_2...]
    #     }
    # }
    models_dict:dict[str, dict[int, list[int]]] = {} 

    for result in results:
        # for each result we have 2 experiments -> 2x(1 gt question, 3 gen questions)
        for key, model_result in result.items():
            if key in id_and_profile:
                continue

            model_result_idx = int(key.split('_')[0])
            model_result_xp_idx = model_result_idx % 4 # idx relative to the current experiments 

            # skip gt question for now
            if model_result_xp_idx == 0:
                continue

            model = get_model(model_result['model_key'])
            model_name = model['name'] # type: ignore
            print(f"+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")
            print(f"q_idx: {model_result_idx} | model_result: {model_result} | model: {model_name}\n")

            for quest_key, quest in model_result.items():
                if quest_key in non_question:
                    continue

                quest_idx = int(quest_key.split('_q')[-1])
                quest_value = int(quest) +1

                print(f"quest_idx {quest_idx} | quest {quest_idx} | quest_value {quest_value}")

                if not models_dict.get(model_name):
                    models_dict[model_name] = {}

                if models_dict[model_name].get(quest_idx):
                    models_dict[model_name][quest_idx].append(quest_value)
                else:
                    models_dict[model_name][quest_idx] = [quest_value]

    return models_dict

def get_answers_means(models_dict:dict[str, dict[int, list[int]]]) -> dict[str, dict[int, float]]:
    mean_models_dict:dict[str, dict[int, float]] = {}

    for model_name, question_dict in models_dict.items():
        for quest_idx, values in question_dict.items():
            values_mean = sum(values)/len(values)

            if not mean_models_dict.get(model_name):
                mean_models_dict[model_name] = {}

            mean_models_dict[model_name][quest_idx] = values_mean

    return mean_models_dict

def main():
    gen_qustions = get_gen_questions()
    print(f"gen_qustions:\n{gen_qustions}\n")

    models_dict = get_answers_per_model()
    print(f'models_dict: {models_dict}\n')

    mean_models_dict = get_answers_means(models_dict)
    print(f'mean_models_dict: {mean_models_dict}\n')

    mean_models_df = pd.DataFrame(mean_models_dict)
    print(f'mean_models_df:\n{mean_models_df}\n')

if __name__ == "__main__":
    main()