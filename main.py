from flask import Flask, render_template, url_for, request, flash, redirect, session
import os
from dotenv import load_dotenv
import logging
import requests
from datetime import datetime

# load environment variables from .env at startup so that other modules
# (e.g. alert.py) see them when they import.
load_dotenv()

# pull alert/logging helpers from separate module
from alert import log_failed_login, send_discord_alert, send_email_alert
# supabase log handler module
from log import init_supabase, SupabaseLogHandler

# track failed admin login attempts
failed_attempts = {}

LOG_ENDPOINT = os.getenv("LOG_ENDPOINT")

print("DEBUG: Env loaded")

app = Flask(__name__)
# secret key needed for session management (set via .env or fallback)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# later after supabase creation we register blueprint (placed here as placeholder)
# configure basic logging so we always have console output and can
# see which Flask routes (API calls) are being hit.  supabase handler
# is added later if the client is available.
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")
# werkzeug should log requests at INFO so the access lines appear
logging.getLogger("werkzeug").setLevel(logging.INFO)
# suppress httpx debug chatter (Supabase client uses httpx internally)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# record every incoming request automatically
@app.before_request
def log_every_request():
    user_id = session.get('user_id') or session.get('userid') or 'anonymous'
    path = request.path
    logger.info(f"nav user={user_id} path={path}")
    record_log(user_id, path, 'view')



def record_log(user_id, path, action, meta=None):
    """Insert an entry into the Supabase access_logs table.

    Also write a normal log message so you can watch visits in the
    console regardless of whether Supabase is configured.

    The `access_logs.user_id` column is a UUID in our schema, so we
    can't insert the literal string `'anonymous'`; callers default to
    that when there is no logged-in user.  To avoid the ``22P02`` error
    we simply omit the field when the value isn't a valid UUID.
    """
    logger.info(f"access user={user_id} path={path} action={action} meta={meta}")

    if not supabase:
        return
    payload = {
        'path': path,
        'action': action,
        'timestamp': str(datetime.utcnow())
    }
    # only include user_id when it's not the anonymous placeholder
    if user_id and user_id != 'anonymous':
        payload['user_id'] = user_id
    if meta is not None:
        payload['meta'] = meta
    try:
        supabase.table('access_logs').insert(payload).execute()
    except Exception as e:
        logger.error(f"Failed to insert access log: {e}")

# Import register and dashboard blueprints
from register import register_bp, init_register
from dashboard import bp as dashboard_bp, init_dashboard

@app.route('/')
def index():
    # Flask จะไปหาไฟล์ index.html ในโฟลเดอร์ templates เองโดยอัตโนมัติ
    # บันทึกการเข้าชมสำหรับ dashboard
    user_id = session.get('user_id') or session.get('userid') or 'anonymous'
    record_log(user_id, '/', 'view')
    return render_template('index.html')


@app.route('/logout')
def logout():
    """Simple logout handler that clears session and redirects to home."""
    # optionally record log
    user_id = session.get('user_id') or session.get('userid') or 'anonymous'
    record_log(user_id, '/logout', 'logout')
    session.clear()
    flash('ออกจากระบบเรียบร้อยแล้ว')
    return redirect(url_for('index'))

# ---- Supabase configuration ------------------------------------------------
# read your Supabase connection info from environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PORT = int(os.getenv("PORT", 8083))  # default to 8083 if not set
# optional password variable if you also store it separately
SUPABASE_PASSWORD = os.getenv("SUPABASE_PASSWORD")

# you may need to install the supabase-py client
# pip install supabase
from supabase import create_client, Client

# create a global client instance (reuse for requests)
supabase: Client | None = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # initialise log subsystem so handler can write to the new table
    init_supabase(supabase, table_name="app_logs")

    # add the Supabase handler in addition to the existing console
    # handler; this won't remove anything we've configured above.
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(SupabaseLogHandler())
    # we intentionally do not disable werkzeug/httpx here; werkzeug
    # access logs are useful and httpx is set to WARNING at top to hide
    # its internal traffic.

    # initialize and register feature blueprints
    init_register(supabase)
    app.register_blueprint(register_bp)
    init_dashboard(supabase)
    app.register_blueprint(dashboard_bp)
else:
    # warn if env vars are missing
    app.logger.warning("Supabase environment variables not set; supabase client not initialized")



@app.route('/login', methods=['GET', 'POST'])
def login():
    # แสดงหน้า login เมื่อเป็น GET
    if request.method == 'GET':
        return render_template('login.html')

    # เมื่อเป็น POST ให้ตรวจสอบ credentials กับ Supabase
    userid = request.form.get('username')  # ใช้ userid แทน email
    password = request.form.get('password')
    # always define role so later checks don't crash
    role = None

    if not (userid and password):
        flash('กรุณากรอกทั้ง UserID และ Password')
        return redirect(url_for('login'))

    if not supabase:
        flash('บริการ Supabase ยังไม่ได้ตั้งค่า')
        return redirect(url_for('login'))

    print(f"[DEBUG] Login attempt with userid: {userid}")

    # Query users table to find email by userid
    try:
        user_query = supabase.table('users').select('email, role').eq('userid', userid).execute()
        print(f"[DEBUG] User query response: {user_query}")
        
        if not user_query.data or len(user_query.data) == 0:
            print(f"[DEBUG] User {userid} not found in users table")
            log_failed_login(userid, "User not found in database")
            # we can't know the role of a non-existent user, so skip the
            # admin-alert logic in this case (and avoid NameError).
            flash('UserID หรือ Password ไม่ถูกต้อง')
            return redirect(url_for('login'))
        
        user_record = user_query.data[0]
        email = user_record.get('email')
        role = user_record.get('role', 'viewer')
        
        print(f"[DEBUG] Found user {userid} with email: {email}, role: {role}")
    except Exception as e:
        print(f"[DEBUG] Error querying users table: {str(e)}")
        flash('เกิดข้อผิดพลาดในการตรวจสอบ')
        return redirect(url_for('login'))

    # sign in ผ่าน Supabase auth ด้วย email
    try:
        print(f"[DEBUG] Attempting to sign in with email: {email}")
        auth_response = supabase.auth.sign_in_with_password({
            'email': email,
            'password': password
        })
        print(f"[DEBUG] Auth response: {auth_response}")
    except Exception as e:
        print(f"[DEBUG] Auth error: {str(e)}")
        log_failed_login(userid, f"Authentication exception: {str(e)}")
        send_email_alert(email, userid)
        if role == 'admin':
            failed_attempts[userid] = failed_attempts.get(userid, 0) + 1
            if failed_attempts[userid] >= 3:
                logger.info("about to send discord alert")
                send_discord_alert(f"Alert: Admin user {userid} has failed login {failed_attempts[userid]} times.")
        flash('UserID หรือ Password ไม่ถูกต้อง')
        return redirect(url_for('login'))

    # Check for auth errors
    if isinstance(auth_response, dict) and auth_response.get('error'):
            error_msg = auth_response['error'].get('message', 'Unknown error')
            print(f"[DEBUG] Login failed: {error_msg}")
            log_failed_login(userid, f"Authentication failed: {error_msg}")
            send_email_alert(email, userid)
            if role == 'admin':
                failed_attempts[userid] = failed_attempts.get(userid, 0) + 1
                if failed_attempts[userid] >= 3:
                    logger.info("about to send discord alert")
                    send_discord_alert(f"Alert: Admin user {userid} has failed login {failed_attempts[userid]} times.")
            flash('UserID หรือ Password ไม่ถูกต้อง')
            return redirect(url_for('login'))
    # Extract user from response
    if isinstance(auth_response, dict) and 'user' in auth_response:
        user = auth_response.get('user')
    elif hasattr(auth_response, 'user'):
        user = auth_response.user
    else:
        print(f"[DEBUG] Could not extract user from auth response")
        flash('ไม่พบข้อมูลผู้ใช้')
        return redirect(url_for('login'))
    
    if not user:
        flash('ไม่พบข้อมูลผู้ใช้')
        return redirect(url_for('login'))

    # เก็บข้อมูลเซสชันพื้นฐาน
    session['user_id'] = user.get('id') if isinstance(user, dict) else user.id
    session['userid'] = userid
    session['password'] = password  # เก็บไว้แสดงบนหน้า admin เพื่อสาธิตเท่านั้น
    session['is_admin'] = (role == 'admin')

    print(f"[DEBUG] Login successful for {userid}, is_admin: {session['is_admin']}")
    flash('ล็อกอินสำเร็จ')
    if session['is_admin']:
        failed_attempts[userid] = 0
        return redirect(url_for('dashboard.admin'))
    return redirect(url_for('index'))

@app.route('/log', methods=['POST'])
def log_endpoint():
    """Endpoint to receive login failure notifications"""
    data = request.get_json()
    if data:
        logger.info(f"Received log notification: {data}")
    return {'status': 'ok'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)