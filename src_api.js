import axios from 'axios';
import { jwtDecode } from 'jwt-decode';

// API Base URL
const API_BASE_URL = 'http://localhost:5000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add JWT token to requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Handle 401 responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ============ AUTH ENDPOINTS ============
export const authAPI = {
  register: (username, email, password) =>
    api.post('/auth/register', { username, email, password }),
  login: (email, password) =>
    api.post('/auth/login', { email, password }),
  getProfile: () =>
    api.get('/auth/profile'),
  changePassword: (oldPassword, newPassword) =>
    api.put('/auth/change-password', { old_password: oldPassword, new_password: newPassword }),
};

// ============ PARKING ENDPOINTS ============
export const parkingAPI = {
  // Vehicles
  registerVehicle: (vehicleNumber, vehicleType = 'car') =>
    api.post('/parking/vehicles', { vehicle_number: vehicleNumber, vehicle_type: vehicleType }),
  getUserVehicles: () =>
    api.get('/parking/vehicles'),
  deleteVehicle: (vehicleId) =>
    api.delete(`/parking/vehicles/${vehicleId}`),
  
  // Slots
  getSlots: () =>
    api.get('/parking/slots'),
  getSlotDetails: (slotId) =>
    api.get(`/parking/slots/${slotId}`),
  
  // Entry/Exit
  vehicleEntry: (vehicleNumber, slotId) =>
    api.post('/parking/entry', { vehicle_number: vehicleNumber, slot_id: slotId }),
  vehicleExit: (vehicleNumber) =>
    api.post('/parking/exit', { vehicle_number: vehicleNumber }),
  
  // Search & History
  searchVehicle: (vehicleNumber) =>
    api.get(`/parking/search?vehicle_number=${vehicleNumber}`),
  getParkingHistory: (page = 1, perPage = 10) =>
    api.get(`/parking/history?page=${page}&per_page=${perPage}`),
  
  // Payments
  processPayment: (transactionId) =>
    api.post(`/parking/payment/${transactionId}`),
  getPendingPayments: () =>
    api.get('/parking/pending-payments'),
};

// ============ BOOKING ENDPOINTS ============
export const bookingAPI = {
  reserveSlot: (slotId, bookingDate) =>
    api.post('/booking/reserve-slot', { slot_id: slotId, booking_date: bookingDate }),
  getUserBookings: () =>
    api.get('/booking/bookings'),
  cancelBooking: (bookingId) =>
    api.post(`/booking/bookings/${bookingId}/cancel`),
  getAvailableSlots: (date) =>
    api.get(`/booking/available-slots?date=${date}`),
};

// ============ ADMIN ENDPOINTS ============
export const adminAPI = {
  // Slots
  addSlot: (slotNumber) =>
    api.post('/admin/slots', { slot_number: slotNumber }),
  getAllSlots: () =>
    api.get('/admin/slots'),
  updateSlot: (slotId, data) =>
    api.put(`/admin/slots/${slotId}`, data),
  deleteSlot: (slotId) =>
    api.delete(`/admin/slots/${slotId}`),
  
  // Dashboard
  getDashboardStats: () =>
    api.get('/admin/dashboard/stats'),
  viewAllTransactions: (page = 1, perPage = 10) =>
    api.get(`/admin/transactions?page=${page}&per_page=${perPage}`),
  listUsers: () =>
    api.get('/admin/users'),
  deleteUser: (userId) =>
    api.delete(`/admin/users/${userId}`),
};

// ============ ANALYTICS ENDPOINTS ============
export const analyticsAPI = {
  getOccupancyRate: () =>
    api.get('/analytics/occupancy-rate'),
  getHourlyOccupancy: () =>
    api.get('/analytics/hourly-occupancy'),
  getRevenueStats: () =>
    api.get('/analytics/revenue-stats'),
  getDailyTransactions: () =>
    api.get('/analytics/daily-transactions'),
  getPeakHours: () =>
    api.get('/analytics/peak-hours'),
};

export default api;