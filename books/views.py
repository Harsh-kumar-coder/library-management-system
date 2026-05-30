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

    query = request.GET.get('q')

    if query:

        books = Book.objects.filter(
            title__icontains=query
        ) | Book.objects.filter(
            author__icontains=query
        ) | Book.objects.filter(
            isbn__icontains=query
        )

    else:

        books = Book.objects.all()

    return render(request, 'books/book_list.html', {
        'books': books,
        'query': query
    })


# ---------------- ADD BOOK ----------------
@login_required
def add_book(request):

    if not (
        request.user.is_superuser or
        request.user.is_staff
    ):
        return redirect('student_dashboard')

    if request.method == 'POST':

        title = request.POST.get('title')
        author = request.POST.get('author')
        isbn = request.POST.get('isbn')
        quantity = request.POST.get('quantity')

        Book.objects.create(
            title=title,
            author=author,
            isbn=isbn,
            quantity=quantity
        )

        return redirect('book_list')

    return render(request, 'books/add_book.html')


# ---------------- EDIT BOOK ----------------
@login_required
def edit_book(request, id):

    if not (
        request.user.is_superuser or
        request.user.is_staff
    ):
        return redirect('student_dashboard')

    book = get_object_or_404(Book, id=id)

    if request.method == 'POST':

        book.title = request.POST.get('title')
        book.author = request.POST.get('author')
        book.isbn = request.POST.get('isbn')
        book.quantity = request.POST.get('quantity')

        book.save()

        return redirect('book_list')

    return render(request, 'books/edit_book.html', {
        'book': book
    })


# ---------------- DELETE BOOK ----------------
@login_required
def delete_book(request, id):

    if not (
        request.user.is_superuser or
        request.user.is_staff
    ):
        return redirect('student_dashboard')

    book = get_object_or_404(Book, id=id)

    book.delete()

    return redirect('book_list')


# ---------------- ISSUE BOOK ----------------
@login_required
def issue_book(request):

    if not (
        request.user.is_superuser or
        request.user.is_staff
    ):
        return redirect('student_dashboard')

    students = User.objects.filter(
        is_staff=False
    )

    books = Book.objects.all()

    if request.method == 'POST':

        student_id = request.POST.get('student')
        book_id = request.POST.get('book')
        issue_date = request.POST.get('issue_date')

        student = User.objects.get(id=student_id)

        book = Book.objects.get(id=book_id)

        return_date = (
            timezone.datetime.strptime(
                issue_date,
                "%Y-%m-%d"
            ).date()
            + timezone.timedelta(days=7)
        )

        fine = 0

        if timezone.now().date() > return_date:

            days_late = (
                timezone.now().date() - return_date
            ).days

            fine = days_late * 5

        IssuedBook.objects.create(
            student=student,
            book=book,
            issue_date=issue_date,
            return_date=return_date,
            fine=fine
        )

        return redirect('return_book')

    return render(request, 'books/issue_book.html', {
        'students': students,
        'books': books
    })


# ---------------- RETURN BOOK ----------------
@login_required
def return_book(request):

    issued_books = IssuedBook.objects.all().order_by(
        'returned',
        '-issue_date'
    )

    if not (
        request.user.is_superuser or
        request.user.is_staff
    ):

        issued_books = issued_books.filter(
            student=request.user
        )

    return render(request, 'books/return_book.html', {
        'issued_books': issued_books
    })


# ---------------- RETURN BOOK ACTION ----------------
@login_required
def return_book_action(request, issue_id):

    if not (
        request.user.is_superuser or
        request.user.is_staff
    ):
        return redirect('student_dashboard')

    issue = get_object_or_404(
        IssuedBook,
        id=issue_id
    )

    issue.returned = True

    issue.save()

    return redirect('return_book')


# ---------------- REQUEST BOOK ----------------
@login_required
def request_book(request):

    books = Book.objects.all()

    # total active books (issued + approved request)
    issued_count = IssuedBook.objects.filter(
        student=request.user,
        returned=False
    ).count()

    approved_request_count = BookRequest.objects.filter(
        student=request.user,
        approved=True
    ).count()

    total_books = issued_count + approved_request_count

    if request.method == 'POST':

        # limit 2 books
        if total_books >= 2:

            return render(request, 'books/request_book.html', {
                'books': books,
                'error': 'You can only request maximum 2 books.'
            })

        book_id = request.POST.get('book')

        book = Book.objects.get(id=book_id)

        already_requested = BookRequest.objects.filter(
            student=request.user,
            book=book,
            approved=False
        ).exists()

        if not already_requested:

            BookRequest.objects.create(
                student=request.user,
                book=book
            )

        return redirect('student_dashboard')

    return render(request, 'books/request_book.html', {
        'books': books,
        'total_books': total_books
    })


# ---------------- VIEW REQUESTS ----------------
@login_required
def view_requests(request):

    if not (
        request.user.is_superuser or
        request.user.is_staff
    ):
        return redirect('student_dashboard')

    # pending top
    requests = BookRequest.objects.all().order_by(
        'approved',
        '-id'
    )

    return render(request, 'books/pending_requests.html', {
        'requests': requests
    })


# ---------------- PENDING REQUESTS ----------------
@login_required
def pending_requests_page(request):

    if not request.user.is_superuser:
        return redirect('login')

    requests = BookRequest.objects.filter(
        approved=False
    ).order_by('-id')

    return render(request, 'books/pending_requests.html', {
        'requests': requests
    })


# ---------------- APPROVE REQUEST ----------------
@login_required
def approve_request(request, request_id):

    if not (
        request.user.is_superuser or
        request.user.is_staff
    ):
        return redirect('student_dashboard')

    req = get_object_or_404(
        BookRequest,
        id=request_id
    )

    # prevent duplicate approval
    if not req.approved:

        req.approved = True
        req.save()

        return_date = (
            timezone.now().date()
            + timezone.timedelta(days=7)
        )

        IssuedBook.objects.create(
            student=req.student,
            book=req.book,
            issue_date=timezone.now().date(),
            return_date=return_date
        )

    return redirect('view_requests')


# ---------------- DONATE ----------------
def donate(request):

    if request.method == "POST":

        name = request.POST.get('name')
        name = name if name else "Anonymous"

        amount = request.POST.get('amount')
        message = request.POST.get('message')

        if amount == '' or amount is None:

            amount = None

        else:

            try:
                amount = int(amount)

            except ValueError:
                amount = None

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
        return redirect('login')

    donations = Donation.objects.all().order_by('-created_at')

    return render(
        request,
        'books/donation_list.html',
        {'donations': donations}
    )

# ---------------- THANK YOU ----------------
def thank_you(request):

    return render(request, 'books/thank_you.html')

# ---------------- CONTACT ----------------
def contact(request):

    if request.method == "POST":

        ContactMessage.objects.create(
            name=request.POST.get('name'),
            email=request.POST.get('email'),
            subject=request.POST.get('subject'),
            message=request.POST.get('message')
        )
        messages.success(
            request,
            "Your message has been sent successfully."
        )

        return redirect('contact')

    return render(request, 'contact.html')

# ---------------- CONTACT MESSAGES ----------------
@login_required
def contact_messages(request):

    if not request.user.is_superuser:
        return redirect('login')

    messages = ContactMessage.objects.all().order_by('-created_at')

    return render(
        request,
        'contact_messages.html',
        {'messages': messages}
    )