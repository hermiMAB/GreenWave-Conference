import tkinter as tk
from tkinter import ttk, messagebox
import re
from collections import defaultdict
from classes import TicketType, PaymentMethod, AppState, Attendee, ExhibitionPass, AllAccessPass
from storage import data_store

# ==========================================
# ASSETS & CONFIGURATION
# ==========================================

COLORS = {
    "primary": "#2E7D32",  # Deep Forest Green
    "secondary": "#E8F5E9",  # Light Mint
    "accent": "#F57C00",  # Orange/Amber
    "text": "#212121",  # Dark Grey
    "white": "#FFFFFF",  # Pure White
    "danger": "#C62828",  # Red
    "header": "#1B5E20",  # Darkest Green
    "card_bg": "#F9F9F9"  # Light Grey for Cards
}

FONTS = {
    "h1": ("Segoe UI", 24, "bold"),
    "h2": ("Segoe UI", 18, "bold"),
    "body": ("Segoe UI", 11),
    "bold": ("Segoe UI", 11, "bold"),
    "small": ("Segoe UI", 9),
    "mono": ("Courier New", 10)
}


def add_bg(widget):
    widget.configure(bg=COLORS["secondary"])


class GreenWaveApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("GreenWave Conference 2026")
        self.geometry("1200x850")
        self.configure(bg=COLORS["secondary"])

        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", padding=5)
        style.configure("Treeview.Heading", font=FONTS["bold"], background=COLORS["primary"], foreground="white")
        style.configure("Treeview", font=FONTS["body"], rowheight=30)
        style.configure("TNotebook.Tab", font=FONTS["bold"], padding=[10, 5])
        style.configure("TProgressbar", thickness=20)

        self.container = tk.Frame(self, bg=COLORS["secondary"])
        self.container.pack(fill="both", expand=True)
        self.switch_frame(WelcomeScreen)

    def switch_frame(self, cls, context=None):
        for c in self.container.winfo_children(): c.destroy()
        f = cls(self.container, self, context) if context else cls(self.container, self)
        f.pack(fill="both", expand=True)


# ----------------------------------------------------
# AUTH SCREENS
# ----------------------------------------------------
class WelcomeScreen(tk.Frame):
    def __init__(self, parent, controller, context=None):
        super().__init__(parent);
        add_bg(self)
        center = tk.Frame(self, bg=COLORS["white"], padx=50, pady=50, relief="raised", borderwidth=1)
        center.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(center, text="GreenWave Conference", font=("Segoe UI", 32, "bold"), fg=COLORS["primary"],
                 bg="white").pack()
        tk.Label(center, text="April 15-18, 2026", font=FONTS["h2"], fg="gray", bg="white").pack(pady=(0, 20))
        tk.Button(center, text="Login", font=FONTS["bold"], bg=COLORS["primary"], fg="white", width=25, pady=10,
                  command=lambda: controller.switch_frame(LoginScreen)).pack(pady=10)
        tk.Button(center, text="Register", font=FONTS["bold"], bg=COLORS["accent"], fg="white", width=25, pady=10,
                  command=lambda: controller.switch_frame(RegistrationScreen)).pack(pady=10)


class LoginScreen(tk.Frame):
    def __init__(self, parent, controller, context=None):
        super().__init__(parent);
        add_bg(self);
        self.c = controller
        box = tk.Frame(self, bg="white", padx=40, pady=40, relief="raised")
        box.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(box, text="Sign In", font=FONTS["h1"], bg="white", fg=COLORS["primary"]).pack(pady=20)
        tk.Label(box, text="Email:", bg="white", font=FONTS["bold"]).pack(anchor="w")
        self.e = tk.Entry(box, width=35, font=FONTS["body"]);
        self.e.pack(pady=5)
        tk.Label(box, text="Password:", bg="white", font=FONTS["bold"]).pack(anchor="w")
        self.p = tk.Entry(box, width=35, font=FONTS["body"], show="*");
        self.p.pack(pady=5)
        tk.Button(box, text="Login", bg=COLORS["primary"], fg="white", font=FONTS["bold"], width=30,
                  command=self.do_login).pack(pady=20)
        tk.Button(box, text="Back", bg="#eee", width=30, command=lambda: controller.switch_frame(WelcomeScreen)).pack()

    def do_login(self):
        em, pw = self.e.get().strip(), self.p.get().strip()
        # Admin Login
        if em == "afshan.parkar@zu.ac.ae" and pw == "12345678":
            self.c.switch_frame(AdminDashboard)
            return
        user = data_store.attendees.get(em)
        if user and user.password == pw:
            AppState.current_user = user
            self.c.switch_frame(ProfileScreen)
        else:
            messagebox.showerror("Error", "Invalid credentials")


class RegistrationScreen(tk.Frame):
    def __init__(self, parent, controller, context=None):
        super().__init__(parent)
        add_bg(self)
        self.c = controller
        box = tk.Frame(self, bg="white", padx=40, pady=40, relief="raised")
        box.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(box, text="Create Account", font=FONTS["h1"], bg="white", fg=COLORS["primary"]).pack(pady=20)

        self.n = self.mk(box, "Full Name")
        self.e = self.mk(box, "Email")
        self.ph = self.mk(box, "Phone (05xxxxxxxx)")
        self.pw = self.mk(box, "Password (min 8 chars)", show="*")

        tk.Button(box, text="Register", bg=COLORS["accent"], fg="white", font=FONTS["bold"], width=30,
                  command=self.reg).pack(pady=20)
        tk.Button(box, text="Back", bg="#eee", width=30, command=lambda: controller.switch_frame(WelcomeScreen)).pack()

    def mk(self, p, txt, show=None):
        tk.Label(p, text=txt, bg="white", font=FONTS["small"]).pack(anchor="w")
        e = tk.Entry(p, width=35, font=FONTS["body"], show=show)
        e.pack(pady=(0, 10))
        return e

    def reg(self):
        try:
            # Get inputs
            n = self.n.get().strip()
            e = self.e.get().strip()
            p = self.ph.get().strip()
            pw = self.pw.get().strip()

            # 1. Check Empty Fields
            if not all([n, e, p, pw]):
                raise ValueError("All fields required")

            # 2. Validate Email
            if not re.match(r"[^@]+@[^@]+\.[^@]+", e):
                raise ValueError("Invalid Email")

            # 3. Validate Phone (Must be 10 digits, start with 0)
            if not (p.isdigit() and len(p) == 10 and p.startswith('0')):
                raise ValueError("Phone must be 10 digits starting with 0")

            # 4. Validate Password Length
            if len(pw) < 8:
                raise ValueError("Password min 8 chars")

            # 5. Check Duplicate
            if e in data_store.attendees:
                raise ValueError("Email already exists")

            # Save
            data_store.attendees[e] = Attendee(f"U{len(data_store.attendees) + 1}", n, e, p, pw)
            data_store.save_all()

            messagebox.showinfo("Success", "Account created")
            self.c.switch_frame(LoginScreen)

        except ValueError as ex:
            messagebox.showerror("Error", str(ex))

# --- USER SCREENS ---
class ProfileScreen(tk.Frame):
    def __init__(self, parent, controller, context=None):
        super().__init__(parent);
        add_bg(self);
        u = AppState.current_user
        hdr = tk.Frame(self, bg=COLORS["header"], height=80);
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"Hello, {u.name}", font=FONTS["h1"], bg=COLORS["header"], fg="white").pack(side="left",
                                                                                                       padx=20, pady=20)
        tk.Button(hdr, text="Logout", bg=COLORS["danger"], fg="white",
                  command=lambda: controller.switch_frame(LoginScreen)).pack(side="right", padx=20)

        grid = tk.Frame(self, bg=COLORS["secondary"]);
        grid.pack(pady=40)
        self.card(grid, 0, 0, "Workshops", "Browse exhibitions and\nreserve your seats.", "Reserve Now",
                  lambda: controller.switch_frame(ExhibitionBrowserFrame))
        self.card(grid, 0, 1, "Tickets", "Purchase new tickets\nor upgrade existing.", "Buy Ticket",
                  lambda: controller.switch_frame(TicketPurchaseScreen), "Upgrade",
                  lambda: controller.switch_frame(UpgradeTicketScreen))
        self.card(grid, 1, 0, "My Schedule", "View your daily itinerary\nand reserved sessions.", "View Schedule",
                  lambda: ScheduleWindow(controller, u))
        self.card(grid, 1, 1, "Account", "Manage profile, view pass,\nor delete account.", "Manage Profile",
                  lambda: EditProfileWindow(controller, u), "My Tickets", lambda: TicketManagerWindow(controller, u))

    def card(self, parent, r, c, title, desc, b1t, c1, b2t=None, c2=None):
        f = tk.Frame(parent, bg="white", width=300, height=220, relief="raised", borderwidth=1)
        f.grid(row=r, column=c, padx=15, pady=15);
        f.pack_propagate(False)
        tk.Label(f, text=title, font=FONTS["h2"], bg="white", fg=COLORS["primary"]).pack(pady=(20, 5))
        tk.Label(f, text=desc, font=FONTS["body"], bg="white", fg="gray").pack()
        tk.Button(f, text=b1t, bg=COLORS["primary"], fg="white", width=20, command=c1).pack(side="bottom", pady=10)
        if b2t: tk.Button(f, text=b2t, bg=COLORS["accent"], fg="white", width=20, command=c2).pack(side="bottom",
                                                                                                   pady=(0, 5))


class TicketPurchaseScreen(tk.Frame):
    def __init__(self, parent, controller, context=None):
        super().__init__(parent)
        self.controller = controller
        add_bg(self)
        main = tk.Frame(self, bg="white", padx=40, pady=40, relief="groove", borderwidth=2)
        main.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(main, text="Checkout", font=FONTS["h1"], bg="white", fg=COLORS["primary"]).pack(pady=(0, 20))

        # 1. Bundle Selection
        lf1 = tk.LabelFrame(main, text="1. Bundle", bg="white", font=FONTS["bold"], padx=10, pady=10)
        lf1.pack(fill="x", pady=5)
        self.b_var = tk.StringVar(value="1 Exhibition (200 AED)")
        cb = ttk.Combobox(lf1, textvariable=self.b_var,
                          values=("1 Exhibition (200 AED)", "2 Exhibitions (400 AED)", "All-Access (500 AED)"),
                          width=40, state="readonly")
        cb.pack()
        cb.bind("<<ComboboxSelected>>", self.upd)

        # 2. Exhibition Selection
        lf2 = tk.LabelFrame(main, text="2. Select Exhibitions", bg="white", font=FONTS["bold"], padx=10, pady=10)
        lf2.pack(fill="x", pady=5)
        self.lb = tk.Listbox(lf2, selectmode="multiple", height=4, width=50)
        for e in data_store.exhibitions: self.lb.insert(tk.END, e.name)
        self.lb.pack()

        # 3. Payment
        lf3 = tk.LabelFrame(main, text="3. Payment", bg="white", font=FONTS["bold"], padx=10, pady=10)
        lf3.pack(fill="x", pady=5)

        self.pm = ttk.Combobox(lf3, values=["CreditCard", "DebitCard", "Wallet"], state="readonly")
        self.pm.current(0)
        self.pm.grid(row=0, column=0, padx=5)
        self.pm.bind("<<ComboboxSelected>>", self.cvv_t)  # Link dropdown to toggle function

        self.pid = tk.Entry(lf3, width=20)
        self.pid.grid(row=0, column=1, padx=5)

        # CVV UI Elements (Hidden/Shown based on selection)
        self.lc = tk.Label(lf3, text="CVV:", bg="white")
        self.ec = tk.Entry(lf3, width=5)

        # Initialize UI state
        self.cvv_t()

        tk.Button(main, text="Confirm & Pay", bg=COLORS["primary"], fg="white", font=FONTS["bold"], width=40,
                  command=self.buy).pack(pady=20)
        tk.Button(main, text="Cancel", command=lambda: controller.switch_frame(ProfileScreen)).pack()

    def cvv_t(self, e=None):
        """Shows CVV input only if CreditCard is selected"""
        if self.pm.get() == "CreditCard":
            self.lc.grid(row=0, column=2, padx=5)
            self.ec.grid(row=0, column=3, padx=5)
        else:
            self.lc.grid_forget()
            self.ec.grid_forget()

    def upd(self, e=None):
        self.lb.selection_clear(0, tk.END)
        if "All" in self.b_var.get():
            for i in range(self.lb.size()): self.lb.selection_set(i)
            self.lb.config(state="disabled")
        else:
            self.lb.config(state="normal")

    def buy(self):
        b = self.b_var.get()
        idx = self.lb.curselection()
        if "1 Ex" in b and len(idx) != 1: messagebox.showerror("Error", "Select exactly 1 exhibition"); return
        if "2 Ex" in b and len(idx) != 2: messagebox.showerror("Error", "Select exactly 2 exhibitions"); return

        sel = [self.lb.get(i) for i in idx]
        pr = 500.0 if "All" in b else (400.0 if "2" in b else 200.0)
        tt = TicketType.AllAccessPass if "All" in b else TicketType.ExhibitionPass

        # Collect Data correctly (get actual inputs)
        pd = {
            "card_number": self.pid.get().strip(),
            "wallet_id": self.pid.get().strip(),
            "cvv": self.ec.get().strip()  # Capture the real CVV input
        }

        t, err = AppState.current_user.purchase_ticket(tt, pr, PaymentMethod[self.pm.get()], pd, sel)
        if err:
            messagebox.showerror("Failed", err)
        else:
            messagebox.showinfo("Success", "Ticket Purchased! Please select an exhibition to book your workshops now.")
            self.controller.switch_frame(ExhibitionBrowserFrame)


class ExhibitionBrowserFrame(tk.Frame):
    def __init__(self, parent, controller, context=None):
        super().__init__(parent);
        add_bg(self)
        tk.Label(self, text="Exhibitions", font=FONTS["h1"], bg=COLORS["secondary"]).pack(pady=20)
        lb = tk.Listbox(self, font=FONTS["body"], height=6);
        lb.pack(padx=40, pady=10, fill="x")
        for e in data_store.exhibitions: lb.insert(tk.END, e.name)

        tk.Button(self, text="View Workshops", bg=COLORS["primary"], fg="white", font=FONTS["bold"],
                  command=lambda: [controller.switch_frame(WorkshopListFrame, context=data_store.exhibitions[
                      lb.curselection()[0]]) if lb.curselection() else None]).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.switch_frame(ProfileScreen)).pack()


class WorkshopListFrame(tk.Frame):
    def __init__(self, parent, controller, context):
        super().__init__(parent);
        self.c = controller;
        self.ex = context;
        add_bg(self)
        tk.Label(self, text=context.name, font=FONTS["h1"], bg=COLORS["secondary"]).pack(pady=10)

        d = sorted(list(set(w.date for w in context.workshops)))
        cb = ttk.Combobox(self, values=d, state="readonly");
        cb.current(0);
        cb.pack();
        cb.bind("<<ComboboxSelected>>", self.ref)
        self.cb_ = cb

        self.tv = ttk.Treeview(self, columns=("ID", "Top", "Time", "St"), show="headings")
        self.tv.pack(padx=20, pady=10, fill="x")
        for c in ("ID", "Top", "Time", "St"): self.tv.heading(c, text=c)
        self.ref()

        btn_frame = tk.Frame(self, bg=COLORS["secondary"]);
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Reserve", bg="green", fg="white", font=FONTS["bold"], command=self.res).pack(
            side="left", padx=5)
        tk.Button(btn_frame, text="Cancel Reservation", bg="orange", fg="white", font=FONTS["bold"],
                  command=self.can).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Back", command=lambda: controller.switch_frame(ExhibitionBrowserFrame)).pack(
            side="left", padx=5)

    def ref(self, e=None):
        for i in self.tv.get_children(): self.tv.delete(i)
        for w in self.ex.workshops:
            if w.date == self.cb_.get():
                st = "Reserved" if AppState.current_user.attendee_id in w.attendees_ids else f"{w.get_seats_remaining()} left"
                self.tv.insert("", "end", values=(w.workshop_id, w.topic, f"{w.start_time}-{w.end_time}", st))

    def res(self):
        sel = self.tv.selection()
        if sel:
            r, err = AppState.current_user.reserve_workshop(self.tv.item(sel[0])['values'][0])
            if err:
                messagebox.showerror("Error", err)
            else:
                messagebox.showinfo("Success", "Reserved! You can cancel this later if needed.")
                self.ref()

    def can(self):
        sel = self.tv.selection()
        if not sel: return
        wid = self.tv.item(sel[0])['values'][0]
        res = next((r for r in data_store.reservations if
                    r.workshop_id == wid and r.attendee_id == AppState.current_user.attendee_id and r.status), None)
        if res:
            AppState.current_user.cancel_reservation(res.reservation_id)
            messagebox.showinfo("Cancelled", "Reservation cancelled.")
            self.ref()
        else:
            messagebox.showerror("Error", "You don't have a reservation for this workshop.")


class EditProfileWindow(tk.Toplevel):
    def __init__(self, c, u):
        super().__init__();
        self.title("Edit");
        self.geometry("400x500")
        tk.Label(self, text="Edit Profile", font=FONTS["h2"]).pack(pady=10)
        tk.Label(self, text="Name:");
        n = tk.Entry(self);
        n.insert(0, u.name);
        n.pack()
        tk.Label(self, text="Phone:");
        p = tk.Entry(self);
        p.insert(0, u.phone);
        p.pack()
        tk.Label(self, text="Password:");
        pw = tk.Entry(self);
        pw.insert(0, u.password);
        pw.pack()
        tk.Button(self, text="Save", bg="green", fg="white",
                  command=lambda: [u.update_profile(n.get(), u.email, p.get(), pw.get()), self.destroy()]).pack(pady=20)

        tk.Label(self, text="Danger Zone", fg="red", font=FONTS["bold"]).pack(pady=(20, 5))
        tk.Button(self, text="DELETE ACCOUNT", bg="red", fg="white", command=lambda: self.del_acc(c, u)).pack()

    def del_acc(self, controller, u):
        if messagebox.askyesno("CONFIRM", "Are you sure? This cannot be undone."):
            del data_store.attendees[u.email]
            data_store.save_all()
            self.destroy()
            controller.switch_frame(LoginScreen)
            messagebox.showinfo("Bye", "Account deleted.")


class UpgradeTicketScreen(tk.Frame):
    def __init__(self, parent, controller, context=None):
        super().__init__(parent);
        add_bg(self);
        self.c = controller
        tk.Label(self, text="Upgrade Ticket", font=FONTS["h1"], bg=COLORS["secondary"]).pack(pady=20)
        self.tm = {};
        v = []
        for tid in AppState.current_user.tickets:
            t = next((tk for tk in data_store.tickets if tk.ticket_id == tid), None)
            if t and isinstance(t, ExhibitionPass): v.append(f"ID {t.ticket_id}"); self.tm[f"ID {t.ticket_id}"] = t
        self.cb = ttk.Combobox(self, values=v, state="readonly", width=40);
        self.cb.pack();
        self.cb.bind("<<ComboboxSelected>>", self.os)
        self.ax = ttk.Combobox(self, width=30, state="readonly");
        self.ax.pack(pady=5);
        self.ax.bind("<<ComboboxSelected>>", self.cp)
        self.va = tk.BooleanVar();
        tk.Checkbutton(self, text="Upgrade to All-Access", variable=self.va, command=self.cp).pack()
        self.lp = tk.Label(self, text="Cost: 0", font=FONTS["h2"], bg=COLORS["secondary"]);
        self.lp.pack(pady=10)
        tk.Button(self, text="Pay & Upgrade", bg=COLORS["accent"], fg="white", command=self.dup).pack(pady=10)
        tk.Button(self, text="Back", command=lambda: controller.switch_frame(ProfileScreen)).pack()

    def os(self, e):
        t = self.tm[self.cb.get()]
        av = [e.name for e in data_store.exhibitions if e.name not in t.selected_exhibitions]
        self.ax['values'] = av

    def cp(self, e=None):
        if not self.cb.get(): return
        t = self.tm[self.cb.get()]
        c = (500 - t.price) if self.va.get() else 200
        self.cost = c;
        self.lp.config(text=f"Cost: AED {c}")

    def dup(self):
        if not self.cb.get(): return
        t = self.tm[self.cb.get()]
        nt = TicketType.AllAccessPass if self.va.get() else TicketType.ExhibitionPass
        add = [self.ax.get()] if self.ax.get() and not self.va.get() else None
        t, err = AppState.current_user.upgrade_ticket(t.ticket_id, nt, float(self.cost), add)
        if err:
            messagebox.showerror("Error", err)
        else:
            messagebox.showinfo("Success", "Upgraded"); self.c.switch_frame(ProfileScreen)


# --- ADMIN ---
class AdminDashboard(tk.Frame):
    def __init__(self, parent, controller, context=None):
        super().__init__(parent);
        self.controller = controller;
        add_bg(self)

        h = tk.Frame(self, bg="#333", height=60);
        h.pack(fill="x")
        tk.Label(h, text="Admin Dashboard", font=FONTS["h2"], bg="#333", fg="white").pack(side="left", padx=20)
        tk.Button(h, text="Logout", bg=COLORS["danger"], fg="white",
                  command=lambda: controller.switch_frame(LoginScreen)).pack(side="right", padx=20)

        c = tk.Frame(self, bg=COLORS["secondary"], padx=20, pady=20);
        c.pack(fill="both", expand=True)
        tabs = ttk.Notebook(c);
        tabs.pack(fill="both", expand=True)
        self.t1 = tk.Frame(tabs, bg="white");
        tabs.add(self.t1, text=" All Orders ");
        self.build_orders()
        self.t2 = tk.Frame(tabs, bg="white");
        tabs.add(self.t2, text=" Analytics ");
        self.build_analytics()
        self.t3 = tk.Frame(tabs, bg="white");
        tabs.add(self.t3, text=" Capacity ");
        self.build_capacity()

    def build_orders(self):
        head = tk.Frame(self.t1, bg="#ddd", pady=5);
        head.pack(fill="x")
        cols = ["ID", "Date", "Customer", "Ticket", "Price", "Actions"]
        wds = [10, 15, 25, 20, 10, 30]
        for i, t in enumerate(cols): tk.Label(head, text=t, width=wds[i], font=("Arial", 10, "bold"), bg="#ddd",
                                              anchor="w").grid(row=0, column=i, padx=5)

        can = tk.Canvas(self.t1, bg="white");
        frm = tk.Frame(can, bg="white")
        scr = tk.Scrollbar(self.t1, orient="vertical", command=can.yview);
        can.configure(yscrollcommand=scr.set);
        scr.pack(side="right", fill="y")
        can.pack(side="left", fill="both", expand=True);
        can.create_window((0, 0), window=frm, anchor="nw")
        frm.bind("<Configure>", lambda e: can.configure(scrollregion=can.bbox("all")))

        tot = 0
        for t in data_store.tickets:
            tot += t.price
            u = next((u for u in data_store.attendees.values() if u.attendee_id == t.attendee_id), None)
            em = u.email if u else "Unknown"
            desc = "All Access" if t.ticket_type == TicketType.AllAccessPass else "Exhibition Pass"
            r = tk.Frame(frm, bg="white", pady=5, borderwidth=1, relief="solid");
            r.pack(fill="x", pady=2)
            tk.Label(r, text=t.ticket_id, width=wds[0], anchor="w").grid(row=0, column=0, padx=5)
            tk.Label(r, text=t.purchase_date, width=wds[1], anchor="w").grid(row=0, column=1, padx=5)
            tk.Label(r, text=em, width=wds[2], anchor="w").grid(row=0, column=2, padx=5)
            tk.Label(r, text=desc, width=wds[3], anchor="w").grid(row=0, column=3, padx=5)
            tk.Label(r, text=f"{t.price}", width=wds[4], anchor="w").grid(row=0, column=4, padx=5)
            af = tk.Frame(r);
            af.grid(row=0, column=5, padx=5)

            # --- RESTORED BUTTONS ---
            tk.Button(af, text="Modify", font=("Arial", 8), command=lambda t=t: self.mod(t)).pack(side="left", padx=5)
            tk.Button(af, text="Del", font=("Arial", 8), bg="#ffcccc", command=lambda t=t: self.dele(t)).pack(
                side="left", padx=5)
            tk.Button(af, text="View Pass", font=("Arial", 8),
                      command=lambda t=t, u=u: ViewPassWindow(self.controller, t, u)).pack(side="left", padx=5)

        tk.Label(self.t1, text=f"Total Sales: AED {tot}", font=FONTS["h2"], bg="#eee").pack(side="bottom", anchor="w",
                                                                                            padx=20, pady=10)

    def mod(self, ticket):
        top = tk.Toplevel(self);
        top.title(f"Modify Ticket {ticket.ticket_id}");
        top.geometry("300x250");
        add_bg(top)
        tk.Label(top, text="Ticket Type:", bg=COLORS["secondary"]).pack(pady=5)
        type_var = tk.StringVar(value=ticket.ticket_type.name)
        cb = ttk.Combobox(top, textvariable=type_var, values=["ExhibitionPass", "AllAccessPass"]);
        cb.pack(pady=5)
        tk.Label(top, text="Price (AED):", bg=COLORS["secondary"]).pack(pady=5)
        price_ent = tk.Entry(top);
        price_ent.insert(0, str(ticket.price));
        price_ent.pack(pady=5)

        def save():
            try:
                new_p = float(price_ent.get())
                new_t_str = type_var.get()
                new_t = TicketType[new_t_str]
                ticket.price = new_p
                ticket.ticket_type = new_t
                if new_t == TicketType.ExhibitionPass and not hasattr(ticket, 'selected_exhibitions'):
                    ticket.selected_exhibitions = [e.name for e in data_store.exhibitions]
                data_store.save_all()
                self.controller.switch_frame(AdminDashboard)
                top.destroy()
                messagebox.showinfo("Success", "Ticket updated.")
            except ValueError:
                messagebox.showerror("Error", "Invalid Price")

        tk.Button(top, text="Save Changes", command=save, bg=COLORS["primary"], fg="white").pack(pady=20)

    def dele(self, t):
        if messagebox.askyesno("Confirm", "Delete this ticket?"):
            u = next((u for u in data_store.attendees.values() if u.attendee_id == t.attendee_id), None)
            if u: u.refund_ticket(t.ticket_id)
            self.controller.switch_frame(AdminDashboard)

    def build_analytics(self):
        tv = ttk.Treeview(self.t2, columns=("Type", "Count", "Revenue"), show="headings")
        for c in ("Type", "Count", "Revenue"): tv.heading(c, text=c)
        tv.pack(fill="both", expand=True, padx=20, pady=20)
        c = defaultdict(int);
        r = defaultdict(float)
        for t in data_store.tickets:
            k = "All Access" if t.ticket_type == TicketType.AllAccessPass else "Exhibition"
            c[k] += 1;
            r[k] += t.price
        for k in c: tv.insert("", "end", values=(k, c[k], f"AED {r[k]}"))

    def build_capacity(self):
        top = tk.Frame(self.t3, bg="white");
        top.pack(pady=10)
        d = sorted(list(set(w.date for w in data_store.workshops.values())))
        self.cb = ttk.Combobox(top, values=d, state="readonly");
        self.cb.current(0);
        self.cb.pack(side="left")
        self.cb.bind("<<ComboboxSelected>>", self.ref_cap)
        tk.Button(top, text="Refresh", command=lambda: [data_store.load_all(), self.ref_cap()]).pack(side="left",
                                                                                                     padx=10)
        self.cf = tk.Frame(self.t3, bg="white");
        self.cf.pack(fill="both", expand=True, padx=20)
        self.ref_cap()

    def ref_cap(self, e=None):
        for w in self.cf.winfo_children(): w.destroy()
        d = self.cb.get()
        for w in [x for x in data_store.workshops.values() if x.date == d]:
            r = tk.Frame(self.cf, pady=5, bg="white");
            r.pack(fill="x")
            tk.Label(r, text=f"{w.topic} ({w.start_time})", width=40, anchor="w", bg="white").pack(side="left")
            p = (len(w.attendees_ids) / w.capacity) * 100
            ttk.Progressbar(r, length=200, value=p).pack(side="left", padx=10)
            tk.Label(r, text=f"{len(w.attendees_ids)}/{w.capacity} Booked", bg="white").pack(side="left")


# --- UTILS ---
class ScheduleWindow(tk.Toplevel):
    def __init__(self, c, u):
        super().__init__();
        self.title("Schedule");
        self.geometry("700x400")
        tv = ttk.Treeview(self, columns=("Topic", "Date", "Time", "Loc"), show="headings")
        for x in ("Topic", "Date", "Time", "Loc"): tv.heading(x, text=x)
        tv.pack(fill="both", expand=True)
        for r in data_store.reservations:
            if r.attendee_id == u.attendee_id and r.status:
                ws = data_store.workshops.get(r.workshop_id)
                tv.insert("", "end", values=(ws.topic, ws.date, f"{ws.start_time}-{ws.end_time}", ws.exhibition_name))


class TicketManagerWindow(tk.Toplevel):
    def __init__(self, c, u):
        super().__init__();
        self.title("My Tickets");
        self.geometry("500x500")
        fr = tk.Frame(self);
        fr.pack(fill="both", expand=True)
        for tid in u.tickets:
            t = next((x for x in data_store.tickets if x.ticket_id == tid), None)
            if t:
                cf = tk.Frame(fr, relief="groove", bd=2, pady=5);
                cf.pack(fill="x", padx=10, pady=5)
                lbl = "All Access" if t.ticket_type == TicketType.AllAccessPass else "Exhibition Pass"
                tk.Label(cf, text=f"{lbl} (ID {t.ticket_id})", font=FONTS["bold"]).pack(anchor="w")
                tk.Button(cf, text="View Pass", command=lambda t=t: ViewPassWindow(c, t, u)).pack(side="left")
                if t.ticket_type != TicketType.AllAccessPass: tk.Button(cf, text="Upgrade",
                                                                        command=lambda: [self.destroy(), c.switch_frame(
                                                                            UpgradeTicketScreen)]).pack(side="left")
                tk.Button(cf, text="Refund", bg="red", fg="white",
                          command=lambda t=t: [u.refund_ticket(t.ticket_id), self.destroy()]).pack(side="right")


class ViewPassWindow(tk.Toplevel):
    def __init__(self, p, t, u):
        super().__init__();
        self.title("Pass");
        self.configure(bg="white");
        self.geometry("550x700")
        c = tk.Canvas(self, bg="white", width=510, height=700, highlightthickness=0);
        c.pack(pady=20)
        c.create_text(255, 30, text="GREENWAVE CONFERENCE 2026", font=("Courier", 16, "bold"), fill="green")
        c.create_text(255, 60, text="OFFICIAL PASS", font=("Courier", 14, "bold"))
        y = 100;
        tp = "All-Access" if t.ticket_type == TicketType.AllAccessPass else "Exhibition Pass"
        c.create_text(30, y, text=f"TYPE: {tp}", anchor="w", font=("Courier", 12, "bold"));
        c.create_text(480, y, text=f"ID: {t.ticket_id}", anchor="e", font=("Courier", 12, "bold"))
        y += 30;
        c.create_text(30, y, text=f"HOLDER: {u.name}", anchor="w", font=("Courier", 10));
        c.create_text(480, y, text=f"DATE: {t.purchase_date}", anchor="e", font=("Courier", 10))
        y += 20;
        c.create_line(30, y, 480, y);
        y += 30;
        c.create_text(30, y, text="ACCESS:", anchor="w", font=("Courier", 12, "bold"))
        y += 20;
        exs = [e.name for e in
               data_store.exhibitions] if t.ticket_type == TicketType.AllAccessPass else t.selected_exhibitions
        for e in exs: c.create_text(50, y, text=f"- {e}", anchor="w", font=("Courier", 10)); y += 20
        y += 10;
        c.create_text(30, y, text="WORKSHOPS:", anchor="w", font=("Courier", 12, "bold"));
        y += 20
        has = False
        for r in data_store.reservations:
            if r.attendee_id == u.attendee_id and r.status:
                ws = data_store.workshops.get(r.workshop_id)
                if ws: c.create_text(50, y, text=f"- {ws.topic}", anchor="w", font=("Courier", 10)); y += 20; has = True
        if not has: c.create_text(50, y, text="- None", anchor="w", font=("Courier", 10)); y += 20
        y += 10;
        c.create_line(30, y, 480, y);
        y += 30;
        c.create_text(30, y, text=f"PRICE: AED {t.price}", anchor="w", font=("Courier", 12, "bold"))


if __name__ == "__main__":
    app = GreenWaveApp()
    app.mainloop()