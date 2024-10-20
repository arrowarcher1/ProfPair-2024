import boto3
import json
from flask import Flask, render_template, jsonify, request, session
import pandas as pd
from io import StringIO
import os
import csv

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Initialize s3 and smaker
s3 = boto3.client('s3', region_name='us-west-2')
sagemaker_runtime = boto3.client('sagemaker-runtime', region_name='us-west-2')

BUCKET_NAME = 'profpairstorage'
DATA_FILE = 'professor_scores_and_tags.json'
SAGEMAKER_ENDPOINT_NAME = 'canvas-new-deployment-10-19-2024-6-03-PM'


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/review')
def review():
    return render_template('input_data.html')


@app.route('/submit_user_data', methods=['POST'])
def submit_user_data():
    user_data = {
        'study_hours': request.form.get('study_hours'),
        'credits': request.form.get('credits'),
        'stress_level': request.form.get('stress_level'),
        'office_hours': request.form.get('office_hours'),
        'extracurriculars': request.form.get('extracurriculars')
    }
    session['user_data'] = user_data
    return jsonify({"message": "Data received successfully"}), 200


@app.route('/university')
def university():
    return render_template('university.html')


def get_professor_data():
    try:
        # get from s3
        response = s3.get_object(Bucket=BUCKET_NAME, Key=DATA_FILE)
        return json.loads(response['Body'].read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching data: {str(e)}")
        return None


def create_csv_from_data(professor_data, course_professors, user_data):
    csv_data = []
    stress_level_mapping = {'Low': 0, 'Medium': 1, 'High': 2}

    for professor in course_professors:
        row = {
            'Professor': professor,
            'Study Hours': float(user_data['study_hours']),
            'Credits Taken': int(user_data['credits']),
            'Stress Level': stress_level_mapping.get(user_data['stress_level'], 1),
            'Office Hours Attended': float(user_data['office_hours']),
            'Extracurricular Hours': float(user_data['extracurriculars'])
        }
        csv_data.append(row)

    df = pd.DataFrame(csv_data)
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False, header=False)
    csv_string = csv_buffer.getvalue()

    return csv_string


def send_to_sagemaker_endpoint(csv_data):
    try:
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=SAGEMAKER_ENDPOINT_NAME,
            ContentType='text/csv',
            Body=csv_data
        )

        raw_response = response['Body'].read().decode('utf-8')

        # get data from csb
        reader = csv.reader(StringIO(raw_response))
        results = []
        for row in reader:
            if row:
                predicted_grade = row[0]  # Get predicted grade
                results.append(predicted_grade)

        return results
    except Exception as e:
        return None


@app.route('/get_scores/<course>')
def get_scores(course):
    try:
        professor_data = get_professor_data()
        if not professor_data:
            return jsonify({"error": "Failed to fetch data"}), 500

        user_data = session.get('user_data')
        if not user_data:
            return jsonify({"error": "User data not found"}), 400

        course_professors = {
            'CSE 007': ['Kim', 'Ross', 'Mclean', 'Gonzales', 'Tucker'],
            'CSE 017': ['Lee', 'Brown'],
            'CSE 109': ['White', 'Green'],
            'CSE 216': ['Black', 'Blue'],
            'CSE 303': ['Red', 'Yellow'],
        }

        if course not in course_professors:
            return jsonify({"error": "Course not found"}), 404

        csv_data = create_csv_from_data(professor_data, course_professors[course], user_data)
        sagemaker_results = send_to_sagemaker_endpoint(csv_data)

        if sagemaker_results is None:
            return jsonify({"error": "Failed to process data with SageMaker"}), 500

        response = {}
        for i, professor in enumerate(course_professors[course]):
            overall_score = professor_data.get(professor, {}).get('score', 'No score available')
            if isinstance(overall_score, (int, float)):
                overall_score = f"{overall_score:.2f}"

            if i < len(sagemaker_results):
                response[professor] = f"{overall_score} ({sagemaker_results[i]})"
            else:
                response[professor] = f"{overall_score} (No prediction available)"

        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/get_tags/<course>')
def get_tags(course):
    try:
        professor_data = get_professor_data()
        if not professor_data:
            return jsonify({"error": "Failed to fetch data"}), 500

        course_professors = {
            'CSE 007': ['Kim', 'Ross', 'Mclean', 'Gonzales', 'Tucker'],
            'CSE 017': ['Lee', 'Brown'],
            'CSE 109': ['White', 'Green'],
            'CSE 216': ['Black', 'Blue'],
            'CSE 303': ['Red', 'Yellow'],
        }

        if course not in course_professors:
            return jsonify({"error": "Course not found"}), 404

        # collect tags
        professor_tags = {}
        for professor in course_professors[course]:
            professor_tags[professor] = {
                "tags": {tag: count for tag, count in professor_data.get(professor, {}).get('tags', {}).items() if
                         count >= 5}
            }

        return jsonify(professor_tags)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
