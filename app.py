from flask import Flask, render_template, request, send_file
import os
import time
import random
import string
from pymongo import MongoClient
from datetime import datetime, timedelta

app = Flask(__name__)

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
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

@app.route('/upload', methods=['GET', 'POST'])
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
        
        download_link = f'<a href="/download/{random_text}/{filename}">Download {filename}</a>'
        return f'File uploaded successfully! {download_link}'
    
    return render_template('upload.html')

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
    threshold_time = datetime.now() - timedelta(hours=48)
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
