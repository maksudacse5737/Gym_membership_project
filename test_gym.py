# test_gym.py
# Task 5 - Unit tests for the Gym Membership and Class Booking System
# Author: Maksuda Rahman Anti (69214)
#
# Run in the VS Code terminal with:   python -m unittest -v test_gym
#
# Each test builds its own small set of objects in setUp(), so the tests do
# not depend on each other and the results are always the same.
# Test IDs (UT01, UT02 ...) match Table 11 in the report.

import datetime
import unittest
from unittest.mock import patch

from main import (Admin, Booking, BookingStatus, ClassCategory, ClassStatus,
                  FitnessClass, GymSystem, Member, MonthlyMembership, Trainer,
                  YearlyMembership)
import validation as v


class GymTestBase(unittest.TestCase):
    """Shared test data used by every test class below."""

    def setUp(self):
        self.now = datetime.datetime.now()
        today = self.now.date()
        start = today - datetime.timedelta(days=30)
        end = today + datetime.timedelta(days=335)

        self.trainer = Trainer("T01", "John Doe", "john@gym.com", "0412345678", "Yoga")

        self.alice = Member("M01", "Alice Johnson", "alice@example.com", "0400111222",
                            start, "0400000000")
        self.alice.membership = MonthlyMembership("MS01", start, end)

        self.bob = Member("M02", "Bob Williams", "bob@example.com", "0400333444",
                          start, "0400000000")
        self.bob.membership = YearlyMembership("MS02", start, end)

        self.admin = Admin("A01", "Charlie Admin", "admin@gym.com", "0400999888",
                           start, "0400000000", "EMP01", "1234")

        # A Yoga class tomorrow with only 2 places, so "full" is easy to test
        self.yoga = FitnessClass("C01", "Morning Flow Yoga", ClassCategory.YOGA,
                                 self.now + datetime.timedelta(days=1), 60, 2,
                                 10.00, "Studio A", self.trainer)
        self.hiit = FitnessClass("C03", "HIIT Burnout", ClassCategory.HIIT,
                                 self.now + datetime.timedelta(days=2), 45, 8,
                                 15.00, "Main Gym", self.trainer)

    def make_booking(self, member, fitness_class, booking_id="B1"):
        """Helper: create a booking and add it to the class."""
        booking = Booking(booking_id, member, fitness_class,
                          fitness_class.get_calculated_fee(member))
        fitness_class.add_booking(booking)
        return booking


# ---------------------------------------------------------------
# 1. Fee calculation (polymorphism: each membership gives its own discount)
# ---------------------------------------------------------------
class TestFeeCalculation(GymTestBase):

    def test_ut01_monthly_member_pays_full_price(self):
        self.assertAlmostEqual(self.yoga.get_calculated_fee(self.alice), 10.00)

    def test_ut02_yearly_member_pays_half_price(self):
        self.assertAlmostEqual(self.hiit.get_calculated_fee(self.bob), 7.50)

    def test_ut03_membership_fees_match_design(self):
        self.assertEqual(self.alice.membership.calculate_fee(), 60.00)
        self.assertEqual(self.bob.membership.calculate_fee(), 600.00)

    def test_ut04_fee_saved_on_booking_does_not_change(self):
        booking = self.make_booking(self.alice, self.yoga)
        self.yoga.base_fee = 20.00            # admin raises the price later
        self.assertAlmostEqual(booking.fee_paid, 10.00)


# ---------------------------------------------------------------
# 2. Search (GymSystem)
# ---------------------------------------------------------------
class TestSearch(GymTestBase):

    def setUp(self):
        super().setUp()
        self.system = GymSystem()
        self.system.preload_data()

    def test_ut05_preload_creates_5_classes_and_3_users(self):
        self.assertGreaterEqual(len(self.system.classes), 5)
        self.assertGreaterEqual(len(self.system.members), 3)

    def test_ut06_search_by_valid_id(self):
        found = self.system.search_class_by_id("C03")
        self.assertIsNotNone(found)
        self.assertEqual(found.title, "HIIT Burnout")

    def test_ut07_search_by_invalid_id_returns_none(self):        # V10
        self.assertIsNone(self.system.search_class_by_id("X99"))

    def test_ut08_search_by_part_of_name(self):
        titles = [c.title for c in self.system.search_classes_by_name("yoga")]
        self.assertEqual(sorted(titles), ["Evening Gentle Yoga", "Morning Flow Yoga"])

    def test_ut09_search_by_category(self):
        found = self.system.search_classes_by_category("Spin")
        self.assertEqual([c.class_id for c in found], ["C04"])


# ---------------------------------------------------------------
# 3. Creating, cancelling and completing bookings (transactions)
# ---------------------------------------------------------------
class TestBookingRules(GymTestBase):

    def test_ut10_valid_booking_is_allowed(self):
        ok, _ = v.check_booking_allowed(self.alice, self.yoga)
        self.assertTrue(ok)

    def test_ut11_class_becomes_full_and_refuses_more(self):    # V1
        self.make_booking(self.alice, self.yoga, "B1")
        self.make_booking(self.bob, self.yoga, "B2")
        self.assertEqual(self.yoga.status, ClassStatus.FULL)
        ok, message = v.check_booking_allowed(self.admin_with_membership(), self.yoga)
        self.assertFalse(ok)
        self.assertIn("full", message)

    def test_ut12_same_member_cannot_book_twice(self):          # V2
        self.make_booking(self.alice, self.hiit)
        ok, message = v.check_booking_allowed(self.alice, self.hiit)
        self.assertFalse(ok)
        self.assertIn("already booked", message)

    def test_ut13_suspended_member_cannot_book(self):           # V3
        self.alice.membership.suspend()
        ok, message = v.check_booking_allowed(self.alice, self.yoga)
        self.assertFalse(ok)
        self.assertIn("suspended", message)

    def test_ut14_expired_member_cannot_book(self):             # V4
        old = datetime.date(2024, 1, 1)
        self.alice.membership = MonthlyMembership("MS09", old, datetime.date(2024, 1, 31))
        ok, message = v.check_booking_allowed(self.alice, self.yoga)
        self.assertFalse(ok)
        self.assertIn("expired", message)

    def test_ut15_cancelled_class_cannot_be_booked(self):       # V5
        self.yoga.status = ClassStatus.CANCELLED
        ok, message = v.check_booking_allowed(self.alice, self.yoga)
        self.assertFalse(ok)
        self.assertIn("Cancelled", message)

    def test_ut16_class_that_started_cannot_be_booked(self):    # V6
        self.yoga.start_time = self.now - datetime.timedelta(hours=1)
        ok, message = v.check_booking_allowed(self.alice, self.yoga)
        self.assertFalse(ok)
        self.assertIn("already started", message)

    def test_ut17_cancel_frees_a_place_and_reopens_class(self):
        b1 = self.make_booking(self.alice, self.yoga, "B1")
        self.make_booking(self.bob, self.yoga, "B2")
        self.assertTrue(b1.cancel())
        self.assertEqual(b1.status, BookingStatus.CANCELLED)
        self.assertEqual(self.yoga.status, ClassStatus.OPEN)
        self.assertEqual(self.yoga.available_spaces(), 1)

    def test_ut18_cancelled_booking_cannot_be_cancelled_again(self):
        booking = self.make_booking(self.alice, self.hiit)
        booking.cancel()
        self.assertFalse(booking.cancel())

    def test_ut19_mark_attended_completes_booking(self):        # V11
        self.make_booking(self.alice, self.hiit)
        ok, _, booking = v.check_can_mark_attended(self.alice, self.hiit)
        self.assertTrue(ok)
        self.assertTrue(booking.mark_attended())
        self.assertEqual(booking.status, BookingStatus.COMPLETED)

    def test_ut20_cannot_mark_attendance_without_booking(self): # V11
        ok, message, booking = v.check_can_mark_attended(self.bob, self.hiit)
        self.assertFalse(ok)
        self.assertIsNone(booking)

    def admin_with_membership(self):
        """Helper: give the admin a valid membership so only 'full' can fail."""
        self.admin.membership = YearlyMembership(
            "MS03", self.now.date() - datetime.timedelta(days=1),
            self.now.date() + datetime.timedelta(days=300))
        return self.admin


# ---------------------------------------------------------------
# 4. Admin-only rules and data entry rules
# ---------------------------------------------------------------
class TestAdminAndDataRules(GymTestBase):

    def test_ut21_capacity_boundaries(self):                    # V7
        self.assertTrue(v.check_capacity(1)[0])
        self.assertTrue(v.check_capacity(30)[0])
        self.assertFalse(v.check_capacity(0)[0])
        self.assertFalse(v.check_capacity(31)[0])

    def test_ut22_class_with_bad_capacity_is_rejected(self):    # V7
        with self.assertRaises(ValueError):
            FitnessClass("C99", "Too Big", ClassCategory.SPIN, self.now, 30, 50,
                         14.00, "Spin Room")

    def test_ut23_negative_price_is_rejected(self):             # V8
        self.assertFalse(v.check_fee(-5)[0])
        self.assertFalse(v.check_fee(0)[0])
        with self.assertRaises(ValueError):
            FitnessClass("C98", "Free Class", ClassCategory.YOGA, self.now, 30, 10,
                         -5, "Studio A")

    def test_ut24_trainer_cannot_teach_two_classes_at_once(self):  # V9
        same_time = self.yoga.start_time + datetime.timedelta(minutes=30)
        ok, _ = v.check_trainer_free(self.trainer, same_time, 45, [self.yoga])
        self.assertFalse(ok)
        later = self.yoga.start_time + datetime.timedelta(minutes=60)
        ok, _ = v.check_trainer_free(self.trainer, later, 45, [self.yoga])
        self.assertTrue(ok)

    def test_ut25_admin_with_correct_pin_gets_access(self):     # V12
        self.assertTrue(v.check_admin_access(self.admin, "1234")[0])

    def test_ut26_wrong_pin_or_normal_member_is_refused(self):  # V12
        self.assertFalse(v.check_admin_access(self.admin, "0000")[0])
        self.assertFalse(v.check_admin_access(self.alice, "1234")[0])

    def test_ut27_admin_details_override(self):                 # polymorphism
        self.assertTrue(self.admin.get_details().startswith("[ADMIN]"))
        self.assertFalse(self.alice.get_details().startswith("[ADMIN]"))

    def test_ut28_report_date_range(self):
        start = datetime.date(2026, 10, 1)
        end = datetime.date(2026, 10, 31)
        self.assertTrue(v.check_date_range(start, end)[0])
        self.assertFalse(v.check_date_range(end, start)[0])


# ---------------------------------------------------------------
# 5. Keyboard input: bad input is refused and the user is asked again
#    patch() types the answers for us, one after another.
# ---------------------------------------------------------------
class TestKeyboardInput(unittest.TestCase):

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["abc", "0", "45", "12"])
    def test_ut29_number_input_asks_again_until_valid(self, _input, _print):
        self.assertEqual(v.read_int_in_range("Capacity: ", 1, 30), 12)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["31/02/2026", "2026-10-28", "28/10/2026"])
    def test_ut30_date_input_asks_again_until_valid(self, _input, _print):
        self.assertEqual(v.read_date("Date: "), datetime.date(2026, 10, 28))

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["-5", "ten", "12.50"])
    def test_ut31_price_input_asks_again_until_valid(self, _input, _print):
        self.assertEqual(v.read_positive_float("Price: "), 12.50)

    @patch("builtins.print")
    @patch("builtins.input", side_effect=["x99", "c02"])
    def test_ut32_unknown_id_asks_again(self, _input, _print):  # V10
        classes = {"C01": None, "C02": None}
        self.assertEqual(v.read_existing_id("Class ID: ", classes, "class"), "C02")


if __name__ == "__main__":
    unittest.main(verbosity=2)
