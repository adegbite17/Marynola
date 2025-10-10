import React, {useState} from 'react';
import {Container, Paper, TextField, Button, Typography, Box, Link, Alert} from '@mui/material';
import {useNavigate} from 'react-router-dom';
import ApiService from '../../services/api';

const ForgotPassword = () => {
    const navigate = useNavigate();
    const [step, setStep] = useState(1); // 1: email, 2: code + new password
    const [formData, setFormData] = useState({
        email: '',
        code: '',
        newPassword: '',
        confirmPassword: ''
    });
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({...formData, [e.target.name]: e.target.value});
        setError('');
    };

    const handleEmailSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            console.log('Sending verification code to:', formData.email);
            const response = await ApiService.forgotPassword({email: formData.email});
            console.log('Forgot password response:', response);

            setSuccess('Verification code sent to your email. Please check your inbox and spam folder.');
            setStep(2);
        } catch (error) {
            console.error('Forgot password error:', error);
            setError(error.message || 'Failed to send verification code. Please check your email and try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleResetSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        // Validate passwords match
        if (formData.newPassword !== formData.confirmPassword) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        // Validate password length
        if (formData.newPassword.length < 6) {
            setError('Password must be at least 6 characters long');
            setLoading(false);
            return;
        }

        // Validate code is provided
        if (!formData.code.trim()) {
            setError('Please enter the verification code');
            setLoading(false);
            return;
        }

        try {
            console.log('Resetting password with:', {
                email: formData.email,
                code: formData.code,
                password: formData.newPassword
            });

            const response = await ApiService.resetPassword({
                email: formData.email,
                code: formData.code.trim(),
                password: formData.newPassword
            });

            console.log('Reset password response:', response);
            setSuccess('Password reset successfully! Redirecting to login...');

            // Clear form
            setFormData({
                email: '',
                code: '',
                newPassword: '',
                confirmPassword: ''
            });

            // Redirect to login after 3 seconds
            setTimeout(() => {
                navigate('/login');
            }, 3000);

        } catch (error) {
            console.error('Reset password error:', error);
            setError(error.message || 'Failed to reset password. Please check your verification code and try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleResendCode = async () => {
        setLoading(true);
        setError('');
        setSuccess('');

        try {
            await ApiService.forgotPassword({email: formData.email});
            setSuccess('New verification code sent to your email.');
        } catch (error) {
            console.error('Resend code error:', error);
            setError('Failed to resend code. Please try again.');
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
                            onError={(e) => {
                                e.target.style.display = 'none';
                            }}
                        />
                        <Typography variant="h4" gutterBottom>
                            {step === 1 ? 'Forgot Password' : 'Reset Password'}
                        </Typography>
                        <Typography variant="body2" color="textSecondary">
                            {step === 1
                                ? 'Enter your email address and we\'ll send you a verification code'
                                : 'Enter the verification code from your email and your new password'
                            }
                        </Typography>
                    </Box>

                    {error && (
                        <Alert severity="error" sx={{mb: 2}}>
                            {error}
                        </Alert>
                    )}

                    {success && (
                        <Alert severity="success" sx={{mb: 2}}>
                            {success}
                        </Alert>
                    )}

                    {step === 1 ? (
                        <form onSubmit={handleEmailSubmit}>
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
                                autoFocus
                                placeholder="Enter your registered email address"
                            />
                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                sx={{mt: 3, mb: 2}}
                                disabled={loading || !formData.email.trim()}
                            >
                                {loading ? 'Sending Code...' : 'Send Verification Code'}
                            </Button>
                        </form>
                    ) : (
                        <form onSubmit={handleResetSubmit}>
                            <TextField
                                fullWidth
                                margin="normal"
                                name="email"
                                label="Email Address"
                                type="email"
                                value={formData.email}
                                disabled
                                sx={{mb: 2, backgroundColor: '#f5f5f5'}}
                            />
                            <TextField
                                fullWidth
                                margin="normal"
                                name="code"
                                label="Verification Code"
                                value={formData.code}
                                onChange={handleChange}
                                required
                                disabled={loading}
                                autoFocus
                                placeholder="Enter the code from your email"
                                inputProps={{maxLength: 10}}
                            />
                            <TextField
                                fullWidth
                                margin="normal"
                                name="newPassword"
                                label="New Password"
                                type="password"
                                value={formData.newPassword}
                                onChange={handleChange}
                                required
                                disabled={loading}
                                placeholder="Enter your new password (min 6 characters)"
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
                                placeholder="Confirm your new password"
                            />
                            <Button
                                type="submit"
                                fullWidth
                                variant="contained"
                                sx={{mt: 3, mb: 2}}
                                disabled={loading || !formData.code.trim() || !formData.newPassword || !formData.confirmPassword}
                            >
                                {loading ? 'Resetting Password...' : 'Reset Password'}
                            </Button>

                            <Box sx={{textAlign: 'center', mt: 2}}>
                                <Button
                                    variant="text"
                                    onClick={handleResendCode}
                                    disabled={loading}
                                    size="small"
                                >
                                    Didn't receive the code? Resend
                                </Button>
                            </Box>

                            <Box sx={{textAlign: 'center', mt: 1}}>
                                <Button
                                    variant="text"
                                    onClick={() => setStep(1)}
                                    disabled={loading}
                                    size="small"
                                >
                                    Change Email Address
                                </Button>
                            </Box>
                        </form>
                    )}

                    <Box sx={{textAlign: 'center', mt: 3}}>
                        <Link
                            component="button"
                            type="button"
                            variant="body2"
                            onClick={() => navigate('/login')}
                            sx={{textDecoration: 'none'}}
                            disabled={loading}
                        >
                            Back to Login
                        </Link>
                    </Box>
                </Paper>
            </Box>
        </Container>
    );
};

export default ForgotPassword;
