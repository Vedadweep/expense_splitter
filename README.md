# Expense Splitter Microservice

A clean, production-style microservice for splitting expenses among groups — built with **FastAPI**, **SQLAlchemy**, and a **greedy debt-minimization algorithm** that computes the fewest transactions needed to settle all balances.



---

## Features

- **Group Management** — Create groups, add members
- **Flexible Expense Splitting** — Equal split or fully custom per-member amounts
- **Smart Settlement Engine** — Greedy O(n log n) algorithm minimizes the number of payments needed
- **Balance Tracking** — See exactly who owes whom and how much
- **Input Validation** — Custom splits are validated to match the expense total
- **Auto Docs** — Swagger UI at `/docs`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| ORM | SQLAlchemy (many-to-many relationships) |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Validation | Pydantic v2 |
| Algorithm | Greedy debt minimization |
| Testing | Pytest + TestClient |
| CI/CD | GitHub Actions |

---

## Getting Started

```bash
git clone https://github.com/Vedadweep/expense-splitter.git
cd expense-splitter
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## API Endpoints

### Groups & Members
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/groups/members` | Register a member |
| POST | `/api/v1/groups/` | Create a group with members |
| POST | `/api/v1/groups/{group_id}/members/{member_id}` | Add member to group |
| GET | `/api/v1/groups/{group_id}` | Get group details |

### Expenses
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/expenses/{group_id}` | Add expense (equal or custom split) |
| GET | `/api/v1/expenses/{group_id}` | List all group expenses |
| DELETE | `/api/v1/expenses/{group_id}/{expense_id}` | Remove an expense |

### Settlements
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/settlements/{group_id}` | Get optimal settlement plan |

---

## Settlement Algorithm

The settlement engine uses a **greedy two-pointer approach**:
1. Compute each member's net balance (total paid − total owed)
2. Separate into creditors (net positive) and debtors (net negative)
3. Greedily match largest debtor to largest creditor, repeat until settled

This minimizes the number of transactions required.

**Example:** 3 people, Alice paid ₹300 for all → Bob owes Alice ₹100, Carol owes Alice ₹100. The plan outputs exactly 2 transactions instead of a naive 3.

---

## Running Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

12 test cases covering: member creation, group management, equal splits, custom splits, split validation, settlement computation, and edge cases (already-balanced groups).

---

## Project Structure

```
expense-splitter/
├── app/
│   ├── main.py
│   ├── models/
│   │   ├── database.py       # DB engine & session
│   │   └── models.py         # Group, Member, Expense, ExpenseShare (many-to-many)
│   ├── schemas/schemas.py    # Pydantic schemas + SettlementPlan
│   └── routers/
│       ├── groups.py         # Group & member endpoints
│       ├── expenses.py       # Expense creation + split logic
│       └── settlements.py    # Greedy settlement algorithm
├── tests/test_api.py
├── .github/workflows/ci.yml
├── requirements.txt
└── README.md
```
