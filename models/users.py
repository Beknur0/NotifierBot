from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Model

if TYPE_CHECKING:
    from .notifications import NotificationsModel

class UsersModel(Model):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str | None] = mapped_column(default=None, nullable=True)

    notifications: Mapped[list["NotificationsModel"]] = relationship(back_populates="user")