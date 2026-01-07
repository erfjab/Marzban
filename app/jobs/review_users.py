from logging import getLogger
from datetime import datetime, timedelta
from types import SimpleNamespace
from typing import TYPE_CHECKING
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy import Integer, and_, cast, func, or_
from sqlalchemy.orm import Session, joinedload, load_only

from app import scheduler, xray
from app.db import GetDB
from app.db.models import User
from app.models.user import UserStatus
from app.utils.timer import JobTimer
from config import JOB_REVIEW_USERS_INTERVAL

logger = getLogger("uvicorn.error")
executor = ThreadPoolExecutor(max_workers=5)
pending_removals = set()


def bg_remove_user(user_id: int, user_username: str):
    if user_id in pending_removals:
        return

    pending_removals.add(user_id)
    u = SimpleNamespace(id=user_id, username=user_username)
    try:
        xray.operations.remove_user(u)
    except Exception as e:
        logger.exception(f"Failed to remove user id={u.id}: {e}")
    finally:
        pending_removals.discard(user_id)


def review():
    timer = JobTimer("review_users")
    now = datetime.utcnow()
    now_ts = now.timestamp()
    now_epoch = int(now_ts)
    with GetDB() as db:
        timer.checkpoint("db_connected")
        limited_cond = and_(
            User.data_limit.isnot(None),
            User.used_traffic >= User.data_limit,
        )
        expired_cond = and_(User.expire.isnot(None), User.expire <= now_ts)

        query = (
            db.query(User)
            .options(joinedload(User.next_plan))
            .filter(
                User.status == UserStatus.active,
                or_(limited_cond, expired_cond),
            )
        )
        logger.info(f"Found {query.count()} active users to review")
        timer.checkpoint("fetched_active_users")
        limited_ids = []
        expired_ids = []
        for user in query:
            timer.checkpoint(f"review_user_id_{user.id}")
            logger.warning(f"Reviewing user id={user.id} username={user.username}")
            limited = user.data_limit and user.used_traffic >= user.data_limit
            expired = user.expire and user.expire <= now_ts

            executor.submit(bg_remove_user, user.id, user.username)

            if limited:
                limited_ids.append(user.id)
            elif expired:
                expired_ids.append(user.id)


        if limited_ids:
            db.query(User).filter(User.id.in_(limited_ids)).update(
                {User.status: UserStatus.limited, User.last_status_change: now},
                synchronize_session=False,
            )
            logger.warning(f"{len(limited_ids)} user(s) set to limited")

        if expired_ids:
            db.query(User).filter(User.id.in_(expired_ids)).update(
                {User.status: UserStatus.expired, User.last_status_change: now},
                synchronize_session=False,
            )
            logger.warning(f"{len(expired_ids)} user(s) set to expired")

        stuck_users = (
            db.query(User)
            .filter(
                User.id.notin_(pending_removals),
                User.status.in_([UserStatus.expired, UserStatus.limited]),
                User.online_at > User.last_status_change + timedelta(minutes=1),
            )
            .all()
        )
        if stuck_users:
            logger.warning(f"Found {len(stuck_users)} stuck users to remove")
            for user in stuck_users:
                executor.submit(bg_remove_user, user.id, user.username)
        db.query(User).filter(User.id.in_([u.id for u in stuck_users])).update(
            {User.last_status_change: now}, synchronize_session=False
        )
        db.commit()

        timer.checkpoint("review_active_users")

        query = db.query(User).filter(
            User.status == UserStatus.on_hold,
            or_(
                and_(
                    User.online_at.isnot(None),
                    func.coalesce(User.edit_at, User.created_at) <= User.online_at,
                ),
                and_(User.on_hold_timeout.isnot(None), User.on_hold_timeout <= now),
            ),
        )

        updated_rows = query.update(
            {
                User.status: UserStatus.active,
                User.last_status_change: now,
                User.expire: cast(now_epoch + User.on_hold_expire_duration, Integer),
                User.on_hold_expire_duration: None,
                User.on_hold_timeout: None,
            },
            synchronize_session=False,
        )
        if updated_rows:
            logger.warning(f"{updated_rows} on-hold user(s) activated")
        db.commit()
        timer.checkpoint("review_on_hold_users")
    timer.stop()


scheduler.add_job(
    review,
    "interval",
    seconds=JOB_REVIEW_USERS_INTERVAL,
    coalesce=True,
    max_instances=1,
)
