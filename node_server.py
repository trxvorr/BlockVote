from flask import Flask
from blockchain import Blockchain

# Initialize the Flask App
app = Flask(__name__)

# Initialize the Blockchain
blockchain = Blockchain()

@app.route('/', methods=['GET'])
def home():
    return "BlockVote Node is Running Successfully!", 200

if __name__ == '__main__':
    # Run the server on Port 5000
    app.run(host='0.0.0.0', port=5000)
