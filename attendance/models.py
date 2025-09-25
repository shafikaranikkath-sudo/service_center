from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
# Create your models here.


class CheckLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='check_logs')
    check_in_time = models.DateTimeField(default=timezone.now)
    check_out_time = models.DateTimeField(null=True, blank=True)


    class Meta:
        ordering = ['-check_in_time']



    def __str__(self):
        return f"{self.user.username} - {self.check_in_time:%Y-%m-%d %H:%M}"


    @property
    def is_open(self):
        return self.check_out_time is None
    
    @property
    def total_hours(self):
        """Return time worked (up to checkout, or until now if still open)."""
        if self.check_in_time:
            end_time = self.check_out_time or timezone.now()
            delta = end_time - self.check_in_time
            hours, remainder = divmod(delta.seconds, 3600)
            minutes = remainder // 60
            return f"{hours}h {minutes}m"
        return "-"
    
def user_profile_upload_path(instance, filename):
    # Each user’s profile picture goes into their own folder
    return f"profile_pics/user_{instance.user.id}/{filename}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_pic = models.ImageField(upload_to=user_profile_upload_path, default="default_profile.png", blank=True)

    def __str__(self):
        return f"{self.user.username} Profile"    