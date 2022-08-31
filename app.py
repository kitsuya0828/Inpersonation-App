from flask import Flask
	
# generate instance
app = Flask(__name__)	

# endpoint
@app.route("/")
def test():
    return "<h1>It Works!!</h1>"