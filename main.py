import base64
from PIL import Image
from flask import Flask, request
import gzip
import gradio as gr
from pymongo import MongoClient
from io import BytesIO
from transformers import pipeline
# Create a MongoClient to the MongoDB server
client = MongoClient('mongodb+srv://guarddesign:HALXBHFFMvhm5kYb@cluster0.hblmqfd.mongodb.net/?retryWrites=true&w=majority')
# Get the database you want to use
db = client['guard-design']
collection = db['user_images']
app = Flask(__name__)
pipe = pipeline("image-classification", "umm-maybe/AI-image-detector")

@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/compress', methods=['POST'])
def compress_it():
    data = request.json
    user_name = data['user_name']
    image_data = data['image_data']
    image_title = data['image_title']
    # Encode the image string as bytes
    image_data_bytes = image_data.encode('utf-8')
    # Open the image file
    image = Image.open(BytesIO(base64.b64decode(image_data)))
    inputs = gr.Image(type="pil")
    is_fake = image_classifier(image)
    print(is_fake)
    if is_fake['human'] > is_fake['artificial']:
        # Compress the image data using gzip
        compressed_data = gzip.compress(image_data_bytes)
        # Encode the compressed data in base64
        base64_data = base64.b64encode(compressed_data).decode()
        document = {'image_data': base64_data,
                    'image_title': user_name + '__' + image_title
                    }
        result = collection.insert_one(document)
        return str(result.inserted_id)
    return 'Sorry your image was made by an ai'
def image_classifier(image):
    outputs = pipe(image)
    results = {}
    for result in outputs:
        results[result['label']] = result['score']
    return results
@app.route('/decompress', methods=['POST'])
def decompress_it():
    data = request.json
    user_name = data['user_name']
    image_title = data['image_title']
    id = user_name+'__'+image_title
    document = {'image_title' : id}
    chosen_document = collection.find_one(document)
    # Decompress the data
    decompressed_data = gzip.decompress(base64.b64decode(chosen_document['image_data']))
    string_data = decompressed_data.decode()
    return string_data


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
