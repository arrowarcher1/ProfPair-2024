import csv
import boto3
import json
import io
from collections import Counter


def fetch_scores_from_s3(bucket_name, file_key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=file_key)
    body = obj['Body'].read().decode('utf-8')
    return load_professors_scores(io.StringIO(body))

def load_professors_scores(file_like_object):
    professors_scores = {}
    csvreader = csv.DictReader(file_like_object)
    
    for row in csvreader:
        course = row['Course']
        professor = row['Professor']
        overall_score = row['Overall Score']
        
        if course not in professors_scores:
            professors_scores[course] = {}
        professors_scores[course][professor] = overall_score

    return professors_scores

# Initialize the Comprehend client
comprehend = boto3.client('comprehend', region_name='us-west-2')
s3 = boto3.client('s3')

def detect_sentiment(text):
    # Run AWS sent. analysis
    response = comprehend.detect_sentiment(Text=text, LanguageCode='en')
    
    # Get scores
    return response['Sentiment'], response['SentimentScore']

def classify_text(text, endpoint_arn):
    # Call custom classifier endpoint for comments
    response = comprehend.classify_document(
        Text=text,
        EndpointArn=endpoint_arn
    )

    top_class = max(response['Classes'], key=lambda x: x['Score'])
    return top_class['Name']

def calculate_professor_score(overall_rating, difficulty_rating, workload_rating, sentiment_scores):
    positive_score = sentiment_scores['Positive']
    neutral_score = sentiment_scores['Neutral']
    mixed_score = sentiment_scores['Mixed']
    
    # Weighted value of scroes
    review_comment_rating = (positive_score * 50) + (neutral_score * 30) + (mixed_score * 20)

    # scale to 100
    score = (
        (overall_rating / 5 * 40) +  ((1- difficulty_rating / 5) * 20) +  ((1- workload_rating / 5) * 20) +  (review_comment_rating)  
    )

    return score

def read_professors_from_csv(filename, endpoint_arn):
    professor_data = {}

    with open(filename, mode='r') as file:
        reader = csv.DictReader(file)

        for row in reader:
            professor_name = row['Professor']
            overall_rating = float(row['Overall Rating'])
            difficulty_rating = float(row['Difficulty'])
            workload_rating = float(row['Workload'])
            review_comment = row['review']
            
            #sent analysis forreview
            sentiment, sentiment_scores = detect_sentiment(review_comment)
            
            # get tag
            tag = classify_text(review_comment, endpoint_arn)
            
            # calc score
            score = calculate_professor_score(overall_rating, difficulty_rating, workload_rating, sentiment_scores)
            
            # aggregate scores
            if professor_name in professor_data:
                professor_data[professor_name]['scores'].append(score)
                professor_data[professor_name]['tags'].append(tag)
            else:
                professor_data[professor_name] = {
                    'scores': [score],
                    'tags': [tag]
                }

    # Overall scores and tags for all prof
    overall_professor_data = {}
    for prof, data in professor_data.items():
        avg_score = sum(data['scores']) / len(data['scores'])
        tag_counts = Counter(data['tags'])
        
        overall_professor_data[prof] = {
            'score': avg_score,
            'tags': dict(tag_counts)
        }
    
    return overall_professor_data

def upload_scores_to_s3(scores, bucket_name, file_name):
    json_data = json.dumps(scores, indent=2)
    
    #upload json with prof info to s3
    s3.put_object(Bucket=bucket_name, Key=file_name, Body=json_data)
    print(f"Scores uploaded to S3 bucket '{bucket_name}' as '{file_name}'.")


filename = 'dataset1.csv'
endpoint_arn = 'arn:aws:comprehend:us-west-2:695903889427:document-classifier-endpoint/tagextractor'
professor_data = read_professors_from_csv(filename, endpoint_arn)

# Print Scores and tag
for professor, data in professor_data.items():
    print(f"Professor: {professor}")
    print(f"  Overall Score: {data['score']:.2f}/100")
    print("  Tags:")
    for tag, count in data['tags'].items():
        print(f"    {tag}: {count}")
    print()

bucket_name = 'profpairstorage'
file_name = 'professor_scores_and_tags.json'
upload_scores_to_s3(professor_data, bucket_name, file_name)