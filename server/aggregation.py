from config import *
from datetime import datetime
import mysql.connector
import boto3
import requests
import openai
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))


# Set your API key
# Note: PLEASE DO NOT RUN THIS MORE THAN ONCE OR TWICE, IT COST LIKE 0.02 cents every time it runs


def get_db_connection():
    """Create a connection to the RDS database"""
    return mysql.connector.connect(
        host=RDS_HOST,
        port=RDS_PORT,
        database=RDS_DATABASE,
        user=RDS_USERNAME,
        password=RDS_PASSWORD
    )


def generate_image(prompt, size="1024x1024", n=1):
    """
    Generates an image from a prompt using OpenAI's DALL·E API and saves it to s3.

    Parameters:
    - prompt (str): The textual description of the image you want to generate.
    - size (str): The size of the generated image. Options: "256x256", "512x512", "1024x1024".
    - n (int): Number of images to generate.
    """
    try:
        # Validate environment variables
        validate_env()

        # Set OpenAI API key
        openai.api_key = OPENAI_API_KEY

        # Initialize S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )
        bucket_name = 'pixelspatchwork'

        # Get database connection
        db_conn = get_db_connection()
        cursor = db_conn.cursor()

        # Make sure we have a Day record for today
        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute("""
            INSERT IGNORE INTO Day (date, total_votes, total_participants, is_current)
            VALUES (%s, 0, 0, TRUE)
        """, (today,))
        db_conn.commit()

        # Call OpenAI's Image Generation API
        response = openai.Image.create(
            prompt=prompt,
            n=n,
            size=size,
            response_format="url"
        )

        # Extract image URLs from the response
        image_urls = [data['url'] for data in response['data']]
        uploaded_images = []

        # Download and save each image
        for idx, url in enumerate(image_urls):
            image_response = requests.get(url)
            if image_response.status_code == 200:

                # Generate unique image ID using timestamp
                image_id = f"{int(datetime.now().timestamp())}_{idx}"

                # Define S3 path
                s3_path = f'daily-submissions/{today}/{image_id}.png'

                # Upload to S3
                try:
                    s3.put_object(
                        Bucket=bucket_name,
                        Key=s3_path,
                        Body=image_response.content,
                        ContentType='image/png'
                    )

                    # Insert into database
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
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        image_id,
                        s3_path,
                        prompt,
                        'default_user',  # Placeholder user ID
                        today,
                        0,  # Initial upvotes
                        0,  # Initial downvotes
                        0   # Initial flags
                    ))
                    db_conn.commit()

                    uploaded_images.append((image_id, s3_path))
                    print(
                        f"Image {idx+1} uploaded to s3://{bucket_name}/{s3_path} and saved to database")
                except Exception as e:
                    print(f"Failed to upload to S3: {e}")
            else:
                print(f"Failed to download image {
                      idx+1}. Status Code: {image_response.status_code}")

        return uploaded_images

    except openai.error.OpenAIError as e:
        print(f"An OpenAI error occurred: {e}")
        return []
    except mysql.connector.Error as e:
        print(f"Database error occurred: {e}")
        return []
    except Exception as e:
        print(f"Failed to upload to S3 or database: {e}")
        db_conn.rollback()
        return []
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'db_conn' in locals() and db_conn:
            db_conn.close()


if __name__ == "__main__":
    # Define your prompt and output path
    user_prompt = "A rabbit with a clown nose"

    # Generate the image and upload to S3
    uploaded_images = generate_image(prompt=user_prompt, size="1024x1024", n=1)

    # Print results
    for image_id, s3_path in uploaded_images:
        print(f"Generated image ID: {image_id}")
        print(f"S3 path: {s3_path}")
