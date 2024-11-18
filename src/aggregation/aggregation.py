import os
import openai
import requests
from PIL import Image

# Set your API key
#Note: PLEASE DO NOT RUN THIS MORE THAN ONCE OR TWICE, IT COST LIKE 0.02 cents every time it runs

def generate_image(prompt, output_path, size="1024x1024", n=1):
    """
    Generates an image from a prompt using OpenAI's DALL·E API and saves it locally.

    Parameters:
    - prompt (str): The textual description of the image you want to generate.
    - output_path (str): The file path where the generated image will be saved.
    - size (str): The size of the generated image. Options: "256x256", "512x512", "1024x1024".
    - n (int): Number of images to generate.
    """
    try:
        # Set OpenAI API key

        if not openai.api_key:
            raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")

        # Call OpenAI's Image Generation API
        response = openai.Image.create(
            prompt=prompt,
            n=n,
            size=size,
            response_format="url"  # Can also be "b64_json" if you prefer base64
        )

        # Extract image URLs from the response
        image_urls = [data['url'] for data in response['data']]

        # Download and save each image
        for idx, url in enumerate(image_urls):
            image_response = requests.get(url)
            if image_response.status_code == 200:
                with open(f"{output_path}_{idx+1}.png", "wb") as f:
                    f.write(image_response.content)
                print(f"Image {idx+1} saved to {output_path}_{idx+1}.png")
            else:
                print(f"Failed to download image {idx+1}. Status Code: {image_response.status_code}")

    except openai.error.OpenAIError as e:
        print(f"An OpenAI error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # Define your prompt and output path
    user_prompt = "A rabbit with a clown nose"
    output_file = "/Users/jasonfigueroa/Nets2130-Project/src/output_image.png"

    # Generate the image
    generate_image(prompt=user_prompt, output_path=output_file, size="1024x1024", n=1)

