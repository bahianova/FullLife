from flask import Blueprint, render_template, request
from app.models import Post

main = Blueprint('main', __name__)


@main.route("/")
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=5)
    return render_template('public/index.html', posts=posts)


@main.route("/about")
def about():
    return render_template('public/about.html', title='About')
