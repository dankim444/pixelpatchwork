# Project Overview

This project is a Flask-based web application that allows users to vote on images as part of a crowdsourcing experiment. It leverages a structured file system for static assets and templates and uses Flask as the backend framework.

---

## How the Code Runs

### 1. Setup:

- Install dependencies from requirements.txt using pip install -r requirements.txt.
- Create a .env file based on .env.example to set environment variables.
- Activate the virtual environment in the venv/ directory.

### 2. Execution:

- Run the Flask app using python app.py.
- The app serves dynamic web pages via Flask templates, with assets (CSS, JS, images) loaded from the static/ folder.

### 3. Features:

- Users can view and vote on images.
- Votes are stored persistently and dynamically update the UI.

## Planned Analysis

### 1. Accuracy of Crowd Predictions:

- Establish a “ground truth” ranking (expert-based) and measure the deviation of crowd rankings from this baseline.

### 2. Behavioral Insights:

- Track voting trends to identify user preferences and interaction patterns.
