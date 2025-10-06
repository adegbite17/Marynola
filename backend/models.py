from datetime import datetime, timedelta
from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import random



# User model for customers and admins
class Boss(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(225), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reset_token = db.Column(db.String(6), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    # Relationship to staff
    staff_members = db.relationship('Staff', backref='boss', lazy=True, cascade='all, delete-orphan')


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_reset_token(self):
        """Generate a 6-digit reset code"""

        code = f"{random.randint(100000, 999999)}"
        self.reset_token = code
        self.reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)  # Expires in 15 minutes
        db.session.commit()
        return code

    @staticmethod
    def verify_reset_token(email, code):
        """Verify reset code"""

        boss = Boss.query.filter_by(email=email.lower()).first()
        if not boss or not boss.reset_token:
            return None

        if boss.reset_token_expiry and datetime.utcnow() > boss.reset_token_expiry:
            # Code expired, clear it
            boss.reset_token = None
            boss.reset_token_expiry = None
            db.session.commit()
            return None

        if boss.reset_token == code:
            return boss
        return None

    def clear_reset_code(self):
        """Clear reset code after successful password reset"""
        self.reset_token = None
        self.reset_token_expiry = None
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'company_name': self.company_name,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'created_at': self.created_at.isoformat()
        }



# Staff model for employee details
class Staff(db.Model):
    __tablename__ = 'staff'

    id = db.Column(db.Integer, primary_key=True)
    # Staff details as per your requirements
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    national_insurance_number = db.Column(db.String(20), unique=True, nullable=False)
    home_address = db.Column(db.Text, nullable=False)
    telephone_number = db.Column(db.String(20), nullable=False)
    employment_status = db.Column(db.String(50), nullable=False)  # Full-time, Part-time, Contract
    immigration_status = db.Column(db.String(100), nullable=False)
    visa_type = db.Column(db.String(50), nullable=False)
    visa_sharecode = db.Column(db.String(20), nullable=False)
    sex = db.Column(db.String(10), nullable=False)  # Male, Female, Other
    date_of_birth = db.Column(db.Date, nullable=False)
    proof_of_id = db.Column(db.String(255), nullable=False)  # File path for uploaded ID

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    boss_id = db.Column(db.Integer, db.ForeignKey('boss.id'), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'firstname': self.firstname,
            'lastname': self.lastname,
            'national_insurance_number': self.national_insurance_number,
            'home_address': self.home_address,
            'telephone_number': self.telephone_number,
            'employment_status': self.employment_status,
            'immigration_status': self.immigration_status,
            'visa_type': self.visa_type,
            'visa_sharecode': self.visa_sharecode,
            'sex': self.sex,
            'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
            'proof_of_id': self.proof_of_id
        }