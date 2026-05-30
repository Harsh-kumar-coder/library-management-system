"""
Library Management System - Books App Tests
==========================================
Books, issuing, returning, requests, fines ke tests
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from books.models import Book, IssuedBook, BookRequest, Donation, ContactMessage
from accounts.models import Profile


# ============================================================
#  HELPERS
# ============================================================

def make_admin(username='admin1', password='pass123'):
    u = User.objects.create_user(
        username=username, password=password,
        email=f'{username}@t.com',
        is_staff=True, is_superuser=True, is_active=True
    )
    Profile.objects.create(user=u, role='admin')
    return u


def make_staff(username='staff1', password='pass123'):
    u = User.objects.create_user(
        username=username, password=password,
        email=f'{username}@t.com',
        is_staff=True, is_active=True
    )
    Profile.objects.create(user=u, role='staff')
    return u


def make_student(username='stu1', password='pass123'):
    u = User.objects.create_user(
        username=username, password=password,
        email=f'{username}@t.com',
        first_name=f'ROLL{username}',
        is_active=True
    )
    Profile.objects.create(user=u, role='student')
    return u


def make_book(title='Django Book', quantity=3):
    return Book.objects.create(
        title=title, author='Author A', isbn='ISBN-X', quantity=quantity
    )


def issue_book_to(student, book, days_ago=0, days_overdue=0):
    """Helper: book issue karo, optionally overdue banao"""
    today = timezone.now().date()
    issue_date = today - timezone.timedelta(days=days_ago)
    if days_overdue:
        return_date = today - timezone.timedelta(days=days_overdue)
    else:
        return_date = issue_date + timezone.timedelta(days=14)
    return IssuedBook.objects.create(
        student=student,
        book=book,
        issue_date=issue_date,
        return_date=return_date,
        fine=0,
        returned=False
    )


# ============================================================
#  BOOK CRUD TESTS
# ============================================================

class BookCRUDTest(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.student = make_student()
        self.client.login(username='admin1', password='pass123')

    def test_add_book_success(self):
        resp = self.client.post(reverse('add_book'), {
            'title': 'Python 101',
            'author': 'Guido',
            'isbn': 'ISBN-PY101',
            'quantity': 5,
        })
        self.assertRedirects(resp, reverse('book_list'))
        self.assertTrue(Book.objects.filter(title='Python 101').exists())

    def test_add_book_missing_title(self):
        """Title missing hone pe book add nahi hona chahiye"""
        resp = self.client.post(reverse('add_book'), {
            'title': '',
            'author': 'Guido',
            'isbn': 'ISBN-001',
            'quantity': 3,
        })
        self.assertEqual(resp.status_code, 200)  # form wapas aata hai
        self.assertFalse(Book.objects.filter(author='Guido').exists())

    def test_add_book_invalid_quantity(self):
        """Invalid quantity (text ya 0) pe reject"""
        resp = self.client.post(reverse('add_book'), {
            'title': 'Bad Qty',
            'author': 'Auth',
            'isbn': 'ISBN-BAD',
            'quantity': 'abc',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Book.objects.filter(title='Bad Qty').exists())

    def test_add_book_duplicate_isbn(self):
        """Duplicate ISBN pe reject"""
        make_book()  # isbn='ISBN-X'
        resp = self.client.post(reverse('add_book'), {
            'title': 'Another Book',
            'author': 'Auth2',
            'isbn': 'ISBN-X',
            'quantity': 2,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Book.objects.filter(title='Another Book').exists())

    def test_edit_book_success(self):
        book = make_book()
        resp = self.client.post(reverse('edit_book', args=[book.id]), {
            'title': 'Updated Title',
            'author': 'New Author',
            'isbn': 'ISBN-UPD',
            'quantity': 4,
        })
        self.assertRedirects(resp, reverse('book_list'))
        book.refresh_from_db()
        self.assertEqual(book.title, 'Updated Title')

    def test_edit_book_quantity_below_issued(self):
        """Issued count se kam quantity set nahi honi chahiye"""
        book = make_book(quantity=3)
        issue_book_to(self.student, book)
        issue_book_to(make_student('stu2'), book)

        resp = self.client.post(reverse('edit_book', args=[book.id]), {
            'title': book.title,
            'author': book.author,
            'isbn': book.isbn,
            'quantity': 1,  # 2 issued hain, 1 se kam nahi ho sakta
        })
        self.assertEqual(resp.status_code, 200)  # error, form wapas
        book.refresh_from_db()
        self.assertEqual(book.quantity, 3)  # unchanged

    def test_delete_book_success(self):
        book = make_book()
        resp = self.client.get(reverse('delete_book', args=[book.id]))
        self.assertRedirects(resp, reverse('book_list'))
        self.assertFalse(Book.objects.filter(id=book.id).exists())

    def test_delete_book_with_active_issues_blocked(self):
        """Issued book delete nahi honi chahiye"""
        book = make_book()
        issue_book_to(self.student, book)
        resp = self.client.get(reverse('delete_book', args=[book.id]))
        self.assertTrue(Book.objects.filter(id=book.id).exists())  # still exists

    def test_student_cannot_add_book(self):
        """Student book add nahi kar sakta"""
        self.client.login(username='stu1', password='pass123')
        resp = self.client.post(reverse('add_book'), {
            'title': 'Hacked Book',
            'author': 'Hacker',
            'isbn': 'HACK',
            'quantity': 1,
        })
        # Should redirect away
        self.assertNotEqual(resp.status_code, 200)
        self.assertFalse(Book.objects.filter(title='Hacked Book').exists())


# ============================================================
#  ISSUE BOOK TESTS
# ============================================================

class IssueBookTest(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.student = make_student()
        self.book = make_book(quantity=2)
        self.client.login(username='admin1', password='pass123')

    def test_issue_book_success(self):
        today = timezone.now().date().strftime('%Y-%m-%d')
        resp = self.client.post(reverse('issue_book'), {
            'student': self.student.id,
            'book': self.book.id,
            'issue_date': today,
        })
        self.assertRedirects(resp, reverse('return_book'))
        self.assertTrue(
            IssuedBook.objects.filter(
                student=self.student, book=self.book, returned=False
            ).exists()
        )

    def test_issue_book_unavailable(self):
        """Stock 0 hone pe issue nahi hona chahiye"""
        stu2 = make_student('stu2')
        single_book = make_book('Single Book', quantity=1)
        issue_book_to(stu2, single_book)  # already issued

        today = timezone.now().date().strftime('%Y-%m-%d')
        resp = self.client.post(reverse('issue_book'), {
            'student': self.student.id,
            'book': single_book.id,
            'issue_date': today,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            IssuedBook.objects.filter(book=single_book, returned=False).count(), 1
        )

    def test_issue_book_student_limit_2(self):
        """Student ko 2 se zyada books issue nahi ho sakti"""
        stu3 = make_student('stu3')
        book2 = make_book('Book Two', quantity=3)
        book3 = make_book('Book Three', quantity=3)

        issue_book_to(stu3, self.book)
        issue_book_to(stu3, book2)

        today = timezone.now().date().strftime('%Y-%m-%d')
        resp = self.client.post(reverse('issue_book'), {
            'student': stu3.id,
            'book': book3.id,
            'issue_date': today,
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            IssuedBook.objects.filter(student=stu3, returned=False).count(), 2
        )

    def test_return_date_is_14_days_after_issue(self):
        today = timezone.now().date()
        resp = self.client.post(reverse('issue_book'), {
            'student': self.student.id,
            'book': self.book.id,
            'issue_date': today.strftime('%Y-%m-%d'),
        })
        issued = IssuedBook.objects.get(student=self.student, book=self.book)
        expected_return = today + timezone.timedelta(days=14)
        self.assertEqual(issued.return_date, expected_return)


# ============================================================
#  RETURN BOOK TESTS
# ============================================================

class ReturnBookTest(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.student = make_student()
        self.book = make_book()
        self.client.login(username='admin1', password='pass123')

    def test_return_book_success(self):
        issued = issue_book_to(self.student, self.book)
        resp = self.client.get(reverse('return_book_action', args=[issued.id]))
        self.assertRedirects(resp, reverse('return_book'))
        issued.refresh_from_db()
        self.assertTrue(issued.returned)

    def test_return_already_returned_book(self):
        """Already returned book dobara return nahi ho sakti"""
        issued = issue_book_to(self.student, self.book)
        issued.returned = True
        issued.save()
        resp = self.client.get(reverse('return_book_action', args=[issued.id]))
        # Should redirect with warning, not error
        self.assertEqual(resp.status_code, 302)

    def test_fine_calculated_on_return(self):
        """Overdue book pe fine calculate hona chahiye"""
        # 5 days overdue
        issued = issue_book_to(self.student, self.book, days_ago=19, days_overdue=5)
        resp = self.client.get(reverse('return_book_action', args=[issued.id]))
        issued.refresh_from_db()
        self.assertEqual(issued.fine, 25)  # 5 days * Rs. 5

    def test_no_fine_on_time_return(self):
        """Time pe return hone pe fine 0 hona chahiye"""
        issued = issue_book_to(self.student, self.book, days_ago=3)
        resp = self.client.get(reverse('return_book_action', args=[issued.id]))
        issued.refresh_from_db()
        self.assertEqual(issued.fine, 0)

    def test_student_cannot_return_others_book(self):
        """Student doosre student ki book return nahi kar sakta"""
        stu2 = make_student('stu2')
        issued = issue_book_to(stu2, self.book)
        self.client.login(username='stu1', password='pass123')
        resp = self.client.get(reverse('return_book_action', args=[issued.id]))
        # Should be redirected away (access denied)
        self.assertEqual(resp.status_code, 302)
        issued.refresh_from_db()
        self.assertFalse(issued.returned)


# ============================================================
#  BOOK REQUEST TESTS
# ============================================================

class BookRequestTest(TestCase):

    def setUp(self):
        self.admin = make_admin()
        self.student = make_student()
        self.book = make_book()
        self.client.login(username='stu1', password='pass123')

    def test_request_book_success(self):
        resp = self.client.post(reverse('request_book'), {
            'book': self.book.id
        })
        self.assertRedirects(resp, reverse('student_dashboard'))
        self.assertTrue(
            BookRequest.objects.filter(
                student=self.student, book=self.book
            ).exists()
        )

    def test_request_limit_2(self):
        """2 se zyada requests nahi ho sakti"""
        book2 = make_book('Book 2', quantity=3)
        book3 = make_book('Book 3', quantity=3)

        # First 2 books request karo
        self.client.post(reverse('request_book'), {'book': self.book.id})
        self.client.post(reverse('request_book'), {'book': book2.id})

        # Third book request try karo
        resp = self.client.post(reverse('request_book'), {'book': book3.id})
        self.assertFalse(
            BookRequest.objects.filter(student=self.student, book=book3).exists()
        )

    def test_duplicate_request_blocked(self):
        """Same book ka duplicate request nahi hona chahiye"""
        self.client.post(reverse('request_book'), {'book': self.book.id})
        self.client.post(reverse('request_book'), {'book': self.book.id})
        count = BookRequest.objects.filter(
            student=self.student, book=self.book
        ).count()
        self.assertEqual(count, 1)

    def test_request_already_issued_book_blocked(self):
        """Already issued book ke liye request nahi ho sakti"""
        issue_book_to(self.student, self.book)
        resp = self.client.post(reverse('request_book'), {'book': self.book.id})
        self.assertFalse(
            BookRequest.objects.filter(
                student=self.student, book=self.book
            ).exists()
        )

    def test_approve_request_issues_book(self):
        """Request approve hone pe IssuedBook create hona chahiye"""
        BookRequest.objects.create(student=self.student, book=self.book)
        req = BookRequest.objects.get(student=self.student, book=self.book)

        self.client.login(username='admin1', password='pass123')
        resp = self.client.get(reverse('approve_request', args=[req.id]))

        req.refresh_from_db()
        self.assertTrue(req.approved)
        self.assertTrue(
            IssuedBook.objects.filter(
                student=self.student, book=self.book
            ).exists()
        )

    def test_approve_request_unavailable_book(self):
        """Stock 0 hone pe request approve nahi honi chahiye"""
        limited_book = make_book('Limited', quantity=1)
        stu2 = make_student('stu2')
        issue_book_to(stu2, limited_book)  # stock used

        req = BookRequest.objects.create(student=self.student, book=limited_book)

        self.client.login(username='admin1', password='pass123')
        resp = self.client.get(reverse('approve_request', args=[req.id]))

        req.refresh_from_db()
        self.assertFalse(req.approved)

    def test_reject_request(self):
        """Request reject hone pe delete ho jaana chahiye"""
        req = BookRequest.objects.create(student=self.student, book=self.book)

        self.client.login(username='admin1', password='pass123')
        resp = self.client.get(reverse('reject_request', args=[req.id]))

        self.assertFalse(BookRequest.objects.filter(id=req.id).exists())


# ============================================================
#  BOOK SEARCH TEST
# ============================================================

class BookSearchTest(TestCase):

    def setUp(self):
        self.admin = make_admin()
        Book.objects.create(title='Django Basics', author='Alice', isbn='001', quantity=2)
        Book.objects.create(title='Python Tips', author='Bob', isbn='002', quantity=2)
        self.client.login(username='admin1', password='pass123')

    def test_search_by_title(self):
        resp = self.client.get(reverse('book_list') + '?q=django')
        self.assertEqual(resp.status_code, 200)
        books = resp.context['books']
        self.assertEqual(books.count(), 1)
        self.assertEqual(books.first().title, 'Django Basics')

    def test_search_by_author(self):
        resp = self.client.get(reverse('book_list') + '?q=bob')
        books = resp.context['books']
        self.assertEqual(books.first().author, 'Bob')

    def test_empty_search_returns_all(self):
        resp = self.client.get(reverse('book_list'))
        books = resp.context['books']
        self.assertEqual(books.count(), 2)


# ============================================================
#  DONATION TESTS
# ============================================================

class DonationTest(TestCase):

    def test_donation_success(self):
        resp = self.client.post(reverse('donate'), {
            'name': 'Ramesh',
            'amount': '100',
            'message': 'For the library',
        })
        self.assertRedirects(resp, reverse('thank_you'))
        self.assertTrue(Donation.objects.filter(name='Ramesh').exists())

    def test_anonymous_donation(self):
        resp = self.client.post(reverse('donate'), {
            'name': '',
            'amount': '50',
            'message': '',
        })
        self.assertRedirects(resp, reverse('thank_you'))
        self.assertTrue(Donation.objects.filter(name='Anonymous').exists())

    def test_negative_amount_rejected(self):
        resp = self.client.post(reverse('donate'), {
            'name': 'Bad',
            'amount': '-100',
            'message': '',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Donation.objects.filter(name='Bad').exists())


# ============================================================
#  CONTACT MESSAGE TESTS
# ============================================================

class ContactMessageTest(TestCase):

    def test_contact_form_success(self):
        resp = self.client.post(reverse('contact'), {
            'name': 'Suresh',
            'email': 'suresh@test.com',
            'subject': 'Library Hours',
            'message': 'What time does the library open?',
        })
        self.assertRedirects(resp, reverse('contact'))
        self.assertTrue(ContactMessage.objects.filter(name='Suresh').exists())

    def test_contact_form_missing_fields(self):
        """Incomplete form submit nahi hona chahiye"""
        resp = self.client.post(reverse('contact'), {
            'name': 'Partial',
            'email': '',
            'subject': '',
            'message': '',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ContactMessage.objects.filter(name='Partial').exists())

    def test_only_admin_views_messages(self):
        """Admin hi contact messages dekh sakta hai"""
        make_student('msgstu')
        self.client.login(username='msgstu', password='pass123')
        resp = self.client.get(reverse('contact_messages'))
        self.assertNotEqual(resp.status_code, 200)  # redirected
