from django.db.models.signals import post_save
from django.dispatch import receiver
from jobs.models import Job
from profiles.models import Profile
from applications.models import Notification
from accounts.models import User

def normalize_skills(value):
    if isinstance(value, str):
        return {skill.strip().lower() for skill in value.split(',') if skill.strip()}
    if isinstance(value, (list, tuple, set)):
        return {str(skill).strip().lower() for skill in value if str(skill).strip()}
    return set()

@receiver(post_save, sender=Job)
def notify_matching_seekers(sender, instance, created, **kwargs):
    # Only trigger for new jobs
    if not created:
        return

    # If the job has no required skills, skip (or you can match by keywords)
    if not instance.skills_required:
        return

    # Normalise job skills to lowercase set
    job_skills = normalize_skills(instance.skills_required)
    if not job_skills:
        return

    # Get all active seekers
    seekers = User.objects.filter(role='seeker', is_active=True)

    for seeker in seekers:
        # Check if user wants to receive alerts (default True)
        if hasattr(seeker, 'alert_preference') and not seeker.alert_preference.receive_job_alerts:
            continue

        profile = Profile.objects.filter(user=seeker).first()
        if not profile or not profile.skills:
            continue

        # Normalise seeker skills
        seeker_skills = normalize_skills(profile.skills)

        # If intersection exists, send notification
        matching_skills = job_skills & seeker_skills
        if matching_skills:
            Notification.objects.create(
                recipient=seeker,
                sender=instance.posted_by,
                notification_type='job_alert',   # you may need to add this choice in Notification model
                title='New Job Matching Your Skills',
                message=f"New job '{instance.title}' at {instance.company} matches your skills: {', '.join(sorted(matching_skills))}",
                related_application=None
            )
