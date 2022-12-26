import base64
import io

from PIL import Image
from bson import ObjectId
from flask import Flask, request, redirect, url_for, render_template
import gzip
from passlib.hash import pbkdf2_sha256
import gradio as gr
from pymongo import MongoClient
from io import BytesIO
from transformers import pipeline
# Create a MongoClient to the MongoDB server
client = MongoClient('mongodb+srv://guarddesign:HALXBHFFMvhm5kYb@cluster0.hblmqfd.mongodb.net/?retryWrites=true&w=majority')
# Get the database you want to use
db = client['guard-design']
user_images = db['user_images']
users = db["users"]
users_cnt = db["users"]
pages = db["pages"]
followers = db["followers"]
likes = db["likes"]
app = Flask(__name__)
pipe = pipeline("image-classification", "umm-maybe/AI-image-detector")

#### MODELS
class User:
    def __init__(self,user_id,username ,email, password):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password = password

    def save(self):
        db.users.insert_one({'username': self.username,'email': self.email, 'password': self.password})
    def follow(self, to_id):
        follower_doc = db.followers.find_one({'following_id': to_id , 'follower_id' : self.user_id})
        if follower_doc is None:
            db.followers.insert_one({'following_id': self.to_id,'follower_id': self.user_id})

@app.route('/')
def index():
    return 'Hello, World!'


@app.route('/signup', methods=['POST'])
def signup():
    id_gen_doc = db.users_cnt.find_one({'name' : 'guard.design.generator'})
    uid = id_gen_doc['_id']
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    hashed_password = pbkdf2_sha256.hash(password)
    current_user = User(uid,username,email,hashed_password)
    current_user.save()
    users_cnt.update_one(
        {'name' : 'guard.design.generator'},
        {'$inc': {'_id': +1}}
    )
    return 'yes'#redirect(url_for('login_page'))

@app.route('/login_page')
def login():
    # login logic goes here
    return render_template('login.html')

@app.route('/like', methods=['POST'])
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
        likes.insert_one(document).inserted_id
        return "+1"


@app.route('/follow', methods=['POST'])
def follow_user():
    data = request.json
    # get the user ID of the user to be followed from the request body
    to_id = data['to_id']
    from_id = data['from_id']
    # your logic for following the user goes here
    # for example, you might add the user to a list of users being followed by the current user
    current_user.follow(user_id)

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
# def image_classifier(image):
#     outputs = pipe(image)
#     results = {}
#     for result in outputs:
#         results[result['label']] = result['score']
#     return results
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
    app.run(host='0.0.0.0', port=5000)
