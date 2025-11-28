import datetime
from enum import Enum
from typing import List, Optional


# We do not import storage at the top to avoid circular errors.
# We import it inside methods where needed.

# ==========================================
# ENUMS & CONSTANTS
# ==========================================

class TicketType(Enum):
    ExhibitionPass = 1
    AllAccessPass = 2


class PaymentMethod(Enum):
    DebitCard = 1
    CreditCard = 2
    Wallet = 3


class AppState:
    """Global state to hold the currently logged-in user."""
    current_user = None


# ==========================================
# LOGIC MODELS
# ==========================================

class Workshop:
    def __init__(self, workshop_id: str, topic: str, date: str, start_time: str, end_time: str, exhibition_name: str,
                 capacity: int = 30):
        self.workshop_id = workshop_id
        self.topic = topic
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.exhibition_name = exhibition_name
        self.capacity = capacity
        self.attendees_ids: List[str] = []

    def is_full(self) -> bool:
        return len(self.attendees_ids) >= self.capacity

    def add_attendee(self, user_id: str) -> bool:
        if self.is_full(): return False
        if user_id in self.attendees_ids: return False
        self.attendees_ids.append(user_id)
        return True

    def remove_attendee(self, user_id: str) -> bool:
        if user_id in self.attendees_ids:
            self.attendees_ids.remove(user_id)
            return True
        return False

    def get_seats_remaining(self) -> int:
        return self.capacity - len(self.attendees_ids)


class Exhibition:
    def __init__(self, name: str, location: str):
        self.name = name
        self.location = location
        self.workshops: List[Workshop] = []

    def add_workshop(self, ws: Workshop):
        self.workshops.append(ws)


class Ticket:
    def __init__(self, ticket_id: int, attendee_id: str, price: float, ticket_type: TicketType):
        self.ticket_id = ticket_id
        self.attendee_id = attendee_id
        self.price = price
        self.ticket_type = ticket_type
        self.purchase_date = datetime.datetime.now().strftime("%d / %B / %Y")


class ExhibitionPass(Ticket):
    def __init__(self, ticket_id: int, attendee_id: str, price: float, selected_exhibitions: List[str]):
        super().__init__(ticket_id, attendee_id, price, TicketType.ExhibitionPass)
        self.selected_exhibitions = selected_exhibitions if isinstance(selected_exhibitions, list) else [
            selected_exhibitions]


class AllAccessPass(Ticket):
    def __init__(self, ticket_id: int, attendee_id: str, price: float):
        super().__init__(ticket_id, attendee_id, price, TicketType.AllAccessPass)


class Payment:
    def __init__(self, payment_id: int, attendee_id: str, amount: float, method: PaymentMethod, details: str):
        self.payment_id = payment_id
        self.attendee_id = attendee_id
        self.amount = amount
        self.method = method
        self.details = details
        self.timestamp = datetime.datetime.now()


class Reservation:
    def __init__(self, reservation_id: int, attendee_id: str, workshop_id: str, status: bool = True):
        self.reservation_id = reservation_id
        self.attendee_id = attendee_id
        self.workshop_id = workshop_id
        self.status = status

    def cancel(self):
        self.status = False


class Attendee:
    def __init__(self, attendee_id: str, name: str, email: str, phone: str, password: str):
        self.attendee_id = attendee_id
        self.name = name
        self.email = email
        self.phone = phone
        self.password = password
        self.tickets: List[int] = []
        self.reservations: List[int] = []

    def update_profile(self, new_name, new_email, new_phone, new_password):
        # Local import to prevent circular dependency
        from storage import data_store

        if new_email != self.email and new_email in data_store.attendees:
            return "Email already taken"

        if new_email != self.email:
            del data_store.attendees[self.email]
            self.email = new_email
            data_store.attendees[self.email] = self

        self.name = new_name
        self.phone = new_phone
        if new_password:
            self.password = new_password
        data_store.save_all()
        return None

    def purchase_ticket(self, ticket_type: TicketType, price: float, payment_method: PaymentMethod,
                        payment_details: dict, selected_exhibitions: List[str] = None):
        from storage import data_store
        try:
            masked = "Wallet"
            if payment_method in (PaymentMethod.CreditCard, PaymentMethod.DebitCard):
                cn = payment_details.get('card_number', '').strip()
                if not cn.isdigit() or len(cn) != 16: raise ValueError("Card must be 16 digits")
                masked = f"Card **{cn[-4:]}"
            else:
                if not payment_details.get('wallet_id'): raise ValueError("Wallet ID required")
                masked = f"Wallet: {payment_details.get('wallet_id')}"

            pay = Payment(len(data_store.payments) + 1, self.attendee_id, price, payment_method, masked)
            data_store.payments.append(pay)

            tid = len(data_store.tickets) + 1
            if ticket_type == TicketType.ExhibitionPass:
                t = ExhibitionPass(tid, self.attendee_id, price, selected_exhibitions)
            else:
                t = AllAccessPass(tid, self.attendee_id, price)

            data_store.tickets.append(t)
            self.tickets.append(tid)
            data_store.save_all()
            return t, None

        except ValueError as e:
            return None, str(e)

    def refund_ticket(self, ticket_id: int):
        from storage import data_store
        t = next((tk for tk in data_store.tickets if tk.ticket_id == ticket_id), None)
        if not t: return "Not found"
        act_res = [r for r in data_store.reservations if r.attendee_id == self.attendee_id and r.status]
        for r in act_res:
            self.cancel_reservation(r.reservation_id)
        if ticket_id in self.tickets: self.tickets.remove(ticket_id)
        if t in data_store.tickets: data_store.tickets.remove(t)
        data_store.save_all()
        return None

    def upgrade_ticket(self, ticket_id: int, new_access: TicketType, cost: float, adds: List[str] = None):
        from storage import data_store
        t = next((tk for tk in data_store.tickets if tk.ticket_id == ticket_id), None)
        if not t: return None, "Not found"

        if new_access == TicketType.ExhibitionPass and isinstance(t, ExhibitionPass):
            if adds:
                for x in adds:
                    if x not in t.selected_exhibitions: t.selected_exhibitions.append(x)
                t.price += cost
            else:
                return None, "No exhibitions added"
        elif new_access == TicketType.AllAccessPass:
            idx = data_store.tickets.index(t)
            up = AllAccessPass(t.ticket_id, t.attendee_id, 500.0)
            data_store.tickets[idx] = up
            t = up
        data_store.save_all()
        return t, None

    def reserve_workshop(self, workshop_id: str):
        from storage import data_store
        ws = data_store.workshops.get(workshop_id)
        if not ws: return None, "Workshop not found"
        if not self.can_access(ws.exhibition_name): return None, f"You don't have a ticket for {ws.exhibition_name}"
        if not ws.add_attendee(self.attendee_id): return None, "Workshop Full or already booked"

        res = Reservation(len(data_store.reservations) + 1, self.attendee_id, workshop_id)
        data_store.reservations.append(res)
        data_store.save_all()
        return res, None

    def cancel_reservation(self, rid):
        from storage import data_store
        r = next((x for x in data_store.reservations if x.reservation_id == rid), None)
        if not r or not r.status: return "Invalid"
        ws = data_store.workshops.get(r.workshop_id)
        if ws: ws.remove_attendee(self.attendee_id)
        r.cancel()
        data_store.save_all()
        return None

    def can_access(self, ex_name):
        from storage import data_store
        for tid in self.tickets:
            t = next((x for x in data_store.tickets if x.ticket_id == tid), None)
            if t:
                if t.ticket_type == TicketType.AllAccessPass: return True
                if hasattr(t, 'selected_exhibitions') and ex_name in t.selected_exhibitions: return True
        return False