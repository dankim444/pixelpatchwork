import logging
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


@app.route('/goodbye')
def goodbye():
    return render_template('pages/goodbye.html')


def get_db_connection():
    """Create a connection to the RDS database"""
    return mysql.connector.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        database=RDS_DATABASE,
        user=RDS_USERNAME,
        password=RDS_PASSWORD
    )


def insert_day(image_id, today):
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        logging.info("Database successfully connected")
        logging.info(f'image_id: {image_id}')
        logging.info(f'today date: {today}')

        # first insert with NULL seed_image_id if record doesn't exist
        cursor.execute("""
            INSERT INTO Day (date, seed_image_id, total_votes, total_participants, is_current)
            SELECT %s, NULL, 0, 0, TRUE
            WHERE NOT EXISTS (SELECT 1 FROM Day WHERE date = %s)
        """, (today, today))

        db_conn.commit()
        logging.info(f"Successfully added Day record for today: {today}")

    except Exception as db_error:
        logging.error(f"Database error: {db_error}")
        raise
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db_conn' in locals():
            db_conn.close()


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
        # validate credentials
        validate_env()

        # set up OpenAI API key
        openai.api_key = OPENAI_API_KEY

        # generate image with prompt
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
            logging.error(
                f"Failed to download image: {image_response.status_code}")
            logging.error(f"Failed to download image: {
                          image_response.status_code}")
            return jsonify({'error': 'Failed to download image'}), 500

        # generate a unique image ID
        image_id = str(uuid.uuid4())

        # define the S3 path
        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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

        # insert the image and day record into the database
        logging.info(f"WHAT IS TODAYYYYYYY: {today}")
        insert_day(image_id, today)

        # return the image information
        full_image_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_path}"
        return jsonify({'imageUrl': full_image_url, 'image_id': image_id, 'day': today, 'created_at': created_at}), 200

    except openai.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        return jsonify({'error': 'Failed to generate image'}), 500

    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Failed to generate image'}), 500


@app.route('/track-user', methods=['POST'])
def track_user():
    logging.info("Endpoint /track-user was hit")
    data = request.get_json()
    user_id = data.get('user_id')
    created_at = data.get('created_at')

    if not user_id or not created_at:
        return jsonify({'error': 'Missing user_id or created_at'}), 400

    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        logging.info("Database successfully connected")
        logging.info(f'user_id: {user_id}')
        # reformat date so it can be referenced by foreign keys
        created_at = datetime.strptime(created_at, "%m/%d/%Y, %I:%M:%S %p")
        created_at = created_at.strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f'created_at: {created_at}')

        # Insert or update the user in the database
        cursor.execute("""
            INSERT INTO User (user_id, username, created_at, is_banned)
            VALUES (%s, %s, %s, FALSE)
        """, (user_id, 'Unknown', created_at))
        db_conn.commit()

        logging.info("User tracked successfully!")

        return jsonify({'message': 'User tracked successfully'}), 200
    except Exception as e:
        logging.error(f"Error tracking user: {e}")
        return jsonify({'error': 'Failed to track user'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db_conn' in locals():
            db_conn.close()


@app.route('/insert-image', methods=['POST'])
def insert_image():
    logging.info("Endpoint /insert-image was hit")
    data = request.get_json()

    try:
        image_id = data.get('image_id')
        s3_path = data.get('s3_path')
        prompt_text = data.get('prompt_text')
        creator_id = data.get('creator_id')
        day = data.get('day')
        created_at = data.get('created_at')
        upvotes = data.get('upvotes', 0)
        downvotes = data.get('downvotes', 0)
        flags = data.get('flags', 0)

        logging.info(f'image_id: {image_id}')
        logging.info(f's3_path: {s3_path}')
        logging.info(f'creator_id: {creator_id}')
        logging.info(f'day: {day}')

        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        logging.info("Database successfully connected")

        cursor.execute("""
            INSERT INTO Image (
                image_id, 
                s3_path, 
                prompt_text, 
                created_at,
                creator_id, 
                day,  
                upvotes, 
                downvotes, 
                flags
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (image_id, s3_path, prompt_text, created_at, creator_id, day, upvotes, downvotes, flags))

        # update the Day record with the image_id
        cursor.execute("""
            UPDATE Day 
            SET seed_image_id = %s
            WHERE date = %s AND seed_image_id IS NULL
        """, (image_id, day))

        db_conn.commit()

        logging.info("Successfully loaded into Image table!")

        return jsonify({'message': 'Image inserted successfully'}), 201

    except Exception as e:
        logging.error(f"Error inserting image into database: {e}")
        return jsonify({'error': 'Failed to insert image into database'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db_conn' in locals():
            db_conn.close()


@app.route('/get-images', methods=['GET'])
def get_images():
    logging.info("Endpoint /get-images was hit")
    day = request.args.get('day')

    if not day:
        return jsonify({'message': 'Day is required'}), 400

    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)

        logging.info("Database successfully connected")

        # query for images for the given day, limited to 10
        cursor.execute("""
            SELECT image_id, s3_path, prompt_text, upvotes, downvotes
            FROM Image
            WHERE day = %s
            LIMIT 10
        """, (day,))

        images = cursor.fetchall()

        if images:
            return jsonify({'images': images}), 200
        else:
            return jsonify({'message': 'Looks like there were no images from today!'}), 200

    except Exception as e:
        logging.error(f"Error fetching images: {e}")
        return jsonify({'error': 'Failed to fetch images'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db_conn' in locals():
            db_conn.close()


@app.route('/vote-image', methods=['POST'])
def vote_image():
    data = request.get_json()
    image_id = data.get('image_id')
    current_vote = data.get('current_vote')  # -1, 0, +1
    new_vote = data.get('new_vote')  # -1, 0, +1

    if not image_id or current_vote not in [-1, 0, 1] or new_vote not in [-1, 0, 1]:
        return jsonify({'error': 'Invalid image ID or vote values'}), 400

    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        # calculate the changes in upvotes and downvotes
        upvote_change = 0
        downvote_change = 0

        if current_vote == 0 and new_vote == 1:
            upvote_change = 1
        elif current_vote == 1 and new_vote == 0:
            upvote_change = -1
        elif current_vote == 1 and new_vote == -1:
            upvote_change = -1
            downvote_change = 1
        elif current_vote == 0 and new_vote == -1:
            downvote_change = 1
        elif current_vote == -1 and new_vote == 0:
            downvote_change = -1
        elif current_vote == -1 and new_vote == 1:
            downvote_change = -1
            upvote_change = 1
        # else no change

        # ensure votes don't go negative
        cursor.execute(
            "UPDATE Image SET upvotes = GREATEST(0, upvotes + %s), downvotes = GREATEST(0, downvotes + %s) WHERE image_id = %s",
            (upvote_change, downvote_change, image_id)
        )
        db_conn.commit()

        return jsonify({'message': 'Vote recorded successfully'}), 200

    except Exception as e:
        logging.error(f"Error voting on image: {e}")
        return jsonify({'error': 'Failed to record vote'}), 500
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db_conn' in locals():
            db_conn.close()


if __name__ == '__main__':
    app.run(debug=True)
