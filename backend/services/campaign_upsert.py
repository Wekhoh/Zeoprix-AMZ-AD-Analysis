"""Campaign / placement / daily-record upsert helpers.

Extracted from ``import_service.py`` to keep the orchestration module
focused on file-handling + orchestration. These helpers are used by the
CSV and operation-log import paths.
"""

from sqlalchemy.orm import Session

from backend.models import (
    AdGroup,
    Campaign,
    CampaignDailyRecord,
    Marketplace,
    PlacementRecord,
)
from backend.utils.campaign_parser import (
    extract_bidding_strategy_type,
    extract_default_bid,
    get_portfolio_name,
)


def get_or_create_campaign(db: Session, campaign_name: str, bidding_strategy: str = "") -> Campaign:
    """Get the US-marketplace Campaign by name; create it (and its 1:1
    AdGroup) if missing.

    Note: this helper is scoped to the default "US" marketplace — it's
    used by the import path which predates multi-marketplace support.
    ``backend/services/migration_service.py`` has a different helper
    with the same base name but a marketplace-id parameter.
    """
    marketplace = db.query(Marketplace).filter_by(code="US").first()
    if not marketplace:
        marketplace = Marketplace(code="US", name="美国站", currency="USD")
        db.add(marketplace)
        db.flush()

    campaign = (
        db.query(Campaign).filter_by(name=campaign_name, marketplace_id=marketplace.id).first()
    )
    if campaign:
        return campaign

    strategy = bidding_strategy or extract_bidding_strategy_type(campaign_name)
    campaign = Campaign(
        name=campaign_name,
        marketplace_id=marketplace.id,
        ad_type="SP",
        targeting_type="auto",
        match_type="close",
        bidding_strategy=strategy,
        base_bid=extract_default_bid(campaign_name),
        portfolio=get_portfolio_name(campaign_name),
    )
    db.add(campaign)
    db.flush()

    # 1:1 ad group mirrors the campaign
    ad_group = AdGroup(
        campaign_id=campaign.id,
        name=campaign_name,
        default_bid=extract_default_bid(campaign_name),
    )
    db.add(ad_group)
    db.flush()

    return campaign


def upsert_placement_record(db: Session, campaign_id: int, data: dict) -> str:
    """Insert-or-update a PlacementRecord keyed by (date, campaign_id,
    placement_type). Returns one of ``'imported' / 'updated' / 'skipped'``.

    Float comparisons use a 0.01 tolerance to avoid spurious updates from
    CSV float-precision noise.
    """
    existing = (
        db.query(PlacementRecord)
        .filter_by(
            date=data["date"],
            campaign_id=campaign_id,
            placement_type=data["placement"],
        )
        .first()
    )

    if existing:
        changed = False
        for field, db_field in [
            ("impressions", "impressions"),
            ("clicks", "clicks"),
            ("spend", "spend"),
            ("orders", "orders"),
            ("sales", "sales"),
        ]:
            old_val = getattr(existing, db_field)
            new_val = data[field]
            if isinstance(new_val, float):
                if abs((old_val or 0) - new_val) > 0.01:
                    setattr(existing, db_field, new_val)
                    changed = True
            elif old_val != new_val:
                setattr(existing, db_field, new_val)
                changed = True

        return "updated" if changed else "skipped"

    record = PlacementRecord(
        date=data["date"],
        campaign_id=campaign_id,
        placement_type=data["placement"],
        bidding_strategy=data.get("bidding_strategy"),
        impressions=data["impressions"],
        clicks=data["clicks"],
        spend=data["spend"],
        orders=data["orders"],
        sales=data["sales"],
    )
    db.add(record)
    return "imported"


def upsert_campaign_daily_record(db: Session, campaign_id: int, data: dict) -> str:
    """Insert-or-update a CampaignDailyRecord keyed by (date, campaign_id).
    Returns ``'imported' / 'updated' / 'skipped'`` with the same
    float-tolerance semantics as :func:`upsert_placement_record`.
    """
    existing = (
        db.query(CampaignDailyRecord).filter_by(date=data["date"], campaign_id=campaign_id).first()
    )

    if existing:
        changed = False
        for field in ["impressions", "clicks", "spend", "orders", "sales"]:
            old_val = getattr(existing, field)
            new_val = data[field]
            if isinstance(new_val, float):
                if abs((old_val or 0) - new_val) > 0.01:
                    setattr(existing, field, new_val)
                    changed = True
            elif old_val != new_val:
                setattr(existing, field, new_val)
                changed = True
        return "updated" if changed else "skipped"

    record = CampaignDailyRecord(
        date=data["date"],
        campaign_id=campaign_id,
        impressions=data["impressions"],
        clicks=data["clicks"],
        spend=data["spend"],
        orders=data["orders"],
        sales=data["sales"],
    )
    db.add(record)
    return "imported"
