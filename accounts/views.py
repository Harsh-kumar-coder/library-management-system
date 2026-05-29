from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST


from books.models import Book, BookRequest
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

    if request.method == 'POST':

        username = request.POST.get('username')
        roll_number = request.POST.get('roll_number')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:

            messages.error(request, "Passwords do not match")

            return redirect('student_register')

        if User.objects.filter(username=username).exists():

            messages.error(request, "Username already exists")

            return redirect('student_register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=roll_number,
            is_active=False
        )

        Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'student'}
        )

        messages.success(
            request,
            "Student account created. Wait for admin approval."
        )

        return redirect('login')

    return render(request, 'accounts/student_register.html')

# ---------------- STAFF REGISTER ----------------
def staff_register(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        staff_id = request.POST.get('staff_id')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:

            messages.error(request, "Passwords do not match")

            return redirect('staff_register')

        if User.objects.filter(username=username).exists():

            messages.error(request, "Username already exists")

            return redirect('staff_register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=staff_id,
            is_staff=True,
            is_active=False
        )

        Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'staff'}
        )

        messages.success(
            request,
            "Staff account created. Wait for admin approval."
        )

        return redirect('login')

    return render(request, 'accounts/staff_register.html')

# ---------------- ADMIN REGISTER ----------------
def admin_register(request):

    if request.method == 'POST':

        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        admin_code = request.POST.get('admin_code')

        if password != confirm_password:

            messages.error(request, "Passwords do not match")

            return redirect('admin_register')

        if admin_code != "ADMIN123":

            messages.error(request, "Invalid admin code")

            return redirect('admin_register')

        if User.objects.filter(username=username).exists():

            messages.error(request, "Username already exists")

            return redirect('admin_register')

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True,
            is_active=True
        )

        Profile.objects.get_or_create(
            user=user,
            defaults={'role': 'admin'}
        )

        messages.success(
            request,
            "Admin account created successfully"
        )

        return redirect('login')

    return render(request, 'accounts/admin_register.html')

# ---------------- LOGIN ----------------
def login_view(request):

    if request.method == 'POST':

        login_input = request.POST.get('username')
        password = request.POST.get('password')

        user = None

        # USERNAME LOGIN
        user = authenticate(
            request,
            username=login_input,
            password=password
        )

        # EMAIL LOGIN
        if user is None:

            try:

                u = User.objects.get(email=login_input)

                user = authenticate(
                    request,
                    username=u.username,
                    password=password
                )

            except:

                pass

        # ROLL / STAFF ID LOGIN
        if user is None:

            try:

                u = User.objects.get(first_name=login_input)

                user = authenticate(
                    request,
                    username=u.username,
                    password=password
                )

            except:

                pass

        if user is None:

            messages.error(request, "Invalid credentials")

            return redirect('login')

        if not user.is_superuser and not user.is_active:

            messages.error(
                request,
                "Account not approved yet!"
            )

            return redirect('login')

        login(request, user)

        messages.success(
            request,
            "Login successful"
        )

        # SAFE PROFILE
        profile, created = Profile.objects.get_or_create(
            user=user
        )

        # AUTO FIX ROLE
        if user.is_superuser:

            profile.role = 'admin'

        elif user.is_staff:

            profile.role = 'staff'

        else:

            profile.role = 'student'

        profile.save()

        # REDIRECT
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

    messages.success(
        request,
        "Logged out successfully"
    )

    return redirect('login')


# ---------------- ADMIN DASHBOARD ----------------
@login_required
def admin_dashboard(request):

    if not request.user.is_superuser:

        return redirect('login')

    pending_users = User.objects.filter(
        is_active=False
    )

    pending_requests = BookRequest.objects.filter(
        approved=False
    )

    return render(request, 'accounts/admin_dashboard.html', {

        'books_count': Book.objects.count(),

        'users_count': User.objects.count(),

        'pending_users': pending_users,

        'pending_requests': pending_requests

    })


# ---------------- STAFF DASHBOARD ----------------
@login_required
def staff_dashboard(request):

    return render(request, 'accounts/staff_dashboard.html', {

        'books_count': Book.objects.count()

    })


# ---------------- STUDENT DASHBOARD ----------------
@login_required
def student_dashboard(request):

    return render(request, 'accounts/student_dashboard.html', {

        'books_count': Book.objects.count()

    })


# ---------------- PROFILE ----------------
@login_required
def profile_view(request):

    profile, created = Profile.objects.get_or_create(
        user=request.user
    )

    if request.user.is_superuser:

        profile.role = 'admin'

    elif request.user.is_staff:

        profile.role = 'staff'

    else:

        profile.role = 'student'

    profile.save()

    if profile.role == "admin":

        return render(request, 'accounts/admin_profile.html')

    elif profile.role == "staff":

        return render(request, 'accounts/staff_profile.html')

    else:

        return render(request, 'accounts/student_profile.html')

# ---------------- PENDING USERS ----------------
@login_required
def pending_users_page(request):
    if not request.user.is_superuser:
        return redirect('login')

    users = User.objects.filter(is_active=False)

    return render(request, 'accounts/pending_users.html', {
        'users': users
    })

# ---------------- APPROVE USER ----------------
@login_required
def approve_user(request, user_id):

    if not request.user.is_superuser:

        return redirect('login')

    user = get_object_or_404(
        User,
        id=user_id
    )

    user.is_active = True

    user.save()

    messages.success(
        request,
        "User approved successfully"
    )

    return redirect('admin_dashboard')


# ---------------- REJECT USER ----------------
@login_required
def reject_user(request, user_id):

    if not request.user.is_superuser:

        return redirect('login')

    user = get_object_or_404(
        User,
        id=user_id
    )

    user.delete()

    messages.success(
        request,
        "User rejected successfully"
    )

    return redirect('admin_dashboard')

# ---------------- AJAX APPROVE USER ----------------
@login_required
def ajax_approve_user(request, user_id):

    if not request.user.is_superuser:
        return JsonResponse({
            "status": "error",
            "message": "Not allowed"
        })

    if request.method == "POST":

        try:
            user = User.objects.get(id=user_id)
            user.is_active = True
            user.save()

            return JsonResponse({
                "status": "success",
                "message": "User approved"
            })

        except User.DoesNotExist:
            return JsonResponse({
                "status": "error",
                "message": "User not found"
            })

    return JsonResponse({
        "status": "error",
        "message": "Invalid request"
    })