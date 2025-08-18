import aiosmtplib
from email.message import EmailMessage
import decouple



APP_PASSWORD = decouple.config('APP_PASSWORD', default=None)
APP_EMAIL = decouple.config('APP_EMAIL', default=None)
SMTP_HOSTNAME = decouple.config('SMTP_HOSTNAME', default=None)

async def init_smtp():
    smtp_client = aiosmtplib.SMTP(
        hostname=SMTP_HOSTNAME,
        port=465,
        use_tls=True,
        start_tls=False
        )
    await smtp_client.connect()
    await smtp_client.login(
        APP_EMAIL,
        APP_PASSWORD
    )
    return smtp_client

async def send_email(
    To_email: str,
    Subject: str,
    Content: str,
    smtp_client: aiosmtplib.SMTP
):
    message = EmailMessage()
    message["From"] = APP_EMAIL
    message["To"] = To_email
    message["Subject"] = Subject
    message.set_content(Content)

    await smtp_client.send_message(message)
