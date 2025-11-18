import os
from threading import Thread
from dotenv import load_dotenv
from flask_mail import Message
from flask import current_app
from . import mail

load_dotenv()


class EmailService:
    @staticmethod
    def send_password_reset_email(boss):
        """Send 6-digit password reset code via email"""
        # Capture attributes BEFORE generate_reset_code commits
        to_email = boss.email
        firstname = boss.firstname
        company_name = boss.company_name

        code = boss.generate_reset_code()

        # Capture the app instance for the thread
        app = current_app._get_current_object()

        def send_async(app, to_email=to_email, firstname=firstname, company_name=company_name, code=code):
            with app.app_context():  # Push app context into thread
                try:
                    msg = Message(
                        'Password Reset Code',
                        recipients=[to_email],
                        html=f"""
                           <h2>Password Reset Code</h2>
                           <p>Hello {firstname},</p>
                           <p>You have requested to reset your password for {company_name}.</p>
                           <p><strong>Your 6-digit password reset code is:</strong></p>
                           <h2 style="background-color: #f0f0f0; padding: 15px; text-align: center;
                           font-family: monospace; letter-spacing: 3px;">{code}</h2>
                           <p>This code will expire in 15 minutes.</p>
                           <p>If you didn't request this, please ignore this email.</p>
                           <br><p>Best regards,<br>Staff Management System</p>
                       """,
                        body=f"""
                           Hello {firstname},

                           You requested to reset your password for {company_name}.
                           Your 6-digit password reset code is: {code}

                           This code will expire in 15 minutes.
                           If you didn't request this, please ignore this email.
                       """
                    )

                    mail.send(msg)
                    print(f"Email sent successfully to {to_email}!")
                    return True
                except Exception as e:
                    print(f"Email failed: {e}")
                    return False

        Thread(target=send_async, args=[app], daemon=True).start()
        return True
