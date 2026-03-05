from flask import current_app
from flask_mail import Mail, Message
from datetime import datetime

mail = Mail()

def send_booking_confirmation(email, username, slot_number, booking_date):
    """
    Send booking confirmation email
    
    Args:
        email: User's email address
        username: User's username
        slot_number: Parking slot number
        booking_date: Booking date and time
    """
    try:
        msg = Message(
            subject='Parking Slot Booking Confirmation',
            recipients=[email],
            html=f"""
            <html>
                <body>
                    <h2>Booking Confirmation</h2>
                    <p>Dear {username},</p>
                    <p>Your parking slot booking has been confirmed!</p>
                    <div style="background-color: #f0f0f0; padding: 15px; border-radius: 5px;">
                        <p><strong>Slot Number:</strong> {slot_number}</p>
                        <p><strong>Booking Date:</strong> {booking_date.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    <p>Please arrive before your booking time. If you need to cancel, please do so at least 1 hour before your booking.</p>
                    <p>Thank you for using Smart Parking Management System!</p>
                    <p>Best regards,<br>Smart Parking Team</p>
                </body>
            </html>
            """
        )
        
        mail.send(msg)
        return True
    
    except Exception as e:
        print(f"Email sending error: {e}")
        return False


def send_payment_reminder(email, username, amount_due):
    """
    Send payment reminder email
    
    Args:
        email: User's email address
        username: User's username
        amount_due: Amount pending for payment
    """
    try:
        msg = Message(
            subject='Parking Payment Reminder',
            recipients=[email],
            html=f"""
            <html>
                <body>
                    <h2>Payment Reminder</h2>
                    <p>Dear {username},</p>
                    <p>You have a pending parking payment.</p>
                    <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px;">
                        <p><strong>Amount Due:</strong> ${amount_due:.2f}</p>
                    </div>
                    <p>Please complete the payment within 24 hours to avoid additional charges.</p>
                    <p>Thank you!<br>Smart Parking Team</p>
                </body>
            </html>
            """
        )
        
        mail.send(msg)
        return True
    
    except Exception as e:
        print(f"Email sending error: {e}")
        return False