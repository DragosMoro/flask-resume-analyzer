import PyPDF2
import boto3
from flask_cors import CORS
import io
from dotenv import load_dotenv
from flask import Flask, request, jsonify, Response
from service import udemy_service, s3_service
import spacy
from spacy.matcher import PhraseMatcher
import os
from service.classifier_service.classifier_service import classify_resume
from skill_extractor.general_params import SKILL_DB
from skill_extractor.skill_extractor_class import SkillExtractor

nlp = spacy.load("en_core_web_sm")
load_dotenv()

s3_client = boto3.client(
    's3',
    region_name=os.getenv('AWS_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def create_app():
    app = Flask(__name__)
    CORS(app)

    skill_extractor = SkillExtractor(nlp, SKILL_DB, PhraseMatcher)

    @app.route('/analyze', methods=['POST'])
    def process_and_analyze():
        print("Received a request to analyze.")

        # Check if the file part is present in the request
        if 'file' not in request.files:
            print("Error: No file part in request.")
            return jsonify(success=False, message="No file part"), 400

        file = request.files['file']

        # Check if a filename is not empty (file is selected)
        if file.filename == '':
            print("Error: No file selected.")
            return jsonify(success=False, message="No selected file"), 400

        # Check if the job description is provided
        if 'job_description' not in request.form:
            print("Error: No job description provided.")
            return jsonify(success=False, message="No job description provided"), 400

        job_description = request.form['job_description']
        # Process the file if it's allowed
        if file and allowed_file(file.filename):
            success, message, filename = s3_service.upload_file(file)
            if not success:
                return jsonify(success=success, message=message), 500

            resume, content_type = s3_service.get_file(filename)
            if resume is None:
                return jsonify(success=False, message=content_type), 500

            resume = read_resume(io.BytesIO(resume))

            # print(resume)

            # Classify the resume to get missing skills
            result = skill_extractor.process_resume_and_job_description(resume, job_description)
            # print(f"Classified Results: {result}")

            # Fetch course details for missing hard skills
            res = udemy_service.get_course_details(result['missing_hard_skills'])
            # print(f"Udemy Courses Response: {res}")

            merged_result = {
                'udemy_courses': res,
                'missing_hard_skills': result['missing_hard_skills'],
                'missing_soft_skills': result['missing_soft_skills']
            }

            print("Sending merged result.")
            return jsonify(merged_result)
        else:
            print("File not allowed.")
            return jsonify(message="File not allowed"), 400

    @app.route('/classify', methods=['POST'])
    def process_and_classify():
        # Check if the file part is present in the request
        if 'file' not in request.files:
            print("Error: No file part in request.")
            return jsonify(success=False, message="No file part"), 400

        file = request.files['file']

        # Check if a filename is not empty (file is selected)
        if file.filename == '':
            print("Error: No file selected.")
            return jsonify(success=False, message="No selected file"), 400

        # Process the file if it's allowed
        if file and allowed_file(file.filename):
            success, message, filename = s3_service.upload_file(file)
            if not success:
                return jsonify(success=success, message=message), 500

            resume, content_type = s3_service.get_file(filename)
            if resume is None:
                return jsonify(success=False, message=content_type), 500

            resume_text = read_resume(io.BytesIO(resume))

            # Classify the resume to get top matches and skills
            top_matches = classify_resume(resume_text)
            print(top_matches)
            print("Sending merged result.")
            return jsonify(top_matches)
        else:
            print("File not allowed.")
            return jsonify(message="File not allowed"), 400

    return app


def allowed_file(filename):
    # Checks if the file has an extension and if it ends with '.pdf'
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'


def read_resume(file_stream):
    try:
        pdf_reader = PyPDF2.PdfReader(file_stream)
        resume_text = ''
        for page in pdf_reader.pages:
            resume_text += page.extract_text()
        return resume_text
    except Exception as e:
        return str(e)
