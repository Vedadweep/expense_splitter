import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.models.database import Base, get_db

TEST_DB = "sqlite:///./test_splitter.db"
engine = create_engine(TEST_DB, connect_args={"check_same_thread": False})
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)


# --- Helpers ---
def make_member(name, email):
    r = client.post("/api/v1/groups/members", json={"name": name, "email": email})
    assert r.status_code == 201
    return r.json()["id"]

def make_group(name, member_ids):
    r = client.post("/api/v1/groups/", json={"name": name, "member_ids": member_ids})
    assert r.status_code == 201
    return r.json()["id"]


# --- Member tests ---
def test_create_member():
    r = client.post("/api/v1/groups/members", json={"name": "Alice", "email": "alice@test.com"})
    assert r.status_code == 201
    assert r.json()["name"] == "Alice"

def test_duplicate_member_email():
    client.post("/api/v1/groups/members", json={"name": "Alice", "email": "alice@test.com"})
    r = client.post("/api/v1/groups/members", json={"name": "Alice2", "email": "alice@test.com"})
    assert r.status_code == 400


# --- Group tests ---
def test_create_group_with_members():
    a = make_member("Alice", "a@test.com")
    b = make_member("Bob", "b@test.com")
    r = client.post("/api/v1/groups/", json={"name": "Trip", "member_ids": [a, b]})
    assert r.status_code == 201
    assert len(r.json()["members"]) == 2

def test_add_member_to_group():
    a = make_member("Alice", "a@test.com")
    b = make_member("Bob", "b@test.com")
    gid = make_group("Friends", [a])
    r = client.post(f"/api/v1/groups/{gid}/members/{b}")
    assert r.status_code == 200
    assert len(r.json()["members"]) == 2


# --- Expense tests ---
def test_equal_split_expense():
    a = make_member("Alice", "a@test.com")
    b = make_member("Bob", "b@test.com")
    gid = make_group("Trip", [a, b])
    r = client.post(f"/api/v1/expenses/{gid}", json={
        "title": "Hotel", "amount": 200.0, "paid_by_id": a, "split_equally": True
    })
    assert r.status_code == 201
    shares = r.json()["shares"]
    assert len(shares) == 2
    assert all(s["share_amount"] == 100.0 for s in shares)

def test_custom_split_expense():
    a = make_member("Alice", "a@test.com")
    b = make_member("Bob", "b@test.com")
    gid = make_group("Trip", [a, b])
    r = client.post(f"/api/v1/expenses/{gid}", json={
        "title": "Dinner", "amount": 150.0, "paid_by_id": a,
        "split_equally": False, "custom_splits": {str(a): 100.0, str(b): 50.0}
    })
    assert r.status_code == 201

def test_custom_split_wrong_sum():
    a = make_member("Alice", "a@test.com")
    b = make_member("Bob", "b@test.com")
    gid = make_group("Trip", [a, b])
    r = client.post(f"/api/v1/expenses/{gid}", json={
        "title": "Dinner", "amount": 150.0, "paid_by_id": a,
        "split_equally": False, "custom_splits": {str(a): 50.0, str(b): 50.0}
    })
    assert r.status_code == 400

def test_payer_not_in_group():
    a = make_member("Alice", "a@test.com")
    b = make_member("Bob", "b@test.com")
    gid = make_group("Trip", [a])
    r = client.post(f"/api/v1/expenses/{gid}", json={
        "title": "Lunch", "amount": 100.0, "paid_by_id": b, "split_equally": True
    })
    assert r.status_code == 400


# --- Settlement tests ---
def test_settlement_plan_equal_split():
    a = make_member("Alice", "a@test.com")
    b = make_member("Bob", "b@test.com")
    gid = make_group("Trip", [a, b])
    # Alice pays 100 split equally → Bob owes Alice 50
    client.post(f"/api/v1/expenses/{gid}", json={
        "title": "Lunch", "amount": 100.0, "paid_by_id": a, "split_equally": True
    })
    r = client.get(f"/api/v1/settlements/{gid}")
    assert r.status_code == 200
    data = r.json()
    assert data["total_expenses"] == 100.0
    assert len(data["settlements"]) == 1
    assert data["settlements"][0]["amount"] == 50.0

def test_settlement_already_balanced():
    a = make_member("Alice", "a@test.com")
    b = make_member("Bob", "b@test.com")
    gid = make_group("Trip", [a, b])
    # Alice pays 100, Bob pays 100 — balanced
    client.post(f"/api/v1/expenses/{gid}", json={"title": "Lunch", "amount": 100.0, "paid_by_id": a, "split_equally": True})
    client.post(f"/api/v1/expenses/{gid}", json={"title": "Dinner", "amount": 100.0, "paid_by_id": b, "split_equally": True})
    r = client.get(f"/api/v1/settlements/{gid}")
    assert r.status_code == 200
    assert len(r.json()["settlements"]) == 0
