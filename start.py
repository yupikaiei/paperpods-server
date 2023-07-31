from dotenv import load_dotenv
load_dotenv()

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from generator import PodcastGenerator
from elabs import Elabs
import hashlib

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    openai_api_key = db.Column(db.String, nullable=False)
    elabs_api_key = db.Column(db.String, nullable=False)
    podcastName = db.Column(db.String, nullable=True)
    hostName = db.Column(db.String, nullable=True)
    explanationLevel = db.Column(db.String, nullable=True)
    voice_id = db.Column(db.String, nullable=True)

class Podcast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    User_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    image = db.Column(db.String, nullable=True)
    name = db.Column(db.String, nullable=False)
    host = db.Column(db.String, nullable=False)
    explanationLevel = db.Column(db.String, nullable=False)
    voice_id = db.Column(db.String, nullable=False)
    file = db.Column(db.String, nullable=False)
    paperUrl = db.Column(db.String, nullable=False)
    paperTitle = db.Column(db.String, nullable=False)
    liked = db.Column(db.Boolean, nullable=False, default=True)
    played = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=db.func.now())


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///data.db"
db.init_app(app)

with app.app_context():
    db.create_all()

# make dir if not exists
if not os.path.exists('static/media'):
    os.mkdir('static/media')

if not os.path.exists('docs'):
    os.mkdir('docs')

# cors
CORS(app, resources={r"/*": {"origins": "*"}})

# a simple page that says hello
@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/register', methods=['POST'])
def register():
    # parse the form data
    username = request.form['username']
    password = request.form['password']
    openai_api_key = request.form['openai_api_key']
    elabs_api_key = request.form['elabs_api_key']

    # hash password
    hashed_password = hashlib.md5(password.encode()).hexdigest()
    
    # check if username exists
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify(error='Username already exists'), 400
    
    # insert user into db
    user = User(
        username=username,
        password=hashed_password,
        openai_api_key=openai_api_key,
        elabs_api_key=elabs_api_key
    )
    db.session.add(user)
    db.session.commit()

    # create folder for user
    os.mkdir('static/media/' + str(user.id))

    # return success
    return jsonify(
        id=user.id,
        username=user.username,
        podcastName=user.podcastName,
        hostName=user.hostName,
        explanationLevel=user.explanationLevel,
        voice_id=user.voice_id,
        openai_api_key=user.openai_api_key,
        elabs_api_key=user.elabs_api_key,
    ), 200

@app.route('/login', methods=['POST'])
def login():
    # parse the form data
    username = request.form['username']
    password = request.form['password']

    # hash password
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    # check if username exists
    user = User.query.filter_by(username=username).first()
    if not user:
        return jsonify(error='Username does not exist'), 400
    
    # check if password is correct
    if user.password != hashed_password:
        return jsonify(error='Incorrect password'), 400
    
    # return success
    return jsonify(
        id=user.id,
        username=user.username,
        podcastName=user.podcastName,
        hostName=user.hostName,
        explanationLevel=user.explanationLevel,
        voice_id=user.voice_id,
        openai_api_key=user.openai_api_key,
        elabs_api_key=user.elabs_api_key,
    ), 200

@app.route('/update', methods=['POST'])
def update():
    # parse the form data
    id = request.form['id']
    podcastName = request.form['podcastName']
    hostName = request.form['hostName']
    explanationLevel = request.form['explanationLevel']
    voice_id = request.form['voice_id']
    openai_api_key = request.form['openai_api_key']
    elabs_api_key = request.form['elabs_api_key']

    # check if user exists
    user = User.query.filter_by(id=id).first()
    if not user:
        return jsonify(error='User does not exist'), 400
    
    # update user
    user.podcastName = podcastName
    user.hostName = hostName
    user.explanationLevel = explanationLevel
    user.voice_id = voice_id
    user.openai_api_key = openai_api_key
    user.elabs_api_key = elabs_api_key
    db.session.commit()

    # return success
    return jsonify(
        id=user.id,
        username=user.username,
        podcastName=user.podcastName,
        hostName=user.hostName,
        explanationLevel=user.explanationLevel,
        voice_id=user.voice_id,
        openai_api_key=user.openai_api_key,
        elabs_api_key=user.elabs_api_key,
    ), 200

@app.route('/voices')
def voices():
    # get api key from header
    elabs_api_key = request.headers.get('elabs_api_key')
    elabs = Elabs(elabs_api_key)
    return jsonify(elabs.get_voices())

@app.route('/podcasts/<id>')
def podcasts(id):
    print(id)
    # get user
    user = User.query.filter_by(id=id).first()
    if not user:
        return jsonify(error='User does not exist'), 400
    
    # get files in static/media folder
    files = os.listdir('static/media/' + str(user.id))
    # return list of files
    return jsonify(["/static/media/"+ str(user.id) + "/" + file for file in files])

@app.route('/tts', methods=['POST'])
def text_to_speech():
    elabs_api_key = request.headers.get('elabs_api_key')
    elabs = Elabs(elabs_api_key)
    # parse json body
    body = request.get_json()
    print(body)
    text = body['text']
    res = elabs.tts(text)
    print(res)
    return jsonify(res)

@app.route('/upload', methods=['POST'])
def upload_file():
    elabs_api_key = request.headers.get('elabs_api_key')
    elabs = Elabs(elabs_api_key)

    openai_api_key = request.headers.get('openai-api-key')
    podcast_generator = PodcastGenerator(openai_api_key)

    print(request.form)
    # parse the form data
    podcastName = request.form['podcastName']
    hostName = request.form['hostName']
    explanationLevel = request.form['explanationLevel']
    voice_id = request.form['voice_id']
    id = request.form['id']

    print(podcastName)
    print(hostName)
    print(explanationLevel)
    print(voice_id)
    print(id)

    # check if the post request has the file part
    if 'pdf' not in request.files:
        return jsonify(error='No file part'), 400
    file = request.files['pdf']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return jsonify(error='No selected file'), 400
    if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() == 'pdf':
        # response = summarizeDocument(file)
        # corpus = generateScript(file)
        podcastScript = podcast_generator.generatePodcast(podcastName, hostName, explanationLevel, file)
        with open('script.json', 'w') as f:
            f.write(json.dumps(podcastScript))
        
        podcast = elabs.tts_chuncked(user_id=id, text=podcastScript, voice_id=voice_id)

        db.session.add(Podcast(
            User_id=id,
            name=podcastName,
            paperTitle=file.filename,
            host=hostName,
            explanationLevel=explanationLevel,
            voice_id=voice_id,
            file=podcast['url'],
            paperUrl='docs/' + file.filename,
        ))
        db.session.commit()

        return jsonify(result=podcast), 200
        # return jsonify(error='Not implemented'), 200

@app.route('/audio')
def audio():
    elabs_api_key = request.headers.get('elabs_api_key')
    elabs = Elabs(elabs_api_key)

    # Opening JSON file
    f = open('script.json')
    
    # returns JSON object as
    # a dictionary
    podcastScript = json.load(f)

    print(podcastScript)
    podcast = elabs.tts_chuncked(user_id=1, text=podcastScript)

    return jsonify(result=podcast), 200

if __name__ == '__main__':
    app.run(host= '0.0.0.0', debug=True)