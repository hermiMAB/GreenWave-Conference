import pickle
import os
# Import classes so that Pickle knows how to reconstruct objects
from classes import Workshop, Exhibition, Attendee, Ticket, Reservation, Payment


class DataStore:
    def __init__(self):
        self.files = ["attendees", "tickets", "reservations", "payments", "exhibitions"]
        self.attendees = {}
        self.tickets = []
        self.reservations = []
        self.payments = []
        self.exhibitions = []
        self.workshops = {}

    def _load(self, n):
        try:
            with open(f"{n}.pkl", "rb") as f:
                return pickle.load(f)
        except:
            return None

    def _save(self, n, o):
        with open(f"{n}.pkl", "wb") as f: pickle.dump(o, f)

    def load_all(self):
        self.attendees = self._load("attendees") or {}
        self.tickets = self._load("tickets") or []
        self.reservations = self._load("reservations") or []
        self.payments = self._load("payments") or []
        self.exhibitions = self._load("exhibitions") or []

        if not self.exhibitions:
            self._gen_data()

        self.workshops = {}
        for ex in self.exhibitions:
            for ws in ex.workshops:
                self.workshops[ws.workshop_id] = ws

    def save_all(self):
        self._save("attendees", self.attendees)
        self._save("tickets", self.tickets)
        self._save("reservations", self.reservations)
        self._save("payments", self.payments)
        self._save("exhibitions", self.exhibitions)

    def _gen_data(self):
        # 3 DISTINCT WORKSHOPS PER EXHIBITION, REPEATED OVER 4 DAYS
        dates = ["April 15, 2026", "April 16, 2026", "April 17, 2026", "April 18, 2026"]

        ex1_sessions = [("Intro to Climate Data Tools", "10:30 AM", "11:30 AM"),
                        ("Renewable Energy Systems", "12:30 PM", "01:30 PM"),
                        ("Smart Agriculture Solutions", "02:30 PM", "03:30 PM")]

        ex2_sessions = [("Policy Simulation Lab", "09:30 AM", "10:30 AM"),
                        ("Sustainability Reporting 101", "12:00 PM", "01:00 PM"),
                        ("Corporate Environmental Strategy", "02:00 PM", "03:00 PM")]

        ex3_sessions = [("Building Low-Carbon Communities", "12:30 PM", "01:30 PM"),
                        ("Waste Reduction Projects", "02:00 PM", "03:00 PM"),
                        ("Circular Economy in Practice", "03:30 PM", "04:30 PM")]

        e1 = Exhibition("Climate Tech Innovations", "Hall A")
        e2 = Exhibition("Green Policy & Governance", "Hall B")
        e3 = Exhibition("Community Action & Impact", "Hall C")
        self.exhibitions = [e1, e2, e3]

        def add_ws(ex, sessions):
            for d in dates:
                for t, st, et in sessions:
                    wid = f"{t.replace(' ', '_')}_{d}"
                    ws = Workshop(wid, t, d, st, et, ex.name, capacity=30)
                    ex.add_workshop(ws)
                    self.workshops[wid] = ws

        add_ws(e1, ex1_sessions)
        add_ws(e2, ex2_sessions)
        add_ws(e3, ex3_sessions)
        self.save_all()


# Create the global instance here
data_store = DataStore()