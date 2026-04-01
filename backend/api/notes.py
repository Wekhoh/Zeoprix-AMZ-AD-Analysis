"""运营笔记 API"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.note import Note

router = APIRouter()


class NoteCreate(BaseModel):
    campaign_id: Optional[int] = None
    date: Optional[str] = None
    content: str
    note_type: str = "decision"


class NoteOut(BaseModel):
    id: int
    campaign_id: Optional[int]
    date: Optional[str]
    content: str
    note_type: str
    created_at: Optional[str]

    model_config = {"from_attributes": True}


@router.get("", response_model=list[NoteOut])
def list_notes(
    campaign_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    """获取笔记列表"""
    q = db.query(Note)
    if campaign_id:
        q = q.filter(Note.campaign_id == campaign_id)
    notes = q.order_by(Note.created_at.desc()).all()
    return [
        NoteOut(
            id=n.id,
            campaign_id=n.campaign_id,
            date=n.date,
            content=n.content,
            note_type=n.note_type,
            created_at=str(n.created_at) if n.created_at else None,
        )
        for n in notes
    ]


@router.post("", response_model=NoteOut)
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    """创建笔记"""
    record = Note(
        campaign_id=note.campaign_id,
        date=note.date,
        content=note.content,
        note_type=note.note_type,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return NoteOut(
        id=record.id,
        campaign_id=record.campaign_id,
        date=record.date,
        content=record.content,
        note_type=record.note_type,
        created_at=str(record.created_at) if record.created_at else None,
    )


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """删除笔记"""
    record = db.query(Note).filter_by(id=note_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="笔记不存在")
    db.delete(record)
    db.commit()
    return {"success": True}
