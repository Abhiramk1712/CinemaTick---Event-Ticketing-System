# 🎟️ CinemaTick: Smart Event Ticketing System

## 📌 Overview
CinemaTick is a full-stack event ticketing platform enabling users to register, browse events, select seats in real-time, and receive email confirmations with QR codes. Admins can manage events and bookings via an intuitive dashboard. The system leverages a **graph-based Neo4j database**, **FastAPI backend**, and **Streamlit frontend** to ensure seamless, scalable interactions.

## 🏗️ Architecture
| Layer        | Technology               |
|--------------|---------------------------|
| Frontend     | Streamlit (Python)        |
| Backend      | FastAPI (Python REST API) |
| Database     | Neo4j (Graph DB)          |
| Email System | SendGrid API, QR Code     |

**Supporting Libraries:** `requests`, `qrcode`, `Pillow`, `uvicorn`, `streamlit`

## 🔧 System Design

### Frontend (Streamlit)
- User Login/Register
- Browse and filter events by category
- Real-time seat selection (VIP & Standard)
- View and manage bookings
- Admin features: add/update events, manage bookings

### Backend (FastAPI)
- `/register`, `/login` — Authentication
- `/events`, `/add-event`, `/update-event` — Event management
- `/book`, `/cancel` — Booking endpoints
- `/booked-seats/{event_name}` — Seat management
- `/users` — Admin: view user data

### Database (Neo4j)
- Nodes: `User`, `Event`, `Venue`, `Category`
- Relationships:
  - `(:User)-[:BOOKED]->(:Event)`
  - `(:Event)-[:HELD_AT]->(:Venue)`
  - `(:Event)-[:BELONGS_TO]->(:Category)`

## ✨ Key Features
- ✅ Real-time graphical seat booking
- ✅ QR code ticket emailed after booking
- ✅ Admin control for event and booking management
- ✅ Scalable graph database model for fast queries

## 🚀 Setup & Installation

### 1️⃣ Backend
```bash
pip install -r requirements.txt
uvicorn main_cleaned:app --reload
```

### 2️⃣ Frontend
```bash
streamlit run main.py
```

### 3️⃣ Database
- Install [Neo4j Desktop](https://neo4j.com/download/) or use [Neo4j Aura](https://neo4j.com/cloud/aura/)
- Connect via `bolt://localhost:7687` in your FastAPI backend.

## 📩 Email System
- Uses **SendGrid API** to send:
  - Booking confirmation with QR code
  - Cancellation notice with details

## 🔍 Admin Panel Highlights
- View all users and their bookings
- Modify or cancel bookings
- Update event information
- Prevent event creation without VIP/Standard pricing

## 🌱 Future Enhancements
- 💳 Payment gateway integration (Stripe/PayPal)
- 🖨️ Printable ticket generation
- ⭐ Event reviews & ratings
- 🌍 Multilingual support
- 🔐 Social login integration

## 📚 Folder Structure
```
CinemaTick/
├── backend/
│   ├── main_cleaned.py
│   ├── email_utils.py
│   ├── helpers.py
│   ├── api.py
│   └── ...
├── frontend/
│   ├── main.py
│   └── ...
├── requirements.txt
├── README.md
```

## 🧠 Conclusion
CinemaTick demonstrates how combining Neo4j's graph power, FastAPI's performance, and Streamlit’s interactivity results in a highly efficient, real-time event ticketing solution. With smart design and modular structure, it enables seamless admin and user interactions and sets the stage for future extensibility.
