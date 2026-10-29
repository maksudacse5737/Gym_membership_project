# validation.py
# Task 5 - Input validation for the Gym Membership and Class Booking System
# Author: Maksuda Rahman Anti (69214)
#
# This file has two kinds of functions:
#   1. read_...()  functions ask the user for input and keep asking until the
#      input is valid. They never crash the program on bad input.
#   2. check_...() functions test one business rule and return a pair
#      (True/False, message). Because they do not use input(), they are easy
#      to unit test.
# The rule numbers V1 to V12 match Table 9 in our Part A design.

import datetime
from main import Admin, BookingStatus, ClassStatus

DATE_FORMAT = "%d/%m/%Y"   # dates are typed as DD/MM/YYYY, e.g. 28/10/2026


# ---------------------------------------------------------------
# PART 1: Reading keyboard input safely
# ---------------------------------------------------------------

def read_text(prompt):
    """Ask until the user types something that is not empty."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Error: this field cannot be empty. Please try again.")


def read_int_in_range(prompt, low, high):
    """Ask until the user types a whole number between low and high."""
    while True:
        value = input(prompt).strip()
        try:
            number = int(value)
        except ValueError:
            print(f"Error: '{value}' is not a whole number. Please try again.")
            continue
        if low <= number <= high:
            return number
        print(f"Error: please enter a number from {low} to {high}.")


def read_positive_float(prompt):
    """Ask until the user types a number greater than 0 (used for prices)."""
    while True:
        value = input(prompt).strip()
        try:
            number = float(value)
        except ValueError:
            print(f"Error: '{value}' is not a valid amount. Please try again.")
            continue
        if number > 0:
            return number
        print("Error: the amount must be more than $0.")


def read_date(prompt):
    """Ask until the user types a real date in DD/MM/YYYY format."""
    while True:
        value = input(prompt).strip()
        try:
            return datetime.datetime.strptime(value, DATE_FORMAT).date()
        except ValueError:
            print(f"Error: '{value}' is not a valid date. Use DD/MM/YYYY.")


def read_existing_id(prompt, collection, label):
    """V10 - ask until the user types an ID that exists in the collection.
    Typing 0 cancels and returns None so the user is never stuck."""
    while True:
        value = input(prompt).strip().upper()
        if value == "0":
            return None
        if value in collection:
            return value
        print(f"Error: no {label} was found with ID '{value}'. "
              f"Try again or type 0 to go back.")


# ---------------------------------------------------------------
# PART 2: Business rule checks (return True/False and a message)
# ---------------------------------------------------------------

def check_capacity(capacity):
    """V7 - capacity must be a whole number between 1 and 30."""
    if not isinstance(capacity, int) or not (1 <= capacity <= 30):
        return False, "Capacity must be a whole number between 1 and 30."
    return True, "Capacity is valid."


def check_fee(fee):
    """V8 - a price must be more than $0."""
    if not isinstance(fee, (int, float)) or fee <= 0:
        return False, "The price must be more than $0."
    return True, "Price is valid."


def check_date_range(start_date, end_date):
    """Report dates: the start date cannot be after the end date."""
    if start_date > end_date:
        return False, "The start date cannot be after the end date."
    return True, "Date range is valid."


def check_booking_allowed(member, fitness_class, now=None):
    """Runs every booking rule in order and stops at the first problem.
    Covers V1 to V6 from Table 9."""
    if now is None:
        now = datetime.datetime.now()

    membership = member.membership
    if membership is None:
        return False, "This member does not have a membership."
    if membership.is_suspended:                                   # V3
        return False, "Booking refused: the membership is suspended."
    if not membership.is_active(now.date()):                      # V4
        return False, "Booking refused: the membership has expired. Please renew."

    if fitness_class.status == ClassStatus.FULL or not fitness_class.has_space():
        return False, "Booking refused: the class is full."       # V1
    if fitness_class.status != ClassStatus.OPEN:                  # V5
        return False, (f"Booking refused: the class is "
                       f"{fitness_class.status.value}.")
    if fitness_class.start_time <= now:                           # V6
        return False, "Booking refused: the class has already started."

    for booking in fitness_class.bookings:                        # V2
        if (booking.member.member_id == member.member_id
                and booking.status == BookingStatus.BOOKED):
            return False, "Booking refused: the member is already booked in this class."

    return True, "All booking checks passed."


def check_trainer_free(trainer, start_time, duration_min, classes):
    """V9 - one trainer cannot run two classes that overlap in time.
    'classes' is the list of classes that already exist."""
    end_time = start_time + datetime.timedelta(minutes=duration_min)
    for other in classes:
        if other.trainer is not trainer or other.status == ClassStatus.CANCELLED:
            continue
        other_end = other.start_time + datetime.timedelta(minutes=other.duration_min)
        if start_time < other_end and other.start_time < end_time:
            return False, (f"{trainer.full_name} is already teaching "
                           f"{other.title} at that time.")
    return True, "Trainer is available."


def check_can_mark_attended(member, fitness_class):
    """V11 - attendance can only be marked for a member with an active booking.
    Returns (True/False, message, booking or None)."""
    for booking in fitness_class.bookings:
        if (booking.member.member_id == member.member_id
                and booking.status == BookingStatus.BOOKED):
            return True, "Booking found.", booking
    return False, "No active booking was found for this member in this class.", None


def check_admin_access(user, pin):
    """V12 - only an Admin object with the right PIN can open admin tools.
    isinstance() works because Admin inherits from Member."""
    if not isinstance(user, Admin):
        return False, "Access denied: this account is not a staff account."
    if not user.verify_pin(pin):
        return False, "Access denied: the PIN is incorrect."
    return True, "Access granted."
