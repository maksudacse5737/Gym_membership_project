import datetime
from abc import ABC, abstractmethod
from enum import Enum


# ENUMERATIONS (Controlled Attributes)

class ClassCategory(Enum):
    YOGA = "Yoga"
    PILATES = "Pilates"
    SPIN = "Spin"
    HIIT = "HIIT"


class ClassStatus(Enum):
    OPEN = "Open"
    FULL = "Full"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"


class BookingStatus(Enum):
    BOOKED = "Booked"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"



# SUPPORTING: MEMBERSHIP BASE & SUBCLASSES

class Membership(ABC):
    def __init__(self, membership_id: str, start_date: datetime.date, end_date: datetime.date, auto_renew: bool = False):
        self._membership_id = membership_id
        self._start_date = start_date
        self._end_date = end_date
        self._is_suspended = False
        self._auto_renew = auto_renew

    @property
    def membership_id(self) -> str:
        return self._membership_id

    @property
    def is_suspended(self) -> bool:
        return self._is_suspended

    def suspend(self):
        self._is_suspended = True

    def reactivate(self):
        self._is_suspended = False

    def is_active(self, on_date: datetime.date = None) -> bool:
        if on_date is None:
            on_date = datetime.date.today()
        if self._is_suspended:
            return False
        return self._start_date <= on_date <= self._end_date

    @abstractmethod
    def calculate_fee(self) -> float:
        pass

    @abstractmethod
    def get_class_discount(self) -> float:
        pass


class MonthlyMembership(Membership):
    def __init__(self, membership_id: str, start_date: datetime.date, end_date: datetime.date, auto_renew: bool = False):
        super().__init__(membership_id, start_date, end_date, auto_renew)
        self.monthly_fee = 60.00
        self.discount_rate = 0.00

    def calculate_fee(self) -> float:
        return self.monthly_fee

    def get_class_discount(self) -> float:
        return self.discount_rate


class YearlyMembership(Membership):
    def __init__(self, membership_id: str, start_date: datetime.date, end_date: datetime.date, auto_renew: bool = False):
        super().__init__(membership_id, start_date, end_date, auto_renew)
        self.annual_fee = 600.00
        self.discount_rate = 0.50

    def calculate_fee(self) -> float:
        return self.annual_fee

    def get_class_discount(self) -> float:
        return self.discount_rate

class Trainer:
    def __init__(self, trainer_id: str, full_name: str, email: str, phone: str, specialty: str, is_active: bool = True):
        self.trainer_id = trainer_id
        self.full_name = full_name
        self.email = email
        self.phone = phone
        self.specialty = specialty
        self.is_active = is_active


class FitnessClass:
    def __init__(self, class_id: str, title: str, category: ClassCategory, start_time: datetime.datetime, duration_min: int, capacity: int, base_fee: float, room_name: str, trainer: Trainer = None):
        if not (1 <= capacity <= 30):
            raise ValueError("Capacity must be between 1 and 30.")
        if base_fee <= 0:
            raise ValueError("Base fee must be greater than 0.")

        self.class_id = class_id
        self.title = title
        self.category = category
        self.start_time = start_time
        self.duration_min = duration_min
        self.capacity = capacity
        self.base_fee = base_fee
        self.room_name = room_name
        self.trainer = trainer
        self.status = ClassStatus.OPEN
        self.bookings = []

    def available_spaces(self) -> int:
        active_bookings = [b for b in self.bookings if b.status == BookingStatus.BOOKED]
        return self.capacity - len(active_bookings)

    def has_space(self) -> bool:
        return self.available_spaces() > 0

    def add_booking(self, booking) -> bool:
        if not self.has_space() or self.status != ClassStatus.OPEN:
            return False
        self.bookings.append(booking)
        if self.available_spaces() == 0:
            self.status = ClassStatus.FULL
        return True

    def remove_booking(self, booking) -> bool:
        if booking in self.bookings:
            self.bookings.remove(booking)
            if self.available_spaces() > 0 and self.status == ClassStatus.FULL:
                self.status = ClassStatus.OPEN
            return True
        return False

    def get_calculated_fee(self, member) -> float:
        if member.membership:
            discount = member.membership.get_class_discount()
            return self.base_fee * (1.0 - discount)
        return self.base_fee


class Member:
    def __init__(self, member_id: str, full_name: str, email: str, phone: str, joined_on: datetime.date, emergency_contact: str, membership: Membership = None):
        self._member_id = member_id
        self._full_name = full_name
        self._email = email
        self._phone = phone
        self._joined_on = joined_on
        self._emergency_contact = emergency_contact
        self._membership = membership

    @property
    def member_id(self) -> str:
        return self._member_id

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def email(self) -> str:
        return self._email

    @property
    def membership(self) -> Membership:
        return self._membership

    @membership.setter
    def membership(self, value: Membership):
        self._membership = value

    def is_eligible_to_book(self, on_date: datetime.date = None) -> bool:
        if self._membership is None:
            return False
        return self._membership.is_active(on_date)

    def get_details(self) -> str:
        status = "Active" if (self._membership and self._membership.is_active()) else "Inactive/Suspended"
        m_type = type(self._membership).__name__ if self._membership else "None"
        return f"Member ID: {self._member_id} | Name: {self._full_name} | Email: {self._email} | Type: {m_type} | Status: {status}"



# 3. STAFF / ADMIN ROLE: Admin (Inherits from Member)

class Admin(Member):
    def __init__(self, member_id: str, full_name: str, email: str, phone: str, joined_on: datetime.date, emergency_contact: str, employee_id: str, pin_hash: str, membership: Membership = None):
        super().__init__(member_id, full_name, email, phone, joined_on, emergency_contact, membership)
        self._employee_id = employee_id
        self._pin_hash = pin_hash
        self._is_enabled = True

    def verify_pin(self, pin: str) -> bool:
        return pin == self._pin_hash and self._is_enabled

    def get_details(self) -> str:
        base_details = super().get_details()
        return f"[ADMIN] {base_details} | Emp ID: {self._employee_id}"



# 4. TRANSACTION ROLE: Booking

class Booking:
    def __init__(self, booking_id: str, member: Member, fitness_class: FitnessClass, fee_paid: float, created_at: datetime.datetime = None):
        self.booking_id = booking_id
        self.member = member
        self.fitness_class = fitness_class
        self.fee_paid = fee_paid
        self.created_at = created_at if created_at else datetime.datetime.now()
        self.status = BookingStatus.BOOKED
        self.attended = False
        self.attended_at = None
        self.cancelled_at = None
        self.notes = ""

    def mark_attended(self) -> bool:
        if self.status == BookingStatus.BOOKED:
            self.attended = True
            self.attended_at = datetime.datetime.now()
            self.status = BookingStatus.COMPLETED
            return True
        return False

    def cancel(self) -> bool:
        if self.status == BookingStatus.BOOKED:
            self.status = BookingStatus.CANCELLED
            self.cancelled_at = datetime.datetime.now()
            self.fitness_class.remove_booking(self)
            return True
        return False

    def get_details(self) -> str:
        att_str = "Yes" if self.attended else "No"
        return f"Booking #{self.booking_id} | Member: {self.member.full_name} | Class: {self.fitness_class.title} | Fee: ${self.fee_paid:.2f} | Status: {self.status.value} | Attended: {att_str}"


# 5. SYSTEM / MANAGER ROLE: GymSystem

class GymSystem:
    def __init__(self, gym_name: str = "VIT Fitness Hub"):
        self.gym_name = gym_name
        self.members = {}
        self.classes = {}
        self.trainers = {}
        self.bookings = {}
        self._next_booking_id = 1001

# Task3 Data Preload method 

import datetime

class GymSystem:
   

    def preload_data(self):
        """
        Task 3: On program start, instantiates at least:
        1. 5 Item/Asset objects (FitnessClass)
        2. 3 User/Customer objects (Member / Admin)
        """
        print("[System] Preloading initial system data...")

        # Preload Supporting Trainers
        t1 = Trainer("T01", "John Doe", "john@gym.com", "0412345678", "Yoga & Pilates")
        t2 = Trainer("T02", "Sarah Smith", "sarah@gym.com", "0487654321", "HIIT & Spin")
        self.trainers[t1.trainer_id] = t1
        self.trainers[t2.trainer_id] = t2

        # 1. Instantiate 3 User / Customer Objects 
        
        # User 1: Regular Member with Monthly Membership
        m1 = Member("M01", "Alice Johnson", "alice@example.com", "0400111222", datetime.date(2025, 1, 1), "0400000000")
        m1.membership = MonthlyMembership("MS01", datetime.date(2026, 1, 1), datetime.date(2026, 12, 31))

        # User 2: Regular Member with Yearly Membership
        m2 = Member("M02", "Bob Williams", "bob@example.com", "0400333444", datetime.date(2025, 3, 15), "0400000000")
        m2.membership = YearlyMembership("MS02", datetime.date(2026, 1, 1), datetime.date(2026, 12, 31))

        # User 3: Staff / Admin Object (inherits from Member)
        admin1 = Admin("A01", "Charlie Admin", "admin@gym.com", "0400999888", datetime.date(2024, 1, 1), "0400000000", "EMP01", "1234")
        admin1.membership = YearlyMembership("MS03", datetime.date(2026, 1, 1), datetime.date(2026, 12, 31))

        self.members[m1.member_id] = m1
        self.members[m2.member_id] = m2
        self.members[admin1.member_id] = admin1

     
        # 2. Instantiate 5 Item / Asset Objects (Requirement met)
       
        now = datetime.datetime.now()
        
        c1 = FitnessClass("C01", "Morning Flow Yoga", ClassCategory.YOGA, now + datetime.timedelta(days=1, hours=2), 60, 10, 10.00, "Studio A", t1)
        c2 = FitnessClass("C02", "Power Pilates", ClassCategory.PILATES, now + datetime.timedelta(days=2, hours=3), 45, 12, 12.00, "Studio B", t1)
        c3 = FitnessClass("C03", "HIIT Burnout", ClassCategory.HIIT, now + datetime.timedelta(days=1, hours=5), 45, 8, 15.00, "Main Gym", t2)
        c4 = FitnessClass("C04", "Express Spin", ClassCategory.SPIN, now + datetime.timedelta(days=3, hours=1), 30, 15, 14.00, "Spin Room", t2)
        c5 = FitnessClass("C05", "Evening Gentle Yoga", ClassCategory.YOGA, now + datetime.timedelta(days=4, hours=4), 60, 5, 10.00, "Studio A", t1)

        for c in [c1, c2, c3, c4, c5]:
            self.classes[c.class_id] = c

        print(f"[System] Successfully preloaded {len(self.members)} users and {len(self.classes)} fitness classes.") 