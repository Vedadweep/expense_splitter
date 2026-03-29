from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


class MemberCreate(BaseModel):
    name: str
    email: EmailStr

class MemberResponse(BaseModel):
    id: int
    name: str
    email: str
    class Config:
        from_attributes = True


class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    member_ids: List[int] = []

class GroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    members: List[MemberResponse] = []
    class Config:
        from_attributes = True


class ExpenseCreate(BaseModel):
    title: str
    amount: float
    paid_by_id: int
    category: Optional[str] = "General"
    split_equally: bool = True
    custom_splits: Optional[dict] = None  # {member_id: amount}

class ExpenseShareResponse(BaseModel):
    member_id: int
    share_amount: float
    class Config:
        from_attributes = True

class ExpenseResponse(BaseModel):
    id: int
    group_id: int
    title: str
    amount: float
    category: str
    paid_by_id: int
    created_at: datetime
    shares: List[ExpenseShareResponse] = []
    class Config:
        from_attributes = True


class BalanceEntry(BaseModel):
    member_id: int
    member_name: str
    net_balance: float  # positive = owed money, negative = owes money

class Settlement(BaseModel):
    from_member: str
    to_member: str
    amount: float

class SettlementPlan(BaseModel):
    group_id: int
    balances: List[BalanceEntry]
    settlements: List[Settlement]
    total_expenses: float
