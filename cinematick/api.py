import requests

from config import BASE_URL

def login(email, password):
    res = requests.post(f"{BASE_URL}/login", data={'email': email, 'password': password})
    return res.json() if res.status_code == 200 else None

def register(name, email, phone, password, is_admin=False):
    res = requests.post(f"{BASE_URL}/register", data={
        'name': name,
        'email': email,
        'phone': phone,
        'password': password,
        'is_admin': str(is_admin)
    })
    return res.status_code == 200, res.text

def get_events(category=None):
    url = f"{BASE_URL}/events"
    if category and category != "All":
        url += f"?category={category}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else []

def get_categories():
    res = requests.get(f"{BASE_URL}/categories")
    return res.json() if res.status_code == 200 else []

def get_booked_seats(event_name):
    res = requests.get(f"{BASE_URL}/booked-seats/{event_name}")
    return res.json() if res.status_code == 200 else []

def book_event(user_email, event_name, seats):
    res = requests.post(f"{BASE_URL}/book", json={"user_email": user_email, "event_name": event_name, "seats": seats})
    return res.json() if res.status_code == 200 else {"error": res.text}

def get_user_bookings(email):
    res = requests.get(f"{BASE_URL}/bookings/{email}")
    return res.json() if res.status_code == 200 else []

def cancel_booking(booking_id):
    res = requests.post(f"{BASE_URL}/cancel", json={"booking_id": booking_id})
    return res.json() if res.status_code == 200 else {"error": res.text}
