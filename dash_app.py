#!/usr/bin/env python3
import dash
from dash import dcc, html, Input, Output, State
import json
import os
from openai import OpenAI
from dotenv import load_dotenv
from db_utils import DatabaseManager

# Load environment variables
load_dotenv(override=True)  # Add override=True to force it to take precedence

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Warning: No API key found in environment, please set OPENAI_API_KEY")
    exit(1)

# Initialize OpenAI client and database
client = OpenAI(api_key=api_key)
db = DatabaseManager()

# Initialize the Dash app with external stylesheets
app = dash.Dash(__name__, 
    external_stylesheets=[
        'https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap'
    ]
)

# Add custom CSS for animations
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Add custom CSS here */
            .problem-text {
                font-size: 1.2em;
                line-height: 1.6;
                margin-bottom: 1.5rem;
            }
            .problem-number {
                text-align: center;
                margin-bottom: 1.5rem;
                background-color: rgba(255, 255, 255, 0.6);
                padding: 0.75rem;
                border-radius: 8px;
                backdrop-filter: blur(8px);
            }
            .stats-card {
                margin-bottom: 2rem;
                padding: 1.5rem;
                border-radius: 12px;
                background-color: rgba(255, 255, 255, 0.6);
                backdrop-filter: blur(8px);
                display: flex;
                flex-wrap: wrap;
                gap: 2rem;
                justify-content: space-around;
                align-items: center;
            }
            .feedback-area {
                margin-bottom: 1.5rem;
                padding: 1.5rem;
                border-radius: 12px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.title = "Math Tutor Dashboard"

# Load problems from JSON file
with open("problems.json", "r") as f:
    problems_data = json.load(f)["problems"]

def get_problem(problem_number):
    """Retrieve problem data by problem number."""
    for prob in problems_data:
        if prob["problem_number"] == problem_number:
            return prob
    return None

def evaluate_answer(user_id, problem, user_answer):
    """Use GPT-4o to evaluate the answer and provide personalized feedback using RAG."""
    # Get user's chat history and stats
    chat_history = db.get_chat_history(user_id)
    user_stats = db.get_user_stats(user_id)
    challenging_problems = db.get_challenging_problems(user_id)
    
    # Construct the prompt with problem context and user history
    messages = [
        {"role": "system", "content": """You are a helpful and encouraging math tutor. Your goal is to:
1. Evaluate if the student's answer is correct
2. Provide encouraging feedback based on their history
3. If the answer is wrong, give a helpful hint without giving away the answer
4. Reference their past performance when relevant
5. Keep responses concise and focused"""},
        {"role": "user", "content": f"""Problem: {problem['problem']}
Available hints:
{json.dumps(problem['hints'], indent=2)}
Correct solutions:
{json.dumps(problem['solutions'], indent=2)}
Student's answer: {user_answer}

Student's History:
- Total problems attempted: {len(user_stats)}
- Most challenging problems: {challenging_problems}
- Recent interactions: {json.dumps(chat_history, indent=2)}

Evaluate the answer and provide personalized feedback."""}
    ]
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        feedback = response.choices[0].message.content
        
        # Log the interaction
        db.log_chat(user_id, problem["problem_number"], "user", user_answer)
        db.log_chat(user_id, problem["problem_number"], "assistant", feedback)
        
        return feedback
    except Exception as e:
        return f"Error evaluating answer: {str(e)}"

# Layout with login page
app.layout = html.Div([
    # URL Location (only define it once at the top level)
    dcc.Location(id='url', refresh=False),
    
    # Login page
    html.Div(id='login-page', children=[
        html.H1("Welcome to Math Tutor", style={
            "textAlign": "center",
            "marginBottom": "2rem",
            "color": "#2c3e50",
            "fontFamily": "'Poppins', sans-serif",
            "fontWeight": "600"
        }),
        
        dcc.Input(
            id='username-input',
            type='text',
            placeholder='Enter your name',
            style={
                "width": "100%",
                "maxWidth": "300px",
                "padding": "1rem",
                "marginBottom": "1.5rem",
                "borderRadius": "8px",
                "fontSize": "1.1em",
                "backgroundColor": "rgba(255, 255, 255, 0.75)",
                "backdropFilter": "blur(8px)",
                "border": "2px solid rgba(255, 255, 255, 0.2)",
                "display": "block",
                "margin": "0 auto 1.5rem auto"
            }
        ),
        
        html.Button('START LEARNING', 
            id='login-button',
            n_clicks=0,
            style={
                "backgroundColor": "rgba(0, 123, 255, 0.9)",
                "color": "white",
                "border": "none",
                "padding": "1rem 2rem",
                "borderRadius": "8px",
                "cursor": "pointer",
                "fontSize": "0.9em",
                "fontWeight": "500",
                "letterSpacing": "0.5px",
                "textTransform": "uppercase",
                "display": "block",
                "margin": "0 auto",
                "fontFamily": "'Poppins', sans-serif"
            }
        )
    ], style={
        "maxWidth": "600px",
        "margin": "4rem auto",
        "padding": "0 1.5rem"
    }),
    
    # Main app
    html.Div(id='main-app', style={"display": "none"}, children=[
        # Stats container
        html.Div([
            html.Div(className="card stats-card", style={
                "marginBottom": "2rem",
                "padding": "1.5rem",
                "borderRadius": "12px",
                "backgroundColor": "rgba(255, 255, 255, 0.6)",
                "backdropFilter": "blur(8px)",
                "display": "flex",
                "flexWrap": "wrap",
                "gap": "2rem",
                "justifyContent": "space-around",
                "alignItems": "center"
            }, children=[
                # Welcome message
                html.Div([
                    html.H3("Welcome back!", style={"margin": "0", "fontSize": "1.4em"}),
                    html.Div(id="user-info", style={"fontSize": "1.1em"})
                ]),
                
                # Problems attempted
                html.Div([
                    html.H3("Your Progress", style={"margin": "0", "fontSize": "1.4em"}),
                    html.Div(id="user-stats", style={"fontSize": "1.1em"})
                ]),
                
                # Success rate
                html.Div([
                    html.Div(id="problem-stats", style={"fontSize": "1.1em"})
                ])
            ])
        ]),
        
        # Main content container
        html.Div([
            # Header
            html.H1("Math Tutor", style={
                "textAlign": "center",
                "marginBottom": "2rem",
                "color": "#2c3e50"
            }),
            
            # Problem number indicator
            html.Div(id="progress-indicator", className="problem-number", style={
                "textAlign": "center",
                "marginBottom": "1.5rem",
                "backgroundColor": "rgba(255, 255, 255, 0.6)",
                "padding": "0.75rem",
                "borderRadius": "8px",
                "backdropFilter": "blur(8px)"
            }),
            
            # Problem card
            html.Div([
                html.Div(id="problem-area", className="problem-text", style={
                    "fontSize": "1.2em",
                    "lineHeight": "1.6",
                    "marginBottom": "1.5rem"
                })
            ], className="card problem-card", style={
                "padding": "2rem",
                "borderRadius": "12px",
                "marginBottom": "2rem"
            }),

            # Input and controls
            html.Div([
                dcc.Input(
                    id="answer-input",
                    type="text",
                    placeholder="Enter your answer here",
                    style={
                        "width": "100%",
                        "padding": "1rem",
                        "marginBottom": "1.5rem",
                        "borderRadius": "8px",
                        "fontSize": "1.1em",
                        "backgroundColor": "rgba(255, 255, 255, 0.75)",
                        "backdropFilter": "blur(8px)"
                    }
                ),

                # Button group
                html.Div([
                    html.Button("Get Hint", id="get-hint", n_clicks=0, style={
                        "backgroundColor": "rgba(23, 162, 184, 0.9)",
                        "color": "white",
                        "border": "none",
                        "padding": "1rem 2rem",
                        "borderRadius": "8px",
                        "cursor": "pointer",
                        "fontSize": "0.9em",
                        "fontWeight": "500",
                        "letterSpacing": "0.5px",
                        "textTransform": "uppercase"
                    }),
                    html.Button("Submit Answer", id="submit-answer", n_clicks=0, style={
                        "backgroundColor": "rgba(40, 167, 69, 0.9)",
                        "color": "white",
                        "border": "none",
                        "padding": "1rem 2rem",
                        "borderRadius": "8px",
                        "cursor": "pointer",
                        "fontSize": "0.9em",
                        "fontWeight": "500",
                        "letterSpacing": "0.5px",
                        "textTransform": "uppercase"
                    }),
                    html.Button("See Solution", id="see-solution", n_clicks=0, style={
                        "backgroundColor": "rgba(255, 193, 7, 0.9)",
                        "color": "black",
                        "border": "none",
                        "padding": "1rem 2rem",
                        "borderRadius": "8px",
                        "cursor": "pointer",
                        "fontSize": "0.9em",
                        "fontWeight": "500",
                        "letterSpacing": "0.5px",
                        "textTransform": "uppercase"
                    }),
                    html.Button("Next Problem", id="next-problem", n_clicks=0, style={
                        "backgroundColor": "rgba(0, 123, 255, 0.9)",
                        "color": "white",
                        "border": "none",
                        "padding": "1rem 2rem",
                        "borderRadius": "8px",
                        "cursor": "pointer",
                        "fontSize": "0.9em",
                        "fontWeight": "500",
                        "letterSpacing": "0.5px",
                        "textTransform": "uppercase"
                    })
                ], className="button-group", style={
                    "display": "flex",
                    "justifyContent": "center",
                    "flexWrap": "wrap",
                    "gap": "1rem",
                    "marginBottom": "2rem"
                })
            ]),

            # Feedback areas
            html.Div([
                html.Div(id="feedback", className="card feedback-area", style={
                    "marginBottom": "1.5rem",
                    "padding": "1.5rem",
                    "borderRadius": "12px"
                }),
                html.Div(id="hint-area", className="card feedback-area", style={
                    "marginBottom": "1.5rem",
                    "padding": "1.5rem",
                    "borderRadius": "12px"
                }),
                html.Div(id="solution-area", className="card feedback-area", style={
                    "padding": "1.5rem",
                    "borderRadius": "12px",
                    "lineHeight": "1.6"
                })
            ])
        ], style={
            "maxWidth": "800px",
            "margin": "2rem auto",
            "padding": "0 1.5rem"
        }),
        
        # Store component for state management
        dcc.Store(id="store-state", data={"current_problem": 1, "hint_count": {}, "user_id": None})
    ])
])

# Callback for login
@app.callback(
    [Output('login-page', 'style'),
     Output('main-app', 'style'),
     Output('user-info', 'children'),
     Output('user-stats', 'children'),
     Output('store-state', 'data')],
    [Input('login-button', 'n_clicks')],
    [State('username-input', 'value')]
)
def handle_login(n_clicks, username):
    if not n_clicks or not username:
        return (
            {"display": "block"},  # Show login page
            {"display": "none"},   # Hide main app
            None,
            None,
            {}
        )
    
    # Get or create user
    user_id, name = db.get_user(username)
    
    # Get user stats
    stats = db.get_user_stats(user_id)
    challenging_problems = db.get_challenging_problems(user_id)
    
    # Create user info and stats components
    user_info = html.Div([
        html.H3(f"Welcome back, {name}!", style={"color": "#2c3e50"}),
        html.P(f"You've attempted {len(stats)} different problems")
    ])
    
    stats_component = html.Div([
        html.H4("Your Progress", style={"color": "#2c3e50"}),
        html.Div([
            html.P(f"Problems needing practice: {', '.join(map(str, challenging_problems))}"),
            html.Div([
                html.Div([
                    html.Strong(f"Problem {s['problem_number']}"),
                    html.P(f"Success rate: {s['success_rate']*100:.1f}%")
                ]) for s in stats[:3]
            ])
        ])
    ]) if stats else html.P("Start solving problems to see your statistics!")
    
    return (
        {"display": "none"},    # Hide login page
        {"display": "block"},   # Show main app
        user_info,
        stats_component,
        {"current_problem": 1, "hint_count": {}, "user_id": user_id}
    )

# Update the submit_answer callback to use user tracking
@app.callback(
    Output("feedback", "children"),
    Input("submit-answer", "n_clicks"),
    [State("answer-input", "value"),
     State("store-state", "data")],
    prevent_initial_call=True
)
def submit_answer(n_clicks, answer, data):
    if not n_clicks:
        return ""
    
    current = data.get("current_problem", 1)
    user_id = data.get("user_id")
    
    if not user_id:
        return html.Div("Please log in first.", style={"color": "#dc3545"})
    
    prob = get_problem(current)
    if not prob:
        return html.Div("Problem data not found.", style={"color": "#dc3545"})

    if not answer:
        return html.Div("Please enter an answer.", style={"color": "#ffc107"})

    # Get AI tutor feedback with RAG
    feedback = evaluate_answer(user_id, prob, answer)
    
    # Determine if the answer is correct (basic check)
    is_correct = any(str(answer).strip() in sol["solution"] for sol in prob["solutions"])
    
    # Log the attempt
    db.log_attempt(user_id, current, answer, is_correct)
    
    return html.Div(feedback, style={
        "padding": "15px",
        "backgroundColor": "#f8f9fa",
        "borderRadius": "4px",
        "border": "1px solid #dee2e6",
        "marginBottom": "15px",
        "whiteSpace": "pre-line"
    })

@app.callback(
    Output("problem-area", "children"),
    Input("store-state", "data")
)
def update_problem(data):
    current = data.get("current_problem", 1)
    prob = get_problem(current)
    if prob:
        return f"Problem {current}: {prob['problem']}"
    else:
        return "No problem data available."


@app.callback(
    Output("progress-indicator", "children"),
    Input("store-state", "data")
)
def update_progress(data):
    current = data.get("current_problem", 1)
    total = len(problems_data)
    return f"Problem {current} of {total}"

@app.callback(
    [Output("hint-area", "children"),
     Output("store-state", "data", allow_duplicate=True)],
    Input("get-hint", "n_clicks"),
    State("store-state", "data"),
    prevent_initial_call=True
)
def get_hint(n_clicks, data):
    if not n_clicks:
        return "", data

    current = data.get("current_problem", 1)
    hint_count = data.get("hint_count", {})
    count = hint_count.get(str(current), 0)
    
    prob = get_problem(current)
    if not prob:
        return html.Div("Problem data not found.", style={"color": "#dc3545"}), data

    # Get all hints up to the current count
    hints = []
    for i in range(1, min(count + 2, len(prob["hints"]) + 1)):
        hint_key = str(i)
        hint = prob["hints"].get(hint_key)
        if hint:
            hints.append(html.Div([
                html.Strong(f"Hint {i}: "),
                hint
            ], style={"marginBottom": "10px"}))

    if not hints:
        return html.Div("No more hints available!", style={
            "color": "#6c757d",
            "fontStyle": "italic",
            "padding": "10px",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "4px",
            "marginBottom": "15px"
        }), data

    # Update hint count
    count += 1
    hint_count[str(current)] = count
    data["hint_count"] = hint_count

    return html.Div(hints, style={
        "padding": "15px",
        "backgroundColor": "#f8f9fa",
        "borderRadius": "4px",
        "border": "1px solid #dee2e6",
        "marginBottom": "15px"
    }), data

@app.callback(
    Output("solution-area", "children"),
    Input("see-solution", "n_clicks"),
    State("store-state", "data"),
    prevent_initial_call=True
)
def see_solution(n_clicks, data):
    if not n_clicks:
        return ""

    current = data.get("current_problem", 1)
    prob = get_problem(current)

    if not prob:
        return html.Div("Problem data not found.", style={"color": "#dc3545"})

    solution_elements = []
    for sol in prob["solutions"]:
        solution_elements.extend([
            html.Div([
                html.Strong("Method: ", style={"color": "#6c757d"}),
                html.Span(sol["method"])
            ], style={"marginBottom": "10px"}),
            html.Div(sol["solution"], style={"marginBottom": "20px"})
        ])

    return html.Div(solution_elements, style={
        "padding": "15px",
        "backgroundColor": "#f8f9fa",
        "borderRadius": "4px",
        "border": "1px solid #dee2e6",
        "color": "#495057",
        "lineHeight": "1.5"
    })

@app.callback(
    [Output("store-state", "data", allow_duplicate=True),
     Output("feedback", "children", allow_duplicate=True),
     Output("hint-area", "children", allow_duplicate=True),
     Output("solution-area", "children", allow_duplicate=True)],
    Input("next-problem", "n_clicks"),
    State("store-state", "data"),
    prevent_initial_call=True
)
def next_problem(n_clicks, data):
    if not n_clicks:
        return data, "", "", ""
    current = data.get("current_problem", 1)
    if current >= len(problems_data):
        return data, "You are at the last problem.", "", ""
    current += 1
    data["current_problem"] = current
    hint_count = data.get("hint_count", {})
    if str(current) not in hint_count:
        hint_count[str(current)] = 0
    data["hint_count"] = hint_count
    return data, "", "", ""

if __name__ == "__main__":
    app.run_server(debug=True, port=8054)
