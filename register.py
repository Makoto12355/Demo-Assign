"""
Register blueprint and helper for handling user registration
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for

register_bp = Blueprint('register', __name__)

# global variable which will be set by main after supabase client is created
supabase = None

def init_register(db_client):
    """Call from main.py after creating supabase client."""
    global supabase
    supabase = db_client


def register_user(supabase_client, email, userid, password):
    """
    Register a new user in Supabase
    - Creates auth user with email and password
    - Inserts user record into 'users' table with role='viewer'

    Returns: True if successful, False otherwise
    """
    print(f"[DEBUG] Starting registration for email: {email}, userid: {userid}")

    if not supabase_client:
        print("[DEBUG] ERROR: Supabase client not initialized")
        return False

    try:
        # Sign up user via Supabase Auth
        print(f"[DEBUG] Attempting to sign up user via Supabase Auth...")
        auth_response = supabase_client.auth.sign_up({
            'email': email,
            'password': password,
            'options': {
                'data': {'userid': userid}
            }
        })

        print(f"[DEBUG] Auth response: {auth_response}")

        # Check for auth errors
        if isinstance(auth_response, dict) and auth_response.get('error'):
            error_msg = auth_response['error'].get('message', 'Unknown error')
            print(f"[DEBUG] Auth error: {error_msg}")
            return False

        # Extract user ID from response
        auth_user_id = None
        if isinstance(auth_response, dict) and 'user' in auth_response:
            user = auth_response['user']
            auth_user_id = user.get('id') if isinstance(user, dict) else user.id
        elif hasattr(auth_response, 'user') and auth_response.user:
            auth_user_id = auth_response.user.id

        if not auth_user_id:
            print(f"[DEBUG] ERROR: Could not extract user from auth response")
            print(f"[DEBUG] Response type: {type(auth_response)}, value: {auth_response}")
            return False

        print(f"[DEBUG] User created in Auth with ID: {auth_user_id}")

        # Insert user record into 'users' table with role='viewer'
        print(f"[DEBUG] Inserting user record into 'users' table...")
        insert_response = supabase_client.table('users').insert({
            'user_id': auth_user_id,
            'userid': userid,
            'email': email,
            'role': 'viewer'
        }).execute()

        print(f"[DEBUG] Insert response: {insert_response}")

        print(f"[DEBUG] User {userid} registered successfully with role='viewer'")
        return True

    except Exception as e:
        print(f"[DEBUG] Exception during registration: {str(e)}")
        return False


@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    # แสดงหน้า register เมื่อเป็น GET
    if request.method == 'GET':
        return render_template('register.html')

    # เมื่อเป็น POST ให้ทำการสมัครใช้งาน
    email = request.form.get('email')
    userid = request.form.get('userid')
    password = request.form.get('password')
    password_confirm = request.form.get('password_confirm')

    print(f"[DEBUG] Register attempt - email: {email}, userid: {userid}")

    if not (email and userid and password and password_confirm):
        flash('กรุณากรอกข้อมูลให้ครบถ้วน')
        return redirect(url_for('register.register'))

    if password != password_confirm:
        print(f"[DEBUG] Password mismatch")
        flash('รหัสผ่านไม่ตรงกัน')
        return redirect(url_for('register.register'))

    if not supabase:
        flash('บริการ Supabase ยังไม่ได้ตั้งค่า')
        return redirect(url_for('register.register'))

    # ตรวจสอบว่ามี userid นี้ในตาราง users หรือไม่
    try:
        user_query = supabase.table('users').select('userid').eq('userid', userid).execute()
        if user_query.data and len(user_query.data) > 0:
            print(f"[DEBUG] UserID {userid} already exists in users table")
            flash('IDผู้ใช้งานนี้ถูกใช้งานแล้ว กรุณาเลือกชื่ออื่น')
            return redirect(url_for('register.register'))
    except Exception as e:
        print(f"[DEBUG] Error querying users table during registration: {str(e)}")
        flash('เกิดข้อผิดพลาดในการตรวจสอบบัญชี')
        return redirect(url_for('register.register'))

    success = register_user(supabase, email, userid, password)

    if success:
        print(f"[DEBUG] Registration successful for {userid}")
        flash(f'สมัครใช้งานสำเร็จ! สามารถลงชื่อเข้าใช้ได้เลย')
        return redirect(url_for('login'))
    else:
        print(f"[DEBUG] Registration failed for {userid}")
        flash('การสมัครใช้งานไม่สำเร็จ กรุณาลองใหม่')
        return redirect(url_for('register.register'))
