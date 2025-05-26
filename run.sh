#!/bin/bash
export FLASK_APP=app.py
export FLASK_ENV=development
# export OPENAI_API_KEY=your_key_here  # Gán ở đây nếu muốn
flask run --host=0.0.0.0 --port=5000