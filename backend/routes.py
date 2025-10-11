from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
import os
from datetime import datetime, timedelta

from .services import BossService, StaffService, FileService, ValidationService
from .models import Boss
from flask_jwt_extended import verify_jwt_in_request
import requests
from flask import Response
from flask_jwt_extended import decode_token

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
# In your routes.py - the upload route should keep JWT authentication
def upload_staff_id(staff_id):
    """Upload proof of ID for existing staff member"""
    try:
        boss_id = int(get_jwt_identity())  # ✅ Keep this authentication

        # Get boss by ID, not email
        boss = Boss.query.get(boss_id)
        if not boss:
            return jsonify({'error': 'Boss not found'}), 404

        if 'proof_of_id' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['proof_of_id']
        # This will now use Cloudinary instead of local storage
        result, status = FileService.upload_proof_of_id(file, staff_id, boss.id)
        return jsonify(result), status

    except Exception as e:
        print(f"Error in upload_staff_id: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@main.route('/api/staff/<int:staff_id>/download-id', methods=['GET'])
def download_proof_of_id(staff_id):
    """Download proof of ID file - handles JSON responses from Cloudinary"""
    try:
        # Try to get token from query parameter first
        token = request.args.get('token')

        if token:
            try:
                decoded_token = decode_token(token)
                boss_id = int(decoded_token['sub'])
            except Exception as e:
                print(f"Token decode error: {e}")
                return jsonify({'error': 'Invalid token'}), 401
        else:
            try:
                verify_jwt_in_request()
                boss_id = int(get_jwt_identity())
            except:
                return jsonify({'error': 'Authentication required'}), 401

        staff = StaffService.get_staff_by_id(staff_id, boss_id)
        if not staff or not staff.get('proof_of_id'):
            return jsonify({'error': 'File not found'}), 404

        file_url = staff['proof_of_id']
        print(f"Original URL from database: {file_url}")

        if file_url.startswith('http'):
            try:
                print(f"Fetching from: {file_url}")
                response = requests.get(file_url, timeout=30)
                response.raise_for_status()

                content_type = response.headers.get('Content-Type', '').lower()
                print(f"Response content type: {content_type}")

                # Check if response is JSON
                if 'application/json' in content_type:
                    try:
                        json_data = response.json()
                        print(f"JSON response received: {json_data}")

                        # Extract actual image URL from JSON
                        actual_image_url = None

                        # Common JSON structures from Cloudinary:
                        if 'secure_url' in json_data:
                            actual_image_url = json_data['secure_url']
                        elif 'url' in json_data:
                            actual_image_url = json_data['url']
                        elif 'public_id' in json_data and 'version' in json_data:
                            # Reconstruct Cloudinary URL
                            cloud_name = 'dwghubkst'  # Replace with your actual cloud name
                            actual_image_url = f"https://res.cloudinary.com/{cloud_name}/image/upload/v{json_data['version']}/{json_data['public_id']}.{json_data.get('format', 'jpg')}"

                        if actual_image_url:
                            print(f"Extracted image URL: {actual_image_url}")
                            # Now fetch the actual image
                            image_response = requests.get(actual_image_url, timeout=30)
                            image_response.raise_for_status()

                            # Get file extension
                            file_ext = actual_image_url.split('.')[-1].split('?')[0]
                            filename = f"{staff.get('firstname', 'staff')}_{staff.get('lastname', staff_id)}_proof.{file_ext}"

                            return Response(
                                image_response.content,
                                headers={
                                    'Content-Disposition': f'attachment; filename="{filename}"',
                                    'Content-Type': image_response.headers.get('Content-Type', 'image/jpeg')
                                }
                            )
                        else:
                            return jsonify({'error': 'Could not extract image URL from JSON response'}), 400

                    except Exception as json_error:
                        print(f"Error parsing JSON: {json_error}")
                        return jsonify({'error': 'Invalid JSON response from image service'}), 400

                else:
                    # Response is already an image, serve it directly
                    if '.' in file_url.split('/')[-1]:
                        file_ext = file_url.split('.')[-1].split('?')[0]
                    else:
                        # Guess extension from content type
                        if 'image/jpeg' in content_type:
                            file_ext = 'jpg'
                        elif 'image/png' in content_type:
                            file_ext = 'png'
                        elif 'image/gif' in content_type:
                            file_ext = 'gif'
                        else:
                            file_ext = 'file'

                    filename = f"{staff.get('firstname', 'staff')}_{staff.get('lastname', staff_id)}_proof.{file_ext}"

                    return Response(
                        response.content,
                        headers={
                            'Content-Disposition': f'attachment; filename="{filename}"',
                            'Content-Type': response.headers.get('Content-Type', 'application/octet-stream')
                        }
                    )

            except requests.RequestException as e:
                print(f"Failed to fetch file: {e}")
                return jsonify({'error': f'Failed to fetch file: {str(e)}'}), 500

        return jsonify({'error': 'Invalid file URL'}), 404

    except Exception as e:
        print(f"Download error: {e}")
        return jsonify({'error': 'Failed to download file'}), 500


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
    try:
        boss_id = get_jwt_identity()
        print(f"Download request for boss ID: {boss_id}")

        # Get staff data using StaffService
        staff_list = StaffService.get_staff_by_boss(boss_id)

        if not staff_list:
            return jsonify({'error': 'No staff found'}), 404

        # Create Excel file using FileService
        excel_buffer = FileService.create_staff_excel(staff_list)

        from flask import send_file
        return send_file(
            excel_buffer,
            as_attachment=True,
            download_name=f'staff_list_{boss_id}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"Download error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to generate Excel file'}), 500


# Error Handlers
@main.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@main.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500
