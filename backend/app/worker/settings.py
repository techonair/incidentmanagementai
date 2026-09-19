from ..config import arq_redis_settings
from .jobs import correlate_alert, investigate_incident, shutdown, startup


class WorkerSettings:
    functions = [investigate_incident, correlate_alert]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = arq_redis_settings()
    max_jobs = 10
    job_timeout = 60
    max_tries = 2
