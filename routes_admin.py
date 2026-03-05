from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, ParkingSlot, Vehicle, Transaction
from functools import wraps

# Create blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_required(fn):
    """Decorator to check if user is admin"""
    @wraps(fn)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        identity = get_jwt_identity()
        if identity['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return decorated_function

# ============ PARKING SLOT MANAGEMENT ============

@admin_bp.route('/slots', methods=['POST'])
@admin_required
def add_slot():
    """
    Add a new parking slot
    Required JSON fields: slot_number
    """
    try:
        data = request.get_json()
        
        if not data or not data.get('slot_number'):
            return jsonify({'error': 'Missing slot_number'}), 400
        
        # Check if slot already exists
        if ParkingSlot.query.filter_by(slot_number=data['slot_number']).first():
            return jsonify({'error': 'Slot already exists'}), 409
        
        slot = ParkingSlot(slot_number=data['slot_number'])
        db.session.add(slot)
        db.session.commit()
        
        return jsonify({
            'message': 'Slot created successfully',
            'slot': slot.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/slots', methods=['GET'])
@admin_required
def get_all_slots():
    """
    Get all parking slots with their status
    """
    try:
        slots = ParkingSlot.query.all()
        return jsonify([slot.to_dict() for slot in slots]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/slots/<int:slot_id>', methods=['PUT'])
@admin_required
def update_slot(slot_id):
    """
    Update parking slot details
    Optional JSON fields: slot_number, is_available
    """
    try:
        slot = ParkingSlot.query.get(slot_id)
        
        if not slot:
            return jsonify({'error': 'Slot not found'}), 404
        
        data = request.get_json()
        
        if 'slot_number' in data:
            # Check if new slot number is unique
            existing = ParkingSlot.query.filter_by(slot_number=data['slot_number']).first()
            if existing and existing.id != slot_id:
                return jsonify({'error': 'Slot number already exists'}), 409
            slot.slot_number = data['slot_number']
        
        if 'is_available' in data:
            slot.is_available = data['is_available']
        
        db.session.commit()
        
        return jsonify({
            'message': 'Slot updated successfully',
            'slot': slot.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/slots/<int:slot_id>', methods=['DELETE'])
@admin_required
def delete_slot(slot_id):
    """
    Delete a parking slot
    """
    try:
        slot = ParkingSlot.query.get(slot_id)
        
        if not slot:
            return jsonify({'error': 'Slot not found'}), 404
        
        # Check if slot has active vehicles
        if slot.vehicles:
            return jsonify({'error': 'Cannot delete slot with parked vehicles'}), 409
        
        db.session.delete(slot)
        db.session.commit()
        
        return jsonify({'message': 'Slot deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============ ADMIN DASHBOARD ============

@admin_bp.route('/dashboard/stats', methods=['GET'])
@admin_required
def dashboard_stats():
    """
    Get parking management statistics for admin dashboard
    """
    try:
        total_slots = ParkingSlot.query.count()
        occupied_slots = ParkingSlot.query.filter_by(is_available=False).count()
        available_slots = total_slots - occupied_slots
        
        total_vehicles = Vehicle.query.count()
        parked_vehicles = Vehicle.query.filter_by(is_parked=True).count()
        
        total_transactions = Transaction.query.count()
        pending_payments = Transaction.query.filter_by(payment_status='pending').count()
        completed_payments = total_transactions - pending_payments
        
        total_revenue = db.session.query(db.func.sum(Transaction.fee)).filter(
            Transaction.payment_status == 'paid'
        ).scalar() or 0.0
        
        return jsonify({
            'total_slots': total_slots,
            'available_slots': available_slots,
            'occupied_slots': occupied_slots,
            'occupancy_rate': round((occupied_slots / total_slots * 100) if total_slots > 0 else 0, 2),
            'total_vehicles': total_vehicles,
            'parked_vehicles': parked_vehicles,
            'total_transactions': total_transactions,
            'pending_payments': pending_payments,
            'completed_payments': completed_payments,
            'total_revenue': float(total_revenue)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/transactions', methods=['GET'])
@admin_required
def view_all_transactions():
    """
    Get all parking transactions for admin review
    """
    try:
        # Pagination support
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        pagination = Transaction.query.paginate(page=page, per_page=per_page)
        transactions = [t.to_dict() for t in pagination.items]
        
        return jsonify({
            'transactions': transactions,
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """
    Get all registered users
    """
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """
    Delete a user account (admin only)
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if user.role == 'admin':
            return jsonify({'error': 'Cannot delete admin users'}), 403
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': 'User deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500