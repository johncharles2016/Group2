from flask import Flask, redirect, request, send_file, url_for
from google.cloud import storage, firestore
from werkzeug.utils import secure_filename
import os
import io
from datetime import datetime

# Define the Google Cloud Storage bucket name
BUCKET_NAME = "faugroup2project2"

# Google Cloud Firestore configurations
db = firestore.Client()


# Initialize Google Cloud Storage client
client = storage.Client()

app = Flask(__name__)

@app.route('/')
def index():
    index_html = '''
    <body style="background-color:aqua;">
    <form enctype="multipart/form-data" action="/upload" method="post">
        <div>
            <label for="file">Choose file to upload</label>
            <input type="file" id="file" name="form_file" accept="image/jpeg"/>
        </div>
        <div>
            <button type="submit">Submit</button>
        </div>
    </form>
    <br>
    <a View Images Below</a>
    '''

    for file_info in list_files():
        index_html += f'''
        <div>
            <p>File: {file_info['filename']}</p>
            <p>Size: {file_info['size']} bytes</p>
            <p>Date Added: {file_info['date_added']}</p>
            <p>Location: {file_info['location']}</p>
            <img src="/files/{file_info['filename']}" style="max-width: 500px; max-height: 500px;">
            <br>
            <a href="/files/{file_info['filename']}" download="{file_info['filename']}">Download</a>
            <form action="/delete/{file_info['filename']}" method="post" style="display:inline;">
                <button type="submit" onclick="return confirm('Are you sure you want to delete this file?')">Delete</button>
            </form>
            <hr>
        </div>
        '''

    return index_html

@app.route('/upload', methods=['POST'])
def upload():
    if 'form_file' not in request.files or request.files['form_file'].filename == '':
        # No file provided, use a default image link
        return add_default_image_link()

    file = request.files['form_file']

    # Upload the file to Google Cloud Storage
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(file.filename)

    # Upload the file contents
    blob.upload_from_string(file.read(), content_type=file.content_type)

# Add metadata to Firestore
    metadata = {
        'filename': file.filename,
        'size': len(file.read()),
        'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'location': {BUCKET_NAME},
    }
    db.collection('images').add(metadata)
    # Get metadata
    #metadata = {
    #    'filename': file.filename,
    #    'size': file.size,  # Get size directly from the file object
    #    'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    #    'location': BUCKET_NAME,
    #}

    # Set metadata for the uploaded blob
    #blob.metadata = metadata
    #blob.patch()

    # Display the uploaded image dynamically on the page
    uploaded_image_html = f'''
        <p>Uploaded Image Metadata:</p>
        <p>Filename: {metadata['filename']}</p>
        <p>Size: {metadata['size']} bytes</p>
        <p>Date Added: {metadata['date_added']}</p>
        <p>Location: {metadata['location']}</p>
        <img src="/files/{secure_filename(file.filename)}" style="max-width: 500px; max-height: 500px;">
    '''
    
    return index() + uploaded_image_html

def add_default_image_link():
    default_image_link = "https://th.bing.com/th/id/R.81563b6d493a6773f758262d71277023?rik=uxKRgJB3URJm4g&pid=ImgRaw&r=0"
    return f'''
    <div>
        <p>File: Default Image</p>
        <img src="{default_image_link}" style="max-width: 500px; max-height: 500px;">
        <br>
        <a href="{default_image_link}" download="default_image.png">Download</a>
        <hr>
    </div>
    <br>
    <a href="{url_for('index')}">Back</a>
    '''

@app.route('/files/<filename>')
def get_file(filename):
    # Download the file from Google Cloud Storage
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    file_contents = blob.download_as_string()

    return send_file(
        io.BytesIO(file_contents),
        as_attachment=True,
        download_name=filename
    )

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    # Delete the file from Google Cloud Storage
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.delete()
    # Delete image metadata from Firestore
    images_ref = db.collection('images')
    query = images_ref.where('filename', '==', filename)
    for doc in query.stream():
        doc.reference.delete()

    return redirect("/")

def list_files():
    bucket = client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs()
    file_data = []
    for blob in blobs:
        file_info = {
            'filename': blob.name,
            'size': blob.size,
            'date_added': blob.time_created,
            'location': BUCKET_NAME,
        }
        file_data.append(file_info)
    return file_data

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8083)
