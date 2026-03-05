from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Vehicle, ParkingSlot, Transaction, User
from utils.fee_calculator import calculate_parking_fee
from utils.qr_generator import generate_qr_code
from datetime import datetime
from sqlalchemy import and_

# Create blueprint
parking_bp = Blueprint('parking', __name__, url_prefix='/api/parking')

# ============ VEHICLE MANAGEMENT ============

@parking_bp.route('/vehicles', methods=['POST'])
@jwt_required()
def register_vehicle():
    """
    Register a new vehicle for the user
    Required JSON fields: vehicle_number, vehicle_type (optional)
    """
    try:
        identity = get_jwt_identity()
        data = request.get_json()
        
        if not data or not data.get('vehicle_number'):
            return jsonify({'error': 'Missing vehicle_number'}), 400
        
        # Check if vehicle already registered
        if Vehicle.query.filter_by(vehicle_number=data['vehicle_number']).first():
            return jsonify({'error': 'Vehicle already registered'}), 409
        
        vehicle = Vehicle(
            user_id=identity['id'],
            vehicle_number=data['vehicle_number'],
            vehicle_type=data.get('vehicle_type', 'car')
        )
        
        db.session.add(vehicle)
        db.session.commit()
        
        return jsonify({
            'message': 'Vehicle registered successfully',
            'vehicle': vehicle.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/vehicles', methods=['GET'])
@jwt_required()
def get_user_vehicles():
    """
    Get all vehicles registered by the current user
    """
    try:
        identity = get_jwt_identity()
        vehicles = Vehicle.query.filter_by(user_id=identity['id']).all()
        
        return jsonify([vehicle.to_dict() for vehicle in vehicles]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/vehicles/<int:vehicle_id>', methods=['DELETE'])
@jwt_required()
def delete_vehicle(vehicle_id):
    """
    Delete a registered vehicle (owner only)
    """
    try:
        identity = get_jwt_identity()
        vehicle = Vehicle.query.get(vehicle_id)
        
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        if vehicle.user_id != identity['id']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Check if vehicle is currently parked
        if vehicle.is_parked:
            return jsonify({'error': 'Cannot delete vehicle while parked'}), 409
        
        db.session.delete(vehicle)
        db.session.commit()
        
        return jsonify({'message': 'Vehicle deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============ PARKING ENTRY ============

@parking_bp.route('/entry', methods=['POST'])
@jwt_required()
def vehicle_entry():
    """
    Record vehicle entry into parking lot
    Required JSON fields: vehicle_number, slot_id
    """
    try:
        identity = get_jwt_identity()
        data = request.get_json()
        
        if not data or not all(k in data for k in ('vehicle_number', 'slot_id')):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Find vehicle
        vehicle = Vehicle.query.filter_by(vehicle_number=data['vehicle_number']).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not registered'}), 404
        
        # Find slot
        slot = ParkingSlot.query.get(data['slot_id'])
        if not slot:
            return jsonify({'error': 'Slot not found'}), 404
        
        if not slot.is_available:
            return jsonify({'error': 'Slot not available'}), 409
        
        # Check if vehicle is already parked
        if vehicle.is_parked:
            return jsonify({'error': 'Vehicle already parked'}), 409
        
        # Create transaction
        transaction = Transaction(
            vehicle_id=vehicle.id,
            slot_id=slot.id,
            entry_time=datetime.utcnow(),
            booking_reference=f"PARK{vehicle.id}{slot.id}{datetime.utcnow().timestamp()}"
        )
        
        # Generate QR code
        qr_data = f"Vehicle: {vehicle.vehicle_number}, Slot: {slot.slot_number}, Entry: {transaction.entry_time}"
        transaction.qr_code = generate_qr_code(qr_data)
        
        # Update vehicle and slot status
        vehicle.is_parked = True
        vehicle.current_slot_id = slot.id
        slot.is_available = False
        
        db.session.add(transaction)
        db.session.commit()
        
        return jsonify({
            'message': 'Vehicle entry recorded',
            'transaction': transaction.to_dict(),
            'qr_code': transaction.qr_code
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============ PARKING EXIT ============

@parking_bp.route('/exit', methods=['POST'])
@jwt_required()
def vehicle_exit():
    """
    Record vehicle exit and calculate parking fee
    Required JSON fields: vehicle_number
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('vehicle_number'):
            return jsonify({'error': 'Missing vehicle_number'}), 400
        
        # Find vehicle
        vehicle = Vehicle.query.filter_by(vehicle_number=data['vehicle_number']).first()
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        if not vehicle.is_parked:
            return jsonify({'error': 'Vehicle not currently parked'}), 409
        
        # Find active transaction
        transaction = Transaction.query.filter(
            and_(
                Transaction.vehicle_id == vehicle.id,
                Transaction.exit_time == None
            )
        ).first()
        
        if not transaction:
            return jsonify({'error': 'No active parking session'}), 404
        
        # Record exit time and calculate fee
        exit_time = datetime.utcnow()
        transaction.exit_time = exit_time
        transaction.fee = calculate_parking_fee(transaction.entry_time, exit_time)
        
        # Update vehicle status
        vehicle.is_parked = False
        vehicle.current_slot_id = None
        
        # Update slot availability
        slot = transaction.slot
        slot.is_available = True
        
        db.session.commit()
        
        return jsonify({
            'message': 'Vehicle exit recorded',
            'transaction': transaction.to_dict(),
            'parking_duration': f"{(exit_time - transaction.entry_time).total_seconds() / 3600:.2f} hours",
            'amount_due': transaction.fee
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============ PARKING SLOTS VIEW ============

@parking_bp.route('/slots', methods=['GET'])
def get_slots():
    """
    Get all parking slots with availability status (public endpoint)
    """
    try:
        slots = ParkingSlot.query.all()
        return jsonify([slot.to_dict() for slot in slots]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/slots/<int:slot_id>', methods=['GET'])
def get_slot_details(slot_id):
    """
    Get details of a specific slot
    """
    try:
        slot = ParkingSlot.query.get(slot_id)
        
        if not slot:
            return jsonify({'error': 'Slot not found'}), 404
        
        return jsonify(slot.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ VEHICLE SEARCH ============

@parking_bp.route('/search', methods=['GET'])
@jwt_required()
def search_vehicle():
    """
    Search for vehicle by vehicle number
    Query parameter: vehicle_number
    """
    try:
        vehicle_number = request.args.get('vehicle_number')
        
        if not vehicle_number:
            return jsonify({'error': 'Missing vehicle_number parameter'}), 400
        
        vehicle = Vehicle.query.filter_by(vehicle_number=vehicle_number).first()
        
        if not vehicle:
            return jsonify({'error': 'Vehicle not found'}), 404
        
        result = vehicle.to_dict()
        result['status'] = 'parked' if vehicle.is_parked else 'not_parked'
        
        if vehicle.is_parked:
            slot = ParkingSlot.query.get(vehicle.current_slot_id)
            result['current_slot'] = slot.to_dict() if slot else None
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ PARKING HISTORY ============

@parking_bp.route('/history', methods=['GET'])
@jwt_required()
def get_parking_history():
    """
    Get parking history for the current user
    """
    try:
        identity = get_jwt_identity()
        
        # Get all vehicles of user and their transactions
        vehicles = Vehicle.query.filter_by(user_id=identity['id']).all()
        vehicle_ids = [v.id for v in vehicles]
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = Transaction.query.filter(
            Transaction.vehicle_id.in_(vehicle_ids)
        ).order_by(Transaction.entry_time.desc()).paginate(page=page, per_page=per_page)
        
        transactions = [t.to_dict() for t in pagination.items]
        
        return jsonify({
            'transactions': transactions,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============ PAYMENT STATUS ============

@parking_bp.route('/payment/<int:transaction_id>', methods=['POST'])
@jwt_required()
def process_payment(transaction_id):
    """
    Process payment for a parking transaction
    """
    try:
        transaction = Transaction.query.get(transaction_id)
        
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        # Check if already paid
        if transaction.payment_status == 'paid':
            return jsonify({'error': 'Already paid'}), 409
        
        # In a real application, integrate with payment gateway (Stripe, PayPal, etc.)
        # For now, we simulate successful payment
        transaction.payment_status = 'paid'
        db.session.commit()
        
        return jsonify({
            'message': 'Payment processed successfully',
            'transaction': transaction.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@parking_bp.route('/pending-payments', methods=['GET'])
@jwt_required()
def get_pending_payments():
    """
    Get all pending payments for the user
    """
    try:
        identity = get_jwt_identity()
        
        vehicles = Vehicle.query.filter_by(user_id=identity['id']).all()
        vehicle_ids = [v.id for v in vehicles]
        
        pending = Transaction.query.filter(
            and_(
                Transaction.vehicle_id.in_(vehicle_ids),
                Transaction.payment_status == 'pending',
                Transaction.exit_time != None
            )
        ).all()
        
        return jsonify([t.to_dict() for t in pending]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500