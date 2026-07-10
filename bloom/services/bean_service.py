"""Bean business logic with ownership enforcement."""

from sqlalchemy.orm import Session

from bloom.db.models.bean import Bean
from bloom.db.models.user import User
from bloom.repositories import beans as beans_repo
from bloom.schemas.bean import BeanCreate, BeanUpdate
from bloom.services.access import owns_or_admin
from bloom.services.errors import NotFoundError


def list_beans(db: Session, user: User) -> list[Bean]:
    """List beans the user may see: their own, or all for an admin."""
    return beans_repo.list_for_user(db, None if user.role == "admin" else user.id)


def get_bean(db: Session, bean_id: int, user: User) -> Bean:
    """Fetch a bean the user may access, else raise NotFoundError."""
    bean = beans_repo.get(db, bean_id)
    if bean is None or not owns_or_admin(user, bean.user_id):
        raise NotFoundError("Bean not found")
    return bean


def create_bean(db: Session, data: BeanCreate, user: User) -> Bean:
    """Create a bean owned by ``user``."""
    bean = beans_repo.add(db, user_id=user.id, **data.model_dump())
    db.commit()
    db.refresh(bean)
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
