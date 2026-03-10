import os
import logging
import requests
from datetime import datetime
import resend

logger = logging.getLogger(__name__)

LOG_ENDPOINT = os.getenv("LOG_ENDPOINT")
# don't grab the webhook URL until we need it; the .env file may be
# loaded after this module is imported.
# DISCORD_WEBHOOK = os.getenv("DISCORD_WEBHOOK")


def log_failed_login(userid, reason):
    """Log failed login attempt and send HTTP POST notification"""
    logger.warning(f"Failed login attempt for userid: {userid} - Reason: {reason}")

    if LOG_ENDPOINT:
        try:
            payload = {
                'event': 'failed_login',
                'userid': userid,
                'reason': reason,
                'timestamp': str(datetime.now())
            }
            response = requests.post(LOG_ENDPOINT, json=payload, timeout=5)
            logger.info(f"Sent failed login notification to {LOG_ENDPOINT}, status: {response.status_code}")
        except Exception as e:
            logger.error(f"Failed to send login notification: {str(e)}")


def send_discord_alert(message):
    """Send alert message to Discord webhook"""
    webhook = os.getenv("DISCORD_WEBHOOK")
    if not webhook:
        logger.warning("DISCORD_WEBHOOK not set; skipping Discord alert")
        return
    try:
        payload = {"content": message}
        logger.info(f"Posting to Discord webhook: {message}")
        response = requests.post(webhook, json=payload, timeout=5)
        logger.info(f"Sent Discord alert, status: {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to send Discord alert: {e}")


def send_email_alert(email, userid):
    """Send alert email to user using Resend"""
    logger.info(f"Preparing to send email alert to: {email} for userid: {userid}")
    
    # Use env variable, with a fallback just in case as requested
    api_key = os.getenv("RESEND_API_KEY") 
    if not api_key:
        api_key = "------------------"  # ถ้ามีapikeyที่ได้รับการยืนยันแล้วจะเปลี่ยนมาใส่ตรงนี้ก็ได้แต่ผมขอใส่ในenv
        
    resend.api_key = api_key
    
    try:
        r = resend.Emails.send({
            "from": "demofullstack@resend.dev",
            "to": email,
            "subject": "แจ้งเตือนความปลอดภัย: มีการพยายามเข้าสู่ระบบที่ไม่สำเร็จ",
            "html": f"<p>ตรวจพบการพยายามเข้าสู่ระบบที่ไม่สำเร็จสำหรับบัญชีโทรผู้ใช้: <strong>{userid}</strong></p><p>หากคุณไม่ได้เป็นผู้กระทำการนี้ โปรดตรวจสอบความปลอดภัยของบัญชีท่านทันที</p>"
        })
        logger.info(f"Email alert sent successfully! Response: {r}")
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")
