"""
Event-Based Participant Registration System
A professional event management platform where admins create events with unique
registration links, and participants register themselves publicly.
Features: Admin auth, token-based public registration, event management.

Deployment: Compatible with Render, Heroku, and other WSGI-based platforms.
Start with: gunicorn app:app
"""

import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime
import os
import re
import secrets

app = Flask(__name__)

# ============================================
# CONFIGURATION (Production-Ready)
# ============================================

# Secret key: Use environment variable in production for security
# On Render: Set SECRET_KEY in Environment Variables
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database path: Use environment variable or default to local file
DATABASE = os.environ.get('DATABASE_PATH', 'events.db')

# Admin credentials: Use environment variables in production
# On Render: Set ADMIN_USERNAME and ADMIN_PASSWORD in Environment Variables
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

# Production logging
print(f"🚀 Starting Event Registration System...")
print(f"📁 Database: {DATABASE}")


# ============================================
# DATABASE HELPERS
# ============================================

def get_db_connection():
    """Establish a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with EVENTS and PARTICIPANTS tables."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create EVENTS table with registration token
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS EVENTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            date TEXT,
            registration_token TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create PARTICIPANTS table with unique constraint on (event_id, email)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS PARTICIPANTS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            college TEXT NOT NULL,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (event_id) REFERENCES EVENTS (id) ON DELETE CASCADE,
            UNIQUE(event_id, email)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Run migration to handle existing databases without registration_token column
    migrate_add_registration_token()
    
    print("✓ Database initialized successfully.")


def migrate_add_registration_token():
    """
    Database Migration: Add registration_token column if it doesn't exist.
    
    WHY THIS IS NEEDED:
    - SQLite's CREATE TABLE IF NOT EXISTS doesn't update existing tables
    - If the database was created before the token feature was added,
      the EVENTS table won't have the registration_token column
    - This migration adds the column safely to existing databases
    
    WHEN IT RUNS:
    - Every time the app starts
    - Only modifies the database if the column is missing
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if registration_token column exists in EVENTS table
        # PRAGMA table_info returns info about each column in the table
        cursor.execute("PRAGMA table_info(EVENTS)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'registration_token' not in columns:
            # Column doesn't exist - add it
            # NOTE: SQLite doesn't support adding UNIQUE columns to existing tables
            # with data, so we add it without the UNIQUE constraint
            print("⚙️ Migrating database: Adding registration_token column...")
            cursor.execute('ALTER TABLE EVENTS ADD COLUMN registration_token TEXT')
            conn.commit()
            print("✅ Column added successfully.")
        
        # Generate tokens for any events that don't have one (NULL or empty)
        # This handles old events created before the token feature
        cursor.execute('SELECT id FROM EVENTS WHERE registration_token IS NULL OR registration_token = ""')
        events_without_tokens = cursor.fetchall()
        
        for event in events_without_tokens:
            new_token = generate_registration_token()
            cursor.execute('UPDATE EVENTS SET registration_token = ? WHERE id = ?', (new_token, event['id']))
            print(f"⚙️ Generated token for event ID {event['id']}")
        
        if events_without_tokens:
            conn.commit()
            print(f"✅ Generated tokens for {len(events_without_tokens)} existing event(s).")
        
    except sqlite3.Error as e:
        print(f"⚠️ Migration error (non-fatal): {e}")
        # Don't crash - the app can still work for new events
    finally:
        if conn:
            conn.close()


def generate_registration_token():
    """Generate a secure unique registration token for events."""
    return secrets.token_urlsafe(16)


def get_event_token_safely(event):
    """
    Safely retrieve registration_token from an event row.
    This defensive function prevents IndexError when:
    - The column doesn't exist in an old database
    - The token value is NULL or empty
    
    Args:
        event: SQLite Row object or dict representing an event
    
    Returns:
        str: The registration token, or None if not available
    """
    try:
        # Try to access the token - this may raise IndexError if column doesn't exist
        token = event['registration_token']
        # Return None if token is empty string or None
        return token if token else None
    except (IndexError, KeyError):
        # Column doesn't exist or key not found - return None gracefully
        return None


# ============================================
# AUTHENTICATION HELPERS
# ============================================

def login_required(f):
    """Decorator to protect routes that require admin login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def is_valid_email(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def participant_exists_in_event(email, event_id):
    """Check if participant email already exists for a specific event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT id FROM PARTICIPANTS WHERE email = ? AND event_id = ?',
        (email, event_id)
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


def get_event_by_id(event_id):
    """Fetch a single event by its ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM EVENTS WHERE id = ?', (event_id,))
    event = cursor.fetchone()
    conn.close()
    return event


def get_event_by_token(token):
    """Fetch an event by its registration token."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM EVENTS WHERE registration_token = ?', (token,))
    event = cursor.fetchone()
    conn.close()
    return event


def get_all_events():
    """Fetch all events ordered by creation date."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM EVENTS ORDER BY created_at DESC')
    events = cursor.fetchall()
    conn.close()
    return events


def get_participant_count(event_id):
    """Get the number of participants for an event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM PARTICIPANTS WHERE event_id = ?', (event_id,))
    result = cursor.fetchone()
    conn.close()
    return result['count'] if result else 0


# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/')
def index():
    """Redirect to dashboard if logged in, otherwise to login."""
    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle admin login."""
    # Redirect if already logged in
    if 'admin_logged_in' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Welcome back, Admin!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Handle admin logout."""
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


# ============================================
# DASHBOARD ROUTES (ADMIN ONLY)
# ============================================

@app.route('/dashboard')
@login_required
def dashboard():
    """Display admin dashboard with all events and registration links."""
    events = get_all_events()
    
    # Add participant count and registration URL to each event
    events_with_details = []
    for event in events:
        event_dict = dict(event)
        event_dict['participant_count'] = get_participant_count(event['id'])
        
        # Defensive check: Safely access registration_token
        # This prevents IndexError if the column is missing or NULL in old databases
        token = get_event_token_safely(event)
        
        if token:
            event_dict['registration_url'] = url_for('public_register', token=token, _external=True)
            event_dict['has_token'] = True
        else:
            # Fallback for events without tokens (shouldn't happen after migration)
            event_dict['registration_url'] = None
            event_dict['has_token'] = False
        
        events_with_details.append(event_dict)
    
    return render_template('dashboard.html', events=events_with_details)


# ============================================
# EVENT MANAGEMENT ROUTES (ADMIN ONLY)
# ============================================

@app.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    """Handle event creation with automatic token generation."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        date = request.form.get('date', '').strip()
        
        # Validate inputs
        if not name or len(name) < 3:
            flash('Event name must be at least 3 characters.', 'error')
            return redirect(url_for('create_event'))
        
        if not date:
            flash('Please select an event date.', 'error')
            return redirect(url_for('create_event'))
        
        # Generate unique registration token
        registration_token = generate_registration_token()
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Try inserting with registration_token first (normal case)
            try:
                cursor.execute('''
                    INSERT INTO EVENTS (name, description, date, registration_token)
                    VALUES (?, ?, ?, ?)
                ''', (name, description, date, registration_token))
            except sqlite3.OperationalError as col_err:
                # Fallback: If registration_token column doesn't exist,
                # insert without it (migration will add token later)
                if 'registration_token' in str(col_err):
                    print(f"⚠️ Fallback: Inserting event without token (migration pending)")
                    cursor.execute('''
                        INSERT INTO EVENTS (name, description, date)
                        VALUES (?, ?, ?)
                    ''', (name, description, date))
                else:
                    raise  # Re-raise if it's a different error
            
            conn.commit()
            conn.close()
            
            flash(f'Event "{name}" created successfully! Registration link generated.', 'success')
            return redirect(url_for('dashboard'))
        
        except sqlite3.Error as e:
            flash(f'Database error: {str(e)}', 'error')
            return redirect(url_for('create_event'))
    
    return render_template('create_event.html')


@app.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    """Delete an event and all its participants."""
    event = get_event_by_id(event_id)
    
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Delete participants first
        cursor.execute('DELETE FROM PARTICIPANTS WHERE event_id = ?', (event_id,))
        # Delete event
        cursor.execute('DELETE FROM EVENTS WHERE id = ?', (event_id,))
        
        conn.commit()
        conn.close()
        
        flash(f'Event "{event["name"]}" deleted successfully.', 'success')
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))


# ============================================
# PUBLIC REGISTRATION ROUTES
# ============================================

@app.route('/register/<token>', methods=['GET', 'POST'])
def public_register(token):
    """
    Public registration page accessible via unique event token.
    No login required - open to all participants.
    """
    # Validate token and fetch event
    event = get_event_by_token(token)
    
    if not event:
        flash('Invalid or expired registration link.', 'error')
        return render_template('error.html', 
                             message='Invalid Registration Link',
                             description='The registration link you used is invalid or has expired.')
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        college = request.form.get('college', '').strip()
        
        # Validate inputs
        if not name or len(name) < 2:
            flash('Name must be at least 2 characters.', 'error')
            return redirect(url_for('public_register', token=token))
        
        if not email or not is_valid_email(email):
            flash('Please enter a valid email address.', 'error')
            return redirect(url_for('public_register', token=token))
        
        if participant_exists_in_event(email, event['id']):
            flash('This email is already registered for this event.', 'error')
            return redirect(url_for('public_register', token=token))
        
        if not college or len(college) < 2:
            flash('College/Organization must be at least 2 characters.', 'error')
            return redirect(url_for('public_register', token=token))
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO PARTICIPANTS (event_id, name, email, college)
                VALUES (?, ?, ?, ?)
            ''', (event['id'], name, email, college))
            conn.commit()
            conn.close()
            
            # Redirect to success page
            return redirect(url_for('registration_success', 
                                  event_name=event['name'], 
                                  participant_name=name))
        
        except sqlite3.IntegrityError:
            flash('This email is already registered for this event.', 'error')
            return redirect(url_for('public_register', token=token))
        except sqlite3.Error as e:
            flash(f'Registration failed. Please try again.', 'error')
            return redirect(url_for('public_register', token=token))
    
    return render_template('public_register.html', event=event, token=token)


@app.route('/success')
def registration_success():
    """Display registration success confirmation page."""
    event_name = request.args.get('event_name', 'the event')
    participant_name = request.args.get('participant_name', 'Participant')
    
    return render_template('success.html', 
                         event_name=event_name, 
                         participant_name=participant_name)


# ============================================
# PARTICIPANT MANAGEMENT ROUTES (ADMIN ONLY)
# ============================================

@app.route('/events/<int:event_id>/participants')
@login_required
def view_participants(event_id):
    """View all participants for a specific event (Admin only)."""
    event = get_event_by_id(event_id)
    
    if not event:
        flash('Event not found.', 'error')
        return redirect(url_for('dashboard'))
    
    search_query = request.args.get('search', '').strip().lower()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if search_query:
            cursor.execute('''
                SELECT * FROM PARTICIPANTS 
                WHERE event_id = ? AND (LOWER(name) LIKE ? OR LOWER(email) LIKE ?)
                ORDER BY registered_at DESC
            ''', (event_id, f'%{search_query}%', f'%{search_query}%'))
        else:
            cursor.execute('''
                SELECT * FROM PARTICIPANTS 
                WHERE event_id = ?
                ORDER BY registered_at DESC
            ''', (event_id,))
        
        participants = cursor.fetchall()
        conn.close()
        
        # Generate registration URL
        registration_url = url_for('public_register', token=event['registration_token'], _external=True)
        
        return render_template('participants.html',
                             event=event,
                             participants=participants,
                             search_query=search_query,
                             participant_count=len(participants),
                             registration_url=registration_url)
    
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
        return render_template('participants.html',
                             event=event,
                             participants=[],
                             search_query=search_query,
                             participant_count=0,
                             registration_url='')


@app.route('/events/<int:event_id>/participants/<int:participant_id>/delete', methods=['POST'])
@login_required
def delete_participant(event_id, participant_id):
    """Delete a participant from an event (Admin only)."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM PARTICIPANTS WHERE id = ? AND event_id = ?', 
                      (participant_id, event_id))
        conn.commit()
        conn.close()
        
        flash('Participant removed successfully.', 'success')
    except sqlite3.Error as e:
        flash(f'Database error: {str(e)}', 'error')
    
    return redirect(url_for('view_participants', event_id=event_id))


# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def page_not_found(error):
    """Handle 404 errors."""
    return render_template('error.html',
                         message='Page Not Found',
                         description='The page you are looking for does not exist.'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return render_template('error.html',
                         message='Internal Server Error',
                         description='An unexpected error occurred. Please try again later.'), 500


# ============================================
# APPLICATION ENTRY POINT
# ============================================

# Initialize database on module load (required for Gunicorn)
# This ensures tables exist when the app starts on Render
init_db()

if __name__ == '__main__':
    # Local development server only
    # In production (Render), Gunicorn handles the server
    # Command: gunicorn app:app
    
    # Get port from environment (Render sets PORT automatically)
    port = int(os.environ.get('PORT', 5000))
    
    # Debug mode only in development
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🌐 Running on http://127.0.0.1:{port}")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
