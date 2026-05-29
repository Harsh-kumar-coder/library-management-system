from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ---------------- BOOK MODEL ----------------
class Book(models.Model):

    title = models.CharField(
        max_length=200
    )

    author = models.CharField(
        max_length=200
    )

    isbn = models.CharField(
        max_length=100,
        default='N/A'
    )

    quantity = models.IntegerField(
        default=1
    )

    added_at = models.DateTimeField(
        default=timezone.now
    )

    def __str__(self):
        return self.title


# ---------------- ISSUED BOOK MODEL ----------------
class IssuedBook(models.Model):

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE
    )

    issue_date = models.DateField()

    return_date = models.DateField(
        null=True,
        blank=True
    )

    fine = models.IntegerField(
        default=0
    )

    returned = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.student.username} - {self.book.title}"


# ---------------- BOOK REQUEST MODEL ----------------
class BookRequest(models.Model):

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    book = models.ForeignKey(
        Book,
        on_delete=models.CASCADE
    )

    requested_at = models.DateTimeField(
        default=timezone.now
    )

    approved = models.BooleanField(
        default=False
    )

    def __str__(self):
        return f"{self.student.username} requested {self.book.title}"


# ---------------- DONATION MODEL ----------------
class Donation(models.Model):

    name = models.CharField(
        max_length=100,
        blank=True
    )

    amount = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    message = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name or "Anonymous"