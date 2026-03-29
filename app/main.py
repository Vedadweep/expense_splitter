from fastapi import FastAPI
from app.routers import groups, expenses, settlements
from app.models.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Expense Splitter Microservice",
    description="Split expenses among groups of people. Tracks balances and computes optimal settlements.",
    version="1.0.0"
)

app.include_router(groups.router, prefix="/api/v1/groups", tags=["Groups"])
app.include_router(expenses.router, prefix="/api/v1/expenses", tags=["Expenses"])
app.include_router(settlements.router, prefix="/api/v1/settlements", tags=["Settlements"])

@app.get("/")
def root():
    return {"service": "Expense Splitter", "version": "1.0.0", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "healthy"}
