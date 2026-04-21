"""运营笔记 API"""

from datetime import datetime
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


@router.get("")
def list_notes(
    campaign_id: Optional[int] = Query(None),
    page: Optional[int] = Query(None, ge=1),
    page_size: Optional[int] = Query(None, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """获取笔记列表（不含软删除）.

    Backward-compatible pagination: if neither ``page`` nor ``page_size`` is
    supplied, returns a flat list (legacy shape used by
    ``CampaignDetail.tsx:159,170``). If either is supplied, returns
    ``{data, total, page, page_size}``.
    """
    q = db.query(Note).filter(Note.deleted_at.is_(None))
    if campaign_id:
        q = q.filter(Note.campaign_id == campaign_id)
    q = q.order_by(Note.created_at.desc())

    paginated = page is not None or page_size is not None
    total = q.count() if paginated else 0
    if paginated:
        _page = page or 1
        _size = page_size or 50
        notes = q.offset((_page - 1) * _size).limit(_size).all()
    else:
        notes = q.all()

    items = [
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

    if paginated:
        return {
            "data": items,
            "total": total,
            "page": page or 1,
            "page_size": page_size or 50,
        }
    return items


@router.get("/trash")
def list_trashed_notes(db: Session = Depends(get_db)):
    """获取已删除的笔记（回收站）"""
    notes = (
        db.query(Note).filter(Note.deleted_at.isnot(None)).order_by(Note.deleted_at.desc()).all()
    )
    return [
        {
            "id": n.id,
            "campaign_id": n.campaign_id,
            "date": n.date,
            "content": n.content,
            "note_type": n.note_type,
            "created_at": str(n.created_at) if n.created_at else None,
            "deleted_at": n.deleted_at,
        }
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
    """软删除笔记（可通过 /notes/{id}/restore 恢复）"""
    record = db.query(Note).filter_by(id=note_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="笔记不存在")
    if record.deleted_at:
        raise HTTPException(status_code=400, detail="笔记已在回收站")
    record.deleted_at = datetime.utcnow().isoformat(timespec="seconds")
    db.commit()
    return {"success": True, "id": note_id, "deleted_at": record.deleted_at}


@router.post("/{note_id}/restore")
def restore_note(note_id: int, db: Session = Depends(get_db)):
    """从回收站恢复笔记"""
    record = db.query(Note).filter_by(id=note_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="笔记不存在")
    record.deleted_at = None
    db.commit()
    return {"success": True, "id": note_id}


@router.delete("/{note_id}/permanent")
def permanently_delete_note(note_id: int, db: Session = Depends(get_db)):
    """永久删除笔记（无法恢复）"""
    record = db.query(Note).filter_by(id=note_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="笔记不存在")
    db.delete(record)
    db.commit()
    return {"success": True}
