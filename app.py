from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

passwords = {"test": "GoogleTest",
             "Bob": "Sponge"}
    
@app.route("/")
def login_page():   
    return render_template("login.html")

@app.route("/login",methods=["POST"])
def login():
    username = request.form["username"]
    password = request.form["password"]

    if username in passwords and passwords[username] == password:
        return redirect(url_for("welcome", username=username))
    else:
        return "Invalid Login"

@app.route("/welcome/<username>")
def welcome(username):
    return render_template("welcome.html",username=username)

if __name__ == "__main__":
    app.run(debug=True)
