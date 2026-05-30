from django.urls import path
from . import views

urlpatterns = [

    path('', views.book_list, name='book_list'),

    path('add/', views.add_book, name='add_book'),

    path('edit/<int:id>/', views.edit_book, name='edit_book'),

    path('delete/<int:id>/', views.delete_book, name='delete_book'),

    path('issue-book/', views.issue_book, name='issue_book'),

    path('return-book/', views.return_book, name='return_book'),

    path(
        'return-book-action/<int:issue_id>/',
        views.return_book_action,
        name='return_book_action'
    ),

    path(
        'request-book/',
        views.request_book,
        name='request_book'
    ),

    path(
        'view-requests/',
        views.view_requests,
        name='view_requests'
    ),

    path(
        'approve-request/<int:request_id>/',
        views.approve_request,
        name='approve_request'
    ),

    path(
        'donate/',
        views.donate,
        name='donate'
    ),

    path(
        'donations/',
        views.donation_list,
        name='donation_list'
    ),

    path(
        'thank-you/',
        views.thank_you,
        name='thank_you'
    ),

    path('pending-requests/',
          views.pending_requests_page,
          name='pending_requests'
        ),

    path(
        'contact/',
        views.contact,
        name='contact'
    ),

    path(
        'contact-messages/',
        views.contact_messages,
        name='contact_messages'
    ),
]