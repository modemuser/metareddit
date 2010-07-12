import smtplib
from email.mime.text import MIMEText
from myapp.config import smtp_server, my_email


def sendmail(you, subject, body):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['To'] = you
        msg['From'] = my_email
        s = smtplib.SMTP(smtp_server)
        s.sendmail(my_email, you, msg.as_string())
        s.quit()
        return True
    except:
        return False
