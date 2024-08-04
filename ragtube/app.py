import json
import os

import boto3
from chalice import Chalice, Response
import ragtube.helper as helper

app = Chalice(app_name='ragtube')
sqs = boto3.client('sqs')

SQS_QUEUE_ARN = os.environ['SQS_QUEUE_ARN']
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']


# TODO Add authentication to all http endpoints as described here https://aws.github.io/chalice/api.html#authorization

@app.route('/ping', methods=['POST'])
def index():
    return Response(body='pong',
                    status_code=200,
                    headers={'Content-Type': 'text/plain'})


@app.route('/ingest-video', methods=['POST'])
def ingest_video():
    # This is the JSON body the user sent in their POST request.
    request_body = app.current_request.json_body
    # We'll echo the json body back to the user in a 'user' key.
    url: str = request_body['url']
    if not url:
        return Response(body={'error': 'url is empty'},
                        status_code=400,
                        headers={'Content-Type': 'application/json'})

    message = request_body.get('url', url)

    # Send message to SQS queue
    response = sqs.send_message(
        QueueUrl=SQS_QUEUE_URL,
        MessageBody=message
    )
    return Response(body={'error': None},
                    status_code=201,
                    headers={'Content-Type': 'application/json'})


@app.on_sqs_message(queue_arn=SQS_QUEUE_ARN)
def handler(event):
    for record in event:
        video_url = json.loads(record.body)['url']
        # Download video/audio
        filepath = helper.download_video_in_record(video_url)
        # Upload audio file to s3
        url = helper.upload_audio_to_s3(filepath)
        # Transcribe audio
        audio_text = helper.transcribeAudio(url)
        # Chunk audio text
        chunk_texts = helper.chunkText(audio_text)
        # Calculate embeddings for audioText using bge-large-en-v1.5 on replicate.com
        embeddings = helper.calculateEmbeddingsForBatch(chunk_texts)
        # Insert embeddings into Turso DB
        helper.insert_embeddings_into_db(video_url, chunk_texts, embeddings)


@app.route('/ask', methods=['POST'])
def ask():
    request_body = app.current_request.json_body
    question = request_body['question']
    # Query the vector database for text related to the question
    embedding = helper.calculateEmbeddings(question)
    results = helper.query_embeddings_from_db(embedding)
    values = helper.fetch_records_from_db(list(result['id'] for result in results))
    chunks = [value['metadata']['chunk'] for value in values]
    answer = helper.fetch_answer(chunks, question)
    return Response(body=json.dumps({"answer": answer}), headers={'Content-Type': 'application/json'})

