import React, {useState} from 'react';
import {Container, Paper, TextField, Button, Typography, Box, Alert} from '@mui/material';
import {useNavigate} from 'react-router-dom';
import ApiService from '../../services/api';

const ResetPassword = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        email: '',
        code: '',
        password: '',
        confirmPassword: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({...formData, [e.target.name]: e.target.value});
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        if (formData.password.length < 6) {
            setError('Password must be at least 6 characters long');
            return;
        }

        setLoading(true);
        setError('');

        try {
            await ApiService.resetPasswordWithCode(formData.email, formData.code, formData.password);
            alert('Password reset successful! Please login with your new password.');
            navigate('/login');
        } catch (error) {
            setError(error.message || 'Failed to reset password.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="sm">
            <Box sx={{mt: 8}}>
                <Paper elevation={3} sx={{p: 4}}>
                    <Box sx={{textAlign: 'center', mb: 3}}>
                        <img
                            src="/marynola.jpg"
                            alt="Marynola Logo"
                            style={{
                                width: '100px',
                                height: '100px',
                                objectFit: 'contain',
                                marginBottom: '16px'
                            }}
                        />
                        <Typography variant="h4" gutterBottom>
                            Reset Password
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                            Enter the code sent to your email and your new password
                        </Typography>
                    </Box>

                    {error && (
                        <Alert severity="error" sx={{mb: 2}}>
                            {error}
                        </Alert>
                    )}

                    <form onSubmit={handleSubmit}>
                        <TextField
                            fullWidth
                            margin="normal"
                            name="email"
                            label="Email Address"
                            type="email"
                            value={formData.email}
                            onChange={handleChange}
                            required
                            disabled={loading}
                        />
                        <TextField
                            fullWidth
                            margin="normal"
                            name="code"
                            label="Reset Code"
                            value={formData.code}
                            onChange={handleChange}
                            required
                            disabled={loading}
                            helperText="Enter the code sent to your email"
                        />
                        <TextField
                            fullWidth
                            margin="normal"
                            name="password"
                            label="New Password"
                            type="password"
                            value={formData.password}
                            onChange={handleChange}
                            required
                            disabled={loading}
                            helperText="Password must be at least 6 characters"
                        />
                        <TextField
                            fullWidth
                            margin="normal"
                            name="confirmPassword"
                            label="Confirm New Password"
                            type="password"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            required
                            disabled={loading}
                        />
                        <Button
                            type="submit"
                            fullWidth
                            variant="contained"
                            sx={{mt: 3, mb: 2}}
                            disabled={loading}
                        >
                            {loading ? 'Resetting...' : 'Reset Password'}
                        </Button>
                        <Box sx={{textAlign: 'center'}}>
                            <Button
                                variant="text"
                                onClick={() => navigate('/login')}
                                disabled={loading}
                            >
                                Back to Login
                            </Button>
                        </Box>
                    </form>
                </Paper>
            </Box>
        </Container>
    );
};

export default ResetPassword;
