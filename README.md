# Intro
This repository aims to be a template for user studies in the filed to video-to-music generation. It builds upon the user experiment code from [Controlling Perceived Emotion in Symbolic Music Generation with Monte Carlo Tree Search](https://github.com/lucasnfe/puct-music-emotion).

## Installation
1. Install [MongoDB](https://www.mongodb.com/docs/v7.0/administration/install-on-linux/)
2. Run the following from the project directory 
```
python3 -m venv env
source env/bin/activate
python3 -m pip install -r requirements.txt
``` 

## Running
1. Make sure MongoDB is running `sudo systemctl status mongod`
2. from the project src folder run `python3 study.py --path_audio ./static/audio/mcts --path_test ./static/audio/human`
3. from the project src folder run `flask --app server run`