from flask import Flask, render_template, request
import boto3
import os

app = Flask(__name__)

# AWS S3 Configuration
AWS_REGION = 'ap-south-1'
BUCKET_NAME = 'rekognitionimg-testbucket'  # S3 bucket name
s3_client = boto3.client('s3', region_name=AWS_REGION)
rekognition_client = boto3.client('rekognition', region_name=AWS_REGION)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_to_s3', methods=['POST'])
def upload_to_s3():
    # Check if all required fields are provided
    if not all(key in request.form for key in ['name', 'pan', 'aadhar']):
        return "Please provide name, PAN, and Aadhaar information."

    if 'source_image' not in request.files or 'target_image' not in request.files:
        return "Please upload both source and target images."

    # Get the metadata from the form
    name = request.form['name']
    pan = request.form['pan']
    aadhar = request.form['aadhar']

    # Get uploaded files
    source_file = request.files['source_image']
    target_file = request.files['target_image']

    # Generate new filenames based on metadata
    source_new_name = f"{name}_PAN-{pan}.jpg"
    target_new_name = f"{name}_Aadhaar-{aadhar}.jpg"

    try:
        # Upload files to S3 with the new names
        s3_client.upload_fileobj(source_file, BUCKET_NAME, source_new_name)
        s3_client.upload_fileobj(target_file, BUCKET_NAME, target_new_name)
# Call Rekognition API to compare faces
        response = rekognition_client.compare_faces(
            SourceImage={
                'S3Object': {'Bucket': BUCKET_NAME, 'Name': source_new_name}
            },
            TargetImage={
                'S3Object': {'Bucket': BUCKET_NAME, 'Name': target_new_name}
            },
            SimilarityThreshold=80
        )

        # Process the response
        if response['FaceMatches']:
            result = []
            for face_match in response['FaceMatches']:
                similarity = face_match['Similarity']
                result.append(f"Match Found with {similarity}% similarity!")
            face_result = '<br>'.join(result)
        else:
            face_result = "No face matches found."

        return (f"Files uploaded to S3 successfully!<br>"
                f"Source Image: {source_new_name}<br>"
                f"Target Image: {target_new_name}<br><br>"
                f"Face Comparison Result:<br>{face_result}")

    except Exception as e:
        return f"An error occurred: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
