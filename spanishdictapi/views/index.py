"""
SpanishDictAPI index (main) view.

URLs include:
/
"""

import flask
from spanishdictapi import app

# /
@app.route('/', methods=['GET'])
def index():
    """Display / route"""
    return flask.render_template("index.html")
