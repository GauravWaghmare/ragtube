# Ragtube

# Ragtube

Ragtube is an intelligent video processing and question-answering system that leverages advanced AI models to transcribe audio, analyze content, and provide insightful answers to user queries about video content.

## Features

- Audio transcription from video URLs
- Text chunking for efficient processing
- Integration with advanced language models for question answering
- S3 storage for temporary audio files
- YouTube video downloading capabilities

## How It Works

1. **Video Download**: The system downloads the audio from a given YouTube video URL.
2. **Audio Transcription**: The audio is transcribed using a fast Whisper model.
3. **Text Processing**: The transcription is chunked into manageable pieces.
4. **Vectorization and Storage**: The chunks are vectorized and stored in a vector database for efficient retrieval.
5. **Question Answering**: Users can ask questions about the video content. The system queries the vector database to retrieve relevant context and uses a large language model (Meta-LLaMA 3.1) to generate answers based on this context.

## Usage

To use Ragtube, you'll need to set up the necessary environment and dependencies. Here's a basic guide:

1. Install the required packages (exact requirements to be specified in a `requirements.txt` file).
2. Set up your AWS credentials for S3 access.
3. Ensure you have the necessary API keys for the AI models used (Replicate API key).

4. Run the application using the following make commands:

   - To start the development server:
     ```
     make dev
     ```

   - To run tests:
     ```
     make test
     ```

   - To deploy the application:
     ```
     make deploy
     ```

   - To clean up deployment resources:
     ```
     make clean
     ```

These commands simplify the process of running, testing, and deploying the Ragtube application. Make sure you have `make` installed on your system and that you're in the project's root directory when running these commands.


### APIs

To do a health check
```
curl -X POST --location "https://<hostname>/<stage>/ping" \
    -H "Content-Type: application/json" \
```

To ingest a video

```
curl -X POST --location "https://<hostname>/<stage>/ingest-video" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://www.youtube.com/watch?v=9GumiLIxLMM"}'

```

To ask questions about ingested videos
```
curl -X POST --location "https://<hostname>/<stage>/ask" \
    -H "Content-Type: application/json" \
    -d '{"question": "Why does the weight of the world rests squarely on the shoulders of Ben & Jerry’s?"}'
```




