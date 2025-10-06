import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import ForgotPassword from './components/auth/ForgotPassword';
import Dashboard from './components/dashboard/Dashboard';
import AddStaff from './components/auth/AddStaff';
import EditStaff from './components/auth/EditStaff';
import StaffList from "./components/staff/StaffList";

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const token = localStorage.getItem('token');
  return token ? children : <Navigate to="/login" replace />;
};

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<Navigate to="/login" />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
            <Route
                path="/staff"
                element={
                    <ProtectedRoute>
                        <StaffList />
                    </ProtectedRoute>
                }
            />
          <Route
            path="/add-staff"
            element={
              <ProtectedRoute>
                <AddStaff />
              </ProtectedRoute>
            }
          />
          <Route
            path="/edit-staff/:id"
            element={
              <ProtectedRoute>
                <EditStaff />
              </ProtectedRoute>
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
