import time
import logging

logger = logging.getLogger("uvicorn.error")


class JobTimer:
    def __init__(self, job_name: str):
        self.job_name = job_name
        self.start_time = time.time()
        self.last_checkpoint = self.start_time

    def checkpoint(self, name: str):
        now = time.time()
        duration = now - self.last_checkpoint
        self.last_checkpoint = now

        logger.info(f"✅ Job [{self.job_name}] Step [{name}] took {duration:.4f}s")

    def stop(self):
        now = time.time()
        total_duration = now - self.start_time
        logger.info(f"✅ Job [{self.job_name}] Finished in {total_duration:.4f}s")
