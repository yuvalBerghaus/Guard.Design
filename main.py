import base64
import io
import uuid
from PIL import Image
from bson import ObjectId
from flask import Flask, request, redirect, url_for, render_template, jsonify
import gzip
from passlib.hash import pbkdf2_sha256
from pymongo import MongoClient
from io import BytesIO
import os
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_cors import CORS, cross_origin
load_dotenv()
MONGODB_URI = os.getenv("MONGODB_URI")
# Create a MongoClient to the MongoDB server
client = MongoClient(MONGODB_URI)
# Get the database you want to use
db = client['guard-design']
user_images = db['user_images']
users = db["users"]
pages = db["pages"]
followers = db["followers"]
likes = db["likes"]
app = Flask(__name__)
jwt = JWTManager(app)
cors = CORS(app, resources={r"/*": {"origins":  ["http://localhost:3000", "https://wwww.guard.design"]}})


class User:
    def __init__(self,username ,email, password):
        self.uid = None
        self.username = username
        self.email = email
        self.password = password
    # def start_session(self,user):
    #     session['logged_in'] = True
    #     session['']
    def signup(self):
        if db.users.find_one({'email' : self.email}):
            return jsonify({ "error" : "Email address already in use"}), 400
        self.uid = uuid.uuid4().hex
        db.users.insert_one({'uid':self.uid,'username': self.username,'email': self.email, 'password': self.password})
        return "Registered!", 200
    def login(self):
        current_user = db.users.find_one({'email' : self.email, 'password' : self.password})
        if current_user:
            self.uid = current_user['uid']
            access_token = create_access_token(identity=self.uid)
            return jsonify({'uid':self.uid,'email':self.email,'username':self.username, 'access_token' : access_token}), 200
        return "failed logging in!", 400
    def follow(self, to_id):
        follower_doc = db.followers.find_one({'following_id': to_id , 'follower_id' : self.uid})
        if follower_doc is None:
            db.followers.insert_one({'following_id': self.to_id,'follower_id': self.uid})

    @classmethod
    def from_dict(cls, doc):
        return cls(uid=doc['uid'],username=doc['username'], email=doc['email'], password=doc['password'])


@app.route('/')
def home():
    return render_template('login.html')


@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data['username']
    email = data['email']
    password = data['password']
    current_user = User(username,email,password)
    is_created_obj = current_user.signup()
    return is_created_obj #redirect(url_for('login_page'))

@app.route('/login')
def login():
    # login logic goes here
    data = request.json
    email = data['email']
    password = data['password']
    current_user = User(email=email, password=password)
    res = current_user.login()
    return res

@app.route('/like', methods=['POST'])
@jwt_required
def like():
    data = request.json
    user_id = data['user_id']
    page_id = data['page_id']
    document = {
        'user_id' : ObjectId(user_id),
        'page_id': ObjectId(page_id),
    }
    cursor = likes.find_one(document)
    if cursor is not None:
        pages.update_one(
            {'_id': ObjectId(page_id)},
            {'$inc': {'likes': -1}}
        )
        likes.delete_one(document)
        return "-1"
    else:
        pages.update_one(
            {'_id': ObjectId(page_id)},
            {'$inc': {'likes': 1}}
        )
        likes.insert_one(document)
        return "+1"


@app.route('/follow', methods=['POST'])
def follow():
    data = request.json
    # get the user ID of the user to be followed from the request body
    to_uid = data['to_uid']
    from_uid = data['from_uid']
    current_user = User.from_dict(users.find_one({'uid' : from_uid}))
    # your logic for following the user goes here
    # for example, you might add the user to a list of users being followed by the current user
    current_user.follow(to_uid)

    # return a success message
    return jsonify({'message': 'Successfully followed user'})


@app.route('/compress', methods=['POST'])
def compress_it():
    data = request.json
    user_name = data['user_name']
    image_data = data['image_data']
    image_title = data['image_title']
    # Encode the image string as bytes
    image_data_bytes = image_data.encode('utf-8')
    # Open the image file
    # is_fake = image_classifier(image)
    # Compress the image data using gzip
    compressed_data = gzip.compress(image_data_bytes)
    # Encode the compressed data in base64
    base64_data = base64.b64encode(compressed_data).decode()
    document = {'image_data': base64_data,
                'image_title': user_name + '__' + image_title
                }
    result = user_images.insert_one(document)
    return str(result.inserted_id)

@app.route('/crop', methods=['POST'])
def crop():
    data = request.json
    image_data = data['image_data']
    x1, y1 , x2 , y2 = data['x1'] , data['y1'] , data['x2'] , data['y2']
    img_base64 = base64.b64decode(image_data)
    image_bytes = io.BytesIO(img_base64)
    image_cropped_bytes = io.BytesIO()
    image = Image.open(image_bytes)
    width, height = image.size
    if width >= 500 and height >= 500:
        cropped_im = image.crop((x1, y1, x2, y2))
        cropped_im.save(image_cropped_bytes, format=image.format)
        image_cropped_bytes.seek(0)
        base64_image = base64.b64encode(image_cropped_bytes.getvalue()).decode()
        return base64_image
    return "The image is too small to crop!"
@app.route('/resize', methods=['POST'])
def resize():
    data = request.json
    constant_size = (500,500)
    image_data = data['image_data']
    # Decode the base64-encoded image string
    image_data = base64.b64decode(image_data)
    # Create a file-like object from the image data
    image_bytes = io.BytesIO(image_data)
    # Open the image
    image = Image.open(image_bytes)
    # Resize the image
    resized_image = image.resize(constant_size)
    # Create a new file-like object to hold the resized image data
    resized_image_bytes = io.BytesIO()
    # Save the resized image to the file-like object
    resized_image.save(resized_image_bytes, format=image.format)
    # Seek to the beginning of the file-like object
    resized_image_bytes.seek(0)
    # Encode the resized image data as a base64-encoded string
    resized_base64_image = base64.b64encode(resized_image_bytes.getvalue()).decode()
    return resized_base64_image

@app.route('/decompress', methods=['POST'])
def decompress_it():
    data = request.json
    user_name = data['user_name']
    image_title = data['image_title']
    id = user_name+'__'+image_title
    document = {'image_title' : id}
    chosen_document = user_images.find_one(document)
    # Decompress the data
    decompressed_data = gzip.decompress(base64.b64decode(chosen_document['image_data']))
    string_data = decompressed_data.decode()
    return string_data


if __name__ == '__main__':
    app.run(host='localhost', port=5000)
