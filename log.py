import logging
from datetime import datetime, timedelta

# global supabase client reference (set by init)
supabase = None
_table = "app_logs"


def init_supabase(client, table_name: str = "app_logs"):
    """Initialize the module with a Supabase client and optional table name."""
    global supabase, _table
    supabase = client
    _table = table_name


class SupabaseLogHandler(logging.Handler):
    """A logging handler that inserts records into a Supabase table.

    The table is expected to have at least these columns:
        id uuid primary key default uuid_generate_v4(),
        timestamp timestamptz default now(),
        level text,
        logger text,
        message text,
        user_id uuid,       -- optional
        meta jsonb           -- optional
    """

    def emit(self, record):
        if not supabase:
            return
        try:
            # ลบข้อมูลเกิน 7 วันก่อน insert
            cutoff = datetime.utcnow() - timedelta(days=7)
            supabase.table(_table).delete().lt('timestamp', str(cutoff)).execute()

            payload = {
                "timestamp": str(datetime.utcnow()),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            # if extra fields provided, include them
            if hasattr(record, "user_id"):
                payload["user_id"] = record.user_id
            if hasattr(record, "meta"):
                payload["meta"] = record.meta

            supabase.table(_table).insert(payload).execute()
        except Exception:
            # avoid recursion if logging fails
            pass
