"""Bean business logic with ownership enforcement.

Nothing stops two people (or the same person twice) from logging the same coffee, so a
name that already exists under the same roaster is a 409 the caller can override with
``allow_duplicate`` — see decision 22 in docs/ARCHITECTURE.md. ``merge_beans`` is the
cleanup path for the duplicates that got through anyway.
"""

from sqlalchemy.orm import Session

from bloom.core.logger import get_logger
from bloom.db.models.bean import Bean
from bloom.db.models.roaster import Roaster
from bloom.db.models.user import User
from bloom.repositories import beans as beans_repo
from bloom.repositories import roasters as roasters_repo
from bloom.schemas.bean import BeanCreate, BeanUpdate
from bloom.services import roaster_service
from bloom.services.access import owns_or_admin
from bloom.services.errors import ConflictError, ForbiddenError, NotFoundError

logger = get_logger(__name__)

# Fields describing the coffee itself, adopted from the source on a merge when the target
# holds no information for them. "unknown" is the no-information value of the two NOT NULL
# ones; every other field says so with NULL.
MERGEABLE_FIELDS = (
    "origin_country",
    "region",
    "producer",
    "variety",
    "process",
    "roast_level",
    "roast_type",
    "blend",
    "altitude_masl",
    "tasting_notes_label",
    "rating",
    "website",
    "notes",
)
EMPTY_VALUES = (None, "unknown")


def list_beans(db: Session, user: User, mine: bool = False) -> list[Bean]:
    """List beans. By default all (shared); ``mine`` restricts to the user's own."""
    if mine:
        return beans_repo.list_for_owner(db, user.id)
    return beans_repo.list_all(db)


def get_bean(db: Session, bean_id: int) -> Bean:
    """Fetch a bean (any user may read any bean), else raise NotFoundError."""
    bean = beans_repo.get(db, bean_id)
    if bean is None:
        raise NotFoundError("Bean not found")
    return bean


def get_owned_bean(db: Session, bean_id: int, user: User) -> Bean:
    """Fetch a bean the user may modify (owner or admin), else 404/403."""
    bean = get_bean(db, bean_id)
    if not owns_or_admin(user, bean.user_id):
        raise ForbiddenError("You do not own this bean")
    return bean


def _reject_duplicate(db: Session, *, roaster: Roaster, name: str, exclude_id: int | None, hint: str) -> None:
    existing = beans_repo.get_duplicate(db, roaster_id=roaster.id, name=name, exclude_id=exclude_id)
    if existing is not None:
        raise ConflictError(f"'{existing.name}' from {roaster.name} already exists (bean {existing.id}) — {hint}")


def create_bean(db: Session, data: BeanCreate, user: User, allow_duplicate: bool = False) -> Bean:
    """Create a bean owned by ``user``, resolving its roaster by name (created if new)."""
    fields = data.model_dump()
    roaster = roasters_repo.get_or_create(db, name=fields.pop("roaster"))
    if not allow_duplicate:
        _reject_duplicate(
            db,
            roaster=roaster,
            name=fields["name"],
            exclude_id=None,
            hint="open it, or resend with allow_duplicate=true",
        )
    bean = beans_repo.add(db, user_id=user.id, roaster_id=roaster.id, **fields)
    db.commit()
    db.refresh(bean)
    logger.info("Bean %s (%s) created by user %s", bean.id, bean.name, user.id)
    return bean


def update_bean(db: Session, bean: Bean, data: BeanUpdate, allow_duplicate: bool = False) -> Bean:
    """Apply a partial update to an already-authorized bean."""
    changes = data.model_dump(exclude_unset=True)
    roaster_name = changes.pop("roaster", None)
    previous_roaster = bean.roaster
    roaster = roasters_repo.get_or_create(db, name=roaster_name) if roaster_name is not None else previous_roaster
    # A rename (or a move to another roaster) can land on an existing pair just as a
    # creation can. Checked before the bean is touched, so a rejection leaves nothing
    # half-applied, and excluding the bean itself keeps re-saving unchanged values working.
    if not allow_duplicate and ("name" in changes or roaster_name is not None):
        _reject_duplicate(
            db,
            roaster=roaster,
            name=changes.get("name", bean.name),
            exclude_id=bean.id,
            hint="merge into it instead",
        )
    bean.roaster = roaster
    for field, value in changes.items():
        setattr(bean, field, value)
    if previous_roaster.id != roaster.id:
        db.flush()
        roaster_service.discard_if_abandoned(db, previous_roaster)
    db.commit()
    db.refresh(bean)
    logger.info("Bean %s updated: %s", bean.id, ", ".join(data.model_fields_set) or "no fields")
    return bean


def merge_beans(db: Session, *, target_id: int, source_id: int, user: User) -> Bean:
    """Move every brew and lot of ``source_id`` onto ``target_id``, then delete the source."""
    if target_id == source_id:
        raise ConflictError("Cannot merge a bean into itself")
    target = get_owned_bean(db, target_id, user)
    source = get_owned_bean(db, source_id, user)
    source_roaster = source.roaster

    # The duplicate is often the entry somebody filled in properly, so its data must not
    # die with it: keep the target's values and adopt the source's where it has none.
    adopted = {}
    for field in MERGEABLE_FIELDS:
        if getattr(target, field) in EMPTY_VALUES and getattr(source, field) not in EMPTY_VALUES:
            adopted[field] = getattr(source, field)
    for field, value in adopted.items():
        setattr(target, field, value)

    moved_brews, moved_lots = beans_repo.reassign_children(db, source_id=source.id, target_id=target.id)
    # The reassignment is a bulk UPDATE the session knows nothing about, so the source's
    # loaded collections are stale — deleting it now would cascade them (delete-orphan)
    # and take the brews and lots that just moved with it.
    db.expire(source)
    beans_repo.delete(db, source)
    db.flush()
    if source_roaster.id != target.roaster_id:
        roaster_service.discard_if_abandoned(db, source_roaster)
    db.commit()
    db.refresh(target)
    logger.info(
        "Bean %s merged into %s (%s brews, %s lots moved, adopted: %s)",
        source_id,
        target_id,
        moved_brews,
        moved_lots,
        ", ".join(adopted) or "nothing",
    )
    return target


def delete_bean(db: Session, bean: Bean) -> None:
    """Delete an already-authorized bean (cascades to its brews/tastings)."""
    bean_id = bean.id
    beans_repo.delete(db, bean)
    db.commit()
    logger.info("Bean %s deleted", bean_id)
