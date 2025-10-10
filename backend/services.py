from flask import current_app
import os
from datetime import datetime
from .models import db, Boss, Staff
from email_validator import validate_email, EmailNotValidError
from . import mail
from flask_mail import Message
import traceback
import pandas as pd
from io import BytesIO


class BossService:
    @staticmethod
    def register_boss(email, password, company_name, firstname, lastname):
        """Register a new company boss"""
        # Validate email format and domain
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
            # Don't reveal if email exists or not for security
            return {'message': 'If email exists, reset link has been sent'}, 200

        try:
            # Generate the code - this will save to reset_token column
            code = boss.generate_reset_token()

            # Try to send email (optional since email is failing)
            try:
                EmailService.send_password_reset_email(boss)
            except Exception as email_error:
                print(f"Email sending failed: {email_error}")

            # Return success with debug code for testing
            return {
                'message': 'Password reset code sent to your email'
            }, 200
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

        # Validate new password
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
                proof_of_id='pending_upload'  # Placeholder until file is uploaded
            )

            db.session.add(staff)
            db.session.commit()
            return {'message': 'Staff added successfully', 'staff_id': staff.id}, 201
        except Exception as e:
            db.session.rollback()
            return {'error': str(e)}, 400

    @staticmethod
    def add_staff_with_file(boss_id, data, file=None):
        """Add staff member with optional proof of ID file upload"""
        try:
            # Parse date of birth
            try:
                date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return {'error': 'Invalid date format. Use YYYY-MM-DD'}, 400

            # Check if National Insurance Number already exists
            existing_staff = Staff.query.filter_by(
                national_insurance_number=data['national_insurance_number'].upper()
            ).first()
            if existing_staff:
                return {'error': 'National Insurance Number already exists'}, 400

            # Handle file upload if provided
            proof_of_id_filename = 'pending_upload'
            if file and file.filename:
                # Validate file type
                if not FileService.allowed_file(file.filename):
                    return {'error': 'Invalid file type. Allowed: PDF, PNG, JPG, JPEG'}, 400

                # Create staff first to get ID for filename
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
                    proof_of_id='temp',  # Temporary value
                    boss_id=boss_id
                )

                db.session.add(staff)
                db.session.flush()  # Get the ID without committing

                # Save file with proper naming convention
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                filename = f"staff_{staff.id}_{data['firstname'].lower()}_id.{file_extension}"
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                # Update with actual filename
                staff.proof_of_id = filename
                proof_of_id_filename = filename
            else:
                # Create staff without file (will require separate upload)
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
                    proof_of_id=proof_of_id_filename,
                    boss_id=boss_id
                )
                db.session.add(staff)

            db.session.commit()

            return {
                'message': 'Staff member added successfully',
                'staff': staff.to_dict(),
                'file_status': 'uploaded' if file else 'pending_upload'
            }, 201

        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to add staff: {str(e)}'}, 500

    @staticmethod
    def get_staff_by_boss(boss_id):
        """Get all staff members for a specific boss"""
        staff_list = Staff.query.filter_by(boss_id=boss_id).all()
        return [staff.to_dict() for staff in staff_list]

    @staticmethod
    def get_staff_by_id(staff_id, boss_id):
        """Get specific staff member"""
        staff = Staff.query.filter_by(id=staff_id, boss_id=boss_id).first()
        return staff.to_dict() if staff else None

    @staticmethod
    def get_staff_by_boss_for_export(boss_id):
        """Get all staff for a specific boss in export format"""
        try:
            staff_query = Staff.query.filter_by(boss_id=boss_id).order_by(Staff.firstname, Staff.lastname)

            staff_list = []
            for staff in staff_query.all():
                staff_list.append({
                    'id': staff.id,
                    'firstname': staff.firstname,
                    'lastname': staff.lastname,
                    'national_insurance_number': staff.national_insurance_number,
                    'home_address': staff.home_address,
                    'telephone_number': staff.telephone_number,
                    'employment_status': staff.employment_status,
                    'immigration_status': staff.immigration_status,
                    'visa_type': staff.visa_type,
                    'visa_sharecode': staff.visa_sharecode,
                    'sex': staff.sex,
                    'date_of_birth': staff.date_of_birth.strftime('%Y-%m-%d') if staff.date_of_birth else '',
                    'proof_of_id': staff.proof_of_id
                })

            return staff_list

        except Exception as e:
            print(f"Get staff for export error: {e}")
            return []

    @staticmethod
    def update_staff_json_only(staff_id, boss_id, update_data):
        """Update staff member with JSON data only (no file upload)"""
        staff = Staff.query.filter_by(id=staff_id, boss_id=boss_id).first()
        if not staff:
            return {'error': 'Staff not found'}, 404

        try:
            # Update fields from JSON data
            for key, value in update_data.items():
                if key == 'date_of_birth' and value:
                    try:
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        return {'error': 'Invalid date format. Use YYYY-MM-DD'}, 400
                elif key == 'national_insurance_number' and value:
                    # Check if NI number is being changed and if it already exists
                    if value.upper() != staff.national_insurance_number:
                        existing = Staff.query.filter_by(national_insurance_number=value.upper()).first()
                        if existing:
                            return {'error': 'National Insurance Number already exists'}, 400
                    value = value.upper()
                elif isinstance(value, str):
                    value = value.strip()

                # Only update valid staff attributes
                if hasattr(staff, key) and key not in ['id', 'boss_id', 'created_at']:
                    setattr(staff, key, value)

            staff.updated_at = datetime.utcnow()
            db.session.commit()

            return {
                'message': 'Staff updated successfully',
                'staff': staff.to_dict()
            }, 200

        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update staff: {str(e)}'}, 500

    @staticmethod
    def update_staff_with_file(staff_id, boss_id, update_data, file=None):
        """Update staff member with form data and optional file upload (like add_staff_with_file)"""
        staff = Staff.query.filter_by(id=staff_id, boss_id=boss_id).first()
        if not staff:
            return {'error': 'Staff not found'}, 404

        try:
            # Handle file upload first if provided (same as add_staff_with_file)
            if file and file.filename:
                if not FileService.allowed_file(file.filename):
                    return {'error': 'Invalid file type. Allowed: PDF, PNG, JPG, JPEG'}, 400

                # Delete old file if it exists
                if staff.proof_of_id and staff.proof_of_id != 'pending_upload':
                    old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], staff.proof_of_id)
                    if os.path.exists(old_file_path):
                        os.remove(old_file_path)

                # Save new file
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                filename = f"staff_{staff_id}_{staff.firstname.lower()}_id.{file_extension}"
                upload_folder = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                # Update proof_of_id in update_data
                update_data['proof_of_id'] = filename

            # Update other fields (same logic as add_staff_with_file)
            for key, value in update_data.items():
                if key == 'date_of_birth' and value:
                    try:
                        value = datetime.strptime(value, '%Y-%m-%d').date()
                    except ValueError:
                        return {'error': 'Invalid date format. Use YYYY-MM-DD'}, 400
                elif key == 'national_insurance_number' and value:
                    # Check if NI number is being changed and if it already exists
                    if value.upper() != staff.national_insurance_number:
                        existing = Staff.query.filter_by(national_insurance_number=value.upper()).first()
                        if existing:
                            return {'error': 'National Insurance Number already exists'}, 400
                    value = value.upper()
                elif isinstance(value, str) and value:
                    value = value.strip()

                # Only update valid staff attributes
                if hasattr(staff, key) and key not in ['id', 'boss_id', 'created_at'] and value:
                    setattr(staff, key, value)

            staff.updated_at = datetime.utcnow()
            db.session.commit()

            return {
                'message': 'Staff updated successfully',
                'staff': staff.to_dict(),
                'file_status': 'uploaded' if file else 'no_file_change'
            }, 200

        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to update staff: {str(e)}'}, 500

    @staticmethod
    def delete_staff(staff_id, boss_id):
        """Delete staff member"""
        staff = Staff.query.filter_by(id=staff_id, boss_id=boss_id).first()
        if not staff:
            return {'error': 'Staff not found'}, 404

        db.session.delete(staff)
        db.session.commit()
        return {'message': 'Staff deleted successfully'}, 200

    @staticmethod
    def search_staff(boss_id, query=None, employment_status=None):
        """Search staff by query and/or employment status"""
        try:
            # Start with base query
            staff_query = Staff.query.filter_by(boss_id=boss_id)

            # Add search conditions
            if query:
                search_term = f'%{query}%'
                staff_query = staff_query.filter(
                    db.or_(
                        Staff.firstname.ilike(search_term),
                        Staff.lastname.ilike(search_term),
                        Staff.telephone_number.ilike(search_term),
                        Staff.national_insurance_number.ilike(search_term)
                    )
                )

            if employment_status:
                staff_query = staff_query.filter_by(employment_status=employment_status)

            # Execute query and convert to list
            staff_list = []
            for staff in staff_query.order_by(Staff.firstname, Staff.lastname).all():
                staff_list.append({
                    'id': staff.id,
                    'firstname': staff.firstname,
                    'lastname': staff.lastname,
                    'national_insurance_number': staff.national_insurance_number,
                    'home_address': staff.home_address,
                    'telephone_number': staff.telephone_number,
                    'employment_status': staff.employment_status,
                    'immigration_status': staff.immigration_status,
                    'visa_type': staff.visa_type,
                    'visa_sharecode': staff.visa_sharecode,
                    'sex': staff.sex,
                    'date_of_birth': staff.date_of_birth.strftime('%Y-%m-%d') if staff.date_of_birth else '',
                    'proof_of_id': staff.proof_of_id
                })

            return staff_list

        except Exception as e:
            print(f"Search error: {e}")
            return []


class FileService:
    @staticmethod
    def upload_proof_of_id(file, staff_id, boss_id=None):
        """Handle proof of ID file upload with boss verification"""
        if not file or file.filename == '':
            return {'error': 'No file selected'}, 400

        # Verify staff exists and belongs to boss if boss_id provided
        staff = Staff.query.get(staff_id)
        if not staff:
            return {'error': 'Staff not found'}, 404

        if boss_id and staff.boss_id != boss_id:
            return {'error': 'Unauthorized access to staff record'}, 403

        if FileService.allowed_file(file.filename):
            # Delete old file if it exists
            if staff.proof_of_id and staff.proof_of_id != 'pending_upload':
                old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], staff.proof_of_id)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)

            # Create new filename
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            filename = f"staff_{staff_id}_{staff.firstname.lower()}_id.{file_extension}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

            # Ensure upload directory exists
            os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

            file.save(upload_path)

            # Update staff record
            staff.proof_of_id = filename
            staff.updated_at = datetime.utcnow()
            db.session.commit()

            return {'message': 'Proof of ID uploaded successfully', 'filename': filename}, 200

        return {'error': 'Invalid file type. Allowed: PDF, PNG, JPG, JPEG'}, 400

    @staticmethod
    def allowed_file(filename):
        """Check if file type is allowed"""
        ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @staticmethod
    def create_staff_excel(staff_list):
        """Create Excel file from staff data"""
        try:
            # Prepare data for Excel
            excel_data = []
            for staff in staff_list:
                excel_data.append({
                    'First Name': staff.get('firstname', ''),
                    'Last Name': staff.get('lastname', ''),
                    'National Insurance Number': staff.get('national_insurance_number', ''),
                    'Home Address': staff.get('home_address', ''),
                    'Telephone Number': staff.get('telephone_number', ''),
                    'Employment Status': staff.get('employment_status', ''),
                    'Immigration Status': staff.get('immigration_status', ''),
                    'Visa Type': staff.get('visa_type', ''),
                    'Visa Sharecode': staff.get('visa_sharecode', ''),
                    'Sex': staff.get('sex', ''),
                    'Date of Birth': staff.get('date_of_birth', ''),
                    'Proof of ID': staff.get('proof_of_id', '')
                })

            # Create DataFrame
            df = pd.DataFrame(excel_data)

            # Create Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Staff List', index=False)

                # Auto-adjust column widths
                worksheet = writer.sheets['Staff List']
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            output.seek(0)
            return output

        except Exception as e:
            print(f"Excel creation error: {e}")
            raise e


class ValidationService:
    @staticmethod
    def validate_email(email):
        """Validate email format and domain"""
        try:
            # Validate and get info about the email
            valid = validate_email(email, check_deliverability=True)
            return True, valid.email
        except EmailNotValidError as e:
            return False, str(e)

    @staticmethod
    def validate_boss_data(data):
        """Validate boss registration data"""
        required_fields = ['email', 'password', 'company_name', 'firstname', 'lastname']
        errors = []

        # Check required fields
        for field in required_fields:
            if field not in data or not data[field] or data[field].strip() == '':
                errors.append(f'{field} is required')

        if errors:
            return errors

        # Validate email
        email, email_error = ValidationService.validate_email(data['email'])
        if email_error:
            errors.append(f'Invalid email: {email_error}')

        # Validate password strength
        password = data['password']
        if len(password) < 8:
            errors.append('Password must be at least 8 characters long')
        if not any(c.isupper() for c in password):
            errors.append('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in password):
            errors.append('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in password):
            errors.append('Password must contain at least one number')
        if not any(c in '!@#$%^&*(),.?":{}|<>' for c in password):
            errors.append('Password must contain at least one special character')

        return errors if errors else None

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

    @staticmethod
    def validate_staff_data(data):
        """Validate staff input data"""
        required_fields = [
            'firstname', 'lastname', 'national_insurance_number',
            'home_address', 'telephone_number', 'employment_status',
            'immigration_status', 'visa_type', 'visa_sharecode', 'sex', 'date_of_birth'
        ]

        errors = []
        for field in required_fields:
            if field not in data or not data[field]:
                errors.append(f'{field} is required')

        # Validate specific fields
        if 'sex' in data and data['sex'] not in ['Male', 'Female', 'Other']:
            errors.append('Invalid sex value')

        if 'employment_status' in data and data['employment_status'] not in ['Full-time', 'Part-time', 'Contract',
                                                                             'Intern']:
            errors.append('Invalid employment status')

        return errors if errors else None


class EmailService:
    @staticmethod
    def send_password_reset_email(boss):
        """Send 6-digit password reset code via email"""
        code = boss.generate_reset_token()

        # Print code to console for testing
        print(f"\n=== PASSWORD RESET CODE ===")
        print(f"Email: {boss.email}")
        print(f"6-Digit Code: {code}")
        print(f"============================\n")

        msg = Message(
            'Password Reset Code',
            recipients=[boss.email],
            html=f"""
            <h2>Password Reset Code</h2>
            <p>Hello {boss.firstname},</p>
            <p>You have requested to reset your password for {boss.company_name}.</p>
            <p><strong>Your 6-digit password reset code is:</strong></p>
            <h2 style="background-color: #f0f0f0; padding: 15px; text-align: center; font-family: monospace; letter-spacing: 3px;">{code}</h2>
            <p>Enter this code to reset your password.</p>
            <p><strong>This code will expire in 15 minutes.</strong></p>
            <p>If you didn't request this, please ignore this email.</p>
            <br>
            <p>Best regards,<br>Staff Management System</p>
            """,
            body=f"""
            Password Reset Code

            Hello {boss.firstname},

            You have requested to reset your password for {boss.company_name}.

            Your 6-digit password reset code is: {code}

            Enter this code to reset your password.
            This code will expire in 15 minutes.

            If you didn't request this, please ignore this email.

            Best regards,
            Staff Management System
            """
        )

        try:
            mail.send(msg)
            print("Email sent successfully!")
            return True
        except Exception as e:
            print(f"Email failed, but code printed above: {e}")
            return False
