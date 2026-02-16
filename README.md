# Introduction
This repository aims to be a template for user studies in the filed to video-to-music generation. It builds upon the user experiment code from [Controlling Perceived Emotion in Symbolic Music Generation with Monte Carlo Tree Search](https://github.com/lucasnfe/puct-music-emotion).

# Installation
1. Install [MongoDB](https://www.mongodb.com/docs/v7.0/administration/install-on-linux/)
2. Run the following from the project directory 
```
python3 -m venv env
source env/bin/activate
python3 -m pip install -r requirements.txt
``` 

# Running
1. Make sure MongoDB is running with `sudo systemctl status mongod`.
2. Create a symlink folder in `src/static/experiments` pointing to your experiments folder - more on the folder structure [here](#folder-structure).
3. Define your template inside `study_creator.py`'s `main()` function.
4. from the project src folder run `python3 study_creator.py`.
5. from the project src folder run `flask --app server run`.

# Folder Structure
The site don't expect a very rigid `experiments` folder structure, since you can define your's via a [template](#template-creation). The requirements are that the folders inside `experiments` should be your models names, and every model folder structure sould be the same. An example folder structure could be:

```
src/static/experiments/
    |_Model_Name_1/
        |_fldr_lvl_1_name_1/
            |_fldr_lvl_2_name_1/
                |_video.mp4
            |_fldr_lvl_2_name_2/
                |_video.mp4
        |_fldr_lvl_1_name_2/
            |_fldr_lvl_2_name_1/
                |_video.mp4
            |_fldr_lvl_2_name_2/
                |_video.mp4
    |_Model_Name_2/
        |_fldr_lvl_1_name_1/
            |_fldr_lvl_2_name_1/
                |_video.mp4
            |_fldr_lvl_2_name_2/
                |_video.mp4
        |_fldr_lvl_1_name_2/
            |_fldr_lvl_2_name_1/
                |_video.mp4
            |_fldr_lvl_2_name_2/
                |_video.mp4
```

In KojiGen, the models could be T5->MusicGen, OSSL, GVMGen, etc. The `fldr_lvl_1` could be the categories, which are the games genres. The `fldr_lvl_2` could be the game's names. So a contextualized example would look like:

```
src/static/experiments/
    |_Model_Name_1/
        |_Action/
            |_batman-forever/
                |_video.mp4
            |_brandish/
                |_video.mp4
        |_Adventure/
            |_clock-tower/
                |_video.mp4
            |_kamaitachi-no-yoru/
                |_video.mp4
    |_Model_Name_2/
        |_Action/
            |_batman-forever/
                |_video.mp4
            |_brandish/
                |_video.mp4
        |_Adventure/
            |_clock-tower/
                |_video.mp4
            |_kamaitachi-no-yoru/
                |_video.mp4
```

## Template Creation
In order to create the template that tells `study_creator.py` how to loop the folder structure, create a new intance of the Template class in `study_creator.py`'s `main()`. For KojiGen the Temaplate instance would be:

```python
kojiGen = StudyTemplate(
    name="KojiGen",
    ends_with="_gen.mp4",
    levels = [
        Level("Model", LevelType.MODEL),
        Level("Inference", LevelType.FOLDER, force_folder="inference"),
        Level("Game Genre", LevelType.PICK_ONE)
    ]
)
```

The temaplate receiveives a property called `levels`, which is a list of type `Level`. Each `Level` is another `_fldr_lvl` in the [folder structure](#folder-structure). The first level should be of type `LevelType.MODEL`, representing the results for every model you have.

For the models level onwards the current version of the `study_creator.py` expects a `LevelType.FOLDER` with the `force_folder` property set up untill the `PICK_ONE` level. In KojiGen, the senconde level - called Inference in the template - can have a `inference` and a `checkpoint` folder, where the `checkpoint` contains the model's checkpoint. For that reason we set  `force_folder` to `inference`, since is the inference folder that will contain the videos for the experiment.

The `pick_one` property tell the `study_creator` to pick one file that ends with the string set in the `ends_with` property. In KojiGen, from the genre level - as shown in the [folder structure](#folder-structure) example - we want to retrieve one random video from one random game.