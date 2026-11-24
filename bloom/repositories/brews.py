"""Brew repository — the only place that runs SQL for brews."""

from typing import Any

from sqlalchemy import Select, exists, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from bloom.db.models.bean import Bean
from bloom.db.models.brew import Brew
from bloom.db.models.brew_method import BrewMethod
from bloom.db.models.roaster import Roaster
from bloom.db.models.tasting import Tasting
from bloom.db.models.user import User


def get(db: Session, brew_id: int) -> Brew | None:
    return db.get(Brew, brew_id)


def list_page(
    db: Session,
    *,
    viewer_id: int,
    limit: int,
    offset: int,
    author_id: int | None = None,
    bean_id: int | None = None,
    roaster_id: int | None = None,
    method_id: int | None = None,
    untasted: bool = False,
    q: str | None = None,
) -> tuple[list[Brew], int]:
    """One page of brews (most recent first) matching the filters, plus the total match count.

    ``untasted`` means not yet tasted by ``viewer_id``. Tastings are loaded with the page so the
    caller can pick out the viewer's own without a query per brew.
    """
    stmt: Select[tuple[Brew]] = select(Brew)
    if author_id is not None:
        stmt = stmt.where(Brew.user_id == author_id)
    if bean_id is not None:
        stmt = stmt.where(Brew.bean_id == bean_id)
    if roaster_id is not None:
        stmt = stmt.where(Brew.bean.has(Bean.roaster_id == roaster_id))
    if method_id is not None:
        stmt = stmt.where(Brew.method_id == method_id)
    if untasted:
        stmt = stmt.where(~exists().where(Tasting.brew_id == Brew.id, Tasting.user_id == viewer_id))
    if q:
        stmt = stmt.where(
            or_(
                Brew.bean.has(Bean.name.icontains(q, autoescape=True)),
                Brew.bean.has(Bean.roaster.has(Roaster.name.icontains(q, autoescape=True))),
                Brew.method.has(BrewMethod.name.icontains(q, autoescape=True)),
                Brew.author.has(User.username.icontains(q, autoescape=True)),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    page = (
        stmt.options(joinedload(Brew.method), joinedload(Brew.author), selectinload(Brew.tastings))
        .order_by(Brew.brewed_at.desc(), Brew.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(db.execute(page).unique().scalars().all()), total


def add(db: Session, **fields: Any) -> Brew:
    brew = Brew(**fields)
    db.add(brew)
    db.flush()
    return brew


def delete(db: Session, brew: Brew) -> None:
    db.delete(brew)
