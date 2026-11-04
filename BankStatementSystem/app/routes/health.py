"""Health check blueprint.
Provides a simple endpoint to verify that the Flask app is running.
"""

from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health():
    """Return a JSON payload confirming service health.
    
    Returns
    -------
    Response
        JSON with status and application name.
    """
    return jsonify({
        "status": "success",
        "application": "Bank Statement Processing System"
    })
