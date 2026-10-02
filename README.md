# SafeUPI

SafeUPI is a modular UPI payment-risk detection prototype designed to demonstrate how transaction risk scoring, mule-account detection, and transaction-network analysis can be integrated into a payment workflow.
<img width="938" height="484" alt="image" src="https://github.com/user-attachments/assets/5772b061-1346-4ea4-9c3f-06ad53577ff2" />

<img width="950" height="468" alt="image" src="https://github.com/user-attachments/assets/7f0614bb-7e86-4d7d-b666-e6a4b9984659" />


## Project structure

```text
safeupi/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── QRScanner.jsx
│   │   │   ├── PaymentCard.jsx
│   │   │   ├── RiskBadge.jsx
│   │   │   ├── WarningModal.jsx
│   │   │   ├── StatsCard.jsx
│   │   │   └── TransactionGraph.jsx
│   │   ├── pages/
│   │   │   ├── UserHome.jsx
│   │   │   ├── Payment.jsx
│   │   │   ├── AdminDashboard.jsx
│   │   │   └── AccountDetails.jsx
│   │   ├── services/
│   │   │   └── api.js
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── main.py
│   ├── api/
│   │   ├── payment.py
│   │   ├── admin.py
│   │   └── accounts.py
│   ├── risk_engine/
│   │   ├── risk.py
│   │   ├── features.py
│   │   └── mule_detection.py
│   ├── graph/
│   │   └── transaction_graph.py
│   ├── database/
│   │   ├── database.py
│   │   └── models.py
│   └── requirements.txt
├── data/
│   ├── accounts.csv
│   ├── transactions.csv
│   └── generate_data.py
├── README.md
└── .gitignore
```

## Current implementation

The `data/` directory contains a deterministic synthetic dataset generator. It creates:

- `accounts.csv`: synthetic UPI-account metadata
- `transactions.csv`: synthetic payment transactions
- `generate_data.py`: generator for reproducing the dataset

The `backend/graph/` directory contains:

- `transaction_graph.py`: NetworkX-based transaction graph construction and analysis utilities

## Data model

### accounts.csv

| Column | Description |
|---|---|
| account_id | Synthetic account identifier |
| name | Synthetic account name |
| upi_id | Synthetic UPI ID |
| bank | Synthetic bank label |
| city | Synthetic Indian city |
| account_type | customer / merchant |
| risk_level | low / medium / high |
| is_mule | Synthetic ground-truth flag for demo purposes |
| created_at | Account creation timestamp |

### transactions.csv

| Column | Description |
|---|---|
| transaction_id | Unique transaction identifier |
| sender_id | Sender account |
| receiver_id | Receiver account |
| amount | Transaction amount in INR |
| timestamp | Transaction timestamp |
| channel | UPI / QR / collect |
| status | SUCCESS / FAILED |
| device_id | Synthetic device identifier |
| ip_address | Synthetic private/test IP |
| merchant_category | Synthetic transaction category |
| is_flagged | Synthetic fraud/risk flag |
| risk_score | Synthetic demonstration score |

> The data is synthetic and is intended only for development, demos, testing, and model prototyping. It is not real banking data.

## Generate the data

From the project root:

```bash
python data/generate_data.py
```

Optional arguments:

```bash
python data/generate_data.py --accounts 250 --transactions 5000 --seed 42
```

## Transaction graph module

Install the graph dependency:

```bash
pip install networkx pandas numpy
```

Example:

```python
from backend.graph.transaction_graph import TransactionGraph

graph = TransactionGraph.from_csv(
    "data/transactions.csv",
    "data/accounts.csv"
)

print(graph.summary())

print(graph.top_accounts_by_degree(10))

communities = graph.detect_communities()
print(communities)

print(graph.get_account_neighbors("ACC00001"))
```

The graph treats accounts as nodes and successful transactions as directed edges. Edge attributes include transaction count and total transferred value.

## Risk-engine integration

The graph module is deliberately independent of the risk engine. A backend risk pipeline can combine:

1. Transaction-level features
2. Account history
3. Risk scores
4. Mule-account indicators
5. Graph/network features

Useful graph features include:

- incoming transaction count
- outgoing transaction count
- unique counterparties
- total incoming amount
- total outgoing amount
- in/out amount ratio
- degree centrality
- suspicious-neighbor count
- transaction concentration

## Development notes

This repository is a prototype. Do not connect it to production banking systems without appropriate authentication, authorization, encryption, audit logging, regulatory controls, transaction signing, fraud-review workflows, and security testing.

Synthetic account identifiers, UPI IDs, IP addresses, and device IDs in this repository should not be interpreted as real financial information.

## Suggested backend stack

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- NetworkX
- pandas / NumPy
- scikit-learn

## Suggested frontend stack

- React
- Vite
- Axios
- React Router
- Recharts or Plotly
- A QR scanning library compatible with the browser

## Running the graph demo

```bash
python backend/graph/transaction_graph.py \
    --transactions data/transactions.csv \
    --accounts data/accounts.csv
```

The command prints basic graph statistics and the highest-degree accounts.

## License

For academic, research, and prototype use. Add the project's final license before public distribution.


## Database setup

The backend includes `backend/database/database.py`, which provides:

- SQLAlchemy engine configuration
- `SessionLocal` session factory
- FastAPI-compatible `get_db()` dependency
- `init_db()` table initialization
- SQLite development support
- PostgreSQL support through `DATABASE_URL`

### Install backend dependencies

```bash
cd backend
pip install -r requirements.txt
```

### Local SQLite database

No database server is required for local development. The default database is:

```text
sqlite:///./safeupi.db
```

Initialize the database from Python:

```python
from database.database import init_db

init_db()
```

If importing from the project root:

```python
from backend.database.database import init_db

init_db()
```

### PostgreSQL

Set the environment variable before starting the backend:

```bash
DATABASE_URL="postgresql+psycopg2://username:password@localhost/safeupi"
```

On Windows PowerShell:

```powershell
$env:DATABASE_URL="postgresql+psycopg2://username:password@localhost/safeupi"
```

The database layer intentionally does not hard-code credentials. Do not commit
database passwords, API keys, JWT secrets, or other credentials to Git.
