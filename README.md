# IIC Event Management System

A professional event-based participant registration system built with **Flask** and **SQLite**. Perfect for college events, IIC activities, workshops, and seminars where admins create events and participants self-register using unique links.

## Features

🔐 **Admin Authentication**
- Secure admin login with session management
- Protected admin routes
- Clean logout functionality

📅 **Event Management**
- Create events with name, description, and date
- Auto-generate unique registration links per event
- View all events on admin dashboard
- Delete events and associated participants
- Track participant count per event

🔗 **Public Registration Links**
- Each event gets a unique, shareable registration URL
- Participants register themselves (no login required)
- Token-based link validation
- Professional registration forms
- Success confirmation page

👥 **Participant Management**
- View all participants per event
- Search participants by name or email
- Prevent duplicate email entries per event
- Admin-only participant access

🎨 **Modern UI/UX**
- Clean, professional interface
- Card-based event display
- Responsive design for all devices
- Flash messages for user feedback
- Copy-to-clipboard registration links

## System Architecture

### Roles
1. **Admin** (Authenticated)
   - Create and manage events
   - View participant lists
   - Access dashboard and analytics

2. **Participant** (Public)
   - Register via unique event links
   - No login required
   - Self-service registration

### Access Control
- ✅ Admin pages require authentication
- ✅ Public registration links are open
- ✅ Participants cannot access admin areas
- ✅ Session-based security

## Project Structure

```
project/
├── app.py                          # Flask application
├── events.db                       # SQLite database (auto-created)
├── requirements.txt                # Python dependencies
├── render.yaml                     # Render deployment config
├── templates/
│   ├── base.html                  # Base template
│   ├── login.html                 # Admin login
│   ├── dashboard.html             # Admin dashboard
│   ├── create_event.html          # Event creation
│   ├── public_register.html       # Public registration form
│   ├── participants.html          # Participant list (admin)
│   ├── success.html               # Registration success
│   └── error.html                 # Error pages
└── static/
    └── style.css                  # Professional styling
```

## Installation & Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Application
```bash
python app.py
```

### 3. Access the Application
- **Admin Panel**: `http://127.0.0.1:5000`
- **Login Credentials**:
  - Username: `admin`
  - Password: `admin123`

## Database Schema

### EVENTS Table
```sql
CREATE TABLE EVENTS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    date TEXT,
    registration_token TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### PARTICIPANTS Table
```sql
CREATE TABLE PARTICIPANTS (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    college TEXT NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id) REFERENCES EVENTS (id),
    UNIQUE(event_id, email)
);
```

## Routes

### Admin Routes (Authentication Required)
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Redirect to login/dashboard |
| `/login` | GET/POST | Admin login |
| `/logout` | GET | Admin logout |
| `/dashboard` | GET | Admin dashboard |
| `/events/create` | GET/POST | Create new event |
| `/events/<id>/delete` | POST | Delete event |
| `/events/<id>/participants` | GET | View participants |

### Public Routes (No Authentication)
| Route | Method | Description |
|-------|--------|-------------|
| `/register/<token>` | GET/POST | Public registration form |
| `/success` | GET | Registration success page |

## How It Works

### For Admins:
1. **Login** to admin panel
2. **Create Event** with details
3. **Copy Registration Link** from dashboard
4. **Share Link** with participants via email/WhatsApp/social media
5. **View Participants** as they register
6. **Manage Events** (view stats, delete events)

### For Participants:
1. **Click Registration Link** shared by admin
2. **Fill Registration Form** (name, email, college)
3. **Submit** registration
4. **View Success Page** with confirmation

## Security Features

✓ Token-based registration URLs  
✓ Session-based admin authentication  
✓ Protected admin routes  
✓ SQL injection prevention (parameterized queries)  
✓ Email uniqueness per event  
✓ Input validation and sanitization  

## Customization

### Change Admin Credentials
Edit `app.py`:
```python
ADMIN_USERNAME = 'your_username'
ADMIN_PASSWORD = 'your_password'
```

### Change Secret Key (Required for Production)
```python
app.secret_key = 'your-secure-secret-key-here'
```

## Technologies

- **Backend**: Flask 2.3.2
- **Database**: SQLite3
- **Frontend**: HTML5, CSS3, Jinja2
- **Authentication**: Flask Sessions
- **Security**: Token-based URLs
- **Production Server**: Gunicorn
- **Deployment**: Render (or any WSGI platform)

## 🚀 Deploy to Render (Cloud Hosting)

Deploy this application to get a **public HTTPS URL** for your event registration system.

### Quick Deploy (One-Click)

1. Push your code to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com/)
3. Click **New** → **Blueprint**
4. Connect your GitHub repository
5. Render will auto-detect `render.yaml` and deploy

### Manual Deploy

1. **Create Render Account**: Sign up at [render.com](https://render.com)

2. **New Web Service**:
   - Click **New** → **Web Service**
   - Connect your GitHub repo
   - Configure:
     - **Name**: `iic-event-manager`
     - **Runtime**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`

3. **Set Environment Variables** (in Render Dashboard):
   | Variable | Value | Notes |
   |----------|-------|-------|
   | `SECRET_KEY` | (auto-generate) | Click "Generate" button |
   | `ADMIN_USERNAME` | `your_username` | Your admin login |
   | `ADMIN_PASSWORD` | `your_password` | Secure password |

4. **Deploy**: Click "Create Web Service"

### After Deployment

Your app will be live at: `https://iic-event-manager.onrender.com`

**Test these URLs:**
- `/login` - Admin login page
- `/dashboard` - Event management (after login)
- `/register/<token>` - Public registration (get link from dashboard)

### Important Notes

⚠️ **SQLite Limitation**: Render's free tier uses ephemeral storage. The database resets on redeploy. For persistent data:
- Upgrade to paid tier with persistent disk
- Or migrate to PostgreSQL (recommended for production)

🔒 **Security**: Always set `SECRET_KEY` and `ADMIN_PASSWORD` via environment variables, never in code.

## Use Cases

- IIC (Institution's Innovation Council) events
- College workshops and seminars
- Hackathons and competitions
- Training programs
- Webinars and conferences
- Any institutional event management

## Features Highlights

🎯 **One-Click Copy** - Copy registration links instantly  
📊 **Real-time Stats** - Track participants as they register  
🔍 **Search Functionality** - Find participants quickly  
📱 **Mobile Responsive** - Works on all devices  
✉️ **Email Validation** - Prevent invalid entries  
🚫 **Duplicate Prevention** - One email per event  

---

**Built with ❤️ for modern event management.**
