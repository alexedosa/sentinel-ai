from django.conf import settings
from django.db import models


class Activity(models.Model):
    SOURCE_GITHUB = "github"
    external_id = models.CharField(
        max_length=255,
        unique=True
    )

    source = models.CharField(
        max_length=50
    )

    repository = models.CharField(
        max_length=255
    )

    project = models.CharField(
        max_length=100
    )

    activity_type = models.CharField(
        max_length=100
    )

    subject = models.CharField(
        max_length=200
    )

    summary = models.TextField()

    occurred_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.project} - {self.subject}"


class ProjectState(models.Model):
    project = models.CharField(
        max_length=100,
        unique=True
    )

    current_focus = models.CharField(
        max_length=255
    )

    status = models.CharField(
        max_length=50
    )

    summary = models.TextField()

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.project


class UserSignal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="signals",
        null=True,
        blank=True,
    )

    request = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.request[:80]

class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True,
        db_index=True,
    )

    title = models.CharField(
        max_length=200,
        default="New conversation"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title


class Message(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )

    role = models.CharField(
        max_length=20
    )

    content = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.role}: {self.content[:80]}"