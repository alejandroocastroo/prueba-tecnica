"""
Celery tasks for the shipments app.
"""
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_shipment_notification(shipment_id, notification_type):
    """
    Send notification for shipment status changes.

    Args:
        shipment_id: ID of the shipment
        notification_type: Type of notification ('shipped' or 'delivered')
    """
    from .models import Shipment

    try:
        shipment = Shipment.objects.select_related('order__user').get(id=shipment_id)
        user = shipment.order.user

        if notification_type == 'shipped':
            message = (
                f"Your order #{shipment.order_id} has been shipped! "
                f"Tracking number: {shipment.tracking_number}"
            )
        elif notification_type == 'delivered':
            message = f"Your order #{shipment.order_id} has been delivered!"
        else:
            message = f"Shipment status updated for order #{shipment.order_id}"

        # In production, this would send an email/SMS/push notification
        # For now, we just log it
        logger.info(
            f"Notification sent to {user.email}: {message}"
        )

        return {
            'success': True,
            'user_email': user.email,
            'message': message,
            'notification_type': notification_type
        }

    except Shipment.DoesNotExist:
        logger.error(f"Shipment {shipment_id} not found")
        return {'success': False, 'error': 'Shipment not found'}
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task
def check_delayed_shipments():
    """
    Check for shipments that haven't been shipped within expected timeframe.
    This task can be scheduled to run periodically.
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import Shipment

    threshold = timezone.now() - timedelta(days=3)

    delayed_shipments = Shipment.objects.filter(
        status=Shipment.Status.PENDING,
        created_at__lt=threshold
    ).select_related('order__user')

    for shipment in delayed_shipments:
        logger.warning(
            f"Delayed shipment #{shipment.id} for order #{shipment.order_id} "
            f"(created: {shipment.created_at})"
        )

    return {
        'delayed_count': delayed_shipments.count(),
        'shipment_ids': list(delayed_shipments.values_list('id', flat=True))
    }
