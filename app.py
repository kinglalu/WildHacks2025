from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"  
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    image_link = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(80), nullable=False)  # To associate the listing with the user


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
        image_link = request.form["image_link"]

        new_listing = Listing(name=name, description=description, image_link=image_link, username=username)
        db.session.add(new_listing)
        db.session.commit()
        flash("Listing added successfully!")

    user_listings = Listing.query.filter_by(username=username).all()
    return render_template("listings.html", username=username, listings=user_listings)

@app.route("/delete_listing/<int:listing_id>", methods=["POST"])
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    username = session.get('username')

    if listing.username != username and session['username'] != 'admin':
        flash("You are not authorized to delete this listing.")
        return redirect(url_for('listings', username=username))

    db.session.delete(listing)
    db.session.commit()
    flash("Listing deleted successfully.")
    return redirect(url_for('listings', username=username))

@app.route("/all_listings", methods=["GET", "POST"])
def all_listings():
    username = session.get('username')  # Retrieve username from session

    if not username:
        return redirect(url_for("login_page"))  # Redirect to login if no user is logged in

    # Get all listings in the database
    all_listings = Listing.query.all()
    return render_template("all_listings.html", username=username, listings=all_listings)




if __name__ == "__main__":
    with app.app_context(): 
        db.create_all() 
    app.run(debug=True)