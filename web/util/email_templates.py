from flask import current_app
from util.send_email import send_email


def send_password_reset_email(email, token):
    template_id = current_app.config["PASSWORD_RESET_TEMPLATE"]
    template_data = {
        "link": f"https://app.gridt.org/user/reset_password/confirm?token={token}"
    }

    send_email(email, template_id, template_data)


def send_password_change_notification(email):
    template_id = current_app.config["PASSWORD_CHANGE_NOTIFICATION_TEMPLATE"]
    template_data = {"link": "https://app.gridt.org/user/reset_password/request"}

    send_email(email, template_id, template_data)


def send_email_change_email(email, username, token):
    template_id = current_app.config["EMAIL_CHANGE_TEMPLATE"]
    template_data = {
        "username": username,
        "link": f"https://app.gridt.org/user/change_email/confirm?token={token}",
    }

    send_email(email, template_id, template_data)


def send_email_change_notification(email, username):
    template_id = current_app.config["EMAIL_CHANGE_NOTIFICATION_TEMPLATE"]
    template_data = {"username": username}

    send_email(email, template_id, template_data)
