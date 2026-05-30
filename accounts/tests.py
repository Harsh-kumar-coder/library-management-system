"""
Library Management System - Accounts App Tests
=============================================
Sabhi major features ke liye comprehensive tests
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from books.models import Book, IssuedBook, BookRequest
from accounts.models import Profile
from django.utils import timezone


# ============================================================
#  HELPERS
# ============================================================

def make_admin(username='admin1', password='pass123'):
    u = User.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com',
        is_staff=True, is_superuser=True, is_active=True
    )
    Profile.objects.create(user=u, role='admin')
    return u


def make_staff(username='staff1', password='pass123'):
    u = User.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com',
        is_staff=True, is_active=True
    )
    Profile.objects.create(user=u, role='staff')
    return u


def make_student(username='stu1', password='pass123', active=True):
    u = User.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com',
        first_name=f'ROLL{username}',
        is_active=active
    )
    Profile.objects.create(user=u, role='student')
    return u


def make_book(title='Test Book', quantity=3):
    return Book.objects.create(
        title=title, author='Test Author',
        isbn='ISBN-001', quantity=quantity
    )


# ============================================================
#  REGISTRATION TESTS
# ============================================================

class StudentRegistrationTest(TestCase):

    def test_register_student_success(self):
        """Normal student registration successful honi chahiye"""
        resp = self.client.post(reverse('student_register'), {
            'username': 'newstu',
            'roll_number': 'ROLL001',
            'email': 'newstu@test.com',
            'password': 'pass1234',
            'confirm_password': 'pass1234',
        })
        self.assertRedirects(resp, reverse('login'))
        user = User.objects.get(username='newstu')
        self.assertFalse(user.is_active, "Student inactive hona chahiye pending approval")
        self.assertEqual(user.profile.role, 'student')

    def test_register_password_mismatch(self):
        """Password mismatch pe error aana chahiye"""
        resp = self.client.post(reverse('student_register'), {
            'username': 'stu2',
            'roll_number': 'ROLL002',
            'email': 'stu2@test.com',
            'password': 'pass1234',
            'confirm_password': 'wrong',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='stu2').exists())

    def test_register_duplicate_username(self):
        """Duplicate username pe error"""
        make_student('existingstu')
        resp = self.client.post(reverse('student_register'), {
            'username': 'existingstu',
            'roll_number': 'ROLL999',
            'email': 'new@test.com',
            'password': 'pass1234',
            'confirm_password': 'pass1234',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(User.objects.filter(username='existingstu').count(), 1)

    def test_register_duplicate_email(self):
        """Duplicate email pe registration fail honi chahiye"""
        make_student('stu_a')
        resp = self.client.post(reverse('student_register'), {
            'username': 'stu_b',
            'roll_number': 'ROLL_B',
            'email': 'stu_a@test.com',  # same email
            'password': 'pass1234',
            'confirm_password': 'pass1234',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='stu_b').exists())

    def test_register_short_password(self):
        """6 char se kam password reject hona chahiye"""
        resp = self.client.post(reverse('student_register'), {
            'username': 'stu3',
            'roll_number': 'ROLL003',
            'email': 'stu3@test.com',
            'password': '123',
            'confirm_password': '123',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='stu3').exists())


class AdminRegistrationTest(TestCase):

    def test_admin_register_valid_code(self):
        """Valid admin code se registration"""
        resp = self.client.post(reverse('admin_register'), {
            'username': 'adminuser',
            'email': 'admin@test.com',
            'password': 'pass1234',
            'confirm_password': 'pass1234',
            'admin_code': 'ADMIN123',
        })
        self.assertRedirects(resp, reverse('login'))
        user = User.objects.get(username='adminuser')
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_active)

    def test_admin_register_invalid_code(self):
        """Invalid admin code pe reject"""
        resp = self.client.post(reverse('admin_register'), {
            'username': 'badmin',
            'email': 'badmin@test.com',
            'password': 'pass1234',
            'confirm_password': 'pass1234',
            'admin_code': 'WRONG',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(User.objects.filter(username='badmin').exists())


# ============================================================
#  LOGIN TESTS
# ============================================================

class LoginTest(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.student = make_student('loginstu')
        self.inactive_stu = make_student('inactive_stu', active=False)

    def test_login_with_username(self):
        resp = self.client.post(reverse('login'), {
            'username': 'loginstu', 'password': 'pass123'
        })
        self.assertRedirects(resp, reverse('student_dashboard'))

    def test_login_with_email(self):
        resp = self.client.post(reverse('login'), {
            'username': 'loginstu@test.com', 'password': 'pass123'
        })
        self.assertRedirects(resp, reverse('student_dashboard'))

    def test_login_with_roll_number(self):
        resp = self.client.post(reverse('login'), {
            'username': 'ROLLloginstu', 'password': 'pass123'
        })
        self.assertRedirects(resp, reverse('student_dashboard'))

    def test_login_wrong_password(self):
        resp = self.client.post(reverse('login'), {
            'username': 'loginstu', 'password': 'wrongpass'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    def test_login_inactive_user_blocked(self):
        """Inactive/unapproved user login nahi kar sakta"""
        resp = self.client.post(reverse('login'), {
            'username': 'inactive_stu', 'password': 'pass123'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(resp.wsgi_request.user.is_authenticated)

    def test_admin_redirected_to_admin_dashboard(self):
        resp = self.client.post(reverse('login'), {
            'username': 'admin1', 'password': 'pass123'
        })
        self.assertRedirects(resp, reverse('admin_dashboard'))


# ============================================================
#  USER APPROVAL TESTS
# ============================================================

class UserApprovalTest(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.pending_user = make_student('pending_stu', active=False)
        self.client.login(username='admin1', password='pass123')

    def test_approve_user(self):
        resp = self.client.get(
            reverse('approve_user', args=[self.pending_user.id])
        )
        self.pending_user.refresh_from_db()
        self.assertTrue(self.pending_user.is_active)

    def test_reject_user(self):
        resp = self.client.get(
            reverse('reject_user', args=[self.pending_user.id])
        )
        self.assertFalse(User.objects.filter(id=self.pending_user.id).exists())

    def test_non_admin_cannot_approve(self):
        """Non-admin approve nahi kar sakta"""
        staff = make_staff()
        self.client.login(username='staff1', password='pass123')
        resp = self.client.get(
            reverse('approve_user', args=[self.pending_user.id])
        )
        self.pending_user.refresh_from_db()
        self.assertFalse(self.pending_user.is_active)


# ============================================================
#  DASHBOARD ACCESS TESTS
# ============================================================

class DashboardAccessTest(TestCase):

    def test_admin_dashboard_requires_superuser(self):
        """Staff user admin dashboard access nahi kar sakta"""
        make_staff()
        self.client.login(username='staff1', password='pass123')
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertRedirects(resp, reverse('login'))

    def test_unauthenticated_redirect(self):
        """Bina login ke protected pages redirect karein"""
        resp = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(resp.status_code, 302)

    def test_student_dashboard_loads(self):
        make_student('dashstu')
        self.client.login(username='dashstu', password='pass123')
        resp = self.client.get(reverse('student_dashboard'))
        self.assertEqual(resp.status_code, 200)
