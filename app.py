import sqlite3
import logging
import sys

from flask import (
    Flask,
    jsonify,
    json,
    render_template,
    request,
    url_for,
    redirect,
    flash,
)
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    try:
        connection = sqlite3.connect("database.db")
        connection.row_factory = sqlite3.Row
        return connection
    except:
        logging.error("Database not found")


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    connection.close()

    app.config["DB_CONN_COUNTER"] += 1

    return post


# Define the Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = "your secret key"
app.config["DB_CONN_COUNTER"] = 0

# Define the main route of the web application
@app.route("/")
def index():
    connection = get_db_connection()
    posts = connection.execute("SELECT * FROM posts").fetchall()
    connection.close()

    app.config["DB_CONN_COUNTER"] += 1

    return render_template("index.html", posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route("/<int:post_id>")
def post(post_id):
    post = get_post(post_id)

    if post is None:
        app.logger.debug(
            "A non-existing article is accessed and a 404 page is returned."
        )
        app.logger.error("PostId %d not found", post_id)
        return render_template("404.html"), 404
    else:
        app.logger.debug("Post %s was retrieved", post["title"])
        return render_template("post.html", post=post)


# Define the About Us page
@app.route("/about")
def about():
    app.logger.debug("The 'About Us' page was retrieved")
    return render_template("about.html")


# Define the post creation functionality
@app.route("/create", methods=("GET", "POST"))
def create():
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if not title:
            flash("Title is required!")
        else:
            connection = get_db_connection()
            connection.execute(
                "INSERT INTO posts (title, content) VALUES (?, ?)", (title, content)
            )
            connection.commit()

            app.config["DB_CONN_COUNTER"] += 1

            connection.close()

            app.logger.debug("A new article '%s' was created.", title)
            return redirect(url_for("index"))

    return render_template("create.html")


# Health endpoint
@app.route("/healthz")
def helthz():
    app.logger.debug("/healthz method reached")

    response = app.response_class(
        response=json.dumps({"status:": "Ok -healthy"}),
        status=200,
        mimetype="application/json",
    )
    return response


# Metrics endpoint
@app.route("/metrics")
def metrics():
    app.logger.debug("/metrics endpoint reached")

    connection = get_db_connection()
    cursor = connection.cursor()
    records = cursor.execute("SELECT id FROM posts").fetchall()

    app.config["DB_CONN_COUNTER"] += 1

    connection.close()

    json_response = (
        f"db_connection_count:{app.config['DB_CONN_COUNTER']},post_count:{len(records)}"
    )

    response = app.response_class(
        response=json_response, status=200, mimetype="application/json"
    )

    app.logger.debug("/metrics endpoint returned")

    return response


# start the application on port 3111
if __name__ == "__main__":

    stderr_handler = logging.StreamHandler(stream=sys.stderr)
    stdout_handler = logging.StreamHandler(stream=sys.stdout)

    handlers = [stderr_handler, stdout_handler]

    format_output = "%(asctime)s %(name)s %(levelname)s %(message)s"

    logging.basicConfig(format=format_output, level=logging.DEBUG, handlers=handlers)

    app.run(host="0.0.0.0", port="3111")
