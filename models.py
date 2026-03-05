from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    """User model for authentication and identification"""
    __tablename__ = 'Users'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password hash"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }


class ParkingSlot(db.Model):
    """Parking Slot model for slot management"""
    __tablename__ = 'Parking_Slots'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slot_number = db.Column(db.String(20), unique=True, nullable=False)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicles = db.relationship('Vehicle', backref='parking_slot', lazy=True, cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='slot', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'slot_number': self.slot_number,
            'is_available': self.is_available,
            'created_at': self.created_at.isoformat()
        }


class Vehicle(db.Model):
    """Vehicle model for vehicle tracking"""
    __tablename__ = 'Vehicles'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id', ondelete='CASCADE'), nullable=False)
    vehicle_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(20), default='car')  # car, bike, truck
    current_slot_id = db.Column(db.Integer, db.ForeignKey('Parking_Slots.id', ondelete='SET NULL'), nullable=True)
    is_parked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    transactions = db.relationship('Transaction', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'vehicle_number': self.vehicle_number,
            'vehicle_type': self.vehicle_type,
            'current_slot_id': self.current_slot_id,
            'is_parked': self.is_parked,
            'created_at': self.created_at.isoformat()
        }


class Transaction(db.Model):
    """Transaction model for parking sessions and fee tracking"""
    __tablename__ = 'Transactions'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('Vehicles.id', ondelete='CASCADE'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('Parking_Slots.id', ondelete='CASCADE'), nullable=False)
    entry_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    exit_time = db.Column(db.DateTime, nullable=True)
    fee = db.Column(db.Float, nullable=True)
    payment_status = db.Column(db.String(20), default='pending')  # 'pending' or 'paid'
    qr_code = db.Column(db.Text, nullable=True)  # Base64 encoded QR code
    booking_reference = db.Column(db.String(50), unique=True, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'slot_id': self.slot_id,
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat() if self.exit_time else None,
            'fee': self.fee,
            'payment_status': self.payment_status,
            'qr_code': self.qr_code,
            'booking_reference': self.booking_reference
        }


class Booking(db.Model):
    """Booking model for slot pre-reservations"""
    __tablename__ = 'Bookings'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('Users.id', ondelete='CASCADE'), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey('Parking_Slots.id', ondelete='CASCADE'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'confirmed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='bookings')
    slot = db.relationship('ParkingSlot', backref='bookings')
    
    def to_dict(self):
        """Convert to dictionary for JSON response"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'slot_id': self.slot_id,
            'booking_date': self.booking_date.isoformat(),
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }