from flask import Blueprint, render_template, session, redirect, url_for, flash
from datetime import datetime
import logging

# blueprint setup
bp = Blueprint('dashboard', __name__)

# supabase client will be assigned by init_dashboard
supabase = None
logger = logging.getLogger(__name__)


def init_dashboard(db_client):
    """Initialize module with a Supabase client instance."""
    global supabase
    supabase = db_client


def admin_required(f):
    """Decorator for protecting admin routes in dashboard."""
    from functools import wraps

    @wraps(f)
    def wrapped(*args, **kwargs):
        if not session.get('is_admin'):
            flash('ต้องเป็นผู้ดูแลระบบเท่านั้นเพื่อเข้าใช้งานหน้านี้')
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return wrapped


@bp.route('/admin')
@admin_required
def admin():
    # ดึง log จาก Supabase และสรุปสถิติ
    total = 0
    by_action = {}
    top_users = []
    logs = []
    if supabase:
        try:
            resp = supabase.table('access_logs').select('*').order('timestamp', desc=True).execute()
            logs = resp.data or []
            total = len(logs)
            user_counts: dict = {}
            for row in logs:
                act = row.get('action')
                by_action[act] = by_action.get(act, 0) + 1
                uid = row.get('user_id') or 'anonymous'
                user_counts[uid] = user_counts.get(uid, 0) + 1
            top_users = sorted(user_counts.items(), key=lambda t: t[1], reverse=True)[:5]
        except Exception as e:
            logger.error(f"Error fetching logs for dashboard: {e}")
    return render_template('admin.html',
                           user_id=session.get('user_id'),
                           password=session.get('password'),
                           total=total,
                           by_action=by_action,
                           logs=logs,
                           top_users=top_users)
