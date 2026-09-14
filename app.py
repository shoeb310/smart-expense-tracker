from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "Smart Expense Tracker is running!"


if __name__ == "__main__":
    app.run(debug=True)