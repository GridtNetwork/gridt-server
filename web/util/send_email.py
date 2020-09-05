from flask import current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail


def send_email(to_emails, template_id, template_data):
    msg = Mail(
        from_email="info@gridt.org", to_emails=to_emails
    )
    
    msg.template_id = template_id
    msg.template_data = template_data

    sg = SendGridAPIClient(current_app.config["EMAIL_API_KEY"])
    resp = sg.send(msg)
    return resp.status_code, resp.body, resp.headers