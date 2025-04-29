import streamlit as st
from api import *

def inject_css():
    st.markdown("""
<style>
html, body, .stApp {
    background-color: #fff5f5 !important;
    color: #000000 !important;
    font-family: 'Segoe UI', sans-serif !important;
}

section.main > div {
    background-color: #ffe5e5 !important;
    color: #000000 !important;
}

.stSidebar {
    background-color: #ffebeb !important;
    color: #000000 !important;
}

.st-expander, .st-expanderHeader {
    background-color: #ffe5e5 !important;
    color: #000000 !important;
    border: 1px solid #ffcccc !important;
}

.stButton > button {
    background-color: #b00020 !important;
    color: #ffffff !important;
    border-radius: 8px !important;
}

.stButton > button:hover {
    background-color: #7f0015 !important;
}

input, textarea {
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 1px solid #b00020 !important;
}

h1, h2, h3, h4, h5, h6, .stMarkdown, .css-10trblm, .css-q8sbsg {
    color: #000000 !important;
}

footer {
    visibility: hidden;
}
</style>
""", unsafe_allow_html=True)


def homepage():
    st.markdown("""
    <div class="header">
        <h1>🎟️ Welcome to CinemaTick</h1>
        <p>Your one-stop destination for event bookings</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Browse Events", key="browse_events_btn", type="primary"):
        st.session_state.show_events = True
        show_events()

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
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

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
            st.success("Registration successful")
        else:
            st.error(msg)

def show_events():
    st.header(f"🎭 Events - Category: {st.session_state.selected_category}")
    events = get_events(st.session_state.selected_category)
    if not events:
        st.warning("No events found.")
        return
    for event in events:
        with st.expander(event["name"]):
            st.write(f"📍 Venue: {event['venue']}")
            st.write(f"📅 Date: {event['date']} ⏰ {event['time']}")
            st.write(f"💰 Price: ${event['price']:.2f}")
            st.write(f"🪑 Total Seats: {event['seats']}")
            display_seat_selector(event["name"])

def display_seat_selector(event_name):
    st.subheader("🎯 Select Your Seats")
    booked = get_booked_seats(event_name)
    rows, cols = list("ABCDEF"), list(range(1, 11))
    for r in rows:
        cols_row = st.columns(len(cols))
        for i, c in enumerate(cols):
            seat_id = f"{r}{c}"
            disabled = seat_id in booked
            if cols_row[i].button(seat_id, key=f"{event_name}_{seat_id}", disabled=disabled):
                st.session_state.selected_seats.append(seat_id)

    if st.session_state.selected_seats:
        st.success(f"Selected Seats: {', '.join(st.session_state.selected_seats)}")
        if st.button("Confirm Booking", key=f"confirm_{event_name}"):
            result = book_event(st.session_state.user["email"], event_name, st.session_state.selected_seats)
            if "booking_id" in result:
                st.balloons()
                st.success(f"Booking Confirmed! ID: {result['booking_id']}")
                st.session_state.selected_seats = []
            else:
                st.error(result.get("error", "Failed to book."))

def show_bookings():
    st.header("📖 My Bookings")
    bookings = get_user_bookings(st.session_state.user["email"])
    if not bookings:
        st.info("You haven't booked any events yet.")
        return
    for booking in bookings:
        total_paid = booking.get("total_price", 0)
        status = booking.get("status", "Confirmed").capitalize()
        with st.expander(f"{booking['event']} - Booking #{booking['booking_id']}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Venue:** {booking['venue']}")
                st.write(f"**Date:** {booking['date']} at {booking['time']}")
                st.write(f"**Seats:** {', '.join(booking['seats'])}")
                st.write(f"**Total Paid:** ${total_paid:.2f}")
                st.write(f"**Status:** {status}")
            with col2:
                if status.lower() == "confirmed":
                    if st.button("Cancel Booking", key=f"cancel_{booking['booking_id']}"):
                        res = cancel_booking(booking['booking_id'])
                        if "message" in res:
                            st.success("Booking cancelled.")
                            st.experimental_rerun()
                        else:
                            st.error(res.get("error", "Cancellation failed."))

def show_admin_panel():
    st.header("🛠️ Admin Panel")
    with st.expander("➕ Add New Event"):
        name = st.text_input("Event Name")
        date = st.date_input("Date")
        time = st.time_input("Time")
        venue = st.text_input("Venue")
        price = st.number_input("Price", min_value=0.0)
        category = st.text_input("Category")
        total_seats = st.number_input("Total Seats", min_value=1, step=1)
        if st.button("Add Event"):
            data = {
                "name": name,
                "date": str(date),
                "time": str(time),
                "venue": venue,
                "price": price,
                "category": category,
                "total_seats": total_seats
            }
            res = requests.post(f"{BASE_URL}/add-event", json=data)
            if res.status_code == 200:
                st.success("Event added successfully!")
            else:
                st.error("Failed to add event.")

    st.subheader("📬 Cancel Any Booking")
    users = requests.get(f"{BASE_URL}/users").json()
    for user in users:
        st.markdown(f"**👤 {user['name']}** ({user['email']})")
        bookings = get_user_bookings(user['email'])
        for booking in bookings:
            with st.expander(f"Booking #{booking['booking_id']} for {booking['event']}"):
                st.write(f"📍 {booking['venue']}, {booking['date']} at {booking['time']}")
                st.write(f"🎫 Seats: {', '.join(booking['seats'])}")
                if st.button("Cancel This Booking", key=f"admin_cancel_{booking['booking_id']}"):
                    result = cancel_booking(booking['booking_id'])
                    if "message" in result:
                        st.success("Booking cancelled successfully.")
                        st.experimental_rerun()
                    else:
                        st.error(result.get("error", "Failed to cancel booking."))

    if st.button("Generate Sample Events"):
        res = requests.post(f"{BASE_URL}/generate-sample-events")
        if res.status_code == 200:
            st.success("Sample events generated.")
            st.experimental_rerun()
        else:
            st.error("Failed to generate sample events.")
