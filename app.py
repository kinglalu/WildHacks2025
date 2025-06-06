from flask import Flask, render_template, request, redirect, url_for, flash, session, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
db = SQLAlchemy(app)
migrate = Migrate(app, db)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_link = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(80), nullable=False)

    likes = db.relationship('Like', back_populates='listing', lazy='dynamic')
    dislikes = db.relationship('Dislike', back_populates='listing', lazy='dynamic')  

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)

    listing = db.relationship('Listing', back_populates='likes')

class Dislike(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(80), nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('listing.id'), nullable=False)

    listing = db.relationship('Listing', back_populates='dislikes')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads')

@app.route("/")
def login_page():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]
    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        session['username'] = username  # Store username in session
        return redirect(url_for("welcome", username=username))
    else:
        flash("Invalid login credentials")
        return redirect(url_for("login_page"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")  # Use pbkdf2:sha256

        if User.query.filter_by(username=username).first():
            flash("Username already exists")
            return redirect(url_for("register"))

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for("login_page"))

    return render_template("register.html")


@app.route("/welcome/<username>", methods=["GET", "POST"])
def welcome(username):
    if session['username'] != username:
        return redirect(url_for('welcome', username=session['username']))
        
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        image_link = request.form["image_link"]

        new_listing = Listing(name=name, description=description, image_link=image_link, username=username)
        db.session.add(new_listing)
        db.session.commit()
        flash("Listing published successfully!")

    listings = Listing.query.filter_by(username=username).all()
    return render_template("welcome.html", username=username, listings=listings)

@app.route("/logout", methods=["POST"])
def logout():
    session.pop('username', None)  # Remove username from session
    flash("You have been logged out successfully!")
    return redirect(url_for("login_page"))

@app.route("/listings/<username>", methods=["GET", "POST"])
def listings(username):
    if session['username'] == 'admin':
        all_listings = Listing.query.all()
        return render_template("listings.html", username=username, listings=all_listings)

    if session['username'] != username:
        return redirect(url_for('listings', username=session['username']))

    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        file = request.files.get("image_file")

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            # Use absolute path to upload folder
            upload_folder = os.path.join(app.root_path, 'static', 'uploads')
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)

            # Image link used in HTML is still relative to /static
            image_link = url_for('static', filename='uploads/' + filename)

            new_listing = Listing(
                name=name,
                description=description,
                image_link=image_link,
                username=username
            )
            db.session.add(new_listing)
            db.session.commit()
            flash("Listing added successfully!", "success")
        else:
            flash("Invalid file type. Please upload a valid image.", "danger")

    user_listings = Listing.query.filter_by(username=username).all()
    return render_template("listings.html", username=username, listings=user_listings)


@app.route("/delete_listing/<int:listing_id>", methods=["POST"])
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    username = session.get('username')

    # Check if the current user is the owner or admin
    if session['username'] != listing.username and session['username'] != 'admin':
        flash("You are not authorized to delete this listing.")
        return redirect(url_for('listings', username=username))

    # Delete all likes/dislikes related to this listing
    Like.query.filter_by(listing_id=listing.id).delete()
    Dislike.query.filter_by(listing_id=listing.id).delete()

    # Delete the image associated with the listing
    image_filename = listing.image_link.split('/')[-1]  # Extract the filename from the URL
    upload_folder = os.path.join(app.root_path, 'static', 'uploads')
    image_path = os.path.join(upload_folder, image_filename)

    # Check if the file exists and remove it
    if os.path.exists(image_path):
        os.remove(image_path)

    # Delete the listing itself
    db.session.delete(listing)
    db.session.commit()

    flash("Listing and image deleted successfully.")
    return redirect(url_for('listings', username=username))



@app.route("/all_listings", methods=["GET", "POST"])
def all_listings():
    username = session.get('username')  # Retrieve username from session

    if not username:
        return redirect(url_for("login_page"))  # Redirect to login if no user is logged in

    # Get all listings in the database
    all_listings = Listing.query.all()
    return render_template("all_listings.html", username=username, listings=all_listings)

@app.route("/profile/<username>")
def profile(username):
    listings = Listing.query.filter_by(username=username).all()
    current_user = session.get("username")  # get the logged-in user

    return render_template("profile.html", username=username, listings=listings, current_user=current_user)


@app.route("/like/<int:listing_id>", methods=["POST"])
def like_listing(listing_id):
    username = session.get("username")
    if not username:
        return redirect(url_for("login_page"))

    existing_like = Like.query.filter_by(user=username, listing_id=listing_id).first()
    if not existing_like:
        like = Like(user=username, listing_id=listing_id)
        db.session.add(like)
        db.session.commit()
    
    return redirect(request.referrer or url_for("all_listings"))

@app.route("/unlike/<int:listing_id>", methods=["POST"])
def unlike_listing(listing_id):
    username = session.get("username")
    if not username:
        return redirect(url_for("login_page"))

    like = Like.query.filter_by(user=username, listing_id=listing_id).first()
    if like:
        db.session.delete(like)
        db.session.commit()
    
    return redirect(request.referrer or url_for("all_listings"))

@app.route("/dislike/<int:listing_id>", methods=["POST"])
def dislike_listing(listing_id):
    username = session.get("username")
    if not username:
        return redirect(url_for("login_page"))

    existing_dislike = Dislike.query.filter_by(user=username, listing_id=listing_id).first()
    if not existing_dislike:
        dislike = Dislike(user=username, listing_id=listing_id)
        db.session.add(dislike)
        db.session.commit()
    
    return redirect(request.referrer or url_for("all_listings"))

@app.route("/undislike/<int:listing_id>", methods=["POST"])
def undislike_listing(listing_id):
    username = session.get("username")
    if not username:
        return redirect(url_for("login_page"))

    dislike = Dislike.query.filter_by(user=username, listing_id=listing_id).first()
    if dislike:
        db.session.delete(dislike)
        db.session.commit()
    
    return redirect(request.referrer or url_for("all_listings"))



if __name__ == "__main__":
    with app.app_context(): 
        db.create_all() 
    app.run(debug=True)
