"""Bean business logic with ownership enforcement."""

from sqlalchemy.orm import Session

from bloom.core.logger import get_logger
from bloom.db.models.bean import Bean
from bloom.db.models.user import User
from bloom.repositories import beans as beans_repo
from bloom.schemas.bean import BeanCreate, BeanUpdate
from bloom.services.access import owns_or_admin
from bloom.services.errors import ForbiddenError, NotFoundError

logger = get_logger(__name__)


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


def create_bean(db: Session, data: BeanCreate, user: User) -> Bean:
    """Create a bean owned by ``user``."""
    bean = beans_repo.add(db, user_id=user.id, **data.model_dump())
    db.commit()
    db.refresh(bean)
    logger.info("Bean %s (%s) created by user %s", bean.id, bean.name, user.id)
    return bean


def update_bean(db: Session, bean: Bean, data: BeanUpdate) -> Bean:
    """Apply a partial update to an already-authorized bean."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(bean, field, value)
    db.commit()
    db.refresh(bean)
    return bean


def delete_bean(db: Session, bean: Bean) -> None:
    """Delete an already-authorized bean (cascades to its brews/tastings)."""
    beans_repo.delete(db, bean)
    db.commit()
