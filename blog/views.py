from flask import render_template

from . import app
from .database import session, Entry
from flask.ext.login import login_required
from flask.ext.login import current_user

PAGINATE_BY=10

@app.route("/")
@app.route("/page/<int:page>/")
def entries(page=1):
    # Zero-indexed page
    default_entries = 10
    max_entries = 50

    try:
        entry_limit = int(request.args.get('limit', default_entries))
        print (entry_limit)
        assert entry_limit > 0 # Ensure positive number
        assert entry_limit <= max_entries   # Ensure entries don't exceed max value
    except (ValueError, AssertionError):
        entry_limit = default_entries
        
    page_index = page - 1

    count = session.query(Entry).count()

    start = page_index * entry_limit
    end = start + entry_limit

    total_pages = (count - 1) // entry_limit + 1
    has_next = page_index < total_pages - 1
    has_prev = page_index > 0

    entries = session.query(Entry)
    entries = entries.order_by(Entry.datetime.desc())
    entries = entries[start:end]
    
    if current_user.is_authenticated:
         authenticate = True
         name = current_user.name
    else:
         authenticate = False
         name = "404"
         
    return render_template("entries.html",
        entries=entries,
        has_next=has_next,
        has_prev=has_prev,
        page=page,
        total_pages=total_pages,
        authenticate=authenticate,
        name=name
    )
    
@app.route("/entry/add", methods=["GET"])
@login_required
def add_entry_get():
    return render_template("add_entry.html")

from flask import request, redirect, url_for

@app.route("/entry/add", methods=["POST"])
@login_required
def add_entry_post():
    entry = Entry(
        title=request.form["title"],
        content=request.form["content"],
        author=current_user
    )
    session.add(entry)
    session.commit()
    return redirect(url_for("entries"))
    
@app.route("/entry/<id>")
def view_entry(id):
    entry = session.query(Entry).filter_by(id=id).first()
    if current_user.is_authenticated:
         name = current_user.name
    else:
         name = "404"
    return render_template("view_single_entry.html", entry=entry, name=name)
    
@app.route("/entry/<id>/edit", methods=["GET"])
@login_required
def edit_entry(id):
    entry = session.query(Entry).filter_by(id=id).first()
    
    if current_user.name != entry.author:
        return redirect(url_for("entries"))
        
    return render_template("edit_entry.html", entry=entry)
    
@app.route("/entry/<id>/edit", methods=["POST"])
@login_required
def edit_entry_post(id):
    entry = session.query(Entry).filter_by(id=id).first()
    entry.content=request.form["content"]
    session.commit()
    return redirect(url_for("entries"))
    
@app.route("/entry/<id>/delete", methods=["GET"])
@login_required
def delete_entry_get(id):
    entry=session.query(Entry).filter_by(id=id).first()
    if current_user.name != entry.author:
        return redirect(url_for("entries"))
    return render_template("delete_entry.html", entry=entry)
    
@app.route("/entry/<id>/delete", methods=["POST"])
@login_required
def delete_entry_post(id):
    entry=session.query(Entry).filter_by(id=id).first()
    session.delete(entry)
    session.commit()
    return redirect(url_for("entries"))
    
@app.route("/test")
def test():
    return render_template("test.html")
    
@app.route("/login", methods=["GET"])
def login_get():
    return render_template("login.html")
    
from flask import flash
from flask.ext.login import login_user, logout_user
from werkzeug.security import check_password_hash
from .database import User

@app.route("/login", methods=["POST"])
def login_post():
    email = request.form["email"]
    password = request.form["password"]
    user = session.query(User).filter_by(email=email).first()
    if not user or not check_password_hash(user.password, password):
        flash("Incorrect username or password", "danger")
        return redirect(url_for("login_get"))

    login_user(user)
    return redirect(request.args.get('next') or url_for("entries"))
    
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("entries"))
