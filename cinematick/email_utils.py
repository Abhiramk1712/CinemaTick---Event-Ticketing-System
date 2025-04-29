import qrcode
import requests
from io import BytesIO
import base64

# ✅ REPLACE this with your actual SendGrid API key
SENDGRID_API_KEY = "your_api_key"

def send_email_with_qr(to_email, booking_id, event_name, seats):
    # Generate QR code
    qr_data = f"Booking ID: {booking_id}\nEvent: {event_name}\nSeats: {', '.join(seats)}"
    qr = qrcode.make(qr_data)
    buffer = BytesIO()
    qr.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode QR image in base64
    encoded_image = base64.b64encode(buffer.read()).decode()

    # ✅ REPLACE this with your verified sender email
    from_email = "example123@gmail.com"

    # Build the payload
    payload = {
        "personalizations": [{
            "to": [{"email": to_email}],
            "subject": "🎟️ Your CinemaTick Booking Confirmation"
        }],
        "from": {"email": from_email},
        "content": [{
            "type": "text/plain",
            "value": f"Thanks for booking with CinemaTick!\n\nEvent: {event_name}\nSeats: {', '.join(seats)}\nBooking ID: {booking_id}\n\nYour ticket QR is attached."
        }],
        "attachments": [{
            "content": encoded_image,
            "type": "image/png",
            "filename": "ticket_qr.png"
        }]
    }

    # Send email via SendGrid
    try:
        res = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"}
        )
        res.raise_for_status()
        print(f"✅ Email sent to: {to_email}")
    except Exception as e:
        print("❌ Failed to send email:", e)

def send_cancellation_email(to_email, booking_id, event_name):
    from_email = "teja67514@gmail.com"

    payload = {
        "personalizations": [{
            "to": [{"email": to_email}],
            "subject": "❌ CinemaTick Booking Cancelled"
        }],
        "from": {"email": from_email},
        "content": [{
            "type": "text/plain",
            "value": f"Your booking for '{event_name}' with ID {booking_id} has been successfully cancelled.\n\nWe hope to see you again soon!"
        }]
    }

    try:
        res = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            json=payload,
            headers={"Authorization": f"Bearer {SENDGRID_API_KEY}"}
        )
        res.raise_for_status()
        print(f"✅ Cancellation email sent to: {to_email}")
    except Exception as e:
        print("❌ Failed to send cancellation email:", e)

