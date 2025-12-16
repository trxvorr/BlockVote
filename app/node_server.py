from sys import argv
from flask import Flask

from .blockchain import Blockchain

# Initialize the Flask App
app = Flask(__name__)

# Initialize the Blockchain
blockchain = Blockchain()

@app.route('/', methods=['GET'])
def home():
    return "BlockVote Node is Running Successfully!", 200

if __name__ == '__main__':
    # If the user provides a port number, use it. Otherwise, default to 5000.
    if len(argv) > 1:
        port = int(argv[1])
    else:
        port = 5000
        
    app.run(host='0.0.0.0', port=port)
