from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # ================= PUBLIC PAGES =================
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # ================= AUTH =================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ================= ROLE SELECTION =================
    path('register/', views.select_role, name='select_role'),

    # ================= REGISTER =================
    path('register/student/', views.student_register, name='student_register'),
    path('register/staff/', views.staff_register, name='staff_register'),
    path('register/admin/', views.admin_register, name='admin_register'),

    # ================= DASHBOARDS =================
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/staff/', views.staff_dashboard, name='staff_dashboard'),
    path('dashboard/student/', views.student_dashboard, name='student_dashboard'),

    # ================= PROFILE =================
    path('profile/', views.profile_view, name='profile'),

    # ================= TERMS & CONDITIONS =================
    path('terms/', views.terms_conditions, name='terms_conditions'),
    
    # ================= USER MANAGEMENT =================
    path('user/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('user/reject/<int:user_id>/', views.reject_user, name='reject_user'),

    # ================= PASSWORD RESET =================

    # Step 1: Forgot Password Form
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/forgot_password.html'
        ),
        name='forgot_password'
    ),

    # Step 2: Email Sent Page
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    # Step 3: Reset Password (CONFIRM PAGE - IMPORTANT)
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    # Step 4: Success Page
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    # ================= AJAX =================
    path('pending-users/', views.pending_users_page, name='pending_users'),
    path('ajax/approve-user/<int:user_id>/', views.ajax_approve_user, name='ajax_approve_user'),
]