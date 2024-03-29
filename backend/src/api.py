import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth


import logging

log = logging.getLogger(__name__)

app = Flask(__name__)
setup_db(app)
CORS(app)
"""
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
"""
db_drop_and_create_all()

# ROUTES
"""
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks", methods=["GET"])
def get_drinks():
    # Get all drinks from the database
    drinks = Drink.query.all()

    # If no drinks are found, return a 404 error
    if not drinks:
        abort(404)

    # Format the drinks as a list of short representations
    formatted_drinks = [drink.short() for drink in drinks]

    # Return the formatted drinks as a JSON response
    return jsonify({"success": True, "drinks": formatted_drinks}), 200


"""
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks-detail", methods=["GET"])
@requires_auth("get:drinks-detail")
def drinks_detail(payload):
    drinks = Drink.query.all()
    if not drinks:
        abort(404)

    drinks_long = [drink.long() for drink in drinks]

    return jsonify({"success": True, "drinks": drinks_long}), 200


"""
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks", methods=["POST"])
@requires_auth("post:drinks")
def create_drink(payload):
    data = request.get_json()
    title = data.get("title")
    recipe = data.get("recipe")

    if not all([title, recipe]):
        abort(400)

    drink = Drink(
        title=title, recipe=json.dumps(recipe if isinstance(recipe, list) else [recipe])
    )

    try:
        drink.insert()
    except Exception as e:
        log.error(e, exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": 400,
                    "message": str(e),
                }
            ),
            400,
        )

    drinks = [drink.short()]
    return jsonify({"success": True, "drinks": drinks}), 200


"""
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks/<int:id>", methods=["PATCH"])
@requires_auth("patch:drinks")
def update_drink(payload, id):
    data = request.get_json()
    title = data.get("title")
    recipe = data.get("recipe")

    if not any([title, recipe]):
        abort(400)

    drink = Drink.query.get_or_404(id)

    if title:
        drink.title = title

    if recipe:
        drink.recipe = json.dumps(recipe if isinstance(recipe, list) else [recipe])

    try:
        drink.update()
    except Exception as e:
        log.error(e, exc_info=True)
        return (
            jsonify(
                {
                    "success": False,
                    "error": 400,
                    "message": str(e),
                }
            ),
            400,
        )

    drinks = [drink.short()]
    return jsonify({"success": True, "drinks": drinks}), 200


"""
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
"""


@app.route("/drinks/<int:id>", methods=["DELETE"])
@requires_auth("delete:drinks")
def delete_drink(payload, id):
    Drink.query.get_or_404(id).delete()
    return jsonify({"success": True, "delete": id}), 200


# Error Handling
"""
Example error handling for unprocessable entity
"""
"""
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

"""

"""
@TODO implement error handler for 404
    error handler should conform to general task above
"""


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({"success": False, "error": 422, "message": "unprocessable"}), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"success": False, "error": 400, "message": "Bad request"}), 400


@app.errorhandler(404)
def not_found(error):
    return (
        jsonify({"success": False, "error": 404, "message": "resource not found"}),
        404,
    )


@app.errorhandler(500)
def internal_server_error(error):
    return (
        jsonify({"success": False, "error": 500, "message": "Internal server error"}),
        500,
    )


"""
@TODO implement error handler for AuthError
    error handler should conform to general task above
"""


@app.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify({"success": False, "error": ex.status_code, "message": ex.error})
    response.status_code = ex.status_code
    return response
