# GearGuard: The Ultimate Maintenance Tracker 🛠️

A modern, robust, and intelligent Maintenance Management System designed to bridge the gap between industrial assets and technical teams. Built for the **codingGujarat** hackathon.

---

## 👥 Meet the Team: **CodingGujarat**
- **Aman Nayak** (Team Leader)
- **Vinit Patel**
- **Hiren Dadhaniya**  
- **Radhika Zalodiya**

---

## 🎯 Project Objective
The goal of **GearGuard** is to provide a seamless technical ecosystem where companies can track assets (machines, vehicles, computers), manage specialized maintenance teams, and handle the entire lifecycle of repair requests through an intuitive "Odoo-like" interface.

### Core Philosophy
Connect **Equipment** (what is broken), **Teams** (who fix it), and **Requests** (the work to be done) into one unified, smart workflow.

---

## 🚀 Key Functional Areas

### A. Equipment Management
The central database for all organizational assets.
- **Robust Tracking**: Group and search equipment by Department (e.g., CNC Machine in Production) or by Employee (e.g., Laptop owned by Person).
- **Default Responsibility**: Every asset is pre-assigned to a specific Maintenance Team and a default technician.
- **Asset Metadata**: Tracks Serial Numbers, Purchase Dates, Locations, and Warranty Information.

### B. Maintenance Teams
Specialized groups dedicated to specific asset categories.
- **Team Specialization**: Define teams like Mechanics, Electricians, or IT Support.
- **Member Linking**: Technicians are linked to teams, ensuring that requests are routed to the right experts.

### C. Transactional Maintenance Requests
The heartbeat of the module, managing real-time repair jobs.
- **Request Types**: 
  - **Corrective**: Breakdown repairs for unplanned failures.
  - **Preventive**: Scheduled routine checkups.
- **Smart Logic**: Automatic calculation of "Resolution Success Rate" and tracking of "Overdue Jobs."

---

## 🔄 The Functional Workflow

### Flow 1: The Breakdown (Corrective)
1. **Report**: Any user generates a request.
2. **Auto-Fill**: Selecting an asset automatically pulls its category and maintenance team.
3. **Stages**: The request moves through **New** ➔ **In Progress** ➔ **Repaired**.
4. **Execution**: Technicians record the **Duration** (Hours Spent) upon completion.

### Flow 2: The Routine Checkup (Preventive)
1. **Scheduling**: Managers create Preventive requests with a specific **Scheduled Date**.
2. **Calendar Visibility**: These jobs appear on the **Calendar View**, allowing technicians to plan their day.

---

## 🖥️ User Interface & Views

| View | Description | Key Features |
| :--- | :--- | :--- |
| **Operations Dashboard** | High-level KPI overview. | Dynamic Stats, Requests per Team Chart, Global Search. |
| **Maintenance Board** | Kanban-style task management. | **Drag & Drop** (SortableJS), Technician Avatars, Status Indicators. |
| **Calendar View** | Interactive scheduling. | FullCalendar integration, Click-to-Schedule, Preventive job view. |
| **Asset Inventory** | Comprehensive list of equipment. | Category Filtering, Search by Serial/Name, Smart Buttons. |
| **Notification Center** | Real-time alerts for technicians. | Unread Badge, Auto-updates on Assignment, Dropdown UI. |

---

## ✨ "Smart" Features
- **Smart Buttons**: On the Equipment Detail page, a "Maintenance" button displays the count of open requests for that specific machine and links directly to them.
- **Scrap Logic**: If an asset is deemed unrepairable and moved to "Scrap," the system automatically marks the equipment as **Scrapped** in the inventory.
- **Glassmorphic Design**: A premium, dark-themed UI built with Tailwind CSS for a professional industrial feel.

---

## 🛠️ Technical Stack
- **Backend**: Python, Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Tailwind CSS, Jinja2, Font Awesome
- **Interactive Components**: SortableJS (Kanban), Chart.js (Analytics), FullCalendar (Scheduling)
- **Auth**: Flask-Login with secure password hashing

---

## 📦 Installation & Setup
1. **Install Dependencies**: `pip install flask flask-sqlalchemy flask-login werkzeug`
2. **Run Application**: `python app.py`
3. **Access**: Open `http://127.0.0.1:5000` in your browser.
4. **Login**: Use `admin` / `password` (default) or create a new account via Signup.

---
*Developed with ❤️ by Team **codingGujarat** for the 2025 Hackathon.*
