from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import Group, Member, Expense, ExpenseShare
from app.schemas.schemas import ExpenseCreate, ExpenseResponse

router = APIRouter()


@router.post("/{group_id}", response_model=ExpenseResponse, status_code=201)
def add_expense(group_id: int, expense: ExpenseCreate, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    payer = db.query(Member).filter(Member.id == expense.paid_by_id).first()
    if not payer:
        raise HTTPException(status_code=404, detail="Payer member not found")
    if payer not in group.members:
        raise HTTPException(status_code=400, detail="Payer is not a member of this group")

    db_expense = Expense(
        group_id=group_id,
        paid_by_id=expense.paid_by_id,
        title=expense.title,
        amount=expense.amount,
        category=expense.category
    )
    db.add(db_expense)
    db.flush()  # get db_expense.id before commit

    # --- Split Logic ---
    if expense.split_equally:
        per_person = round(expense.amount / len(group.members), 2)
        for member in group.members:
            share = ExpenseShare(
                expense_id=db_expense.id,
                member_id=member.id,
                share_amount=per_person
            )
            db.add(share)
    else:
        if not expense.custom_splits:
            raise HTTPException(status_code=400, detail="custom_splits required when split_equally=false")
        total = sum(expense.custom_splits.values())
        if round(total, 2) != round(expense.amount, 2):
            raise HTTPException(status_code=400, detail=f"Custom splits sum ({total}) must equal expense amount ({expense.amount})")
        for member_id_str, amount in expense.custom_splits.items():
            member_id = int(member_id_str)
            m = db.query(Member).filter(Member.id == member_id).first()
            if not m or m not in group.members:
                raise HTTPException(status_code=400, detail=f"Member {member_id} not in group")
            share = ExpenseShare(expense_id=db_expense.id, member_id=member_id, share_amount=amount)
            db.add(share)

    db.commit()
    db.refresh(db_expense)
    return db_expense


@router.get("/{group_id}", response_model=list[ExpenseResponse])
def list_expenses(group_id: int, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return db.query(Expense).filter(Expense.group_id == group_id).all()


@router.delete("/{group_id}/{expense_id}", status_code=204)
def delete_expense(group_id: int, expense_id: int, db: Session = Depends(get_db)):
    expense = db.query(Expense).filter(
        Expense.id == expense_id, Expense.group_id == group_id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
