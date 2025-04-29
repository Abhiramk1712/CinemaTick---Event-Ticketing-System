from fastapi import FastAPI, HTTPException, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from neo4j import GraphDatabase
import uvicorn
import uuid
from email_utils import send_email_with_qr, send_cancellation_email
from typing import Optional

import json


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

class EventRequest(BaseModel):
    name: str
    date: str
    time: str
    venue: str
    category: str
    total_seats: int
    vip_price: float
    standard_price: float

class EventUpdateRequest(BaseModel):
    original_name: str  # the current name of the event in DB
    name: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    venue: Optional[str] = None
    category: Optional[str] = None
    total_seats: Optional[int] = None
    vip_price: Optional[float] = None
    standard_price: Optional[float] = None

class BookingRequest(BaseModel):
    user_email: str
    event_name: str
    seats: list

class CancelRequest(BaseModel):
    booking_id: str

class PriceUpdateRequest(BaseModel):
    event_name: str
    vip_price: float
    standard_price: float

@app.post("/register")
def register_user(
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False)
):
    with driver.session() as session:
        existing = session.run("MATCH (u:User {email: $email}) RETURN u", {"email": email}).single()
        if existing:
            raise HTTPException(status_code=400, detail="User already exists")
        session.run("""
            CREATE (u:User {
                name: $name,
                email: $email,
                phone: $phone,
                password: $password,
                is_admin: $is_admin
            })
        """, {
            "name": name,
            "email": email,
            "phone": phone,
            "password": password,
            "is_admin": is_admin
        })
    return {"message": "User registered"}

@app.post("/login")
def login_user(email: str = Form(...), password: str = Form(...)):
    with driver.session() as session:
        result = session.run("MATCH (u:User {email: $email, password: $password}) RETURN u", {
            "email": email,
            "password": password
        }).single()
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return result["u"]

@app.get("/events")
def get_events(category: str = Query(None)):
    with driver.session() as session:
        query = """
            MATCH (e:Event)-[:HELD_AT]->(v:Venue)
            OPTIONAL MATCH (e)-[:BELONGS_TO]->(c:Category)
            WHERE $category IS NULL OR toLower(c.name) = toLower($category)
            RETURN e.name AS name, e.date AS date, e.time AS time,
                   e.total_seats AS seats, v.name AS venue,
                   e.vip_price AS vip_price, e.standard_price AS standard_price,
                   c.name AS category
        """
        results = session.run(query, {"category": category})
        return [dict(r) for r in results]


@app.post("/add-event")
def add_event(req: EventRequest):
    if req.vip_price is None or req.standard_price is None:
        raise HTTPException(status_code=400, detail="VIP and Standard prices are required")

    with driver.session() as session:
        session.run("""
            MERGE (v:Venue {name: $venue})
            MERGE (c:Category {name: $category})
            CREATE (e:Event {
                name: $name, date: $date, time: $time,
                total_seats: $total_seats,
                vip_price: $vip_price,
                standard_price: $standard_price
            })
            MERGE (e)-[:HELD_AT]->(v)
            MERGE (e)-[:BELONGS_TO]->(c)
        """, {
            "name": req.name,
            "date": req.date,
            "time": req.time,
            "venue": req.venue,
            "category": req.category,
            "total_seats": req.total_seats,
            "vip_price": req.vip_price,
            "standard_price": req.standard_price
        })

    return {"message": "Event added"}



@app.get("/event/{event_name}")
def get_event_by_name(event_name: str):
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Event {name: $event_name})-[:HELD_AT]->(v:Venue)
            OPTIONAL MATCH (e)-[:BELONGS_TO]->(c:Category)
            RETURN e.name AS name,
                   e.date AS date,
                   e.time AS time,
                   e.total_seats AS seats,
                   e.vip_price AS vip_price,
                   e.standard_price AS standard_price,
                   v.name AS venue,
                   c.name AS category
        """, {"event_name": event_name}).single()

        if not result:
            raise HTTPException(status_code=404, detail="Event not found")

        return dict(result)




@app.post("/book")
def book_event(req: BookingRequest):
    booking_id = str(uuid.uuid4())
    seat_count = len(req.seats)

    # Define seat types
    vip_rows = ["A", "B"]
    seat_info = [{"seat": s, "type": "VIP" if s[0] in vip_rows else "Standard"} for s in req.seats]

    with driver.session() as session:
        # Check available seats
        available = session.run("""
            MATCH (e:Event {name: $event_name})
            RETURN e.total_seats AS seats
        """, {"event_name": req.event_name}).single()

        if not available or available["seats"] < seat_count:
            raise HTTPException(status_code=400, detail="Not enough seats available")

        try:
            # Store seat_info as JSON string
            session.run("""
                MATCH (u:User {email: $user_email}), (e:Event {name: $event_name})
                CREATE (u)-[:BOOKED {
                    booking_id: $booking_id,
                    seats: $seats,
                    seat_info: $seat_info_str,
                    date: date()
                }]->(e)
            """, {
                "user_email": req.user_email,
                "event_name": req.event_name,
                "booking_id": booking_id,
                "seats": req.seats,
                "seat_info_str": json.dumps(seat_info)
            })

            # Decrement seat count
            session.run("""
                MATCH (e:Event {name: $event_name})
                SET e.total_seats = e.total_seats - $count
            """, {
                "event_name": req.event_name,
                "count": seat_count
            })

            # Send email confirmation
            send_email_with_qr(req.user_email, booking_id, req.event_name, req.seats)

        except Exception as e:
            print("❌ Booking Error:", str(e))
            raise HTTPException(status_code=500, detail="Booking failed due to a server error.")

    return {"message": "Booking successful", "booking_id": booking_id}



@app.post("/cancel")
def cancel_booking(req: CancelRequest):
    try:
        with driver.session() as session:
            booking = session.run("""
                MATCH (u:User)-[b:BOOKED {booking_id: $booking_id}]->(e:Event)
                RETURN u.email AS email, e.name AS event
            """, {"booking_id": req.booking_id}).single()

            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")

            # Send cancellation email BEFORE deleting
            send_cancellation_email(
                to_email=booking["email"],
                booking_id=req.booking_id,
                event_name=booking["event"]
            )

            session.run("""
                MATCH (:User)-[b:BOOKED {booking_id: $booking_id}]->(:Event)
                DELETE b
            """, {"booking_id": req.booking_id})

        return {"message": "Booking cancelled"}

    except Exception as e:
        print(f"❌ Error cancelling booking: {e}")
        raise HTTPException(status_code=500, detail="Server error during booking cancellation")


@app.get("/bookings/{user_email}")
def get_user_bookings(user_email: str):
    with driver.session() as session:
        result = session.run("""
            MATCH (u:User {email: $user_email})-[b:BOOKED]->(e:Event)-[:HELD_AT]->(v:Venue)
            RETURN 
                b.booking_id AS booking_id,
                e.name AS event,
                e.date AS date,
                e.time AS time,
                b.seats AS seats,
                b.seat_info AS seat_info,
                v.name AS venue,
                e.vip_price AS vip_price,
                e.standard_price AS standard_price
        """, {"user_email": user_email})

        bookings = []
        for r in result:
            data = dict(r)
            try:
                seat_info = json.loads(data.get("seat_info", "[]"))
            except:
                seat_info = []

            vip_price = float(data.get("vip_price", 0))
            standard_price = float(data.get("standard_price", 0))

            total = sum(
                vip_price if s.get("type") == "VIP" else standard_price
                for s in seat_info
            )

            data["total_price"] = total
            data["seat_info"] = seat_info
            bookings.append(data)

        return bookings




@app.post("/update-event")
def update_event(req: EventUpdateRequest):
    with driver.session() as session:
        props = {k: v for k, v in req.dict().items() if v is not None and k != "original_name"}
        if not props:
            raise HTTPException(status_code=400, detail="No fields to update")

        set_clauses = ", ".join([f"e.{k} = ${k}" for k in props.keys()])
        params = props.copy()
        params["original_name"] = req.original_name

        query = f"""
            MATCH (e:Event {{name: $original_name}})
            SET {set_clauses}
            RETURN e.name AS name
        """
        result = session.run(query, params).single()
        if not result:
            raise HTTPException(status_code=404, detail="Event not found")

        return {"message": "Event updated successfully"}

@app.get("/booked-seats/{event_name}")
def get_booked_seats(event_name: str):
    with driver.session() as session:
        result = session.run("MATCH (:User)-[b:BOOKED]->(e:Event {name: $event_name}) RETURN b.seats AS seats", {
            "event_name": event_name
        })
        booked = []
        for record in result:
            booked.extend(record["seats"])
        return list(set(booked))

@app.get("/categories")
def get_categories():
    with driver.session() as session:
        result = session.run("MATCH (c:Category) RETURN c.name AS name")
        categories = [record["name"].strip().title() for record in result if record["name"]]
        return sorted(set(categories))  # Remove duplicates and sort alphabetically


@app.get("/users")
def get_all_users():
    with driver.session() as session:
        result = session.run("MATCH (u:User) RETURN u.name AS name, u.email AS email, u.phone AS phone, u.is_admin AS is_admin")
        return [dict(r) for r in result]

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
