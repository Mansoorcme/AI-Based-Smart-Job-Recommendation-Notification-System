"""
Notifications API endpoints.
Handles user notifications for job matches.
"""

from typing import Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core import security
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationInDB
from app.services.notification_service import NotificationService

router = APIRouter()

@router.get("/", response_model=List[NotificationInDB])
def read_notifications(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Get user's notifications.
    """
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return notifications

@router.put("/{notification_id}/read")
def mark_notification_read(
    *,
    db: Session = Depends(get_db),
    notification_id: int,
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Mark a notification as read.
    """
    notification = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()

    return {"message": "Notification marked as read"}

@router.post("/send-test")
def send_test_notification(
    current_user: User = Depends(security.get_current_user),
) -> Any:
    """
    Send a test notification (for development).
    """
    notification_service = NotificationService()
    notification_service.send_notification(
        user_id=current_user.id,
        title="Test Notification",
        message="This is a test notification from the Job Matching System.",
        notification_type="test"
    )

    return {"message": "Test notification sent"}
