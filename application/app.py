from flask import Flask, render_template, request, jsonify
import os

# Initializing Flask app
app = Flask(__name__)

# Defining the folder for saving uploaded files
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)



# Route to render the HTML page
@app.route('/')
def index():
    return render_template('index.html')



# Route to process the prompt and return NER results
@app.route('/submit-prompt', methods=['POST'])
def submit_prompt():
    prompt = request.form.get('prompt')

    if prompt:
        # Run the NER model on the input prompt
        ner_results = nlp(prompt)

        # Return the NER results as JSON
        return jsonify({'response': ner_results})
    else:
        return jsonify({'response': 'No prompt provided'}), 400


# Route to handle file uploads
@app.route('/upload-file', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'response': 'No file part'})
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'response': 'No selected file'})

    if file and file.filename.endswith('.txt'):
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        return jsonify({'response': f'File uploaded successfully: {file.filename}'})
    
    return jsonify({'response': 'Invalid file type. Please upload a .txt file.'})

if __name__ == '__main__':
    app.run(debug=True)
