from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Transaction, ParkingSlot, Vehicle
from datetime import datetime, timedelta
from sqlalchemy import func

# Create blueprint
analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

def admin_required(fn):
    """Check if user is admin"""
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity['role'] != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return fn(*args, **kwargs)
    return wrapper

@analytics_bp.route('/occupancy-rate', methods=['GET'])
@jwt_required()
def occupancy_rate():
    """
    Get current occupancy rate
    """
    try:
        total_slots = ParkingSlot.query.count()
        occupied_slots = db.session.query(func.count(ParkingSlot.id)).filter(
            ParkingSlot.is_available == False
        ).scalar()
        
        if total_slots == 0:
            return jsonify({'error': 'No slots available'}), 404
        
        rate = (occupied_slots / total_slots) * 100
        
        return jsonify({
            'total_slots': total_slots,
            'occupied_slots': occupied_slots,
            'available_slots': total_slots - occupied_slots,
            'occupancy_rate': round(rate, 2)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/hourly-occupancy', methods=['GET'])
@jwt_required()
def hourly_occupancy():
    """
    Get occupancy trend over last 24 hours
    """
    try:
        # Get data for last 24 hours
        hours_data = []
        
        for i in range(24):
            hour_start = datetime.utcnow() - timedelta(hours=24-i)
            hour_end = hour_start + timedelta(hours=1)
            
            # Count transactions active during this hour
            active_count = Transaction.query.filter(
                Transaction.entry_time <= hour_end,
                (Transaction.exit_time == None) | (Transaction.exit_time >= hour_start)
            ).count()
            
            hours_data.append({
                'hour': hour_start.strftime('%H:00'),
                'active_vehicles': active_count
            })
        
        return jsonify(hours_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/revenue-stats', methods=['GET'])
@admin_required()
def revenue_stats():
    """
    Get revenue statistics (admin only)
    """
    try:
        # Total revenue
        total_revenue = db.session.query(func.sum(Transaction.fee)).filter(
            Transaction.payment_status == 'paid'
        ).scalar() or 0.0
        
        # Revenue today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_revenue = db.session.query(func.sum(Transaction.fee)).filter(
            Transaction.payment_status == 'paid',
            Transaction.exit_time >= today_start
        ).scalar() or 0.0
        
        # Revenue this month
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_revenue = db.session.query(func.sum(Transaction.fee)).filter(
            Transaction.payment_status == 'paid',
            Transaction.exit_time >= month_start
        ).scalar() or 0.0
        
        # Pending payments
        pending_amount = db.session.query(func.sum(Transaction.fee)).filter(
            Transaction.payment_status == 'pending',
            Transaction.exit_time != None
        ).scalar() or 0.0
        
        return jsonify({
            'total_revenue': float(total_revenue),
            'today_revenue': float(today_revenue),
            'month_revenue': float(month_revenue),
            'pending_payments': float(pending_amount),
            'currency': 'USD'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/daily-transactions', methods=['GET'])
@admin_required()
def daily_transactions():
    """
    Get transaction count per day for last 7 days (admin only)
    """
    try:
        days_data = []
        
        for i in range(7, 0, -1):
            day_start = (datetime.utcnow() - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = Transaction.query.filter(
                Transaction.entry_time >= day_start,
                Transaction.entry_time < day_end
            ).count()
            
            days_data.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'transactions': count
            })
        
        return jsonify(days_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@analytics_bp.route('/peak-hours', methods=['GET'])
@jwt_required()
def peak_hours():
    """
    Get peak parking hours
    """
    try:
        peak_hours_data = []
        
        for hour in range(24):
            count = Transaction.query.filter(
                func.hour(Transaction.entry_time) == hour
            ).count()
            
            peak_hours_data.append({
                'hour': f"{hour:02d}:00",
                'vehicles': count
            })
        
        # Sort by vehicle count
        peak_hours_data.sort(key=lambda x: x['vehicles'], reverse=True)
        
        return jsonify(peak_hours_data[:5]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500