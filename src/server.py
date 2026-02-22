import os
import random
import typing as tp
import json

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

pick_one_col = db["control_pick_one"]
models_comb_col = db["control_models_combinations"]
questions_col = db["questions"]
results_col = db["results"]

app = Flask(__name__)

XP_MODEL_COMB_KEY = -1
XP_CONTENTS_KEYS = -2
VERBOSE = True

def get_models_combination() -> tp.List[tp.Tuple[int, int]]:
    combination_visits = {}
    models_combinations = models_comb_col.find({})

    for m in models_combinations:
        combination_visits[m['_id']] = m['visits']

    num_models = len(m['paths'])
    min_key = min(combination_visits, key=combination_visits.get) # type: ignore
    min_visists = combination_visits[min_key]

    min_combinations_ids = [combination_id for combination_id, visits in combination_visits.items() if min_visists == visits]
    chosen_combination = random.choice(min_combinations_ids)

    models = []
    for i in range(num_models):
        models.append((chosen_combination, i))

    log_choosen = models_comb_col.find_one({'_id':chosen_combination})

    if VERBOSE: print(f"Chosen Models:\n\t--> Comb Key: {chosen_combination}\n\t--> Paths: {log_choosen['paths']}") # type: ignore

    return models

def get_pick_one_contents() -> tp.List[tp.Tuple[int, int]]:
    pick_one_contents:tp.List[tp.Tuple[int, int]] = []
    pick_one_dict = pick_one_col.find({})

    if VERBOSE: print(f"Chosen Contents:")
    for p in pick_one_dict:
        p_visits:tp.List[int] = p['visits']
        min_visits:int = min(p_visits)

        min_contents = []
        for idx, visits in enumerate(p_visits):
            if min_visits == visits:
                min_contents.append(idx)

        choosen_content = random.choice(min_contents)

        pick_one_contents.append((p['_id'], choosen_content))

        if VERBOSE: 
            print(f"\t--> Pick One Key: {p['_id']} | Name: {p['name']} | Path: {p['contents'][choosen_content]}")

    return pick_one_contents

def get_final_experiment(model_comb_key:tp.List[tp.Tuple[int, int]], contets_keys:tp.List[tp.Tuple[int, int]]):
    experiment = {}
    order = []
    counter = 0

    for model_key in model_comb_key:
        for content_key in contets_keys:
            experiment[counter] = {
                'model_comb_key': model_key,
                'content_key': content_key
            }
            order.append(counter)
            counter += 1
    
    return experiment, order

def get_final_experiment_test(model_comb_key:tp.List[tp.Tuple[int, int]], contets_keys:tp.List[tp.Tuple[int, int]]):
    experiment = {}
    order = []
    counter = 0

    for model_key in model_comb_key[:2]:
        for content_key in contets_keys[:2]:
            experiment[counter] = {
                'model_comb_key': model_key,
                'content_key': content_key
            }
            order.append(counter)
            counter += 1
    
    return experiment, order

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/index_test')
def index_test():
    global VERBOSE
    VERBOSE = True
    # Get least visited models combination id
    model_comb_key:tp.List[tp.Tuple[int, int]] = get_models_combination()

    # Get least visited pick_one contents
    contets_keys:tp.List[tp.Tuple[int, int]] = get_pick_one_contents()

    experiment, order = get_final_experiment_test(model_comb_key, contets_keys)

    experiment[XP_MODEL_COMB_KEY] = model_comb_key[0][0]
    experiment[XP_CONTENTS_KEYS] = contets_keys

    # Randomize pieces order
    random.shuffle(order)

    return render_template(
        'index.html', 
        experiment=experiment,
        order=order,
        sever_name=sever_name
    )

@app.route('/')
def index():
    # Get least visited models combination id
    model_comb_key:tp.List[tp.Tuple[int, int]] = get_models_combination()

    # Get least visited pick_one contents
    contets_keys:tp.List[tp.Tuple[int, int]] = get_pick_one_contents()

    experiment, order = get_final_experiment(model_comb_key, contets_keys)

    experiment[XP_MODEL_COMB_KEY] = model_comb_key[0][0]
    experiment[XP_CONTENTS_KEYS] = contets_keys

    # Randomize pieces order
    random.shuffle(order)

    return render_template(
        'index.html', 
        experiment=experiment,
        order=order,
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

@app.route('/evaluate/<model_comb_key>/<model_comb_idx>/<pick_one_key>/<content_idx>')
def evaluate(model_comb_key:str, model_comb_idx:str, pick_one_key:str, content_idx:str):
    model_path = models_comb_col.find_one({"_id": int(model_comb_key)})['paths'][int(model_comb_idx)] # type: ignore
    content_path = pick_one_col.find_one({"_id": int(pick_one_key)})['contents'][int(content_idx)] # type: ignore

    piece = os.path.join(model_path, content_path)

    # Get questions
    questions = get_questions()

    print(f"\nEVAL QUESNTIONS: {questions}\n")

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
def increment_visits(model_comb_key:int, contets_keys:tp.List[tp.Tuple[int, int]]):
    # Increment model_comb_key visists
    model_comb_filter = {'_id': model_comb_key}
    model_comb_op = {
        '$inc': { 'visists': 1 }
    }

    result = models_comb_col.update_one(model_comb_filter, model_comb_op)

    if VERBOSE: print(f"Model Comb Key {model_comb_key} Visits Updated to {result}")

    # Increment contents visists
    for pick_one_key, content_key in contets_keys:
        pick_one_key = { '_id': pick_one_key }

        content_op = {
            '$inc': {f'visits.{content_key}': 1 }
        }

        result = pick_one_col.update_one(pick_one_key, content_op)

        if VERBOSE: print(f"Pick One Key {pick_one_key} at Content {content_key} Visits Updated to {result.modified_count}")

@app.route('/end', methods = ['GET', 'POST']) # type: ignore
def end():
    if request.method == 'POST':
        result = {}
        if request.form.get('experiment'):
            experiments:str = request.form.get('experiment') # type: ignore
            experiment:dict = json.loads(experiments)

            # Add 1 in used model comb and contents
            model_comb_key = experiment[str(XP_MODEL_COMB_KEY)]
            contets_keys = experiment[str(XP_CONTENTS_KEYS)]

            increment_visits(model_comb_key, contets_keys)

            questions = get_questions()

            for key in experiment:
                if key not in ['_id', str(XP_MODEL_COMB_KEY), str(XP_CONTENTS_KEYS)]:
                    for question in questions:
                        question_id = question['_id']
                        question_key = f'{key}_q{question_id}'

                        result[question_key] = request.form.get(question_key)
                        print(f"SAVING RESULT result[{question_key}] {result[question_key]}")

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