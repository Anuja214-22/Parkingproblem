from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Booking, ParkingSlot, User
from utils.email_sender import send_booking_confirmation
from datetime import datetime

# Create blueprint
booking_bp = Blueprint('booking', __name__, url_prefix='/api/booking')

@booking_bp.route('/reserve-slot', methods=['POST'])
@jwt_required()
def reserve_slot():
    """
    Book/reserve a parking slot for future use
    Required JSON fields: slot_id, booking_date
    """
    try:
        identity = get_jwt_identity()
        data = request.get_json()
        
        if not data or not all(k in data for k in ('slot_id', 'booking_date')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Find slot
        slot = ParkingSlot.query.get(data['slot_id'])
        if not slot:
            return jsonify({'error': 'Slot not found'}), 404
        
        # Parse booking date
        try:
            booking_date = datetime.fromisoformat(data['booking_date'])
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Check for existing booking at same time
        existing_booking = Booking.query.filter(
            Booking.slot_id == data['slot_id'],
            Booking.booking_date == booking_date,
            Booking.status.in_(['pending', 'confirmed'])
        ).first()
        
        if existing_booking:
            return jsonify({'error': 'Slot already booked for this time'}), 409
        
        # Create booking
        booking = Booking(
            user_id=identity['id'],
            slot_id=data['slot_id'],
            booking_date=booking_date,
            status='confirmed'
        )
        
        db.session.add(booking)
        db.session.commit()
        
        # Send confirmation email
        user = User.query.get(identity['id'])
        try:
            send_booking_confirmation(user.email, user.username, slot.slot_number, booking_date)
        except:
            pass  # Email sending failure doesn't block booking
        
        return jsonify({
            'message': 'Slot booked successfully',
            'booking': booking.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/bookings', methods=['GET'])
@jwt_required()
def get_user_bookings():
    """
    Get all bookings made by the current user
    """
    try:
        identity = get_jwt_identity()
        bookings = Booking.query.filter_by(user_id=identity['id']).all()
        
        return jsonify([booking.to_dict() for booking in bookings]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/bookings/<int:booking_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_booking(booking_id):
    """
    Cancel a booking
    """
    try:
        identity = get_jwt_identity()
        booking = Booking.query.get(booking_id)
        
        if not booking:
            return jsonify({'error': 'Booking not found'}), 404
        
        if booking.user_id != identity['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        booking.status = 'cancelled'
        db.session.commit()
        
        return jsonify({
            'message': 'Booking cancelled successfully',
            'booking': booking.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@booking_bp.route('/available-slots', methods=['GET'])
def get_available_slots():
    """
    Get available slots for booking on a specific date
    Query parameter: date (ISO format)
    """
    try:
        date_str = request.args.get('date')
        
        if not date_str:
            return jsonify({'error': 'Missing date parameter'}), 400
        
        try:
            target_date = datetime.fromisoformat(date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
        
        # Get all slots
        all_slots = ParkingSlot.query.all()
        
        # Get booked slots for this date
        booked_bookings = Booking.query.filter(
            Booking.booking_date >= target_date,
            Booking.booking_date < target_date.replace(day=target_date.day + 1),
            Booking.status.in_(['pending', 'confirmed'])
        ).all()
        
        booked_slot_ids = [b.slot_id for b in booked_bookings]
        
        # Return available slots
        available_slots = [
            slot.to_dict() for slot in all_slots 
            if slot.id not in booked_slot_ids
        ]
        
        return jsonify(available_slots), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500