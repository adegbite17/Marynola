from datetime import datetime
import cloudinary.uploader
from email_validator import validate_email, EmailNotValidError
from .models import db, Staff
from .file_services import FileService



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
            #validate date format
            try:
                date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return {'error': 'Invalid date format. Use YYYY-MM-DD'}, 400

            #check for duplicate National Insurance Number
            if Staff.query.filter_by(
                    national_insurance_number=data['national_insurance_number'].upper()
            ).first():
                return {'error': 'National Insurance Number already exists'}, 400

            #create staff record first
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
                proof_of_id='pending_upload',  #default value
                boss_id=boss_id
            )

            db.session.add(staff)
            db.session.flush()  #get staff.id without committing

            #handle file upload to Cloudinary if provided
            if file and file.filename:
                if not FileService.allowed_file(file.filename):
                    return {'error': 'Invalid file type. Allowed: PDF, PNG, JPG, JPEG'}, 400

                file_ext = file.filename.rsplit('.', 1)[1].lower()
                resource_type = "raw" if file_ext == 'pdf' else "image"

                #upload to Cloudinary
                result = cloudinary.uploader.upload(
                    file,
                    folder=f"staff_proofs/boss_{boss_id}",
                    public_id=f"staff_{staff.id}_proof",
                    resource_type=resource_type,
                    overwrite=True,
                    secure=True
                )

                #update staff record with Cloudinary URL
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


    @staticmethod
    def delete_staff(staff_id, boss_id):
        """Delete staff member and their Cloudinary file"""
        try:
            staff = Staff.query.filter_by(id=staff_id, boss_id=boss_id).first()
            if not staff:
                return {'error': 'Staff not found'}, 404

            #delete file from Cloudinary if it exists
            if staff.proof_of_id and staff.proof_of_id.startswith('http'):
                try:
                    import cloudinary.uploader
                    #extract public_id from Cloudinary URL
                    public_id = f"staff_proofs/boss_{boss_id}/staff_{staff_id}_proof"
                    cloudinary.uploader.destroy(public_id)
                except Exception as e:
                    print(f"Failed to delete Cloudinary file: {e}")
                    #continues with database deletion even if file deletion fails

            db.session.delete(staff)
            db.session.commit()

            return {'message': 'Staff deleted successfully'}, 200

        except Exception as e:
            db.session.rollback()
            return {'error': f'Failed to delete staff: {str(e)}'}, 500

    @staticmethod
    def search_staff(boss_id, query='', employment_status=''):
        """Search staff by name, phone, NIN, and/or employment status"""
        try:
            #start with all staff for this boss
            staff_query = Staff.query.filter_by(boss_id=boss_id)

            #apply text search if query provided
            if query:
                search_pattern = f"%{query}%"
                staff_query = staff_query.filter(
                    db.or_(
                        Staff.firstname.ilike(search_pattern),
                        Staff.lastname.ilike(search_pattern),
                        Staff.telephone_number.ilike(search_pattern),
                        Staff.national_insurance_number.ilike(search_pattern)
                    )
                )

            #apply employment status filter if provided
            if employment_status:
                staff_query = staff_query.filter_by(employment_status=employment_status)

            #execute query and return results
            staff_list = staff_query.all()
            return [s.to_dict() for s in staff_list]

        except Exception as e:
            print(f"Search error in StaffService: {e}")
            raise

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
    def update_staff_json_only(staff_id, boss_id, update_data):
        """Update staff member with JSON data only (no file upload)"""
        try:
            staff = Staff.query.filter_by(id=staff_id, boss_id=boss_id).first()
            if not staff:
                return {'error': 'Staff not found'}, 404

            #validate date format if date_of_birth is being updated
            if 'date_of_birth' in update_data:
                try:
                    update_data['date_of_birth'] = datetime.strptime(
                        update_data['date_of_birth'], '%Y-%m-%d'
                    ).date()
                except ValueError:
                    return {'error': 'Invalid date format. Use YYYY-MM-DD'}, 400

            #check for duplicate National Insurance Number (excluding current staff)
            if 'national_insurance_number' in update_data:
                nin = update_data['national_insurance_number'].upper()
                duplicate = Staff.query.filter(
                    Staff.national_insurance_number == nin,
                    Staff.id != staff_id
                ).first()
                if duplicate:
                    return {'error': 'National Insurance Number already exists'}, 400
                update_data['national_insurance_number'] = nin

            #update allowed fields
            allowed_fields = [
                'firstname', 'lastname', 'national_insurance_number', 'home_address',
                'telephone_number', 'employment_status', 'immigration_status',
                'sex', 'date_of_birth', 'visa_type', 'visa_sharecode'
            ]

            for field in allowed_fields:
                if field in update_data:
                    value = update_data[field]
                    #strip whitespace from string fields
                    if isinstance(value, str):
                        value = value.strip()
                    setattr(staff, field, value)

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


