"""
SpanishDictAPI index API.

URLs include:
/api/v1/
"""

import flask
from spanishdictapi import app

# /api/v1/
@app.route('/api/v1/', methods=['GET'])
def api_index():
    """Create the index route."""
    return flask.jsonify(
        conjugate=flask.url_for('api_conjugate'),
        url=flask.url_for('api_index')
    )
