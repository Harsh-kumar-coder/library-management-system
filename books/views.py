from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone

from .models import (
    Book,
    IssuedBook,
    BookRequest,
    Donation,
    ContactMessage
)


# ---------------- BOOK LIST ----------------
@login_required
def book_list(request):

    query = request.GET.get('q', '').strip()

    if query:
        books = (
            Book.objects.filter(title__icontains=query) |
            Book.objects.filter(author__icontains=query) |
            Book.objects.filter(isbn__icontains=query)
        ).distinct()
    else:
        books = Book.objects.all().order_by('title')

    return render(request, 'books/book_list.html', {
        'books': books,
        'query': query
    })


# ---------------- ADD BOOK ----------------
@login_required
def add_book(request):

    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access denied.")
        return redirect('student_dashboard')

    if request.method == 'POST':

        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        isbn = request.POST.get('isbn', '').strip()
        quantity = request.POST.get('quantity', '1').strip()

        # BUG FIX: Validate required fields
        if not title or not author:
            messages.error(request, "Title and Author are required.")
            return render(request, 'books/add_book.html')

        # BUG FIX: Validate quantity is a positive integer
        try:
            quantity = int(quantity)
            if quantity < 1:
                raise ValueError
        except ValueError:
            messages.error(request, "Quantity must be a positive number.")
            return render(request, 'books/add_book.html')

        # BUG FIX: Check duplicate ISBN (if provided)
        if isbn and Book.objects.filter(isbn=isbn).exclude(isbn='N/A').exists():
            messages.error(request, f"ISBN '{isbn}' already exists.")
            return render(request, 'books/add_book.html')

        Book.objects.create(
            title=title,
            author=author,
            isbn=isbn or 'N/A',
            quantity=quantity
        )
        messages.success(request, f"Book '{title}' successfully added.")
        return redirect('book_list')

    return render(request, 'books/add_book.html')


# ---------------- EDIT BOOK ----------------
@login_required
def edit_book(request, id):

    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access denied.")
        return redirect('student_dashboard')

    book = get_object_or_404(Book, id=id)

    if request.method == 'POST':

        title = request.POST.get('title', '').strip()
        author = request.POST.get('author', '').strip()
        isbn = request.POST.get('isbn', '').strip()
        quantity = request.POST.get('quantity', '1').strip()

        # BUG FIX: Validate required fields
        if not title or not author:
            messages.error(request, "Title and Author are required.")
            return render(request, 'books/edit_book.html', {'book': book})

        # BUG FIX: Validate quantity
        try:
            quantity = int(quantity)
            if quantity < 1:
                raise ValueError
        except ValueError:
            messages.error(request, "Quantity must be a positive number.")
            return render(request, 'books/edit_book.html', {'book': book})

        # BUG FIX: Check if quantity going below currently issued count
        issued_count = IssuedBook.objects.filter(book=book, returned=False).count()
        if quantity < issued_count:
            messages.error(
                request,
                f"Quantity {issued_count} cannot be less than the number of currently issued books "
                f"(currently {issued_count} books are issued)."
            )
            return render(request, 'books/edit_book.html', {'book': book})

        book.title = title
        book.author = author
        book.isbn = isbn or 'N/A'
        book.quantity = quantity
        book.save()

        messages.success(request, "Book successfully updated.")
        return redirect('book_list')

    return render(request, 'books/edit_book.html', {'book': book})


# ---------------- DELETE BOOK ----------------
@login_required
def delete_book(request, id):

    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access denied.")
        return redirect('student_dashboard')

    book = get_object_or_404(Book, id=id)

    # BUG FIX: Prevent deletion if book is currently issued
    active_issues = IssuedBook.objects.filter(book=book, returned=False).count()
    if active_issues > 0:
        messages.error(
            request,
            f"This book cannot be deleted — {active_issues} student(s) currently have it issued."
        )
        return redirect('book_list')

    book_title = book.title
    book.delete()
    messages.success(request, f"'{book_title}' successfully deleted.")
    return redirect('book_list')


# ---------------- ISSUE BOOK ----------------
@login_required
def issue_book(request):

    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access denied.")
        return redirect('student_dashboard')

    # BUG FIX: Only show active (approved) students, not all non-staff users
    students = User.objects.filter(is_staff=False, is_superuser=False, is_active=True)
    books = Book.objects.all().order_by('title')

    if request.method == 'POST':

        student_id = request.POST.get('student')
        book_id = request.POST.get('book')
        issue_date = request.POST.get('issue_date')

        # BUG FIX: Validate all fields present
        if not student_id or not book_id or not issue_date:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'books/issue_book.html', {
                'students': students, 'books': books
            })

        try:
            student = User.objects.get(id=student_id)
            book = Book.objects.get(id=book_id)
        except (User.DoesNotExist, Book.DoesNotExist):
            messages.error(request, "Student or Book not found.")
            return render(request, 'books/issue_book.html', {
                'students': students, 'books': books
            })

        # BUG FIX: Check book availability (quantity vs currently issued)
        currently_issued = IssuedBook.objects.filter(book=book, returned=False).count()
        if currently_issued >= book.quantity:
            messages.error(
                request,
                f"'{book.title}' is not available (all copies are issued)."
            )
            return render(request, 'books/issue_book.html', {
                'students': students, 'books': books
            })

        # BUG FIX: Check student book limit (max 2)
        student_active = IssuedBook.objects.filter(
            student=student, returned=False
        ).count()
        if student_active >= 2:
            messages.error(
                request,
                f"{student.username} has already issued 2 books."
            )
            return render(request, 'books/issue_book.html', {
                'students': students, 'books': books
            })

        try:
            issue_date_obj = timezone.datetime.strptime(issue_date, "%Y-%m-%d").date()
        except ValueError:
            messages.error(request, "Invalid date format.")
            return render(request, 'books/issue_book.html', {
                'students': students, 'books': books
            })

        return_date = issue_date_obj + timezone.timedelta(days=14)  # BUG FIX: 14 days is standard

        # BUG FIX: Fine only on actual return, not at issue time
        IssuedBook.objects.create(
            student=student,
            book=book,
            issue_date=issue_date_obj,
            return_date=return_date,
            fine=0
        )

        messages.success(
            request,
            f"'{book.title}' successfully issued to {student.username}. "
            f"Return date: {return_date}"
        )
        return redirect('return_book')

    return render(request, 'books/issue_book.html', {
        'students': students,
        'books': books
    })


# ---------------- RETURN BOOK ----------------
@login_required
def return_book(request):

    if request.user.is_superuser or request.user.is_staff:
        issued_books = IssuedBook.objects.all().order_by('returned', '-issue_date')
    else:
        issued_books = IssuedBook.objects.filter(
            student=request.user
        ).order_by('returned', '-issue_date')

    # BUG FIX: Calculate and update fines dynamically on page load
    today = timezone.now().date()
    for issue in issued_books:
        if not issue.returned and issue.return_date and today > issue.return_date:
            days_late = (today - issue.return_date).days
            new_fine = days_late * 5  # Rs. 5 per day
            if issue.fine != new_fine:
                issue.fine = new_fine
                issue.save()

    return render(request, 'books/return_book.html', {
        'issued_books': issued_books,
        'today': today,
    })


# ---------------- RETURN BOOK ACTION ----------------
@login_required
def return_book_action(request, issue_id):

    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access denied.")
        return redirect('student_dashboard')

    issue = get_object_or_404(IssuedBook, id=issue_id)

    # BUG FIX: Prevent returning already returned book
    if issue.returned:
        messages.warning(request, "This book has already been returned.")
        return redirect('return_book')

    # BUG FIX: Calculate final fine at time of return
    today = timezone.now().date()
    if issue.return_date and today > issue.return_date:
        days_late = (today - issue.return_date).days
        issue.fine = days_late * 5
    else:
        issue.fine = 0

    issue.returned = True
    issue.save()

    messages.success(
        request,
        f"'{issue.book.title}' returned. "
        f"{'Fine: Rs. ' + str(issue.fine) if issue.fine > 0 else 'No fine.'}"
    )
    return redirect('return_book')


# ---------------- REQUEST BOOK ----------------
@login_required
def request_book(request):

    books = Book.objects.all().order_by('title')

    issued_count = IssuedBook.objects.filter(
        student=request.user, returned=False
    ).count()

    # BUG FIX: Only count pending (unapproved) requests, not all approved ones
    pending_request_count = BookRequest.objects.filter(
        student=request.user, approved=False
    ).count()

    total_active = issued_count + pending_request_count

    if request.method == 'POST':

        if total_active >= 2:
            messages.error(request, "You can request a maximum of 2 books.")
            return render(request, 'books/request_book.html', {
                'books': books,
                'total_books': total_active
            })

        book_id = request.POST.get('book')
        if not book_id:
            messages.error(request, "Please select a book.")
            return render(request, 'books/request_book.html', {
                'books': books,
                'total_books': total_active
            })

        try:
            book = Book.objects.get(id=book_id)
        except Book.DoesNotExist:
            messages.error(request, "Book not found.")
            return render(request, 'books/request_book.html', {
                'books': books,
                'total_books': total_active
            })

        # BUG FIX: Check if same book already issued to this student
        already_issued = IssuedBook.objects.filter(
            student=request.user, book=book, returned=False
        ).exists()
        if already_issued:
            messages.error(request, f"'{book.title}' is already issued to you.")
            return render(request, 'books/request_book.html', {
                'books': books,
                'total_books': total_active
            })

        already_requested = BookRequest.objects.filter(
            student=request.user, book=book, approved=False
        ).exists()

        if already_requested:
            messages.warning(request, f"'{book.title}' is already requested by you.")
        else:
            BookRequest.objects.create(student=request.user, book=book)
            messages.success(request, f"Request for '{book.title}' has been sent.")

        return redirect('student_dashboard')

    return render(request, 'books/request_book.html', {
        'books': books,
        'total_books': total_active
    })


# ---------------- VIEW REQUESTS ----------------
@login_required
def view_requests(request):

    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access denied.")
        return redirect('student_dashboard')

    requests = BookRequest.objects.all().order_by('approved', '-id').select_related(
        'student', 'book'
    )

    return render(request, 'books/pending_requests.html', {
        'requests': requests
    })


# ---------------- PENDING REQUESTS PAGE ----------------
@login_required
def pending_requests_page(request):

    if not request.user.is_superuser:
        return redirect('login')

    requests = BookRequest.objects.filter(approved=False).order_by('-id').select_related(
        'student', 'book'
    )

    return render(request, 'books/pending_requests.html', {
        'requests': requests
    })


# ---------------- APPROVE REQUEST ----------------
@login_required
def approve_request(request, request_id):

    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access denied.")
        return redirect('student_dashboard')

    req = get_object_or_404(BookRequest, id=request_id)

    if req.approved:
        messages.warning(request, "This request has already been approved.")
        return redirect('view_requests')

    # BUG FIX: Check availability before approving
    currently_issued = IssuedBook.objects.filter(book=req.book, returned=False).count()
    if currently_issued >= req.book.quantity:
        messages.error(
            request,
            f"'{req.book.title}' is not available (all copies are issued)."
        )
        return redirect('view_requests')

    # BUG FIX: Check student's current book count
    student_active = IssuedBook.objects.filter(
        student=req.student, returned=False
    ).count()
    if student_active >= 2:
        messages.error(
            request,
            f"{req.student.username} has already issued 2 books."
        )
        return redirect('view_requests')

    req.approved = True
    req.save()

    return_date = timezone.now().date() + timezone.timedelta(days=14)

    IssuedBook.objects.create(
        student=req.student,
        book=req.book,
        issue_date=timezone.now().date(),
        return_date=return_date,
        fine=0
    )

    messages.success(
        request,
        f"'{req.book.title}' — {req.student.username} has been approved."
    )
    return redirect('view_requests')


# ---------------- REJECT REQUEST ----------------
@login_required
def reject_request(request, request_id):
    """BUG FIX: New view — reject/delete a book request"""

    if not (request.user.is_superuser or request.user.is_staff):
        messages.error(request, "Access denied.")
        return redirect('student_dashboard')

    req = get_object_or_404(BookRequest, id=request_id)

    if req.approved:
        messages.warning(request, "Approved request cannot be rejected.")
        return redirect('view_requests')

    student_name = req.student.username
    book_title = req.book.title
    req.delete()

    messages.success(request, f"{student_name}'s request for '{book_title}' has been rejected.")
    return redirect('view_requests')


# ---------------- DONATE ----------------
def donate(request):

    if request.method == "POST":

        name = request.POST.get('name', '').strip()
        name = name if name else "Anonymous"

        amount_raw = request.POST.get('amount', '').strip()
        message = request.POST.get('message', '').strip()

        amount = None
        if amount_raw:
            try:
                amount = int(amount_raw)
                # BUG FIX: Validate amount is positive
                if amount <= 0:
                    messages.error(request, "Amount must be a positive number.")
                    return render(request, 'books/donate.html')
            except ValueError:
                messages.error(request, "Amount must be a valid number.")
                return render(request, 'books/donate.html')

        Donation.objects.create(
            name=name,
            amount=amount,
            message=message
        )
        return redirect('thank_you')

    return render(request, 'books/donate.html')


# ---------------- DONATION LIST ----------------
@login_required
def donation_list(request):

    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('login')

    donations = Donation.objects.all().order_by('-created_at')
    total = sum(d.amount for d in donations if d.amount)

    return render(request, 'books/donation_list.html', {
        'donations': donations,
        'total': total,
    })


# ---------------- THANK YOU ----------------
def thank_you(request):
    return render(request, 'books/thank_you.html')


# ---------------- CONTACT ----------------
def contact(request):

    if request.method == "POST":

        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        msg = request.POST.get('message', '').strip()

        # BUG FIX: Validate all fields
        if not name or not email or not subject or not msg:
            messages.error(request, "Please fill in all fields.")
            return render(request, 'contact.html')

        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=msg
        )
        messages.success(request, "Your message has been sent successfully.")
        return redirect('contact')

    return render(request, 'contact.html')


# ---------------- CONTACT MESSAGES ----------------
@login_required
def contact_messages(request):

    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('login')

    # BUG FIX: Renamed local variable to avoid shadowing django messages
    contact_msgs = ContactMessage.objects.all().order_by('-created_at')

    return render(request, 'contact_messages.html', {
        'messages_list': contact_msgs
    })
