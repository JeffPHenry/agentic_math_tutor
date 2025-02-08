#!/usr/bin/env python3
import dash
from dash import dcc, html, Input, Output, State
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Debug: Print API key (first few characters)
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"API Key loaded (first 10 chars): {api_key[:10]}...")
else:
    print("Warning: No API key found!")

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Load problems from JSON file
with open("problems.json", "r") as f:
    problems_data = json.load(f)["problems"]


def get_problem(problem_number):
    """Retrieve problem data by problem number."""
    for prob in problems_data:
        if prob["problem_number"] == problem_number:
            return prob
    return None


def evaluate_answer(problem, user_answer):
    """Use GPT-4o to evaluate the answer and provide helpful feedback."""
    # Construct the prompt with problem context
    messages = [
        {"role": "system", "content": """You are a helpful and encouraging math tutor. Your goal is to:
1. Evaluate if the student's answer is correct
2. Provide encouraging feedback
3. If the answer is wrong, give a helpful hint without giving away the answer
4. Keep responses concise and focused"""},
        {"role": "user", "content": f"""Problem: {problem['problem']}
Available hints:
{json.dumps(problem['hints'], indent=2)}
Correct solutions:
{json.dumps(problem['solutions'], indent=2)}
Student's answer: {user_answer}

Evaluate the answer and provide helpful feedback."""}
    ]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error evaluating answer: {str(e)}"


app = dash.Dash(__name__)
app.title = "Math Tutor Dashboard"

app.layout = html.Div([
    # Main container
    html.Div([
        # Header with progress
        html.Div([
            html.H1("Math Tutor", style={
                "color": "#2c3e50",
                "margin": "0",
                "fontSize": "2.5em"
            }),
            html.Div(id="progress-indicator", style={
                "color": "#6c757d",
                "fontSize": "1.1em",
                "marginTop": "10px"
            })
        ], style={
            "textAlign": "center",
            "marginBottom": "30px"
        }),

        # Problem card
        html.Div([
            html.Div(id="problem-area", style={
                "fontSize": "1.3em",
                "fontWeight": "500",
                "marginBottom": "20px"
            })
        ], style={
            "padding": "25px",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "8px",
            "border": "1px solid #dee2e6",
            "marginBottom": "25px",
            "boxShadow": "0 2px 4px rgba(0,0,0,0.05)"
        }),

        # Input and controls
        html.Div([
            dcc.Input(
                id="answer-input",
                type="text",
                placeholder="Enter your answer here",
                style={
                    "width": "100%",
                    "padding": "12px",
                    "marginBottom": "20px",
                    "borderRadius": "4px",
                    "border": "1px solid #ced4da",
                    "fontSize": "1.1em"
                }
            ),

            # Button group
            html.Div([
                html.Button("Get Hint", id="get-hint", n_clicks=0, style={
                    "backgroundColor": "#17a2b8",
                    "color": "white",
                    "border": "none",
                    "padding": "10px 20px",
                    "margin": "5px",
                    "borderRadius": "4px",
                    "cursor": "pointer",
                    "fontSize": "1em",
                    "transition": "background-color 0.3s"
                }),
                html.Button("Submit Answer", id="submit-answer", n_clicks=0, style={
                    "backgroundColor": "#28a745",
                    "color": "white",
                    "border": "none",
                    "padding": "10px 20px",
                    "margin": "5px",
                    "borderRadius": "4px",
                    "cursor": "pointer",
                    "fontSize": "1em",
                    "transition": "background-color 0.3s"
                }),
                html.Button("See Solution", id="see-solution", n_clicks=0, style={
                    "backgroundColor": "#ffc107",
                    "color": "black",
                    "border": "none",
                    "padding": "10px 20px",
                    "margin": "5px",
                    "borderRadius": "4px",
                    "cursor": "pointer",
                    "fontSize": "1em",
                    "transition": "background-color 0.3s"
                }),
                html.Button("Next Problem", id="next-problem", n_clicks=0, style={
                    "backgroundColor": "#007bff",
                    "color": "white",
                    "border": "none",
                    "padding": "10px 20px",
                    "margin": "5px",
                    "borderRadius": "4px",
                    "cursor": "pointer",
                    "fontSize": "1em",
                    "transition": "background-color 0.3s"
                })
            ], style={
                "display": "flex",
                "justifyContent": "center",
                "flexWrap": "wrap",
                "gap": "10px",
                "marginBottom": "25px"
            })
        ]),

        # Feedback areas
        html.Div([
            html.Div(id="feedback", style={
                "color": "#28a745",
                "marginBottom": "15px",
                "padding": "10px",
                "borderRadius": "4px",
                "fontWeight": "500",
                "textAlign": "center"
            }),
            html.Div(id="hint-area", style={
                "color": "#17a2b8",
                "marginBottom": "15px",
                "padding": "15px",
                "backgroundColor": "#f8f9fa",
                "borderRadius": "4px",
                "border": "1px solid #dee2e6"
            }),
            html.Div(id="solution-area", style={
                "color": "#495057",
                "padding": "15px",
                "backgroundColor": "#f8f9fa",
                "borderRadius": "4px",
                "border": "1px solid #dee2e6",
                "whiteSpace": "pre-line",
                "lineHeight": "1.5"
            })
        ])
    ], style={
        "maxWidth": "800px",
        "margin": "40px auto",
        "padding": "20px"
    }),

    dcc.Store(id="store-state", data={"current_problem": 1, "hint_count": {}})
])

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
    Output("feedback", "children"),
    Input("submit-answer", "n_clicks"),
    State("answer-input", "value"),
    State("store-state", "data"),
    prevent_initial_call=True
)
def submit_answer(n_clicks, answer, data):
    if not n_clicks:
        return ""

    current = data.get("current_problem", 1)
    prob = get_problem(current)
    if not prob:
        return html.Div("Problem data not found.", style={"color": "#dc3545"})

    if not answer:
        return html.Div("Please enter an answer.", style={"color": "#ffc107"})

    # Get AI tutor feedback
    feedback = evaluate_answer(prob, answer)

    return html.Div(feedback, style={
        "padding": "15px",
        "backgroundColor": "#f8f9fa",
        "borderRadius": "4px",
        "border": "1px solid #dee2e6",
        "marginBottom": "15px",
        "whiteSpace": "pre-line"
    })


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

    next_hint_key = str(count + 1)
    hint = prob["hints"].get(next_hint_key)

    if hint:
        count += 1
        hint_count[str(current)] = count
        data["hint_count"] = hint_count
        return html.Div([
            html.Strong(f"Hint {next_hint_key}: ", style={"color": "#17a2b8"}),
            html.Span(hint)
        ], style={
            "padding": "15px",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "4px",
            "border": "1px solid #bee5eb",
            "marginBottom": "15px"
        }), data
    else:
        return html.Div("No more hints available.", style={
            "color": "#6c757d",
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
    app.run_server(debug=True, port=8052)
