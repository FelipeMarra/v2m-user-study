import os
import random
import typing as tp

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
results_col = db["results"]

app = Flask(__name__)

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

    return models

def get_pick_one_contents() -> tp.List[tp.Tuple[int, int]]:
    pick_one_contents:tp.List[tp.Tuple[int, int]] = []
    pick_one_dict = pick_one_col.find({})

    for p in pick_one_dict:
        p_visits:tp.List[int] = p['visits']
        min_visits:int = min(p_visits)

        min_contents = []
        for idx, visits in enumerate(p_visits):
            if min_visits == visits:
                min_contents.append(idx)

        choosen_content = random.choice(min_contents)

        pick_one_contents.append((p['_id'], choosen_content))

    return pick_one_contents

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def index():
    # Get least visited models combination id
    model_comb_key:tp.List[tp.Tuple[int, int]] = get_models_combination()
    print(f"Got model_comb_key {model_comb_key} | type {type(model_comb_key)}")

    # Get least visited pick_one contents
    contets_keys:tp.List[tp.Tuple[int, int]] = get_pick_one_contents()
    print(f"Got pick_one_contents {contets_keys} | type {type(contets_keys)}")

    pieces_dict = {}
    pieces_order = []
    counter = 0

    for model_key in model_comb_key:
        for content_key in contets_keys:
            pieces_dict[counter] = {
                'model_comb_key': model_key,
                'content_key': content_key
            }
            pieces_order.append(counter)
            counter += 1

    # Randomize pieces order
    random.shuffle(pieces_order)

    return render_template(
        'index.html', 
        experiment=pieces_dict,
        order=pieces_order,
        sever_name=sever_name
    )

@app.route('/evaluate/<model_comb_key>/<model_comb_idx>/<pick_one_key>/<content_idx>')
def evaluate(model_comb_key:str, model_comb_idx:str, pick_one_key:str, content_idx:str):
    # print(f"\n ---------> model_comb_key: {model_comb_key} {type(model_comb_key)} | pick_one_key: {pick_one_key}\n")

    model_path = models_comb_col.find_one({"_id": int(model_comb_key)})['paths'][int(model_comb_idx)] # type: ignore
    content_path = pick_one_col.find_one({"_id": int(pick_one_key)})['contents'][int(content_idx)] # type: ignore

    # print(f"\n ---------> model_path: {model_path}\content_path: {content_path}\n")
    piece = os.path.join(model_path, content_path)

    return render_template(
        'evaluate.html', 
        piece=piece,
        sever_name=sever_name
    )

@app.route('/test/<test_id>')
def test(test_id):
    if int(test_id) == 1:
        return render_template(
            'test.html', 
            piece='static/audio/human/e2_real_human_4.mp3',
            q1=1, q2=5, q3=5,
            sever_name=sever_name
        )
    elif int(test_id) == 2:
        return render_template(
            'test.html', 
            piece='static/audio/human/e4_real_human_2.mp3',
            q1=5, q2=2, q3=5,
            sever_name=sever_name
        )

@app.route('/profile')
def profile():
    return render_template('profile.html', sever_name=sever_name)

@app.route('/end', methods = ['GET', 'POST'])
def end():
    if request.method == 'POST':
        result = {}
        if request.form.get('experiment'):
            experiment_id = request.form.get('experiment')
            experiment = experiments_col.find_one({"_id": experiment_id})

            result["experiment_id"] = experiment_id
            for key in experiment:
                if key != '_id' and key != 'system':
                    result[key + "_q1"] = request.form.get(key + "_q1")
                    result[key + "_q2"] = request.form.get(key + "_q2")
                    result[key + "_q3"] = request.form.get(key + "_q3")
                    result[key + "_q4"] = request.form.get(key + "_q4")
                    result[key + "_q5"] = request.form.get(key + "_q5")
                    result[key + "_expl"] = request.form.get(key + "_expl")

            for test in range(1, 3):
                    result["test_{}_q1".format(test)] = request.form.get("test_{}_q1".format(test))
                    result["test_{}_q2".format(test)] = request.form.get("test_{}_q2".format(test))
                    result["test_{}_q3".format(test)] = request.form.get("test_{}_q3".format(test))
                    result["test_{}_q4".format(test)] = request.form.get("test_{}_q4".format(test))
                    result["test_{}_q5".format(test)] = request.form.get("test_{}_q5".format(test))

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