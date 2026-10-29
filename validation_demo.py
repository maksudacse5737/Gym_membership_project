# validation_demo.py
# Task 5 - Shows each validation rule (V1 to V12) working in the console.
# Author: Maksuda Rahman Anti (69214)
# Run with:  python validation_demo.py   then take a screenshot of the output.

import datetime
from main import GymSystem, Booking, ClassStatus
import validation as v


def show(rule, result):
    """Print one line: the rule number, PASS/REFUSED and the message."""
    ok, message = result[0], result[1]
    print(f"{rule:<4} {'PASS   ' if ok else 'REFUSED'}  {message}")


system = GymSystem()
system.preload_data()
alice = system.members["M01"]
bob = system.members["M02"]
admin = system.members["A01"]
yoga = system.classes["C05"]          # Evening Gentle Yoga, 5 places
now = datetime.datetime.now()

print("=== Input validation evidence (rules from Part A, Table 9) ===")

# V1 - fill the class, then try one more booking
for i in range(yoga.capacity):
    yoga.add_booking(Booking(f"F{i}", admin, yoga, 5.0))
show("V1", v.check_booking_allowed(alice, yoga))

# V2 - Alice books HIIT, then tries again
system.book_class("M01", "C03")
show("V2", v.check_booking_allowed(alice, system.classes["C03"]))

# V3 - suspended membership
bob.membership.suspend()
show("V3", v.check_booking_allowed(bob, system.classes["C01"]))
bob.membership.reactivate()

# V4 - pretend today is in 2027, after the membership ended
show("V4", v.check_booking_allowed(bob, system.classes["C01"],
                                   now=datetime.datetime(2027, 1, 5, 9, 0)))

# V5 - cancelled class
system.classes["C04"].status = ClassStatus.CANCELLED
show("V5", v.check_booking_allowed(bob, system.classes["C04"]))

# V6 - class already started
system.classes["C02"].start_time = now - datetime.timedelta(hours=1)
show("V6", v.check_booking_allowed(bob, system.classes["C02"]))

show("V7", v.check_capacity(50))
show("V8", v.check_fee(-5))

c1 = system.classes["C01"]
show("V9", v.check_trainer_free(c1.trainer, c1.start_time, 45, system.classes.values()))

found = system.search_class_by_id("X99")
show("V10", (found is not None, "No class was found with ID 'X99'."))

show("V11", v.check_can_mark_attended(bob, system.classes["C03"]))
show("V12", v.check_admin_access(admin, "0000"))
show("V12", v.check_admin_access(alice, "1234"))
show("OK", v.check_admin_access(admin, "1234"))

print("\n=== Keyboard input: type bad values first, then a good one ===")
capacity = v.read_int_in_range("Enter class capacity (1-30): ", 1, 30)
price = v.read_positive_float("Enter class price: $")
date = v.read_date("Enter report start date (DD/MM/YYYY): ")
class_id = v.read_existing_id("Enter class ID to search: ", system.classes, "class")
print(f"Accepted -> capacity {capacity}, price ${price:.2f}, date {date:%d/%m/%Y}, class {class_id}")
