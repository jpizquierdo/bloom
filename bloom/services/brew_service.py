"""Brew business logic: ownership, the domain EY calculation, and serialization."""

from decimal import Decimal

from sqlalchemy.orm import Session

from bloom.db.models.brew import Brew
from bloom.db.models.user import User
from bloom.domain.calculations import brew_ratio, classify_extraction, extraction_yield
from bloom.repositories import brews as brews_repo
from bloom.schemas.brew import BrewCreate, BrewRead, BrewUpdate, ExtractionDiagnosticsRead
from bloom.services import bean_service, lookups_service
from bloom.services.access import owns_or_admin
from bloom.services.errors import ForbiddenError, NotFoundError


def serialize(brew: Brew) -> BrewRead:
    """Build a BrewRead, computing the (unstored) ratio and diagnostics."""
    category = brew.method.category
    ratio = brew_ratio(brew.dose_grams, brew.yield_grams, brew.water_grams, category)
    if ratio is not None:
        ratio = ratio.quantize(Decimal("0.01"))
    diagnostics = classify_extraction(
        brew.tds_percent, brew.extraction_yield_percent, category
    )
    read = BrewRead.model_validate(brew)
    read.ratio = ratio
    read.diagnostics = ExtractionDiagnosticsRead(
        strength=diagnostics.strength, extraction=diagnostics.extraction
    )
    return read


def list_brews(db: Session) -> list[Brew]:
    """List all brews — the brew log is shared across the instance."""
    return brews_repo.list_all(db)


def get_brew(db: Session, brew_id: int) -> Brew:
    """Fetch a brew (any user may read any brew), else raise NotFoundError."""
    brew = brews_repo.get(db, brew_id)
    if brew is None:
        raise NotFoundError("Brew not found")
    return brew


def get_owned_brew(db: Session, brew_id: int, user: User) -> Brew:
    """Fetch a brew the user may modify (its author or an admin), else 404/403."""
    brew = get_brew(db, brew_id)
    if not owns_or_admin(user, brew.user_id):
        raise ForbiddenError("You are not the author of this brew")
    return brew


def create_brew(db: Session, data: BrewCreate, user: User) -> Brew:
    """Create a brew (authored by ``user``) after validating refs and computing EY.

    Beans are shared, so a brew may be made from any existing bean; ``user`` is
    recorded as the author. Extraction yield is stored once at write time when
    only TDS was measured (and beverage mass is known); an explicit value is kept.
    """
    # Validate references (each raises NotFoundError on failure). The bean only
    # needs to exist — beans are shared, not owned per-brew.
    bean_service.get_bean(db, data.bean_id)
    lookups_service.get_brew_method(db, data.method_id)
    if data.grinder_id is not None:
        lookups_service.get_equipment(db, data.grinder_id)

    ey = data.extraction_yield_percent
    if ey is None and data.tds_percent is not None:
        ey = extraction_yield(data.tds_percent, data.yield_grams, data.dose_grams)

    payload = data.model_dump(exclude_none=True)
    if ey is not None:
        payload["extraction_yield_percent"] = ey
    else:
        payload.pop("extraction_yield_percent", None)

    brew = brews_repo.add(db, user_id=user.id, **payload)
    db.commit()
    db.refresh(brew)
    return brew


def update_brew(db: Session, brew: Brew, data: BrewUpdate) -> Brew:
    """Apply a partial update to an already-authorized brew."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(brew, field, value)
    db.commit()
    db.refresh(brew)
    return brew


def delete_brew(db: Session, brew: Brew) -> None:
    """Delete an already-authorized brew (cascades to its tastings)."""
    brews_repo.delete(db, brew)
    db.commit()
