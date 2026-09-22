from datetime import date as date_type
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import func, ForeignKey

from database import Model

if TYPE_CHECKING:
    from .users import UsersModel

class NotificationsModel(Model):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    title: Mapped[str] = mapped_column(nullable=False)
    job_id: Mapped[str] = mapped_column(nullable=False, unique=True)
    repeat_type: Mapped[str] = mapped_column(nullable=False)
    date: Mapped[date_type | None] = mapped_column(default=None, nullable=True)
    time: Mapped[str | None] = mapped_column(default=None, nullable=True)
    timer_seconds: Mapped[int | None] = mapped_column(default=None, nullable=True)
    weekdays: Mapped[str | None] = mapped_column(default=None, nullable=True)
    month_day: Mapped[str | None] = mapped_column(default=None, nullable=True)
    year_month: Mapped[str | None] = mapped_column(default=None, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.now(),
        default=datetime.utcnow,
    )

    user: Mapped["UsersModel"] = relationship(back_populates="notifications")