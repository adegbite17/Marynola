import traceback
from .services import ValidationService
from .reset_password_utils import EmailService
from .models import db, Boss

class BossService:
    @staticmethod
    def register_boss(email, password, company_name, firstname, lastname):
        """Register a new company boss"""
        is_valid, result = ValidationService.validate_email(email)
        if not is_valid:
            return {'error': f'Invalid email: {result}'}, 400

        validated_email = result

        if Boss.query.filter_by(email=validated_email).first():
            return {'error': 'Email already exists'}, 400

        boss = Boss(
            email=validated_email,
            company_name=company_name,
            firstname=firstname,
            lastname=lastname
        )
        boss.set_password(password)
        db.session.add(boss)
        db.session.commit()

        return {'message': 'Boss registered successfully'}, 201

    @staticmethod
    def authenticate_boss(email, password):
        """Authenticate boss login"""
        boss = Boss.query.filter_by(email=email).first()
        if boss and boss.check_password(password):
            return boss
        return None

    @staticmethod
    def request_password_reset(email):
        """Send password reset email"""
        boss = Boss.query.filter_by(email=email.lower()).first()
        if not boss:
            return {'message': 'If email exists, reset link has been sent'}, 200

        try:
            try:
                EmailService.send_password_reset_email(boss)
            except Exception as email_error:
                print(f"Email sending failed: {email_error}")

            return {'message': 'Password reset code sent to your email'}, 200

        except Exception as e:
            print(f"Error in request_password_reset: {e}")
            traceback.print_exc()
            return {'error': f'Failed to send reset email: {str(e)}'}, 500

    @staticmethod
    def reset_password(email, code, new_password):
        """Reset password using email and code"""
        boss = Boss.verify_reset_code(email, code)
        if not boss:
            return {'error': 'Invalid or expired token'}, 400

        is_valid, message = ValidationService.validate_password(new_password)
        if not is_valid:
            return {'error': message}, 400

        boss.set_password(new_password)
        boss.clear_reset_code()
        db.session.commit()

        return {'message': 'Password reset successfully'}, 200