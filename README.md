# BlockVote - Transparent & Secure Voting System

**BlockVote** is a decentralized, tamper-proof voting platform designed to restore trust in elections. By leveraging a local blockchain and **Blind Signatures**, it ensures that every vote is permanent, verifiable, and completely anonymous.

## 🚀 Key Features
* **Immutable Ledger:** Votes are recorded on a blockchain, making them impossible to alter or delete.
* **Proof of Work:** Mining secures the network against spam attacks.
* **Blind Signatures:** Mathematically proves a vote is valid while keeping the voter's choice secret.
* **P2P Network:** Runs on a distributed network of nodes with automatic peer discovery.
* **Email OTP Authentication:** Two-factor verification before voting.
* **Tamper Evidence:** Real-time integrity checks detect chain corruption.
* **Admin Dashboard:** Protected panel for election management with activity logging.
* **Real-Time Analytics:** Live vote counts with Chart.js visualization.

## 🛠️ Tech Stack
* **Language:** Python 3.x
* **Framework:** Flask (Web Server)
* **Cryptography:** `rsa`, `hashlib` (SHA-256), Blind Signatures
* **Frontend:** HTML5, CSS3, JavaScript, Chart.js
* **Testing:** pytest (68+ tests)

---

## 🏃‍♂️ How to Run the Project Locally

### 1. Clone the Repository
```bash
git clone https://github.com/trxvorr/BlockVote.git
cd BlockVote
```

### 2. Set up the Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Node
```bash
python -m app.node_server
# Or with a custom port:
python -m app.node_server 5001
```

### 5. Access the Application
- **Voting Page:** http://localhost:5000/
- **Admin Dashboard:** http://localhost:5000/admin (Password: `admin123`)

### 6. Run Tests
```bash
pytest tests/ -v
```

### 7. Run Benchmark
```bash
python scripts/benchmark.py
```

---

## 📊 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Voting page |
| `/admin` | GET | Admin dashboard (auth required) |
| `/vote/submit` | POST | Submit a vote |
| `/mine` | GET | Mine pending transactions |
| `/chain` | GET | Get full blockchain |
| `/chain/verify` | GET | Verify chain integrity |
| `/stats` | GET | Get node statistics |
| `/candidates` | GET | List candidates |
| `/votes/count` | GET | Get vote counts |

---

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
