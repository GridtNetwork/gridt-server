import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email(email, subject, body):
    msg = Mail(
        from_email="info@gridt.org",
        to_emails=email,
        subject=subject,
        html_content=body
    )
    
    try:
        sg = SendGridAPIClient(os.environ.get("EMAIL_API_KEY"))
        resp = sg.send(msg)
        return resp.status_code, resp.body, resp.headers
    except Exception as e:
        if e.message:
            return e.message