# BlockVote - Transparent & Secure Voting System

**BlockVote** is a decentralized, tamper-proof voting platform designed to restore trust in elections. By leveraging a local blockchain and **Blind Signatures**, it ensures that every vote is permanent, verifiable, and completely anonymous.

## 🚀 Key Features
* **Immutable Ledger:** Votes are recorded on a blockchain, making them impossible to alter or delete.
* **Decentralized Identity (DID):** Ensures one person = one vote without storing sensitive personal data.
* **Blind Signatures:** Mathematically proves a vote is valid while keeping the voter's choice secret.
* **P2P Network:** Runs on a distributed network of nodes rather than a single central server.

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **Framework:** Flask (Web Server)
* **Cryptography:** `rsa`, `hashlib` (SHA-256)
* **Networking:** HTTP/REST APIs for peer discovery

---

## 🏃‍♂️ How to Run the Project locally

Follow these steps to get the node running on your machine.

### 1. Clone the Repository
**Do not fork.** Clone the main repository directly.
```bash
git clone [https://github.com/trxvorr/BlockVote.git](https://github.com/trxvorr/BlockVote.git)
cd BlockVote
```
### 2. Set up the Environment
It is recommended to use a virtual environment to keep dependencies clean.

For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4. Run the Node

Start the blockchain server:
```bash
python node_server.py
```


### 5. Verify

Open your browser and visit:

http://localhost:5000/ You should see the status message: "BlockVote Node is Running Successfully!"

## Team Workflow (Read Carefully!)

### We follow a strict Feature Branch Workflow. 🛑 DO NOT push directly to the main branch.
### How to Contribute:

Pull the latest code: Always start by making sure your local main is up to date.
    

    git checkout main
    git pull origin main

Create a new branch: Name your branch based on the feature you are working on (e.g., feature/voting-ui or fix/node-sync).
    

    git checkout -b feature/your-feature-name

Code & Test: Write your code and run tests locally to ensure nothing is broken.
    
    pytest /test/#create your test file if it doesnt exist

Push your branch:
    

    git push origin feature/your-feature-name

Open a Pull Request (PR):
- Go to the GitHub repository.

-    Click "Compare & pull request".

-    Add a title and description (mention the Issue # you are fixing, e.g., "Closes #2").

-    Wait for a team member to review and approve.

-    Merge!
