# Agentic Math Tutor

An interactive math tutoring application that uses GPT-4o to provide personalized feedback and guidance to students. The app combines structured math problems with AI-powered tutoring to create an engaging learning experience.

## Features

- Interactive problem-solving interface
- AI-powered personalized feedback
- Progressive hint system
- Detailed solution explanations
- Progress tracking
- Modern, user-friendly interface

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd agentic_math_tutor
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file in the project root and add your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the application:
```bash
python dash_app.py
```

The app will be available at `http://127.0.0.1:8051`

## Technology Stack

- Python
- Dash (for web interface)
- OpenAI GPT-4o (for AI tutoring)
- JSON (for problem data storage)

## Project Structure

- `dash_app.py`: Main application file
- `problems.json`: Math problems database
- `.env`: Environment variables (not tracked in git)
- `requirements.txt`: Project dependencies
