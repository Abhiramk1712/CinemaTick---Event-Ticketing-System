import streamlit as st
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="CinemaTick 🎟️", layout="wide")

# Dark Theme Styling
st.markdown("""
<style>
.stApp { background-color: #1a1a1a; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
.header {
    background: linear-gradient(to right, #8b0000, #330000);
    color: white; padding: 2rem; border-radius: 0 0 12px 12px;
    margin-bottom: 2rem; text-align: center;
}
.stButton>button {
    border-radius: 8px; padding: 0.5rem 1rem;
    background-color: #b00020; color: white;
    border: none; transition: all 0.3s ease;
}
.stButton>button:hover {
    background-color: #7f0015; transform: scale(1.02);
}
.st-expander, .st-expanderHeader, .stSidebar {
    background-color: #2a2a2a !important; color: #e0e0e0 !important;
    border: 1px solid #444 !important;
}
input, textarea {
    background-color: #333333 !important;
    color: #ffffff !important;
    border: 1px solid #b00020 !important;
}
h1, h2, h3, h4, h5, h6, .stMarkdown { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# Session state
if 'user' not in st.session_state:
    st.session_state.user = None
    st.session_state.logged_in = False
    st.session_state.selected_category = "All"
    st.session_state.view = None

# API functions

def login(email, password):
    res = requests.post(f"{BASE_URL}/login", data={'email': email, 'password': password})
    if res.status_code == 403:
        st.warning("Email not confirmed. Please check your inbox.")
        return None
    return res.json() if res.status_code == 200 else None

def register(name, email, phone, password, is_admin=False):
    res = requests.post(f"{BASE_URL}/register", data={
        'name': name, 'email': email, 'phone': phone,
        'password': password, 'is_admin': str(is_admin)
    })
    return res.status_code == 200, res.text

def get_events(category=None):
    url = f"{BASE_URL}/events"
    if category and category.lower() != "all":
        url += f"?category={category.lower()}"  # lowercase for case-insensitive matching
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


def get_event_by_name(event_name):
    res = requests.get(f"{BASE_URL}/event/{event_name}")
    return res.json() if res.status_code == 200 else None


def cancel_booking(booking_id):
    res = requests.post(f"{BASE_URL}/cancel", json={"booking_id": booking_id})
    return res.json() if res.status_code == 200 else {"error": res.text}

def get_all_users():
    res = requests.get(f"{BASE_URL}/users")
    return res.json() if res.status_code == 200 else []

# Views
def homepage():
    st.markdown("""
    <div class="header">
        <h1>🎟️ Welcome to CinemaTick</h1>
        <p>Your one-stop destination for event bookings</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.logged_in:
        st.subheader("🎯 Browse Categories")

        categories = ["All"] + sorted(get_categories(), key=lambda x: x.lower())
        categories = ["All"] + [cat.title() for cat in categories if cat.lower() != "all"]

        selected = st.selectbox("Select Category", categories, key="category_dropdown")
        st.session_state.selected_category = selected

        if st.button("Browse Events", key="browse_events_btn"):
            st.session_state.view = "events"
            st.rerun()


def show_login():
    st.subheader("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login(email, password)
        if user:
            st.success(f"Welcome {user['name']}")
            st.session_state.user = user
            st.session_state.logged_in = True
            st.rerun()
        else:
            if not st.session_state.get("logged_in"):
                st.error("Invalid credentials or email not confirmed")

def show_register():
    st.subheader("Register")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    password = st.text_input("Password", type="password")
    is_admin = st.checkbox("Register as Admin")
    if st.button("Register"):
        success, msg = register(name, email, phone, password, is_admin)
        if success:
            st.success("Registration successful. Please check your email to confirm.")
        else:
            st.error(msg)

def show_events():
    selected_cat = st.session_state.get("selected_category", "All")
    st.header(f"🎭 Events - Category: {selected_cat}")

    # Normalize category for backend query
    query_category = None if selected_cat == "All" else selected_cat.strip().lower()
    events = get_events(query_category)

    if not events:
        st.warning("No events found.")
        return

    for event in events:
        # Safely extract and normalize event category
        event_category = (event.get("category") or "").strip().lower()

        # Skip if event doesn't belong to the selected category (extra safeguard)
        if query_category and event_category != query_category:
            continue

        with st.expander(event["name"]):
            vip_price = event.get("vip_price", 0.0) or 0.0
            standard_price = event.get("standard_price", 0.0) or 0.0

            st.write(f"📍 Venue: {event['venue']}")
            st.write(f"📅 Date: {event['date']} ⏰ {event['time']}")
            st.write(f"💰 VIP: ${vip_price:.2f} | Standard: ${standard_price:.2f}")
            st.write(f"🪑 Total Seats: {event['seats']}")
            display_seat_selector(event["name"])



def display_seat_selector(event_name):
    st.subheader("🎯 Select Your Seats")

    vip_rows = ["A", "B"]
    standard_rows = ["C", "D", "E", "F"]
    all_rows = vip_rows + standard_rows
    cols = list(range(1, 11))

    seat_key = f"selected_seats_{event_name}"
    if seat_key not in st.session_state:
        st.session_state[seat_key] = []

    booked = get_booked_seats(event_name)
    selected = st.session_state[seat_key]

    # ✅ Fetch event pricing
    event = get_event_by_name(event_name)
    vip_price = event.get("vip_price")
    standard_price = event.get("standard_price")

    if vip_price is None or standard_price is None:
        st.error("⚠️ This event has no pricing info. Please contact the admin.")
        return

    # 👇 Seat grid with highlight
    for r in all_rows:
        label = f"VIP Row {r}" if r in vip_rows else f"Standard Row {r}"
        st.markdown(f"**{label}**")
        cols_row = st.columns(len(cols))
        for i, c in enumerate(cols):
            seat_id = f"{r}{c}"
            is_selected = seat_id in selected
            is_booked = seat_id in booked

            btn_label = f"✅ {seat_id}" if is_selected else f"🔲 {seat_id}"

            if cols_row[i].button(btn_label, key=f"{event_name}_{seat_id}", disabled=is_booked):
                if is_selected:
                    selected.remove(seat_id)
                else:
                    selected.append(seat_id)

    # 💰 Pricing breakdown
    if selected:
        vip_count = sum(1 for s in selected if s[0] in vip_rows)
        standard_count = len(selected) - vip_count
        total_price = vip_count * vip_price + standard_count * standard_price

        st.success(f"Selected Seats: {', '.join(selected)}")
        st.info(f"💰 VIP ({vip_count}) x ${vip_price:.2f} = ${vip_count * vip_price:.2f}  \n"
                f"🪑 Standard ({standard_count}) x ${standard_price:.2f} = ${standard_count * standard_price:.2f}  \n"
                f"**Total: ${total_price:.2f}**")

        if st.button("Confirm Booking", key=f"confirm_{event_name}"):
            result = book_event(st.session_state.user["email"], event_name, selected)
            if "booking_id" in result:
                st.balloons()
                st.success(f"Booking Confirmed! ID: {result['booking_id']}")
                st.session_state[seat_key] = []
            else:
                st.error(result.get("error", "Failed to book."))


def show_bookings():
    st.header("📖 My Bookings")

    bookings = get_user_bookings(st.session_state.user["email"])
    if not bookings:
        st.info("You haven't booked any events yet.")
        return

    for booking in bookings:
        # Handle seat_info if it's still a string (backend should return it as a list, but this adds safety)
        seat_info_raw = booking.get("seat_info", [])
        try:
            seat_info = json.loads(seat_info_raw) if isinstance(seat_info_raw, str) else seat_info_raw
        except:
            seat_info = []

        seats_with_types = [
            f"{s['seat']} ({'🟨 VIP' if s['type'] == 'VIP' else '🟦 Standard'})"
            for s in seat_info
        ]

        vip_price = float(booking.get("vip_price", 0))
        standard_price = float(booking.get("standard_price", 0))
        total_paid = sum(
            vip_price if s["type"] == "VIP" else standard_price
            for s in seat_info
        )

        with st.expander(f"{booking['event']} - Booking #{booking['booking_id']}"):
            st.write(f"**📍 Venue:** {booking['venue']}")
            st.write(f"**📅 Date:** {booking['date']} ⏰ {booking['time']}")
            st.write(f"**🪑 Seats:** {', '.join(seats_with_types)}")
            st.write(f"**💰 Total Paid:** ${total_paid:.2f}")

            if st.button("❌ Cancel Booking", key=f"user_cancel_{booking['booking_id']}"):
                result = cancel_booking(booking["booking_id"])
                if result.get("message"):
                    st.success("Booking cancelled successfully.")
                    st.rerun()
                else:
                    st.error(result.get("error", "Failed to cancel booking."))


def show_admin_panel():
    if not st.session_state.logged_in or not st.session_state.user.get("is_admin"):
        st.warning("Access denied. Admins only.")
        return

    st.header("🛠️ Admin Panel")

    # ➕ Add New Event
    with st.expander("➕ Add New Event"):
        name = st.text_input("Event Name")
        date = st.date_input("Date")
        time = st.time_input("Time")
        venue = st.text_input("Venue")
        category = st.text_input("Category")
        total_seats = st.number_input("Total Seats", min_value=1, step=1)
        vip_price = st.number_input("VIP Seat Price", min_value=0.0)
        standard_price = st.number_input("Standard Seat Price", min_value=0.0)
        if st.button("Add Event"):
            data = {
                "name": name, "date": str(date), "time": str(time),
                "venue": venue, "category": category,
                "total_seats": total_seats,
                "vip_price": vip_price, "standard_price": standard_price
            }
            res = requests.post(f"{BASE_URL}/add-event", json=data)
            if res.status_code == 200:
                st.success("Event added successfully!")
            else:
                st.error("Failed to add event.")

    # 📬 Cancel Bookings
    st.subheader("📬 Cancel Any Booking")
    users = get_all_users()
    for user in users:
        st.markdown(f"**👤 {user['name']}** ({user['email']})")
        bookings = get_user_bookings(user['email'])
        if not bookings:
            st.info("No bookings for this user.")
            continue
        for booking in bookings:
            with st.expander(f"Booking #{booking['booking_id']} for {booking['event']}"):
                st.write(f"📍 {booking['venue']}, {booking['date']} at {booking['time']}")
                st.write(f"🎛 Seats: {', '.join(booking['seats'])}")
                if st.button("Cancel This Booking", key=f"admin_cancel_{booking['booking_id']}"):
                    result = cancel_booking(booking["booking_id"])
                    if result.get("message"):
                        st.success(f"✅ Cancelled booking ID: {booking['booking_id']}")
                        st.rerun()
                    else:
                        st.error("❌ Failed to cancel booking.")
                        st.code(result, language='json')

    # 🛠️ Edit Event Details
    st.subheader("✏️ Edit Event Details")
    events = get_events()
    if not events:
        st.info("No events found to edit.")
    else:
        event_names = [event["name"] for event in events]
        selected_event = st.selectbox("Select Event", event_names)

        # Fetch selected event's data
        event_data = next(e for e in events if e["name"] == selected_event)

        new_name = st.text_input("New Event Name", value=event_data["name"])
        new_date = st.text_input("New Date (YYYY-MM-DD)", value=event_data["date"])
        new_time = st.text_input("New Time (HH:MM)", value=event_data["time"])
        new_venue = st.text_input("New Venue", value=event_data["venue"])
        new_category = st.text_input("New Category", value=event_data.get("category", ""))
        new_total_seats = st.number_input("New Total Seats", value=int(event_data["seats"]))
        new_vip_price = st.number_input("New VIP Price", value=float(event_data["vip_price"]))
        new_std_price = st.number_input("New Standard Price", value=float(event_data["standard_price"]))

        if st.button("Update Event", key="update_event_btn"):
            payload = {
                "original_name": selected_event,
                "name": new_name,
                "date": new_date,
                "time": new_time,
                "venue": new_venue,
                "category": new_category,
                "total_seats": new_total_seats,
                "vip_price": new_vip_price,
                "standard_price": new_std_price
            }
            res = requests.post(f"{BASE_URL}/update-event", json=payload)
            if res.status_code == 200:
                st.success("✅ Event updated successfully!")
            else:
                st.error("❌ Failed to update event")


def main():
    if not st.session_state.logged_in or st.session_state.user is None:
        homepage()
        menu = ["Login", "Register"]
        choice = st.sidebar.selectbox("Menu", menu)
        if choice == "Login":
            show_login()
        elif choice == "Register":
            show_register()
        return

    st.sidebar.success(f"Logged in as: {st.session_state.user['name']}")

    nav_options = ["Home", "My Bookings", "Logout"]
    if st.session_state.user.get("is_admin"):
        nav_options.insert(0, "Admin Panel")

    nav = st.sidebar.radio("Navigation", nav_options)

    if nav == "Admin Panel":
        show_admin_panel()
    elif nav == "Home":
        homepage()
        if st.session_state.get("view") == "events":
            show_events()
    elif nav == "My Bookings":
        st.session_state.view = None
        show_bookings()
    elif nav == "Logout":
        st.session_state.clear()
        st.session_state.view = None
        st.rerun()



if __name__ == "__main__":
    main()
