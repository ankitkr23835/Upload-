from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, session, request, render_template, request, send_file
import os
import time
import random
import string
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
# Connect to MongoDB
client = MongoClient('mongodb+srv://ankitkr88588:air8858@cluster0.mceo1nl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client['file_upload']
uploads_collection = db['uploads']

def generate_random_string(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def generate_unique_random_string():
    while True:
        random_text = generate_random_string()
        if not uploads_collection.find_one({'filename': random_text}):
            return random_text

@app.route('/')
def index():
    return 'Welcome to the file-sharing application!'

from flask import redirect, url_for
from flask import request, Response

from werkzeug.utils import secure_filename

@app.route('/upload', methods=['GET', 'POST', 'PUT'])
def upload_file():
    if request.method == 'POST':
        # Generate a random but unique 10-digit text combination of letters and numbers
        random_text = generate_unique_random_string()

        # Create a directory with the generated text if it doesn't exist
        directory_path = os.path.join('uploads', random_text)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        
        uploaded_file = request.files['file']
        filename = uploaded_file.filename
        filename = filename.replace(" ","-")
        
        # Start time for calculating upload speed
        start_time = time.time()
        uploaded_size = 0
        
        # Open the file and save it in the generated directory to calculate speed
        with open(os.path.join(directory_path, filename), 'wb') as file:
            for chunk in uploaded_file.stream:
                file.write(chunk)
                uploaded_size += len(chunk)
                
                # Calculate upload speed
                elapsed_time = time.time() - start_time
                upload_speed = uploaded_size / (1024 * elapsed_time)  # in KB/s
                
                print(f"Uploaded {uploaded_size / 1024:.2f} KB | Speed: {upload_speed:.2f} KB/s", end='\r')
        
        print()  # Move to the next line after upload completion
        
        # Add entry to MongoDB with filename and current time
        uploads_collection.insert_one({'filename': random_text, 'time_created': datetime.now()})
        
        download_link = f'https://upload-1-hen4.onrender.com/download/{random_text}/{filename}'
        if 'User-Agent' in request.headers and 'curl' in request.headers['User-Agent']:
            return f'File uploaded successfully! Download link: {download_link}'
        else:
        # Redirect to upload_success page with download_link query parameter
            session['download_link'] = download_link
        
        # Redirect to the upload_success page
            return redirect('/upload_success')
    elif request.method == 'PUT':
        # Generate a random but unique 10-digit text combination of letters and numbers
        random_text = generate_unique_random_string()

        # Create a directory with the generated text if it doesn't exist
        directory_path = os.path.join('uploads', random_text)
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        # Extract filename from the URL
        uploaded_file = request.files['file']
        filename = uploaded_file.filename

        # Start time for calculating upload speed
        start_time = time.time()
        uploaded_size = 0

        # Open the file and save it in the generated directory to calculate speed
        file_path = os.path.join(directory_path, filename)
        with open(file_path, 'wb') as file:
            while True:
                chunk = request.stream.read(1024)
                if not chunk:
                    break
                file.write(chunk)
                uploaded_size += len(chunk)

                # Calculate upload speed
                elapsed_time = time.time() - start_time
                upload_speed = uploaded_size / (1024 * elapsed_time)  # in KB/s

                print(f"Uploaded {uploaded_size / 1024:.2f} KB | Speed: {upload_speed:.2f} KB/s", end='\r')

        print()  # Move to the next line after upload completion

        # Add entry to MongoDB with filename and current time
        uploads_collection.insert_one({'filename': random_text, 'time_created': datetime.now()})

        download_link = f'https://upload-1-hen4.onrender.com/download/{random_text}/{filename}'
        if 'User-Agent' in request.headers and 'curl' in request.headers['User-Agent']:
            return f'File uploaded successfully! Download link: {download_link}'
        else:
            # Redirect to upload_success page with download_link query parameter
            session['download_link'] = download_link

            # Redirect to the upload_success page
            return redirect('/upload_success')


    return render_template('upload.html')


        
        # Add 


@app.route('/upload_success')
def upload_success():
    # Retrieve the download link from the session
    download_link = session.get('download_link')
    return render_template('upload_success.html', download_link=download_link)
    



@app.route('/download/<directory>/<filename>')
def download_file(directory, filename):
    file_path = os.path.join('uploads', directory, filename)
    if os.path.exists(file_path):
        # Serve the file for download
        return send_file(file_path, as_attachment=True)
    else:
        return 'File not found', 404
        

def delete_old_files():
    # Delete files and directories older than 24 hours
    threshold_time = datetime.now() - timedelta(hours=168)
    old_files = uploads_collection.find({'time_created': {'$lt': threshold_time}})
    for file in old_files:
        file_path = os.path.join('uploads', file['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
        uploads_collection.delete_one({'filename': file['filename']})

if __name__ == '__main__':
    # Run the delete_old_files function periodically (every hour)
    delete_old_files()
    scheduler = BackgroundScheduler()
    scheduler.add_job(delete_old_files, 'interval', hours=1)
    scheduler.start()
    
    app.run(host="0.0.0.0", port=5000, debug=True)
