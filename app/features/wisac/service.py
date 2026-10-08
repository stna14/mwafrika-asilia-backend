from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.features.wisac.models import (
    WisacCategory,
    WisacCategoryGroup,
    WisacEdition,
    WisacNominee,
)
from app.features.wisac.schemas import (
    CategoryCreate,
    CategoryGroupCreate,
    CategoryGroupUpdate,
    CategoryUpdate,
    EditionCreate,
    EditionUpdate,
    NomineeCreate,
    NomineeUpdate,
)


# ---------- Editions ----------

def create_edition(db: Session, payload: EditionCreate) -> WisacEdition:
    existing = db.query(WisacEdition).filter(WisacEdition.year == payload.year).first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Edition for year {payload.year} already exists",
        )

    edition = WisacEdition(**payload.model_dump())
    db.add(edition)
    db.commit()
    db.refresh(edition)
    return edition


def get_edition(db: Session, edition_id: int) -> WisacEdition:
    edition = db.query(WisacEdition).filter(WisacEdition.id == edition_id).first()
    if edition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Edition not found"
        )
    return edition


def get_edition_by_year(db: Session, year: int) -> WisacEdition:
    edition = db.query(WisacEdition).filter(WisacEdition.year == year).first()
    if edition is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Edition for year {year} not found",
        )
    return edition


def list_editions(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    status_filter: str | None = None,
) -> tuple[list[WisacEdition], int]:
    query = db.query(WisacEdition)

    if status_filter:
        query = query.filter(WisacEdition.status == status_filter)

    total = query.with_entities(func.count(WisacEdition.id)).scalar() or 0

    items = (
        query.order_by(WisacEdition.year.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def update_edition(
    db: Session, edition_id: int, payload: EditionUpdate
) -> WisacEdition:
    edition = get_edition(db, edition_id)
    data = payload.model_dump(exclude_unset=True)

    if "year" in data and data["year"] != edition.year:
        clash = (
            db.query(WisacEdition)
            .filter(
                WisacEdition.year == data["year"],
                WisacEdition.id != edition.id,
            )
            .first()
        )
        if clash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Edition for year {data['year']} already exists",
            )

    for key, value in data.items():
        setattr(edition, key, value)

    db.commit()
    db.refresh(edition)
    return edition


def delete_edition(db: Session, edition_id: int) -> None:
    edition = get_edition(db, edition_id)
    db.delete(edition)
    db.commit()


# ---------- Category Groups ----------

def create_category_group(db: Session, payload: CategoryGroupCreate) -> WisacCategoryGroup:
    get_edition(db, payload.edition_id)

    group = WisacCategoryGroup(**payload.model_dump())
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def get_category_group(db: Session, group_id: int) -> WisacCategoryGroup:
    group = db.query(WisacCategoryGroup).filter(WisacCategoryGroup.id == group_id).first()
    if group is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category group not found"
        )
    return group


def list_category_groups(
    db: Session,
    *,
    edition_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[WisacCategoryGroup], int]:
    query = db.query(WisacCategoryGroup)

    if edition_id is not None:
        query = query.filter(WisacCategoryGroup.edition_id == edition_id)

    total = query.with_entities(func.count(WisacCategoryGroup.id)).scalar() or 0

    items = (
        query.order_by(
            WisacCategoryGroup.display_order.asc(),
            WisacCategoryGroup.name.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def update_category_group(
    db: Session, group_id: int, payload: CategoryGroupUpdate
) -> WisacCategoryGroup:
    group = get_category_group(db, group_id)
    data = payload.model_dump(exclude_unset=True)

    if "edition_id" in data and data["edition_id"]:
        get_edition(db, data["edition_id"])

    for key, value in data.items():
        setattr(group, key, value)

    db.commit()
    db.refresh(group)
    return group


def delete_category_group(db: Session, group_id: int) -> None:
    group = get_category_group(db, group_id)
    db.delete(group)
    db.commit()


# ---------- Categories ----------

def create_category(db: Session, payload: CategoryCreate) -> WisacCategory:
    get_edition(db, payload.edition_id)
    if payload.group_id is not None:
        get_category_group(db, payload.group_id)

    category = WisacCategory(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def get_category(db: Session, category_id: int) -> WisacCategory:
    category = db.query(WisacCategory).filter(WisacCategory.id == category_id).first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )
    return category


def list_categories(
    db: Session,
    *,
    edition_id: int | None = None,
    group_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[WisacCategory], int]:
    query = db.query(WisacCategory)

    if edition_id is not None:
        query = query.filter(WisacCategory.edition_id == edition_id)
    if group_id is not None:
        query = query.filter(WisacCategory.group_id == group_id)

    total = query.with_entities(func.count(WisacCategory.id)).scalar() or 0

    items = (
        query.order_by(
            WisacCategory.display_order.asc(),
            WisacCategory.name.asc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def update_category(
    db: Session, category_id: int, payload: CategoryUpdate
) -> WisacCategory:
    category = get_category(db, category_id)
    data = payload.model_dump(exclude_unset=True)

    if "edition_id" in data and data["edition_id"]:
        get_edition(db, data["edition_id"])
    if "group_id" in data and data["group_id"] is not None:
        get_category_group(db, data["group_id"])

    for key, value in data.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> None:
    category = get_category(db, category_id)
    db.delete(category)
    db.commit()


# ---------- Nominees ----------

def create_nominee(db: Session, payload: NomineeCreate) -> WisacNominee:
    category = get_category(db, payload.category_id)

    data = payload.model_dump()
    data["edition_id"] = category.edition_id

    nominee = WisacNominee(**data)
    db.add(nominee)
    db.commit()
    db.refresh(nominee)
    return nominee


def get_nominee(db: Session, nominee_id: int) -> WisacNominee:
    nominee = db.query(WisacNominee).filter(WisacNominee.id == nominee_id).first()
    if nominee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Nominee not found"
        )
    return nominee


def list_nominees(
    db: Session,
    *,
    category_id: int | None = None,
    edition_id: int | None = None,
    status_filter: str | None = None,
    winner_only: bool = False,
    limit: int = 200,
    offset: int = 0,
) -> tuple[list[WisacNominee], int]:
    query = db.query(WisacNominee)

    if category_id is not None:
        query = query.filter(WisacNominee.category_id == category_id)
    if edition_id is not None:
        query = query.filter(WisacNominee.edition_id == edition_id)
    if status_filter:
        query = query.filter(WisacNominee.status == status_filter)
    if winner_only:
        query = query.filter(WisacNominee.winner.is_(True))

    total = query.with_entities(func.count(WisacNominee.id)).scalar() or 0

    items = (
        query.order_by(WisacNominee.total_votes.desc(), WisacNominee.full_name.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return items, total


def update_nominee(
    db: Session, nominee_id: int, payload: NomineeUpdate
) -> WisacNominee:
    nominee = get_nominee(db, nominee_id)
    data = payload.model_dump(exclude_unset=True)

    if "category_id" in data and data["category_id"]:
        category = get_category(db, data["category_id"])
        data["edition_id"] = category.edition_id

    for key, value in data.items():
        setattr(nominee, key, value)

    db.commit()
    db.refresh(nominee)
    return nominee


def delete_nominee(db: Session, nominee_id: int) -> None:
    nominee = get_nominee(db, nominee_id)
    db.delete(nominee)
    db.commit()


# ---------- Winners / Rankings ----------

def _nominee_to_winner_dict(
    nominee: WisacNominee,
    category: WisacCategory,
    edition: WisacEdition,
) -> dict:
    return {
        "nominee_id": nominee.id,
        "name": nominee.stage_name or nominee.full_name,
        "image": nominee.profile_image_url,
        "category_id": category.id,
        "category_name": category.name,
        "edition_id": edition.id,
        "edition_year": edition.year,
        "total_votes": nominee.total_votes or 0,
        "total_free_votes": nominee.total_free_votes or 0,
        "total_paid_votes": nominee.total_paid_votes or 0,
        "winner": bool(nominee.winner),
    }


def list_winners_detailed(
    db: Session,
    *,
    edition_id: int | None = None,
) -> list[dict]:
    query = (
        db.query(WisacNominee, WisacCategory, WisacEdition)
        .join(WisacCategory, WisacNominee.category_id == WisacCategory.id)
        .join(WisacEdition, WisacNominee.edition_id == WisacEdition.id)
        .filter(WisacNominee.winner.is_(True))
    )

    if edition_id is not None:
        query = query.filter(WisacNominee.edition_id == edition_id)

    rows = query.order_by(
        WisacEdition.year.desc(),
        WisacCategory.display_order.asc(),
    ).all()

    return [_nominee_to_winner_dict(nominee, category, edition) for nominee, category, edition in rows]


def list_rankings(
    db: Session,
    *,
    edition_id: int,
) -> list[dict]:
    edition = get_edition(db, edition_id)

    categories = (
        db.query(WisacCategory)
        .filter(WisacCategory.edition_id == edition_id)
        .order_by(WisacCategory.display_order.asc(), WisacCategory.name.asc())
        .all()
    )

    result: list[dict] = []
    for category in categories:
        nominees = (
            db.query(WisacNominee)
            .filter(WisacNominee.category_id == category.id)
            .order_by(
                WisacNominee.total_votes.desc(),
                WisacNominee.full_name.asc(),
            )
            .all()
        )
        result.append(
            {
                "category_id": category.id,
                "category_name": category.name,
                "edition_id": edition.id,
                "edition_year": edition.year,
                "nominees": [
                    _nominee_to_winner_dict(nominee, category, edition)
                    for nominee in nominees
                ],
            }
        )
    return result


def confirm_winner(
    db: Session,
    *,
    category_id: int,
    nominee_id: int,
) -> WisacNominee:
    category = get_category(db, category_id)
    nominee = get_nominee(db, nominee_id)

    if nominee.category_id != category.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nominee does not belong to this category",
        )

    (
        db.query(WisacNominee)
        .filter(WisacNominee.category_id == category.id)
        .update({WisacNominee.winner: False}, synchronize_session=False)
    )
    nominee.winner = True
    db.commit()
    db.refresh(nominee)
    return nominee
