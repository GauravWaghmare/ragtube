import json
import os

import boto3
from chalice import Chalice, Response, CORSConfig
from chalicelib import helper

app = Chalice(app_name='ragtube')
sqs = boto3.client('sqs')

SQS_QUEUE_ARN = os.environ['SQS_QUEUE_ARN']
SQS_QUEUE_URL = os.environ['SQS_QUEUE_URL']

# TODO Add authentication to all http endpoints as described here https://aws.github.io/chalice/api.html#authorization

cors_config = CORSConfig(
    allow_origin='http://localhost:3000',
    allow_headers=['X-Special-Header', 'Content-Type'],
    max_age=600,
    expose_headers=['X-Special-Header'],
    allow_credentials=True
)


@app.route('/ping', methods=['POST'])
def index():
    return Response(body='pong',
                    status_code=200,
                    headers={'Content-Type': 'text/plain'})


@app.route('/ingest-video', methods=['POST'], cors=cors_config)
def ingest_video():
    # This is the JSON body the user sent in their POST request.
    request_body = app.current_request.json_body
    # We'll echo the json body back to the user in a 'user' key.
    url: str = request_body['url']
    if not url:
        return Response(body={'error': 'url is empty'},
                        status_code=400,
                        headers={'Content-Type': 'application/json'})

    message = json.dumps({'url': url})
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
        app.log.info(f"Starting download of {video_url} video")
        filepath = helper.download_video_in_record(video_url)
        app.log.info(f"Finished download of {video_url} video")
        # Upload audio file to s3
        app.log.info(f"Starting upload to s3 of {video_url} video")
        url = helper.upload_audio_to_s3(filepath)
        app.log.info(f"Finished upload to s3 of {video_url} video")
        # Transcribe audio
        app.log.info(f"Starting transcribe of {video_url} video")
        audio_text = helper.transcribeAudio(url)
        app.log.info(f"Finished transcribe of {video_url} video")
        # Chunk audio text
        app.log.info(f"Starting chunking of transcription of {video_url} video")
        chunk_texts = helper.chunkText(audio_text)
        app.log.info(f"Finished chunking of transcription of {video_url} video")
        # Calculate embeddings for audioText using bge-large-en-v1.5 on replicate.com
        app.log.info(f"Starting calculation of embeddings of {video_url} video")
        embeddings = helper.calculateEmbeddingsForBatch(chunk_texts)
        app.log.info(f"Finished calculation of embeddings of {video_url} video")
        # Insert embeddings into Turso DB
        app.log.info(f"Starting insertion of embeddings of {video_url} video")
        helper.insert_embeddings_into_db(video_url, chunk_texts, embeddings)
        app.log.info(f"Finished insertion of embeddings of {video_url} video")


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
