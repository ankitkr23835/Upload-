from flask import Flask, render_template, request,send_file
import os
import time

app = Flask(__name__)

@app.route('/')
def index():
    return 'Welcome to the file-sharing application!'

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Create the 'uploads' directory if it doesn't exist
        if not os.path.exists('uploads'):
            os.makedirs('uploads')
        
        uploaded_file = request.files['file']
        filename = uploaded_file.filename
        
        # Start time for calculating upload speed
        start_time = time.time()
        uploaded_size = 0
        
        # Open the file and save it in chunks to calculate speed
        with open(os.path.join('uploads', filename), 'wb') as file:
            for chunk in uploaded_file.stream:
                file.write(chunk)
                uploaded_size += len(chunk)
                
                # Calculate upload speed
                elapsed_time = time.time() - start_time
                upload_speed = uploaded_size / (1024 * elapsed_time)  # in KB/s
                
                print(f"Uploaded {uploaded_size / 1024:.2f} KB | Speed: {upload_speed:.2f} KB/s", end='\r')
        
        print()  # Move to the next line after upload completion
        return 'File uploaded successfully!'
    
    return render_template('upload.html')
@app.route('/download/<filename>')
def download_file(filename):
    # Serve the file for download
    return send_file('uploads/' + filename, as_attachment=True)
    
if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000,debug=True)
