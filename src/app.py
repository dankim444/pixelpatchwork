import logging
from aggregation import *
from flask_cors import CORS
from flask import request, jsonify, Flask, render_template
import sys

import uuid
from config import *
from datetime import datetime
import mysql.connector
import boto3
import requests
import openai
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)
bucket_name = 'pixelspatchwork'


@app.route('/')
def test():
    return render_template('index.html')


@app.route('/generate')
def generate():
    return render_template('pages/generate.html')


@app.route('/vote')
def vote():
    return render_template('pages/vote.html')


@app.route('/generate-image', methods=['POST'])
def generate_image_endpoint():
    logging.info("Endpoint /generate-image was hit")

    # extract the prompt from the request
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        logging.warning("Prompt is missing in the request")
        return jsonify({'error': 'Prompt is required'}), 400

    try:
        # set up OpenAI API key
        openai.api_key = OPENAI_API_KEY

        # call api
        response = openai.images.generate(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        logging.info("Image generated successfully using OpenAI's API.")

        # extract url
        image_url = response.data[0].url
        logging.info(f"Image URL: {image_url}")

        # download image
        image_response = requests.get(image_url)
        if image_response.status_code != 200:
            logging.error(f"Failed to download image: {
                          image_response.status_code}")
            return jsonify({'error': 'Failed to download image'}), 500

        # generate a unique image ID
        image_id = str(uuid.uuid4())

        # define the S3 path
        today = datetime.now().strftime('%Y-%m-%d')
        s3_path = f'daily-submissions/{today}/{image_id}.png'

        # upload the image to S3
        s3_client = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_path,
            Body=image_response.content,
            ContentType='image/png',
        )
        logging.info(f"Image uploaded successfully to S3: {s3_path}")

        # return the image information
        full_image_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_path}"
        logging.info(f"url: {full_image_url}")
        return jsonify({'imageUrl': full_image_url, 'image_id': image_id})

    except openai.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        return jsonify({'error': 'Failed to generate image'}), 500

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Failed to generate image'}), 500


if __name__ == '__main__':
    app.run(debug=True)
