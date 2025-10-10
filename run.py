from backend import create_app, db
import os
from flask import send_file, send_from_directory

# Create the Flask application instance
app = create_app()

# Configuration
app.config['DEBUG'] = False
app.config['UPLOAD_FOLDER'] = "/tmp/uploads"              #os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.static_folder = "static"
app.static_url_path = ""

# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/<path:path>')
def serve_static_files(path):
    # Skip API routes
    if path.startswith('api/'):
        return None

    # Serve static files
    if os.path.exists(os.path.join('static', path)):
        return send_from_directory('static', path)

    # Fallback for React routing
    return send_file('static/index.html')

# Initialize database tables
with app.app_context():
    try:
        # Drop all tables and recreate them with proper relationships
        #db.drop_all()
        db.create_all()
        print("Database tables recreated successfully with proper relationships!")
    except Exception as e:
        print(f"Error creating database: {e}")

# Run the application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
