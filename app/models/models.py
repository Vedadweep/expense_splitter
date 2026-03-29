from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.database import Base

# Many-to-many: members in a group
group_members = Table(
    "group_members", Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.id")),
    Column("member_id", Integer, ForeignKey("members.id"))
)


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("Member", secondary=group_members, back_populates="groups")
    expenses = relationship("Expense", back_populates="group", cascade="all, delete")


class Member(Base):
    __tablename__ = "members"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)

    groups = relationship("Group", secondary=group_members, back_populates="members")
    paid_expenses = relationship("Expense", back_populates="paid_by")
    shares = relationship("ExpenseShare", back_populates="member")


class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    paid_by_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    title = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String, default="General")
    created_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="expenses")
    paid_by = relationship("Member", back_populates="paid_expenses")
    shares = relationship("ExpenseShare", back_populates="expense", cascade="all, delete")


class ExpenseShare(Base):
    __tablename__ = "expense_shares"
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("members.id"), nullable=False)
    share_amount = Column(Float, nullable=False)

    expense = relationship("Expense", back_populates="shares")
    member = relationship("Member", back_populates="shares")
