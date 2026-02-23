import os
import random
import typing as tp
import json
from copy import deepcopy

from flask import Flask
from flask import request
from flask import render_template, redirect, url_for

from pymongo import MongoClient

# Define host name
# naming this as localhost:500 might make the index.html address be 127.0.0.1:5000
# and the other pages be localhost:500, which will mess with the localStorage
sever_name="127.0.0.1:5000" 

# Connect with database
database_url = "localhost:27017"
client = MongoClient(database_url)
db = client["user_study_test"]

# Create database
pick_one_col = db["pick_one"]
models_col = db["models"]
questions_col = db["questions"]
xp_meta_col = db["xp_meta"] # metadata like template's n_models and n_experiments
results_col = db["results"]

app = Flask(__name__)

VERBOSE = True
GT_KEY = -1
GT_ENDS_WITH = ''

def get_models() -> tp.Tuple[tp.List[int], int]:
    global GT_KEY, GT_ENDS_WITH

    models_visits = {}
    models = models_col.find({})
    n_models:int = xp_meta_col.find_one({'_id': 0})['n_models'] # type: ignore
    gt:str = xp_meta_col.find_one({'_id': 0})['gt'] # type: ignore

    if VERBOSE: print(f"get_models n_models_to_choose {n_models}")

    gt_key = -1
    for m in models:
        if m['name'] != gt:
            models_visits[m['_id']] = m['visits']
        else:
            gt_key = m['_id']
            GT_KEY = gt_key
            GT_ENDS_WITH = m['ends_with']

    if VERBOSE: print(f"get_models gt_key {gt_key} \nmodels_visits: {models_visits}")

    # Choosing from the min visits can't guarantee that we'll choose the amount of models we need, therefore the while loop
    chosen_models_keys = []
    while len(chosen_models_keys) < n_models:
        min_key:tp.List[int] = min(models_visits, key=models_visits.get) # type: ignore
        min_visists = models_visits[min_key]
        if VERBOSE: print(f"get_models min_keys visits {min_key} | min_visists: {min_visists}")

        min_ids = [model_id for model_id, visits in models_visits.items() if min_visists == visits]

        k = n_models-len(chosen_models_keys)
        k = k if len(min_ids) >= k else len(min_ids) # min_ids might have less than k values

        chosen_models_keys += random.sample(min_ids, k=k)
        if VERBOSE: print(f"get_models chosen_models_keys: {chosen_models_keys}")

        # Can't choose the same keys again
        for key in chosen_models_keys:
            if isinstance(models_visits.get(key), int):
                models_visits.pop(key)
                if VERBOSE:
                    choosen_path:str = models_col.find_one({'_id':key})['path'] # type: ignore
                    print(f"chosen model: {key} | models_visits: {models_visits} | path: {choosen_path}\n")

    if VERBOSE: print(f"------------> FINAL chosen_models_keys: {chosen_models_keys}\n")

    return chosen_models_keys, gt_key

def get_contents() -> tp.Tuple[tp.List[tp.Tuple[int, int]], int]:
    pick_one_dict = pick_one_col.find({})
    n_experiments:int = xp_meta_col.find_one({'_id': 0})['n_experiments'] # type: ignore

    p_visits = {}
    for p in pick_one_dict:
        p_visits[p['_id']] = p['visits']

    choosen_pick_one = []
    while len(choosen_pick_one) < n_experiments:
        min_keys:int = min(p_visits, key=p_visits.get) # type: ignore
        min_visits = p_visits[min_keys]

        if VERBOSE: print(f"get_contents pick_one min_keys {min_keys} | min_visists: {min_visits}")

        min_ids = [pick_one_id for pick_one_id, visits in p_visits.items() if min_visits == visits]

        k = n_experiments-len(choosen_pick_one)
        k = k if len(min_ids) >= k else len(min_ids) # min_ids might have less than k values

        choosen_pick_one += random.sample(min_ids, k=k)

        if VERBOSE: print(f"get_contents choosen_pick_one: {choosen_pick_one}")

        # Can't choose the same keys again
        for key in choosen_pick_one:
            if p_visits.get(key):
                if VERBOSE: print(f"get_contents del: {key} | p_visits: {p_visits}")
                p_visits.pop(key)

    # Choose the contents from the chosen pick_one
    chosen_contents:tp.List[tp.Tuple[int, int]] = []

    for key in choosen_pick_one:
        pick_one = pick_one_col.find_one({'_id': key})
        contents_visits:tp.List[int] = pick_one['contents_visits'] # type: ignore

        # Find the index of the first occurrence of the minimum value
        min_visits = min(contents_visits)
        min_indexes = [idx for idx, visits in enumerate(contents_visits) if min_visits == visits]
        min_index = random.choice(min_indexes)

        chosen_contents.append((key, min_index))

        if VERBOSE: 
            print(f"\t--> Pick One Key: {key} | Name: {pick_one['name']} | Path: {pick_one['contents'][min_index]}") # type: ignore

    return chosen_contents, n_experiments

def get_experiment(models_keys:tp.List[int], gt_key:int, contets_keys:tp.List[tp.Tuple[int, int]], n_experiments:int):
    experiments_dict = {}
    counter = 0

    for idx in range(n_experiments):
        # shuffle models for each experiment
        shuffled_model_keys = deepcopy(models_keys)
        if VERBOSE: print(f"BEFORE SHUFFLE get_experiment {idx} | shuffled_model_keys: {shuffled_model_keys}")
        random.shuffle(shuffled_model_keys)

        # insert ground truth at the begining of every experiment
        shuffled_model_keys.insert(0, gt_key)

        if VERBOSE: print(f"AFTER SHUFFLE get_experiment {idx} | shuffled_model_keys: {shuffled_model_keys}")

        for model_key in shuffled_model_keys:
            pick_one_key, content_key = contets_keys[idx]
            experiments_dict[counter] = {
                'xp_idx': idx,
                'model_key': model_key,
                'pick_one_key': pick_one_key,
                'content_key': content_key
            }

            if VERBOSE: print(f"get_experiment experiments_dict {counter}: {experiments_dict[counter]}\n")

            counter += 1

    return experiments_dict

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def index():
    # Get least visited models combination id
    models_keys, gt_key = get_models()

    # Get least visited pick_one contents
    contets_keys, n_experiments = get_contents()

    experiments_dict = get_experiment(models_keys, gt_key, contets_keys, n_experiments)

    return render_template(
        'index.html', 
        experiments_dict=experiments_dict,
        sever_name=sever_name
    )

def get_questions():
    # Get questions
    questions = [
        {
            '_id': question['_id'],
            'header': question['header'],
            'options': list(enumerate(question['options']))
        } 
        for question in questions_col.find({})
    ]

    return questions

# #TODO: Maybe change to only receive the experiment dict key
@app.route('/evaluate/<model_key>/<pick_one_key>/<content_key>')
def evaluate(model_key:str, pick_one_key:str, content_key:str):
    model:tp.Dict[str, tp.Any] = models_col.find_one({"_id": int(model_key)}) # type: ignore
    content_path:str = pick_one_col.find_one({"_id": int(pick_one_key)})['contents'][int(content_key)] # type: ignore
    gen_ends_with:str = xp_meta_col.find_one({'_id': 0})['gen_ends_with'] # type: ignore

    if VERBOSE: print(f"\n EVAL ROUT: \n\tmodel_key: {model_key}\n\tGT_KEY: {GT_KEY}\n\tgen_ends_with {gen_ends_with}\n\tGT_ENDS_WITH: {GT_ENDS_WITH}")

    if model_key == str(GT_KEY):
        content_path = content_path.replace(gen_ends_with, GT_ENDS_WITH)

    piece = os.path.join(model['path'], content_path)

    # Get questions
    questions = get_questions()

    if VERBOSE: print(f"EVAL ROUT QUESNTIONS: {questions}\n")

    return render_template(
        'evaluate.html', 
        piece=piece,
        questions=questions,
        sever_name=sever_name
    )

@app.route('/profile')
def profile():
    # Get questions
    questions = get_questions()

    return render_template(
        'profile.html', 
        questions=questions,
        sever_name=sever_name
    )

# End rout
def increment_visits(models_keys:tp.List[int], contets_keys:tp.List[tp.Tuple[int, int]]):
    for model_key in models_keys:
        # Increment model_comb_key visists
        model_filter = {'_id': model_key}
        model_op = {
            '$inc': { 'visists': 1 }
        }

        result = models_col.update_one(model_filter, model_op)
        if VERBOSE: print(f"Model Comb Key {model_key} Visits Updated to {result}")

    # Increment contents visists
    for pick_one_key, content_key in contets_keys:
        # Increment pick_one visists
        pick_one_key = {'_id': pick_one_key}
        pick_one_op = {
            '$inc': { 'visists': 1 }
        }

        result = pick_one_col.update_one(pick_one_key, pick_one_op)
        if VERBOSE: print(f"Pick One Key {pick_one_key} visits updated to {result.modified_count}")

        # Increment contents visists
        content_op = {
            '$inc': {f'contents_visits.{content_key}': 1 }
        }

        result = pick_one_col.update_one(pick_one_key, content_op)
        if VERBOSE: print(f"Pick One Key {pick_one_key} at Content {content_key} Visits Updated to {result.modified_count}")

@app.route('/end', methods = ['GET', 'POST']) # type: ignore
def end():
    if request.method == 'POST':
        result = {}
        experiments_dict:str = request.form.get('experiments_dict') # type: ignore
        print(f"END ROUT POST experiments_dict as str:\n{experiments_dict}\n")
        if experiments_dict:
            experiments_dict:dict = json.loads(experiments_dict) # type: ignore

            models_keys = []
            contets_keys = []
            questions = get_questions()

            for key, value in experiments_dict.items():
                if key not in ['_id']:
                    model_key = int(value['model_key'])
                    models_keys.append(model_key)

                    pick_one_key = int(value['pick_one_key'])
                    content_key = int(value['content_key'])
                    contets_keys.append((pick_one_key, content_key))

                    content_answer = {
                        'model_key': model_key,
                        'pick_one_key': pick_one_key,
                        'content_key': content_key
                    }

                    for question in questions:
                        question_id = question['_id']
                        question_key = f'{key}_q{question_id}'

                        content_answer[question_key]:str = request.form.get(question_key) # type: ignore

                    result[f'xp_{key}'] = content_answer
                    print(f"SAVING RESULT result[xp_{key}]: {result[f'xp_{key}']}")

            models_keys = list(set(models_keys))
            contets_keys = list(set(contets_keys))
            increment_visits(models_keys, contets_keys)

            result["ethnicity"] = request.form.get("ethnicity")
            result["language"] = request.form.get("language")
            result["year"]     = request.form.get("year")
            result["xp"]       = request.form.get("xp")
            result["comments"] = request.form.get("comments")

            insert_result = results_col.insert_one(result)

            return redirect(
                url_for(
                    'end', 
                    evaluation_id=insert_result.inserted_id,
                    sever_name=sever_name
                )
            )
    else:
        return render_template('end.html', sever_name=sever_name)