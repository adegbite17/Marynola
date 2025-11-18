from io import BytesIO

import pandas as pd
import cloudinary.uploader
from .models import db, Staff


class FileService:
    @staticmethod
    def upload_proof_of_id(file, staff_id, boss_id):
        """Upload file to Cloudinary"""
        try:
            if not file or not file.filename:
                return {'error': 'No file selected'}, 400

            #check file type first
            if not FileService.allowed_file(file.filename):
                return {'error': 'Invalid file type. Allowed: PDF, PNG, JPG, JPEG'}, 400

            #determine resource type based on file extension
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

            #print what is storing
            print(f"Stored URL: {result['secure_url']}")
            print(f"Resource type: {resource_type}")

            return {'message': 'File uploaded successfully', 'file_url': result['secure_url']}, 200

        except Exception as e:
            print(f"Upload error: {e}")
            return {'error': f'Upload failed: {str(e)}'}, 500


    @staticmethod
    def get_staff_by_boss_for_export(staff_list):
        """Create Excel file in memory (cloud-compatible)"""
        try:
            #convert staff data to DataFrame
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

            #create Excel file in memory
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