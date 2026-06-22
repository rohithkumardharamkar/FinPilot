import smtplib
from email.mime.text import MIMEText
from src.core.config import settings

def send_email(subject: str, body: str, to_email: str = None) -> bool:
    """Helper function to send SMTP email notifications."""
    if not settings.EMAIL_USER or not settings.EMAIL_PASSWORD:
        print("Email credentials not configured.")
        return False
        
    target_email = to_email or settings.EMAIL_TO
    if not target_email:
        print("No target recipient email configured.")
        return False
        
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = settings.EMAIL_USER
        msg["To"] = target_email
        
        with smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT) as server:
            server.starttls()
            server.login(settings.EMAIL_USER, settings.EMAIL_PASSWORD)
            server.send_message(msg)
        print(f"Email notification sent successfully to {target_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def email_agent(state: dict) -> dict:
    """
    State-based agent interface wrapper for email sending.
    """
    logs = state.get("logs", [])
    report = state.get("magazine_report", "") or state.get("response", "")
    if not report:
        return {"email_status": "No report or response to send", "logs": logs}
        
    target_email = state.get("target_email") or settings.EMAIL_TO
    success = send_email("Healthcare AI Agent Notification", report, target_email)
    if success:
        return {"email_status": f"Email sent successfully to {target_email}", "logs": logs}
    else:
        return {"email_status": "Failed to send email", "logs": logs}
