from django.contrib import admin
from .models import Book, IssuedBook, Donation, BookRequest, ContactMessage

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display=('id','title','author','isbn','quantity','added_at')
    list_filter=('added_at',)
    search_fields=('title','author','isbn')

@admin.register(IssuedBook)
class IssuedBookAdmin(admin.ModelAdmin):
    list_display=('id','student','book','issue_date','return_date','fine','returned')
    list_filter=('returned','issue_date')
    search_fields=('student__username','book__title')

@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display=('id','student','book','requested_at','approved')
    list_filter=('approved','requested_at')
    search_fields=('student__username','book__title')

@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display=('id','name','amount','created_at')
    list_filter=('created_at',)
    search_fields=('name','message')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display=('id','name','email','subject','created_at')
    list_filter=('created_at',)
    search_fields=('name','email','subject')