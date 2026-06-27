import smtplib
from email.mime.text import MIMEText

from email_config import EMAIL_ADDRESS, EMAIL_PASSWORD

receiver_email = "suldanshiine02@gmail.com"

subject = "Locust Prediction System Test"
body = """
Hello,

This is a test email from the Locust Prediction System.

If you received this email, Gmail integration is working successfully.

Regards,
Locust Prediction System
"""

msg = MIMEText(body)
msg["Subject"] = subject
msg["From"] = EMAIL_ADDRESS
msg["To"] = receiver_email

try:
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(
        EMAIL_ADDRESS,
        EMAIL_PASSWORD
    )

    server.send_message(msg)

    server.quit()

    print("Email sent successfully!")

except Exception as e:
    print("Error:", e)