import requests
import logging
from typing import Optional, Dict, List, Any
from collections import defaultdict
from sqlalchemy.orm import Session
from app.db.models import Admin
from config import MOREBOT_LICENSE, MOREBOT_SECRET

logger = logging.getLogger("uvicorn.error")


class Morebot:
    _base_url = (
        f"https://{MOREBOT_LICENSE}.morebot.top/api/subscriptions/{MOREBOT_SECRET}"
    )
    _timeout = 3
    _failed_reports = defaultdict(int)

    @classmethod
    def get_configs(cls, username: str, configs: Any) -> Optional[Dict]:
        try:
            response = requests.post(
                url=f"{cls._base_url}/{username}/configs",
                json=configs,
                timeout=cls._timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    @classmethod
    def get_users_limit(cls, username: str) -> Optional[int]:
        try:
            response = requests.get(
                url=f"{cls._base_url}/{username}/users_limit", timeout=cls._timeout
            )
            response.raise_for_status()
            data = response.json()
            return data.get("users_limit", None)
        except requests.RequestException:
            return None

    @classmethod
    def report_admin_usage(
        cls, db: Session, users_usage: List[Dict[str, Any]], user_admin_map: any
    ) -> bool:
        if not users_usage:
            return True
        current_admin_usage = defaultdict(int)
        for user_usage in users_usage:
            user_id = int(user_usage["uid"])
            admin_id = user_admin_map.get(user_id)
            if admin_id:
                current_admin_usage[admin_id] += user_usage["value"]
        current_total = sum(current_admin_usage.values())
        failed_total = sum(cls._failed_reports.values())
        
        logger.info(f"📊 New usage total: {current_total / (1024**3):.2f} GB")
        logger.info(f"📊 Previous failed usage total: {failed_total / (1024**3):.2f} GB")
        total_admin_usage = defaultdict(int)
        for admin_id, failed_usage in cls._failed_reports.items():
            total_admin_usage[admin_id] = failed_usage
        for admin_id, current_usage in current_admin_usage.items():
            total_admin_usage[admin_id] += current_usage        
        total_to_report = sum(total_admin_usage.values())
        logger.info(f"📊 Total to report: {total_to_report / (1024**3):.2f} GB")

        admins = dict(db.query(Admin.id, Admin.username).all())

        report_data = [
            {"username": admins.get(admin_id, "Unknown"), "usage": int(value)}
            for admin_id, value in total_admin_usage.items()
            if value > 0
        ]

        if not report_data:
            return True
        
        try:
            response = requests.post(
                f"{cls._base_url}/usages", json=report_data, timeout=cls._timeout
            )
            response.raise_for_status()
            logger.info(f"✅ Report sent successfully - Total: {total_to_report / (1024**3):.2f} GB")
            cls._failed_reports.clear()
            return True
        except requests.RequestException as e:
            logger.error(f"❌ Report failed: {str(e)}")
            for admin_id, usage in current_admin_usage.items():
                cls._failed_reports[admin_id] += usage
            
            new_failed_total = sum(cls._failed_reports.values())
            logger.info(f"📊 Failed usage saved: {new_failed_total / (1024**3):.2f} GB")
            return False