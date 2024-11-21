import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import openai
import requests
import boto3
from datetime import datetime
from config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, OPENAI_API_KEY, validate_env

# Set your API key
#Note: PLEASE DO NOT RUN THIS MORE THAN ONCE OR TWICE, IT COST LIKE 0.02 cents every time it runs

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

        # Call OpenAI's Image Generation API
        response = openai.Image.create(
            prompt=prompt,
            n=n,
            size=size,
            response_format="url" 
        )

        # Extract image URLs from the response
        image_urls = [data['url'] for data in response['data']]

        # Get current date for S3 folder
        today = datetime.now().strftime('%Y-%m-%d')
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
                    uploaded_images.append((image_id, s3_path))
                    print(f"Image {idx+1} uploaded to s3://{bucket_name}/{s3_path}")
                except Exception as e:
                    print(f"Failed to upload to S3: {e}")
            else:
                print(f"Failed to download image {idx+1}. Status Code: {image_response.status_code}")
        return uploaded_images

    except openai.error.OpenAIError as e:
        print(f"An OpenAI error occurred: {e}")
        return []
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return []

if __name__ == "__main__":
    # Define your prompt and output path
    user_prompt = "A rabbit with a clown nose"

    # Generate the image and upload to S3
    uploaded_images = generate_image(prompt=user_prompt, size="1024x1024", n=1)

    # Print results
    for image_id, s3_path in uploaded_images:
        print(f"Generated image ID: {image_id}")
        print(f"S3 path: {s3_path}")