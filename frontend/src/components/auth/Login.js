import React, { useState } from 'react';
import { Container, Paper, TextField, Button, Typography, Box, Link, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ApiService from '../../services/api';

const Login = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      console.log('Attempting login with:', formData.email);
      const data = await ApiService.login(formData);
      console.log('Login response:', data);

      // Store authentication data
      if (data.token || data.access_token) {
        localStorage.setItem('token', data.token || data.access_token);
        console.log('Token stored:', data.token || data.access_token);
      }

      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
        console.log('User data stored:', data.user);
      }

      // Force navigation
      console.log('Navigating to dashboard...');
      navigate('/dashboard', { replace: true });

      // Additional fallback
      setTimeout(() => {
        if (window.location.pathname !== '/dashboard') {
          window.location.href = '/dashboard';
        }
      }, 100);

    } catch (error) {
      console.error('Login error:', error);
      setError(error.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  // Check if user is already logged in
  React.useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      navigate('/dashboard', { replace: true });
    }
  }, [navigate]);

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Box sx={{ textAlign: 'center', mb: 3 }}>
            <img
              src="/marynola.jpg"
              alt="Marynola Logo"
              style={{
                width: '100px',
                height: '100px',
                objectFit: 'contain',
                marginBottom: '16px'
              }}
              onError={(e) => {
                e.target.style.display = 'none';
              }}
            />
            <Typography variant="h4" gutterBottom>
              Login to Marynola LTD
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              margin="normal"
              name="email"
              label="Email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <TextField
              fullWidth
              margin="normal"
              name="password"
              label="Password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              required
              disabled={loading}
            />
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              disabled={loading}
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>
            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Link
                component="button"
                type="button"
                variant="body2"
                onClick={() => navigate('/register')}
                sx={{ textDecoration: 'none', mr: 2 }}
                disabled={loading}
              >
                Don't have an account? Register
              </Link>
              <br />
              <Link
                component="button"
                type="button"
                variant="body2"
                onClick={() => navigate('/forgot-password')}
                sx={{ textDecoration: 'none', mt: 1 }}
                disabled={loading}
              >
                Forgot Password?
              </Link>
            </Box>
          </form>
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;

