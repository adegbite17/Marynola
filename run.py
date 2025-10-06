from backend import create_app, db
import os
# Create the Flask application instance
app = create_app()

# Configuration
app.config['DEBUG'] = False
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


# Create upload directory if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

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
