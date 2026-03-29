from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from collections import defaultdict
from app.models.database import get_db
from app.models.models import Group, Expense, ExpenseShare
from app.schemas.schemas import SettlementPlan, BalanceEntry, Settlement

router = APIRouter()


def minimize_settlements(balances: dict) -> list[Settlement]:
    """
    Greedy algorithm to minimize the number of transactions needed to settle all debts.
    Time complexity: O(n log n) where n = number of members.
    """
    creditors = []  # people owed money (positive balance)
    debtors = []    # people who owe money (negative balance)

    for name, balance in balances.items():
        if balance > 0.01:
            creditors.append([balance, name])
        elif balance < -0.01:
            debtors.append([abs(balance), name])

    creditors.sort(reverse=True)
    debtors.sort(reverse=True)

    settlements = []
    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        credit_amt, creditor = creditors[i]
        debt_amt, debtor = debtors[j]
        transfer = min(credit_amt, debt_amt)

        settlements.append(Settlement(
            from_member=debtor,
            to_member=creditor,
            amount=round(transfer, 2)
        ))

        creditors[i][0] -= transfer
        debtors[j][0] -= transfer

        if creditors[i][0] < 0.01:
            i += 1
        if debtors[j][0] < 0.01:
            j += 1

    return settlements


@router.get("/{group_id}", response_model=SettlementPlan)
def get_settlement_plan(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    expenses = db.query(Expense).filter(Expense.group_id == group_id).all()

    # Build balance map: member_id -> net balance
    paid = defaultdict(float)   # how much each member paid
    owed = defaultdict(float)   # how much each member owes

    total_expenses = 0.0
    for exp in expenses:
        paid[exp.paid_by_id] += exp.amount
        total_expenses += exp.amount
        for share in exp.shares:
            owed[share.member_id] += share.share_amount

    # Net balance = paid - owed (positive = others owe you, negative = you owe others)
    member_map = {m.id: m.name for m in group.members}
    net_balances = {}
    for member in group.members:
        net_balances[member.name] = round(paid[member.id] - owed[member.id], 2)

    balance_entries = [
        BalanceEntry(
            member_id=m.id,
            member_name=m.name,
            net_balance=net_balances[m.name]
        )
        for m in group.members
    ]

    settlements = minimize_settlements(net_balances)

    return SettlementPlan(
        group_id=group_id,
        balances=balance_entries,
        settlements=settlements,
        total_expenses=round(total_expenses, 2)
    )
