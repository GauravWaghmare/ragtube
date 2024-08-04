import json
import os
from datetime import datetime, timedelta
from uuid import uuid4

import boto3
import replicate
import yt_dlp
from botocore.exceptions import ClientError
from chalice import Chalice
from transformers import AutoTokenizer
from pinecone.grpc import PineconeGRPC as Pinecone
from ragtube.db import INDEX_NAME

VIDEO_BUCKET = os.environ['VIDEO_BUCKET']
EMBEDDING_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"

app = Chalice(app_name='ragtube')
s3 = boto3.client('s3')

pc = Pinecone(api_key=os.environ['PINECONE_API_KEY'])
index = pc.Index(INDEX_NAME)


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """
    Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        print(f"Error: {e}")
        return None

    return response


def insert_embeddings_into_db(url, chunks, embeddings):
    index.upsert(vectors=[{"id": str(uuid4()),
                           "values": embedding,
                           "metadata": {
                               "url": url,
                               "chunk": chunk
                           }} for chunk, embedding in zip(chunks, embeddings)], )


def query_embeddings_from_db(embedding):
    output = index.query(
        vector=embedding,
        top_k=3,
        include_values=True
    )
    return output["matches"]


def fetch_records_from_db(ids):
    records = index.fetch(ids)
    return records["vectors"].values()


def calculateEmbeddingsForBatch(chunk_texts):
    output = replicate.run(
        "replicate/all-mpnet-base-v2:b6b7585c9640cd7a9572c6e129c9549d79c9c31f0d3fdce7baac7c67ca38f305",
        input={
            "text_batch": json.dumps(chunk_texts)
        }
    )
    return map(lambda x: x['embedding'], output)


def calculateEmbeddings(chunk_text):
    output = replicate.run(
        "replicate/all-mpnet-base-v2:b6b7585c9640cd7a9572c6e129c9549d79c9c31f0d3fdce7baac7c67ca38f305",
        input={
            "text": json.dumps(chunk_text)
        }
    )
    return output[0]['embedding']


def chunkText(audioText):
    tokenizer = AutoTokenizer.from_pretrained(EMBEDDING_MODEL_NAME)

    # Tokenize the full paragraph
    token_ids = tokenizer.encode(audioText)

    # Split into chunks with overlap
    chunk_size = 512
    overlap = 50
    chunks = []
    for i in range(0, len(token_ids), chunk_size - overlap):
        chunk = token_ids[i:i + chunk_size]
        chunks.append(chunk)

    # Convert chunks back to text
    chunk_texts = [tokenizer.decode(chunk) for chunk in chunks]
    return chunk_texts


def transcribeAudio(url):
    output = replicate.run(
        "vaibhavs10/incredibly-fast-whisper:3ab86df6c8f54c11309d4d1f930ac292bad43ace52d10c80d87eb258b3c9f79c",
        input={
            "task": "transcribe",
            "audio": url,
            "language": "english",
            "timestamp": "chunk",
            "batch_size": 64,
            "diarise_audio": False
        }
    )

    audioText = output["text"]
    return audioText


def upload_audio_to_s3(filepath):
    object_name = filepath.split('/')[-1]

    # Calculate expiration date
    expiration_date = datetime.utcnow() + timedelta(hours=1)
    expiration_string = expiration_date.strftime('%Y-%m-%dT%H:%M:%SZ')

    s3.upload_file(filepath, VIDEO_BUCKET, object_name, ExtraArgs={
        'Expires': expiration_date,
        'Metadata': {'expiry-date': expiration_string}
    })
    s3_url = create_presigned_url(VIDEO_BUCKET, object_name)
    # Delete file at filepath
    os.remove(filepath)
    return s3_url


def download_video_in_record(video_url):
    filepath = f"./{uuid4()}.m4a"
    # YouTube(url).streams.get_audio_only().download()
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': filepath,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    return filepath


def fetch_answer(chunks, question):
    # The meta/meta-llama-3.1-405b-instruct model can stream output as it's running.
    result = []
    for event in replicate.stream(
            "meta/meta-llama-3.1-405b-instruct",
            input={
                "top_k": 50,
                "top_p": 0.9,
                "prompt": question,
                "max_tokens": 1024,
                "min_tokens": 0,
                "temperature": 0.6,
                "system_prompt": f"Given the following context, {' '.join(chunks)}",
                "presence_penalty": 0,
                "frequency_penalty": 0
            },
    ):
        result.append(str(event))
    return ''.join(result)
