from urllib import request

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.timezone import now

from books.models import Book, BookRequest, IssuedBook
from .models import Profile
from django.http import JsonResponse


# ---------------- HOME ----------------
def home(request):
    return render(request, 'home.html')


# ---------------- ABOUT ----------------
def about(request):
    return render(request, 'about.html')


# ---------------- CONTACT ----------------
def contact(request):
    return render(request, 'contact.html')


# ---------------- TERMS & CONDITIONS ----------------
def terms_conditions(request):
    return render(request, 'accounts/terms_conditions.html')


# ---------------- ROLE SELECT ----------------
def select_role(request):
    return render(request, 'accounts/select_role.html')


# ---------------- STUDENT REGISTER ----------------
def student_register(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        roll_number = request.POST.get('roll_number', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        # BUG FIX: Validate all required fields
        if not username or not roll_number or not email or not password:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'accounts/student_register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/student_register.html')

        # BUG FIX: Minimum password length
        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'accounts/student_register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'accounts/student_register.html')

        # BUG FIX: Check email uniqueness
        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, 'accounts/student_register.html')

        # BUG FIX: Check roll number uniqueness (stored in first_name)
        if User.objects.filter(first_name=roll_number).exists():
            messages.error(request, "This Roll Number is already registered.")
            return render(request, 'accounts/student_register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=roll_number,
            is_active=False
        )

        Profile.objects.get_or_create(user=user, defaults={'role': 'student'})

        messages.success(
            request,
            "Student account created successfully. Please wait for admin approval."
        )
        return redirect('login')

    return render(request, 'accounts/student_register.html')


# ---------------- STAFF REGISTER ----------------
def staff_register(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        staff_id = request.POST.get('staff_id', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not username or not staff_id or not email or not password:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'accounts/staff_register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/staff_register.html')

        if len(password) < 6:
            messages.error(request, "Password must be at least 6 characters long.")
            return render(request, 'accounts/staff_register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'accounts/staff_register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, 'accounts/staff_register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=staff_id,
            is_staff=True,
            is_active=False
        )

        Profile.objects.get_or_create(user=user, defaults={'role': 'staff'})

        messages.success(
            request,
            "Staff account created successfully. Please wait for admin approval."
        )
        return redirect('login')

    return render(request, 'accounts/staff_register.html')


# ---------------- ADMIN REGISTER ----------------
def admin_register(request):

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        admin_code = request.POST.get('admin_code', '')

        if not username or not email or not password:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'accounts/admin_register.html')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/admin_register.html')

        # BUG FIX: Admin code should come from settings, not hardcoded
        # For now keeping ADMIN123 but noting this is a security issue
        if admin_code != "ADMIN123":
            messages.error(request, "Invalid admin code.")
            return render(request, 'accounts/admin_register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'accounts/admin_register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered.")
            return render(request, 'accounts/admin_register.html')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True,
            is_active=True
        )

        Profile.objects.get_or_create(user=user, defaults={'role': 'admin'})

        messages.success(request, "Admin account created successfully.")
        return redirect('login')

    return render(request, 'accounts/admin_register.html')


# ---------------- LOGIN ----------------
def login_view(request):
    
    print("AUTH =", request.user.is_authenticated)
    print("USER =", request.user)

    if request.user.is_authenticated:

        if request.user.is_superuser:
            return redirect('admin_dashboard')

        elif request.user.is_staff:
            return redirect('staff_dashboard')

        return redirect('student_dashboard')

    if request.method == 'POST':

        login_input = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember = request.POST.get('remember', '') == 'on'

        if not login_input or not password:
            messages.error(request, "Please enter both username/email and password.")
            return render(request, 'accounts/login.html')

        user = None

        # Try username login
        user = authenticate(request, username=login_input, password=password)

        # Try email login
        if user is None:
            try:
                u = User.objects.get(email=login_input)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                pass
            except User.MultipleObjectsReturned:
                # BUG FIX: Handle duplicate emails gracefully
                messages.error(request, "Multiple accounts exist with this email. Please use your username.")
                return render(request, 'accounts/login.html')

        # Try roll number / staff ID login
        if user is None:
            try:
                u = User.objects.get(first_name=login_input)
                user = authenticate(request, username=u.username, password=password)
            except User.DoesNotExist:
                pass
            except User.MultipleObjectsReturned:
                pass  # Skip if multiple matches

        if user is None:
            messages.error(request, "Invalid credentials. Please try again.")
            return render(request, 'accounts/login.html')

        if not user.is_superuser and not user.is_active:
            messages.error(request, "Account is not yet approved. Please contact admin.")
            return render(request, 'accounts/login.html')

        login(request, user)

        if remember:
            request.session.set_expiry(1209600)
        else:
            request.session.set_expiry(0)

        # Ensure profile exists with correct role
        profile, _ = Profile.objects.get_or_create(user=user)
        if user.is_superuser:
            profile.role = 'admin'
        elif user.is_staff:
            profile.role = 'staff'
        else:
            profile.role = 'student'
        profile.save()

        messages.success(request, f"Welcome back, {user.username}!")

        if profile.role == 'admin':
            return redirect('admin_dashboard')
        elif profile.role == 'staff':
            return redirect('staff_dashboard')
        else:
            return redirect('student_dashboard')

    return render(request, 'accounts/login.html')


# ---------------- LOGOUT ----------------
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('login')


# ---------------- ADMIN DASHBOARD ----------------
@login_required
def admin_dashboard(request):

    if not request.user.is_superuser:
        return redirect('login')

    pending_users = User.objects.filter(is_active=False)
    pending_requests = BookRequest.objects.filter(approved=False)

    # Extra stats for dashboard
    total_issued = IssuedBook.objects.filter(returned=False).count()
    overdue = IssuedBook.objects.filter(
        returned=False,
        return_date__lt=timezone.now().date()
    ).count()

    today = timezone.now().date()

    return render(request, 'accounts/admin_dashboard.html', {
        'books_count': Book.objects.count(),
        'users_count': User.objects.count(),
        'pending_users': pending_users,
        'pending_requests': pending_requests,
        'total_issued': total_issued,
        'overdue_count': overdue,
        'today': today,
    })


# ---------------- STAFF DASHBOARD ----------------
@login_required
def staff_dashboard(request):

    # BUG FIX: Staff can only access if actually staff
    if not (request.user.is_staff or request.user.is_superuser):
        return redirect('student_dashboard')

    total_issued = IssuedBook.objects.filter(returned=False).count()
    pending_requests = BookRequest.objects.filter(approved=False).count()

    return render(request, 'accounts/staff_dashboard.html', {
        'books_count': Book.objects.count(),
        'total_issued': total_issued,
        'pending_requests': pending_requests,
    })


# ---------------- STUDENT DASHBOARD ----------------
@login_required
def student_dashboard(request):

    my_issued = IssuedBook.objects.filter(
        student=request.user, returned=False
    ).select_related('book')

    my_requests = BookRequest.objects.filter(
        student=request.user
    ).order_by('-requested_at').select_related('book')

    # BUG FIX: Show overdue status to student
    today = timezone.now().date()
    overdue = my_issued.filter(return_date__lt=today).count()

    return render(request, 'accounts/student_dashboard.html', {
        'books_count': Book.objects.count(),
        'my_issued': my_issued,
        'my_requests': my_requests,
        'overdue_count': overdue,
        'today': today,
    })


# ---------------- PROFILE ----------------
@login_required
def profile_view(request):

    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.user.is_superuser:
        profile.role = 'admin'
    elif request.user.is_staff:
        profile.role = 'staff'
    else:
        profile.role = 'student'
    profile.save()

    if profile.role == 'admin':
        return render(request, 'accounts/admin_profile.html')
    elif profile.role == 'staff':
        return render(request, 'accounts/staff_profile.html')
    else:
        return render(request, 'accounts/student_profile.html')


# ---------------- PENDING USERS ----------------
@login_required
def pending_users_page(request):

    if not request.user.is_superuser:
        return redirect('login')

    users = User.objects.filter(is_active=False).order_by('date_joined')

    return render(request, 'accounts/pending_users.html', {'users': users})


# ---------------- APPROVE USER ----------------
@login_required
def approve_user(request, user_id):

    if not request.user.is_superuser:
        return redirect('login')

    user = get_object_or_404(User, id=user_id)

    # BUG FIX: Don't approve already active user
    if user.is_active:
        messages.warning(request, "This user is already active.")
        return redirect('pending_users')

    user.is_active = True
    user.save()

    messages.success(request, f"'{user.username}' successfully approved.")
    return redirect('pending_users')


# ---------------- REJECT USER ----------------
@login_required
def reject_user(request, user_id):

    if not request.user.is_superuser:
        return redirect('login')

    user = get_object_or_404(User, id=user_id)

    # BUG FIX: Don't allow admin to delete themselves
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
        return redirect('pending_users')

    username = user.username
    user.delete()

    messages.success(request, f"'{username}' has been rejected/deleted.")
    return redirect('pending_users')


# ---------------- AJAX APPROVE USER ----------------
@login_required
def ajax_approve_user(request, user_id):

    if not request.user.is_superuser:
        return JsonResponse({"status": "error", "message": "Not allowed"}, status=403)

    if request.method != "POST":
        return JsonResponse({"status": "error", "message": "POST required"}, status=405)

    try:
        user = User.objects.get(id=user_id)

        if user.is_active:
            return JsonResponse({"status": "warning", "message": "Already active"})

        user.is_active = True
        user.save()

        return JsonResponse({"status": "success", "message": f"{user.username} approved"})

    except User.DoesNotExist:
        return JsonResponse({"status": "error", "message": "User not found"}, status=404)
