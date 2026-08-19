from django.db import models


class Activity(models.Model):
    project = models.CharField(max_length=100)
    activity_type = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    status = models.CharField(max_length=50)
    summary = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project} - {self.subject}"


class ProjectState(models.Model):
    project = models.CharField(max_length=100, unique=True)
    current_focus = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    summary = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.project