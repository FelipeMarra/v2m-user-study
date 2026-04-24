import os
import json

import pandas as pd
import numpy as np

# Load data from json
RESULTS_PATH = "./results"

def read_jsonl(file_path) -> dict:
    parent_dict = {}

    with open(file_path, 'r') as f: 
        for line in f.readlines():
            line_dict:dict = json.loads(line)

            if isinstance(line_dict["_id"], dict):
                key = line_dict["_id"]["$oid"]
            else:
                key = line_dict["_id"]

            parent_dict[key] = line_dict

    return parent_dict

answers:dict = read_jsonl(f"{RESULTS_PATH}/answers.jsonl")
questions:dict = read_jsonl(f"{RESULTS_PATH}/questions.jsonl")
models:dict = read_jsonl(f"{RESULTS_PATH}/models.jsonl")
pick_one:dict = read_jsonl(f"{RESULTS_PATH}/pick_one.jsonl")
gt_questions:dict = read_jsonl(f"{RESULTS_PATH}/gt_questions.jsonl")
results:dict = read_jsonl(f"{RESULTS_PATH}/results.jsonl")
xp_meta:dict = read_jsonl(f"{RESULTS_PATH}/xp_meta.jsonl")

def get_gen_questions() -> dict[int, str]:
    gen_qustions:dict[int, str] = {}
    for question in questions.values():
        gen_qustions[int(question['_id'])] = question['header']

    return gen_qustions

def get_model(model_id:int):
    model = models[model_id]

    return model

def get_answers_per_model() -> dict[str, dict[int, list[int]]]:
    id_and_profile = ['_id', 'year', 'xp', 'gender', 'comments', 'play_freq', 'snes_familiarity']
    non_question = ['model_key', 'pick_one_key', 'content_key']

    # {
    #     model_name: {
    #         question_idx: [question_value_1, question_value_2...]
    #     }
    # }
    models_dict:dict[str, dict[int, list[int]]] = {} 

    for result in results.values():
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

def get_answers_means(models_dict:dict[str, dict[int, list[int]]]) -> dict[str, dict[int, str]]:
    mean_models_dict:dict[str, dict[int, str]] = {}

    for model_name, question_dict in models_dict.items():
        for quest_idx, values in question_dict.items():
            values_array = np.array(values)
            values_mean = round(values_array.mean(), 3)
            values_std = round(values_array.std(), 3)

            if not mean_models_dict.get(model_name):
                mean_models_dict[model_name] = {}

            mean_models_dict[model_name][quest_idx] = f"{values_mean}+-{values_std}"

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