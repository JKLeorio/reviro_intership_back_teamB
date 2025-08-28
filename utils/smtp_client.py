import aiosmtplib
from email.message import EmailMessage
import decouple
import logging
from conf import DEBUG


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
):
    if not DEBUG:
        from main import app
        # smtp_client: aiosmtplib.SMTP | None = getattr(app.state, "smtp_client", None)
        smtp_client: aiosmtplib.SMTP = await init_smtp()
        message = EmailMessage()
        message["From"] = APP_EMAIL
        message["To"] = To_email
        message["Subject"] = Subject
        message.set_content(Content)
        
        # if smtp_client is None:
        #     smtp_client = await init_smtp()
        #     app.state.smtp_client = smtp_client
        logging.info(f"send email from {APP_EMAIL} To {To_email} \n Subject {Subject}")

        try:
            await smtp_client.send_message(message)
            logging.info(f"Email sent successfully to {To_email}")
        except aiosmtplib.errors.SMTPException as e:
            logging.error(f"SMTP error: {e}")
            raise
        except (
            aiosmtplib.errors.SMTPConnectError,
            aiosmtplib.errors.SMTPServerDisconnected,
            OSError) as e:
            logging.warning(f"SMTP connection lost: {e}, restarting client...")
            try:
                if smtp_client is not None:
                    await smtp_client.quit()
                    return
            except Exception:
                pass
            # app.state.smtp_client = await init_smtp()
        await smtp_client.quit()

    