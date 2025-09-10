import os, smtplib, ssl, json, logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SLACK_WEBHOOK = os.getenv("ALERT_SLACK_WEBHOOK")

def alert_failure(pipeline: str, repo: str, url: str, logs: str | None = None):
    """
    Send failure alerts via Slack webhook and/or email when a CI/CD pipeline fails.
    
    Args:
        pipeline: Name of the failed pipeline
        repo: Repository name
        url: URL to the build/run (optional)
        logs: Build logs (optional, will be truncated)
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    title = f"🚨 CI/CD Pipeline Failure Alert"
    
    # Create structured message
    slack_message = f"""*{title}*
📋 *Pipeline:* {pipeline}
📁 *Repository:* {repo}
🕒 *Time:* {timestamp}
🔗 *Build URL:* {url or 'N/A'}
📝 *Status:* FAILED ❌"""
    
    # Add logs if available (truncated for readability)
    if logs:
        log_snippet = logs[:500] + "..." if len(logs) > 500 else logs
        slack_message += f"\n\n*Recent Logs:*\n```{log_snippet}```"
    
    # Email message (more detailed)
    email_subject = f"❌ CI/CD Failure: {pipeline} in {repo}"
    email_body = f"""CI/CD Pipeline Failure Alert

Pipeline: {pipeline}
Repository: {repo}
Time: {timestamp}
Build URL: {url or 'N/A'}
Status: FAILED

"""
    
    if logs:
        email_body += f"Build Logs:\n{'-'*50}\n{logs[:2000]}\n{'-'*50}\n"
    
    email_body += "\nThis is an automated alert from the CI/CD Pipeline Health Dashboard."
    
    # Send alerts
    slack_sent = _send_slack_alert(slack_message)
    email_sent = _send_email_alert(email_subject, email_body)
    
    # Log alert status
    if slack_sent or email_sent:
        logger.info(f"Alert sent for {pipeline} failure - Slack: {slack_sent}, Email: {email_sent}")
    else:
        logger.warning(f"No alert methods configured for {pipeline} failure")

def _send_slack_alert(message: str) -> bool:
    """Send alert to Slack via webhook. Returns True if successful."""
    if not SLACK_WEBHOOK:
        logger.debug("Slack webhook not configured, skipping Slack alert")
        return False
    
    try:
        payload = {
            "text": message,
            "username": "CI/CD Monitor",
            "icon_emoji": ":rotating_light:"
        }
        
        response = requests.post(
            SLACK_WEBHOOK, 
            json=payload,
            timeout=10,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            logger.info("Slack alert sent successfully")
            return True
        else:
            logger.error(f"Slack webhook failed with status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Slack webhook error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected Slack error: {e}")
        return False

def _send_email_alert(subject: str, body: str) -> bool:
    """Send alert via email. Returns True if successful."""
    # Get SMTP configuration
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    sender = os.getenv("ALERT_EMAIL_FROM")
    recipient = os.getenv("ALERT_EMAIL_TO")

    if not (smtp_host and sender and recipient):
        logger.debug("Email configuration incomplete, skipping email alert")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = recipient
        msg["Reply-To"] = sender
        
        # Add body
        msg.attach(MIMEText(body, "plain"))
        
        # Create SMTP connection
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls(context=context)
            
            # Login if credentials provided
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            
            # Send email
            server.sendmail(sender, [recipient], msg.as_string())
            
        logger.info(f"Email alert sent successfully to {recipient}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP authentication failed: {e}")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected email error: {e}")
        return False

# Legacy function names for backward compatibility
def _slack(title: str, body: str):
    """Legacy function - use _send_slack_alert instead"""
    _send_slack_alert(f"*{title}*\n{body}")

def _email(subject: str, body: str):
    """Legacy function - use _send_email_alert instead"""
    _send_email_alert(subject, body)
