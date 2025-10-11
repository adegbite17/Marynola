import os
import traceback
from datetime import datetime
from io import BytesIO

import pandas as pd
import cloudinary.uploader
from flask import current_app
from flask_mail import Message
from email_validator import validate_email, EmailNotValidError

from .models import db, Boss, Staff
from . import mail
import requests


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
            code = boss.generate_reset_token()

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
        boss = Boss.verify_reset_token(email, code)
        if not boss:
            return {'error': 'Invalid or expired token'}, 400

        is_valid, message = ValidationService.validate_password(new_password)
        if not is_valid:
            return {'error': message}, 400

        boss.set_password(new_password)
        boss.clear_reset_code()
        db.session.commit()

        return {'message': 'Password reset successfully'}, 200



class StaffService:
    @staticmethod
    def add_staff(boss_id, staff_data):
        """Add new staff member"""
        try:
            staff = Staff(
                boss_id=boss_id,
                firstname=staff_data['firstname'],
                lastname=staff_data['lastname'],
                national_insurance_number=staff_data['national_insurance_number'],
                home_address=staff_data['home_address'],
                telephone_number=staff_data['telephone_number'],
                employment_status=staff_data['employment_status'],
                immigration_status=staff_data['immigration_status'],
                visa_type=staff_data.get('visa_type'),
                visa_sharecode=staff_data.get('visa_sharecode'),
                sex=staff_data['sex'],
                date_of_birth=datetime.strptime(staff_data['date_of_birth'], '%Y-%m-%d').date(),
                proof_of_id='pending_upload'
            )
            db.session.add(staff)
            db.session.commit()
            return {'message': 'Staff added successfully', 'staff_id': staff.id}, 201
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 400

    @staticmethod
    def add_staff_with_file(boss_id, data, file=None):
        """Add staff member with optional proof of ID file upload to Cloudinary"""
        try:
            # Validate date format
            try:
                date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return {'error': 'Invalid date format. Use YYYY-MM-DD'}, 400

            # Check for duplicate National Insurance Number
            if Staff.query.filter_by(
                    national_insurance_number=data['national_insurance_number'].upper()
            ).first():
                return {'error': 'National Insurance Number already exists'}, 400

            # Create staff record first
            staff = Staff(
                firstname=data['firstname'].strip(),
                lastname=data['lastname'].strip(),
                national_insurance_number=data['national_insurance_number'].upper(),
                home_address=data['home_address'].strip(),
                telephone_number=data['telephone_number'].strip(),
                employment_status=data['employment_status'],
                immigration_status=data['immigration_status'].strip(),
                visa_type=data['visa_type'].strip(),
                visa_sharecode=data['visa_sharecode'].strip(),
                sex=data['sex'],
                date_of_birth=date_of_birth,
                proof_of_id='pending_upload',  # Default value
                boss_id=boss_id
            )

            db.session.add(staff)
            db.session.flush()  # Get staff.id without committing

            # Handle file upload to Cloudinary if provided
            if file and file.filename:
                if not FileService.allowed_file(file.filename):
                    return {'error': 'Invalid file type. Allowed: PDF, PNG, JPG, JPEG'}, 400

                file_ext = file.filename.rsplit('.', 1)[1].lower()
                resource_type = "raw" if file_ext == 'pdf' else "image"

                # Upload to Cloudinary
                result = cloudinary.uploader.upload(
                    file,
                    folder=f"staff_proofs/boss_{boss_id}",
                    public_id=f"staff_{staff.id}_proof",
                    resource_type=resource_type,
                    overwrite=True,
                    secure=True
                )

                # Update staff record with Cloudinary URL
                staff.proof_of_id = result['secure_url']

            db.session.commit()

            return {
                'message': 'Staff member added successfully',
                'staff': staff.to_dict(),
                'file_status': 'uploaded' if file else 'pending_upload'
            }, 201

        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to add staff: {str(e)}'}, 500

    # In services.py - StaffService class
    @staticmethod
    def delete_staff(staff_id, boss_id):
        """Delete staff member and their Cloudinary file"""
        try:
            staff = Staff.query.filter_by(id=staff_id, boss_id=boss_id).first()
            if not staff:
                return {'error': 'Staff not found'}, 404

            # Delete file from Cloudinary if it exists
            if staff.proof_of_id and staff.proof_of_id.startswith('http'):
                try:
                    import cloudinary.uploader
                    # Extract public_id from Cloudinary URL
                    public_id = f"staff_proofs/boss_{boss_id}/staff_{staff_id}_proof"
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    print(f"Failed to delete Cloudinary file: {e}")
                    # Continue with database deletion even if file deletion fails

            db.session.delete(staff)
            db.session.commit()

            return {'message': 'Staff deleted successfully'}, 200

        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to delete staff: {str(e)}'}, 500

    @staticmethod
    def get_staff_by_boss(boss_id):
        """Get all staff members for a specific boss"""
        staff_list = Staff.query.filter_by(boss_id=boss_id).all()
        return [s.to_dict() for s in staff_list]

    @staticmethod
    def get_staff_by_id(staff_id, boss_id):
        """Get specific staff member"""
        staff = Staff.query.filter_by(id=staff_id, boss_id=boss_id).first()
        return staff.to_dict() if staff else None

    @staticmethod
    def update_staff_with_file(staff_id, boss_id, update_data, file=None):
        """Update staff with optional file upload to Cloudinary"""
        try:
            staff = Staff.query.filter_by(id=staff_id, boss_id=boss_id).first()
            if not staff:
                return {'error': 'Staff not found'}, 404

            for field, value in update_data.items():
                if field != 'proof_of_id' and hasattr(staff, field):
                    setattr(staff, field, value)

            if file and file.filename:
                result = cloudinary.uploader.upload(
                    file,
                    folder=f"staff_proofs/boss_{boss_id}",
                    public_id=f"staff_{staff_id}_proof",
                    resource_type="auto",
                    overwrite=True
                )
                staff.proof_of_id = result['secure_url']

            db.session.commit()
            return {'message': 'Staff updated successfully'}, 200

        except Exception as e:
            db.session.rollback()
            return {'error': f'Update failed: {str(e)}'}, 500



class FileService:
    @staticmethod
    def upload_proof_of_id(file, staff_id, boss_id):
        """Upload file to Cloudinary"""
        try:
            if not file or not file.filename:
                return {'error': 'No file selected'}, 400

            # Check file type first
            if not FileService.allowed_file(file.filename):
                return {'error': 'Invalid file type. Allowed: PDF, PNG, JPG, JPEG'}, 400

            # Determine resource type based on file extension
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            if file_ext == 'pdf':
                resource_type = "raw"
            else:
                resource_type = "image"

            result = cloudinary.uploader.upload(
                file,
                folder=f"staff_proofs/boss_{boss_id}",
                public_id=f"staff_{staff_id}_proof",
                resource_type=resource_type,  # Use specific type instead of "auto"
                overwrite=True,
                secure=True  # Force HTTPS
            )

            staff = Staff.query.filter_by(id=staff_id, boss_id=boss_id).first()
            if not staff:
                return {'error': 'Staff not found'}, 404

            staff.proof_of_id = result['secure_url']
            db.session.commit()

            # Debug: Print what we're storing
            print(f"Stored URL: {result['secure_url']}")
            print(f"Resource type: {resource_type}")

            return {'message': 'File uploaded successfully', 'file_url': result['secure_url']}, 200

        except Exception as e:
            print(f"Upload error: {e}")
            return {'error': f'Upload failed: {str(e)}'}, 500

    # In services.py - FileService class
    @staticmethod
    def get_staff_by_boss_for_export(staff_list):
        """Create Excel file in memory (cloud-compatible)"""
        try:
            # Convert staff data to DataFrame
            df_data = []
            for staff in staff_list:
                df_data.append({
                    'ID': staff.get('id'),
                    'First Name': staff.get('firstname'),
                    'Last Name': staff.get('lastname'),
                    'National Insurance': staff.get('national_insurance_number'),
                    'Home Address': staff.get('home_address'),
                    'Telephone': staff.get('telephone_number'),
                    'Employment Status': staff.get('employment_status'),
                    'Immigration Status': staff.get('immigration_status'),
                    'Visa Type': staff.get('visa_type'),
                    'Visa Share Code': staff.get('visa_sharecode'),
                    'Sex': staff.get('sex'),
                    'Date of Birth': staff.get('date_of_birth'),
                    'Proof of ID': 'Uploaded' if staff.get('proof_of_id') and staff.get(
                        'proof_of_id') != 'pending_upload' else 'Pending'
                })

            df = pd.DataFrame(df_data)

            # Create Excel file in memory
            excel_buffer = BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Staff List', index=False)

            excel_buffer.seek(0)
            return excel_buffer

        except Exception as e:
            raise Exception(f"Failed to create Excel file: {str(e)}")

    @staticmethod
    def allowed_file(filename):
        """Check if file type is allowed"""
        ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def create_staff_excel(staff_list):
        """Create Excel file from staff data"""
        try:
            df = pd.DataFrame([
                {
                    'First Name': s.get('firstname', ''),
                    'Last Name': s.get('lastname', ''),
                    'National Insurance Number': s.get('national_insurance_number', ''),
                    'Home Address': s.get('home_address', ''),
                    'Telephone Number': s.get('telephone_number', ''),
                    'Employment Status': s.get('employment_status', ''),
                    'Immigration Status': s.get('immigration_status', ''),
                    'Visa Type': s.get('visa_type', ''),
                    'Visa Sharecode': s.get('visa_sharecode', ''),
                    'Sex': s.get('sex', ''),
                    'Date of Birth': s.get('date_of_birth', ''),
                    'Proof of ID': s.get('proof_of_id', '')
                } for s in staff_list
            ])

            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Staff List', index=False)

                worksheet = writer.sheets['Staff List']
                for column in worksheet.columns:
                    max_length = max(len(str(cell.value)) for cell in column if cell.value)
                    col_letter = column[0].column_letter
                    worksheet.column_dimensions[col_letter].width = min(max_length + 2, 50)

            output.seek(0)
            return output

        except Exception as e:
            print(f"Excel creation error: {e}")
            raise e



class ValidationService:
    @staticmethod
    def validate_email(email):
        try:
            valid = validate_email(email, check_deliverability=True)
            return True, valid.email
        except EmailNotValidError as e:
            return False, str(e)

    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if not password or len(password.strip()) == 0:
            return False, 'Password is required'
        if len(password) < 8:
            return False, 'Password must be at least 8 characters long'
        if not any(c.isupper() for c in password):
            return False, 'Password must contain at least one uppercase letter'
        if not any(c.islower() for c in password):
            return False, 'Password must contain at least one lowercase letter'
        if not any(c.isdigit() for c in password):
            return False, 'Password must contain at least one number'
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
            return False, 'Password must contain at least one special character'
        return True, 'Password is valid'


# ==========================================================
#                     EMAIL SERVICE
# ==========================================================
class EmailService:
    @staticmethod
    def send_password_reset_email(boss):
        """Send 6-digit password reset code via email"""
        code = boss.generate_reset_token()

        print(f"\n=== PASSWORD RESET CODE ===\n"
              f"Email: {boss.email}\n"
              f"6-Digit Code: {code}\n"
              f"============================\n")

        msg = Message(
            'Password Reset Code',
            recipients=[boss.email],
            html=f"""
                <h2>Password Reset Code</h2>
                <p>Hello {boss.firstname},</p>
                <p>You have requested to reset your password for {boss.company_name}.</p>
                <p><strong>Your 6-digit password reset code is:</strong></p>
                <h2 style="background-color: #f0f0f0; padding: 15px; text-align: center; 
                font-family: monospace; letter-spacing: 3px;">{code}</h2>
                <p>This code will expire in 15 minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
                <br><p>Best regards,<br>Staff Management System</p>
            """,
            body=f"""
                Hello {boss.firstname},

                You requested to reset your password for {boss.company_name}.
                Your 6-digit password reset code is: {code}

                This code will expire in 15 minutes.
                If you didn't request this, please ignore this email.
            """
        )

        try:
            mail.send(msg)
            print("Email sent successfully!")
            return True
        except Exception as e:
            print(f"Email failed (but code printed): {e}")
            return False
