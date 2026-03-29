from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.models.database import get_db
from app.models.models import Group, Member
from app.schemas.schemas import GroupCreate, GroupResponse, MemberCreate, MemberResponse

router = APIRouter()


@router.post("/members", response_model=MemberResponse, status_code=201)
def create_member(member: MemberCreate, db: Session = Depends(get_db)):
    if db.query(Member).filter(Member.email == member.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    m = Member(name=member.name, email=member.email)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.post("/", response_model=GroupResponse, status_code=201)
def create_group(group: GroupCreate, db: Session = Depends(get_db)):
    members = []
    for mid in group.member_ids:
        m = db.query(Member).filter(Member.id == mid).first()
        if not m:
            raise HTTPException(status_code=404, detail=f"Member {mid} not found")
        members.append(m)
    g = Group(name=group.name, description=group.description, members=members)
    db.add(g)
    db.commit()
    db.refresh(g)
    return g


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(group_id: int, db: Session = Depends(get_db)):
    g = db.query(Group).filter(Group.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    return g


@router.post("/{group_id}/members/{member_id}", response_model=GroupResponse)
def add_member_to_group(group_id: int, member_id: int, db: Session = Depends(get_db)):
    g = db.query(Group).filter(Group.id == group_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    m = db.query(Member).filter(Member.id == member_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Member not found")
    if m in g.members:
        raise HTTPException(status_code=400, detail="Member already in group")
    g.members.append(m)
    db.commit()
    db.refresh(g)
    return g


@router.get("/", response_model=list[GroupResponse])
def list_groups(db: Session = Depends(get_db)):
    return db.query(Group).all()
