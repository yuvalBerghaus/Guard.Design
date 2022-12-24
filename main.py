import base64

from flask import Flask, request
import gzip
from pymongo import MongoClient

# Create a MongoClient to the MongoDB server
client = MongoClient('mongodb+srv://guarddesign:HALXBHFFMvhm5kYb@cluster0.hblmqfd.mongodb.net/?retryWrites=true&w=majority')
# Get the database you want to use
db = client['guard-design']
collection = db['newsletter']
app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/lika', methods=['POST'])
def rangaha():
    data = request.json
    print(data)
    return 'hello'

@app.route('/compress', methods=['POST'])
def compress_it():
    data = request.json
    image_string = data['image']
    # Encode the image string as bytes
    image_data = image_string.encode('utf-8')
    # Compress the image data using gzip
    compressed_data = gzip.compress(image_data)
    # Convert the compressed data to a base64-encoded string
    compressed_string = base64.b64encode(compressed_data).decode('utf-8')
    #TODO - Collection of string64 images
    return image_string



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
