import logging
from aggregation import generate_image
from flask_cors import CORS
from flask import request, jsonify, Flask, render_template
import sys
sys.path.append('.')


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
    data = request.get_json()
    prompt = data.get('prompt')
    if not prompt:
        logging.warning("Prompt is missing in the request")
        return jsonify({'error': 'Prompt is required'}), 400

    images = generate_image(prompt=prompt, size="1024x1024", n=1)
    if images:
        image_id, s3_path = images[0]
        image_url = f"https://{bucket_name}.s3.amazonaws.com/{s3_path}"
        logging.info(f"Image generated successfully: {image_url}")
        return jsonify({'imageUrl': image_url})
    else:
        logging.error("Failed to generate image")
        return jsonify({'error': 'Failed to generate image'}), 500


if __name__ == '__main__':
    app.run(debug=True)
