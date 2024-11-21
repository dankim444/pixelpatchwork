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


@app.route('/submit-image', methods=['POST'])
def submit_image():
    data = request.get_json()
    image_id = data.get('image_id')
    s3_path = data.get('s3_path')
    prompt_text = data.get('prompt_text')
    creator_id = data.get('creator_id', 'default_user') # Replace with actual user authentication later
    day = data.get('day')

    # validate required fields
    if not (image_id and s3_path and prompt_text and day):
        logging.warning("Missing required fields in /submit-image request")
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # connect to db
        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        # insert the image data into the Image table
        cursor.execute("""
            INSERT INTO Image (
                image_id, 
                s3_path, 
                prompt_text, 
                creator_id,
                day,
                upvotes,
                downvotes,
                flags
            ) VALUES (%s, %s, %s, %s, %s, 0, 0, 0)
        """, (image_id, s3_path, prompt_text, creator_id, day))
        db_conn.commit()

        logging.info(
            f"Image {image_id} successfully submitted to the database")
        return jsonify({'message': 'Image submitted successfully'}), 200

    except Exception as e:
        logging.error(f"Error in /submit-image: {e}")
        return jsonify({'error': 'Failed to submit image'}), 500

    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db_conn' in locals() and db_conn:
            db_conn.close()


if __name__ == '__main__':
    app.run(debug=True)
