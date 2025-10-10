from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import os
from datetime import datetime, timedelta

from .services import BossService, StaffService, FileService, ValidationService
from .models import Boss

# Create blueprint
main = Blueprint('main', __name__)


# Boss Authentication Routes
@main.route('/api/register', methods=['POST'])
def register_boss():
    """Register a new company boss"""
    data = request.get_json()

    required_fields = ['email', 'password', 'company_name', 'firstname', 'lastname']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    result, status = BossService.register_boss(
        data['email'],
        data['password'],
        data['company_name'],
        data['firstname'],
        data['lastname']
    )
    return jsonify(result), status


@main.route('/api/login', methods=['POST'])
def login():
    """Boss login"""
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password required'}), 400

    boss = BossService.authenticate_boss(data['email'], data['password'])
    if boss:
        access_token = create_access_token(
            identity=str(boss.id),
            expires_delta=timedelta(hours=24)
        )
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'boss_info': {
                'id': boss.id,
                'email': boss.email,
                'company_name': boss.company_name,
                'firstname': boss.firstname,
                'lastname': boss.lastname
            }
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401


@main.route('/api/debug/get-reset-token', methods=['POST'])
def get_reset_token_debug():
    """DEBUG ONLY - Get current reset code for testing"""
    data = request.get_json()
    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400

    boss = Boss.query.filter_by(email=data['email'].lower()).first()
    if boss and boss.reset_token:
        if boss.reset_token_expiry and datetime.utcnow() <= boss.reset_token_expiry:
            return jsonify({
                'email': boss.email,
                'code': boss.reset_token,
                'expires_at': boss.reset_token_expiry.isoformat()
            }), 200

    return jsonify({'error': 'No active reset code found'}), 404


@main.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset"""
    data = request.get_json()

    if not data or 'email' not in data:
        return jsonify({'error': 'Email is required'}), 400

    result, status = BossService.request_password_reset(data['email'])
    return jsonify(result), status


@main.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Reset password using email and 6-digit code"""
    data = request.get_json()

    if not data or 'email' not in data or 'code' not in data or 'password' not in data:
        return jsonify({'error': 'Email, code, and new password are required'}), 400

    result, status = BossService.reset_password(data['email'], data['code'], data['password'])
    return jsonify(result), status


@main.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    """Boss logout"""
    return jsonify({'message': 'Logged out successfully'}), 200


# Staff Management Routes
@main.route('/api/staff', methods=['POST'])
@jwt_required()
def add_staff():
    try:
        boss_id = int(get_jwt_identity())

        print("=== COMPLETE DEBUG INFO ===")
        print("Request method:", request.method)
        print("Content-Type:", request.content_type)
        print("Request headers:", dict(request.headers))

        if request.content_type and 'multipart/form-data' in request.content_type:
            data = dict(request.form)
            file = request.files.get('proof_of_id')
            print("FormData received:")
            for key, value in data.items():
                print(f"  {key}: '{value}' (type: {type(value)}, length: {len(str(value)) if value else 0})")
            print("File:", file.filename if file else "No file")
        else:
            data = request.get_json()
            print("JSON data received:")
            for key, value in data.items():
                print(f"  {key}: '{value}' (type: {type(value)}, length: {len(str(value)) if value else 0})")
            file = None

        print("Boss ID:", boss_id)
        print("========================")

        result, status_code = StaffService.add_staff_with_file(boss_id, data, file)
        return jsonify(result), status_code

    except Exception as e:
        print(f"Route exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500



@main.route('/api/staff', methods=['GET'])
@jwt_required()
def get_all_staff():
    """Get all staff members for the logged-in boss"""
    boss_id = int(get_jwt_identity())
    staff_list = StaffService.get_staff_by_boss(boss_id)
    return jsonify({'staff': staff_list}), 200


@main.route('/api/staff/<int:staff_id>', methods=['GET'])
@jwt_required()
def get_staff(staff_id):
    """Get specific staff member"""
    boss_id = int(get_jwt_identity())
    staff = StaffService.get_staff_by_id(staff_id, boss_id)

    if staff:
        return jsonify({'staff': staff}), 200
    return jsonify({'error': 'Staff not found'}), 404


@main.route('/api/staff/<int:staff_id>', methods=['PUT'])
@jwt_required()
def update_staff(staff_id):
    """Update staff member with JSON data only"""
    try:
        boss_id = int(get_jwt_identity())

        boss = Boss.query.get(boss_id)
        if not boss:
            return jsonify({'error': 'Boss not found'}), 404

        # Only handle JSON data for this route
        update_data = request.get_json()
        if not update_data:
            return jsonify({'error': 'No JSON data provided'}), 400

        result, status = StaffService.update_staff_json_only(staff_id, boss.id, update_data)
        return jsonify(result), status

    except Exception as e:
        print(f"Error in update_staff: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@main.route('/api/staff/<int:staff_id>/update-with-file', methods=['PUT'])
@jwt_required()
def update_staff_with_file(staff_id):
    """Update staff member with form data and optional file upload"""
    try:
        boss_id = int(get_jwt_identity())

        boss = Boss.query.get(boss_id)
        if not boss:
            return jsonify({'error': 'Boss not found'}), 404

        # Get form data (like in add_staff_with_file)
        update_data = request.form.to_dict()
        file = request.files.get('proof_of_id')

        if not update_data:
            return jsonify({'error': 'No form data provided'}), 400

        result, status = StaffService.update_staff_with_file(staff_id, boss.id, update_data, file)
        return jsonify(result), status

    except Exception as e:
        print(f"Error in update_staff_with_file: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@main.route('/api/staff/<int:staff_id>', methods=['DELETE'])
@jwt_required()
def delete_staff(staff_id):
    """Delete staff member"""
    boss_id = int(get_jwt_identity())
    result, status = StaffService.delete_staff(staff_id, boss_id)
    return jsonify(result), status


# File Upload Routes for ID Documents
@main.route('/api/staff/<int:staff_id>/upload-id', methods=['POST'])
@jwt_required()
def upload_staff_id(staff_id):
    """Upload proof of ID for existing staff member"""
    try:
        boss_id = int(get_jwt_identity())  # This is the boss ID, not email

        # Get boss by ID, not email
        boss = Boss.query.get(boss_id)
        if not boss:
            return jsonify({'error': 'Boss not found'}), 404

        if 'proof_of_id' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['proof_of_id']
        result, status = FileService.upload_proof_of_id(file, staff_id, boss.id)
        return jsonify(result), status

    except Exception as e:
        print(f"Error in upload_staff_id: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@main.route('/api/staff/<int:staff_id>/download-id', methods=['GET'])
@jwt_required()
def download_proof_of_id(staff_id):
    """Download proof of ID document"""
    boss_id = int(get_jwt_identity())

    # Verify staff belongs to this boss
    staff = StaffService.get_staff_by_id(staff_id, boss_id)
    if not staff or not staff.get('proof_of_id'):
        return jsonify({'error': 'File not found'}), 404

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], staff['proof_of_id'])
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)

    return jsonify({'error': 'File not found on server'}), 404


# Dashboard/Analytics Routes
@main.route('/api/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    """Get dashboard statistics"""
    boss_id = int(get_jwt_identity())
    staff_list = StaffService.get_staff_by_boss(boss_id)

    stats = {
        'total_staff': len(staff_list),
        'employment_status_breakdown': {},
        'immigration_status_breakdown': {},
        'gender_breakdown': {}
    }

    for staff in staff_list:
        # Employment status breakdown
        emp_status = staff['employment_status']
        stats['employment_status_breakdown'][emp_status] = stats['employment_status_breakdown'].get(emp_status, 0) + 1

        # Immigration status breakdown
        imm_status = staff['immigration_status']
        stats['immigration_status_breakdown'][imm_status] = stats['immigration_status_breakdown'].get(imm_status, 0) + 1

        # Gender breakdown
        gender = staff['sex']
        stats['gender_breakdown'][gender] = stats['gender_breakdown'].get(gender, 0) + 1

    return jsonify({
        'statistics': stats,
        'recent_staff': staff_list[-5:]  # Last 5 added staff
    }), 200


@main.route('/api/staff/search', methods=['GET'])
@jwt_required()
def search_staff():
    """Search staff by query and/or employment status"""
    try:
        boss_id = int(get_jwt_identity())
        query = request.args.get('q', '').strip()
        employment_status = request.args.get('employment_status', '')

        print(f"Search request - Boss ID: {boss_id}, Query: '{query}', Employment Status: '{employment_status}'")

        # Allow search with either query or employment_status or both
        staff_list = StaffService.search_staff(boss_id, query, employment_status)

        print(f"Search results: {len(staff_list)} staff found")

        return jsonify({'staff': staff_list}), 200

    except Exception as e:
        print(f"Search error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@main.route('/api/staff/download', methods=['GET'])
@jwt_required()
def download_staff_excel():
    """Download staff data as Excel file"""
    try:
        boss_id = int(get_jwt_identity())
        print(f"Download request for boss ID: {boss_id}")

        # Get all staff for this boss using the export method
        staff_list = StaffService.get_staff_by_boss_for_export(boss_id)
        print(f"Found {len(staff_list)} staff members for download")

        if not staff_list:
            return jsonify({'error': 'No staff data to download'}), 404

        # Create Excel file
        excel_file = FileService.create_staff_excel(staff_list)
        print("Excel file created successfully")

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'staff_list_{boss_id}.xlsx'
        )

    except Exception as e:
        print(f"Download error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# Error Handlers
@main.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@main.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
