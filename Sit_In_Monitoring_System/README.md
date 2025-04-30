# Sit In Monitoring System

## Overview
The Sit In Monitoring System is a web application designed to manage and monitor sit-in sessions for students. It provides functionalities for administrators to view and manage student records, reservations, feedback, and resources.

## Project Structure
```
Sit_In_Monitoring_System
├── static
│   ├── css
│   │   └── styles.css          # CSS styles for the project
│   └── js
│       └── calendar.js         # JavaScript for displaying a calendar
├── templates
│   ├── admin_base.html         # Base HTML template for the admin dashboard
│   ├── admin_schedule.html      # HTML template for the admin schedule page
│   ├── base.html               # Base HTML template for the application
│   ├── schedule.html           # HTML template for the schedule page
├── app.py                      # Main application file with Flask setup
└── README.md                   # Documentation for the project
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd Sit_In_Monitoring_System
   ```
3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Run the application:
   ```
   python app.py
   ```
2. Open your web browser and go to `http://127.0.0.1:5000` to access the application.

## Features
- Admin dashboard for managing sit-in sessions.
- View and manage student records.
- Handle reservations and feedback.
- Upload and manage resources.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.