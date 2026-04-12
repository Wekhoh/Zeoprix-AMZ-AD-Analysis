"""自动化规则 API"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Rule
from backend.services.rule_engine import evaluate_rules, get_rule_results

router = APIRouter()


class RuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    condition_field: str
    condition_operator: str
    condition_value: float
    condition_min_data: int = 0
    period_days: int = 7
    action_type: str
    is_active: int = 1


class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    condition_field: Optional[str] = None
    condition_operator: Optional[str] = None
    condition_value: Optional[float] = None
    condition_min_data: Optional[int] = None
    period_days: Optional[int] = None
    action_type: Optional[str] = None
    is_active: Optional[int] = None


@router.get("")
def list_rules(db: Session = Depends(get_db)):
    """列出所有规则"""
    rules = db.query(Rule).order_by(Rule.id).all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "condition_field": r.condition_field,
            "condition_operator": r.condition_operator,
            "condition_value": r.condition_value,
            "condition_min_data": r.condition_min_data,
            "period_days": r.period_days,
            "action_type": r.action_type,
            "is_active": r.is_active,
            "last_run_at": r.last_run_at,
            "created_at": str(r.created_at) if r.created_at else None,
        }
        for r in rules
    ]


@router.post("")
def create_rule(body: RuleCreate, db: Session = Depends(get_db)):
    """创建规则"""
    valid_fields = {"acos", "roas", "clicks", "orders", "spend", "ctr", "cpc"}
    if body.condition_field not in valid_fields:
        raise HTTPException(
            status_code=400,
            detail=f"无效条件字段，可选: {', '.join(sorted(valid_fields))}",
        )

    valid_operators = {">", "<", ">=", "<=", "=="}
    if body.condition_operator not in valid_operators:
        raise HTTPException(
            status_code=400,
            detail=f"无效操作符，可选: {', '.join(sorted(valid_operators))}",
        )

    rule = Rule(
        name=body.name,
        description=body.description,
        condition_field=body.condition_field,
        condition_operator=body.condition_operator,
        condition_value=body.condition_value,
        condition_min_data=body.condition_min_data,
        period_days=body.period_days,
        action_type=body.action_type,
        is_active=body.is_active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return {"id": rule.id, "name": rule.name}


@router.put("/{rule_id}")
def update_rule(rule_id: int, body: RuleUpdate, db: Session = Depends(get_db)):
    """更新规则"""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)

    db.commit()
    return {"id": rule.id, "name": rule.name}


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """删除规则"""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    db.delete(rule)
    db.commit()
    return {"success": True}


@router.post("/evaluate")
def evaluate_all_rules(db: Session = Depends(get_db)):
    """手动触发所有规则评估"""
    results = evaluate_rules(db)
    return {"total_triggered": len(results), "results": results}


@router.get("/{rule_id}/results")
def get_single_rule_results(rule_id: int, db: Session = Depends(get_db)):
    """获取指定规则的评估结果"""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    results = get_rule_results(db, rule_id)
    return {"rule_id": rule_id, "rule_name": rule.name, "results": results}


@router.get("/suggestions/bulk-upload-export")
def export_suggestions_bulk_upload(db: Session = Depends(get_db)):
    """导出所有规则建议为 Amazon Bulk Upload Excel。

    运营下载后：
    1. 填写 Bid/Budget 列的具体数值
    2. 删除"参考:"开头的列
    3. 上传到 Seller Central → Campaign Manager → Bulk Operations
    """
    from io import BytesIO

    from fastapi.responses import StreamingResponse

    from backend.services.bulk_upload_service import generate_suggestion_bulk_upload

    results = evaluate_rules(db)
    excel_bytes = generate_suggestion_bulk_upload(results)

    return StreamingResponse(
        BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=suggestion_bulk_upload.xlsx"},
    )


@router.get("/{rule_id}/dry-run")
def dry_run_rule(rule_id: int, db: Session = Depends(get_db)):
    """Dry Run 预览：查看该规则如果执行会触发多少活动，不产生任何副作用。

    与 /results 的区别：dry-run 不更新 last_run_at，不写入数据库。
    运营可以在正式执行前确认影响范围。
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="规则不存在")
    results = get_rule_results(db, rule_id, dry_run=True)
    return {
        "rule_id": rule_id,
        "rule_name": rule.name,
        "dry_run": True,
        "total_triggered": len(results),
        "results": results,
    }
