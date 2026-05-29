from django.contrib import admin
from .models import Book, IssuedBook

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'title',
        'author',
        'isbn',
        'quantity',
        'added_at',
    )

    list_filter = (
        'added_at',
    )


@admin.register(IssuedBook)
class IssuedBookAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'student',
        'book',
        'issue_date',
        'returned',
    )