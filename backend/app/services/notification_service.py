"""
Notification service.
Handles sending notifications to users.
"""

from typing import Optional
from app.core.config import settings
from app.core.logger import logger

class NotificationService:
    """
    Service for managing user notifications.
    """

    def __init__(self):
        # In production, this would integrate with email services, push notifications, etc.
        pass

    def send_notification(
        self,
        user_id: int,
        title: str,
        message: str,
        notification_type: str = "system"
    ) -> bool:
        """
        Send a notification to a user.

        Args:
            user_id: User ID to send notification to
            title: Notification title
            message: Notification message
            notification_type: Type of notification

        Returns:
            True if notification was sent successfully
        """
        try:
            # In a real implementation, this would:
            # 1. Store notification in database
            # 2. Send email if configured
            # 3. Send push notification if applicable
            # 4. Send SMS if configured

            logger.info(f"Notification sent to user {user_id}: {title}")

            # For now, just log the notification
            return True

        except Exception as e:
            logger.error(f"Failed to send notification to user {user_id}: {e}")
            return False

    def send_job_match_notification(
        self,
        user_id: int,
        job_title: str,
        company: str,
        match_score: float
    ) -> bool:
        """
        Send notification for a high job match.

        Args:
            user_id: User ID
            job_title: Job title
            company: Company name
            match_score: ATS match score

        Returns:
            True if notification was sent successfully
        """
        title = f"High Job Match: {job_title}"
        message = f"Great news! Your resume matches {match_score:.1f}% with {job_title} at {company}. Consider applying!"

        return self.send_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="job_match"
        )

    def send_weekly_summary(
        self,
        user_id: int,
        total_matches: int,
        high_matches: int
    ) -> bool:
        """
        Send weekly summary of job matches.

        Args:
            user_id: User ID
            total_matches: Total number of matches this week
            high_matches: Number of high-scoring matches

        Returns:
            True if notification was sent successfully
        """
        title = "Weekly Job Match Summary"
        message = f"This week you had {total_matches} job matches, with {high_matches} high-scoring opportunities. Keep up the great work!"

        return self.send_notification(
            user_id=user_id,
            title=title,
            message=message,
            notification_type="weekly_summary"
        )

    def send_email_notification(
        self,
        email: str,
        subject: str,
        body: str
    ) -> bool:
        """
        Send email notification (if email is configured).

        Args:
            email: Recipient email
            subject: Email subject
            body: Email body

        Returns:
            True if email was sent successfully
        """
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP not configured, skipping email notification")
            return False

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            msg = MIMEMultipart()
            msg['From'] = settings.EMAIL_FROM
            msg['To'] = email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            text = msg.as_string()
            server.sendmail(settings.EMAIL_FROM, email, text)
            server.quit()

            logger.info(f"Email sent to {email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            return False
