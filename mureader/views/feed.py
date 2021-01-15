from flask import Blueprint, render_template
from flask_jwt_extended import current_user, verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError

from mureader import models
from mureader.main import jwt_required

feed_blueprint = Blueprint('feed', __name__)

@feed_blueprint.route('/last', methods=['GET'])
def last():
    try:
        verify_jwt_in_request()
    except NoAuthorizationError:
        pass
    entries = models.Entry.query.order_by(models.Entry.updated_at.desc()).limit(100)
    return render_template('news.html', entries=entries, user=current_user)

@feed_blueprint.route('/news', methods=['GET'])
@jwt_required
def news():
    entries = models.UserEntry.query \
        .join(models.Entry) \
        .filter(models.UserEntry.user==current_user, models.UserEntry.liked==False)
    entries = entries.order_by(models.Entry.updated_at.desc())
    return render_template('news.html', entries=entries, user=current_user)

@feed_blueprint.route('/liked', methods=['GET'])
@jwt_required
def liked():
    entries = models.UserEntry.query \
        .join(models.Entry) \
        .filter(models.UserEntry.user==current_user, models.UserEntry.liked==True) \
        .order_by(models.Entry.updated_at.desc())
    return render_template('news.html', entries=entries, user=current_user)
