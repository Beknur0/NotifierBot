from datetime import datetime, timedelta, timezone
import string
import secrets
from typing import Any

from apscheduler.jobstores.base import JobLookupError

from scheduler import scheduler
from .schedules_handlers import notifying_user


def generate_user_job_id(telegram_id: int, length: int = 4) -> str:
    alphabet = string.ascii_letters + string.digits
    random_suffix = "".join(secrets.choice(alphabet) for _ in range(length))
    return f"{telegram_id}_{random_suffix}"


async def add_exact_job(
    user_id: int,
    date: str,
    time: str,
):
    date_string = date + " " + time
    run_datetime = datetime.strptime(date_string, "%d.%m.%Y %H:%M")
    job_id = generate_user_job_id(user_id)
    scheduler.add_job(
        func=notifying_user,
        trigger="date",
        run_date=run_datetime,
        kwargs={
            "user_id": user_id,
            "job_id": job_id,
            "type": "exact",
        },
        id=job_id,
    )
    return job_id


async def add_timer_job(
    user_id: int,
    seconds: int,
):
    job_id = generate_user_job_id(user_id)
    run_time = datetime.now(timezone.utc) + timedelta(seconds=seconds)
    scheduler.add_job(
        func=notifying_user,
        trigger="date",
        run_date=run_time,
        kwargs={
            "user_id": user_id,
            "job_id": job_id,
            "type": "timer",
        },
        id=job_id,
    )
    return job_id


async def add_week_job(
    user_id: int,
    weekdays: str,
    time: str,
):
    job_id = generate_user_job_id(user_id)
    en = {
        "1": "mon",
        "2": "tue",
        "3": "wed",
        "4": "thu",
        "5": "fri",
        "6": "sat",
        "7": "sun",
    }
    for i, j in en.items():
        weekdays = weekdays.replace(i, j)
    h, m = time.split(":")
    scheduler.add_job(
        func=notifying_user,
        trigger="cron",
        day_of_week=weekdays,
        hour=int(h),
        minute=int(m),
        kwargs={
            "user_id": user_id,
            "job_id": job_id,
            "type": "week",
        },
        id=job_id,
    )
    return job_id


async def add_month_job(
    user_id: int,
    month_day: str,
    time: str,
):
    job_id = generate_user_job_id(user_id)
    h, m = time.split(":")
    scheduler.add_job(
        func=notifying_user,
        trigger="cron",
        day=int(month_day) if month_day.isdigit() else month_day,
        hour=int(h),
        minute=int(m),
        kwargs={
            "user_id": user_id,
            "job_id": job_id,
            "type": "month",
        },
        id=job_id,
    )
    return job_id


async def add_year_job(
    user_id: int,
    year_month: str,
    time: str,
):
    job_id = generate_user_job_id(user_id)
    day, mon = year_month.split(".")
    h, m = time.split(":")
    scheduler.add_job(
        func=notifying_user,
        trigger="cron",
        month=int(mon),
        day=int(day),
        hour=int(h),
        minute=int(m),
        kwargs={
            "user_id": user_id,
            "job_id": job_id,
            "type": "year",
        },
        id=job_id,
    )
    return job_id


async def update_exact_job(
    job_id: str,
    dictionary: dict[str, Any],
) -> bool:
    processed_dict: dict[str, Any] = {"job_id": job_id}
    if dictionary.get("date"):
        date_string = (
            dictionary.get("date").strftime("%d.%m.%Y") + " " + dictionary.get("time")
        )
        run_datetime = datetime.strptime(date_string, "%d.%m.%Y %H:%M")
        processed_dict["trigger"] = "date"
        processed_dict["run_date"] = run_datetime
    elif dictionary.get("timer_seconds"):
        run_time = datetime.now() + timedelta(seconds=dictionary.get("timer_seconds"))
        processed_dict["trigger"] = "date"
        processed_dict["run_date"] = run_time
    elif dictionary.get("weekdays"):
        en = {
            "1": "mon",
            "2": "tue",
            "3": "wed",
            "4": "thu",
            "5": "fri",
            "6": "sat",
            "7": "sun",
        }
        weekdays: str = dictionary.get("weekdays")
        for i, j in en.items():
            weekdays = weekdays.replace(i, j)
        h, m = dictionary.get("time").split(":")
        processed_dict["trigger"] = "cron"
        processed_dict["day_of_week"] = weekdays
        processed_dict["hour"] = int(h)
        processed_dict["minute"] = int(m)
    elif dictionary.get("month_day"):
        month_day = dictionary.get("month_day")
        h, m = dictionary.get("time").split(":")
        processed_dict["trigger"] = "cron"
        processed_dict["day"] = int(month_day) if month_day.isdigit() else month_day
        processed_dict["hour"] = int(h)
        processed_dict["minute"] = int(m)
    elif dictionary.get("year_month"):
        day, mon = dictionary.get("year_month").split(".")
        h, m = dictionary.get("time").split(":")
        processed_dict["trigger"] = "cron"
        processed_dict["month"] = int(mon)
        processed_dict["day"] = int(day)
        processed_dict["hour"] = int(h)
        processed_dict["minute"] = int(m)
    try:
        job = scheduler.get_job(job_id)
        is_paused = job.next_run_time is None
        scheduler.reschedule_job(**processed_dict)
        if is_paused:
            scheduler.pause_job(job_id=job_id)
        return True
    except JobLookupError:
        return False


async def pause_job(job_id: str):
    scheduler.pause_job(job_id=job_id)


async def resume_job(job_id: str):
    scheduler.resume_job(job_id=job_id)


async def delete_job(job_id: str):
    scheduler.remove_job(job_id=job_id)
