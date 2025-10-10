import React, {useState} from 'react';
import {Container, Paper, TextField, Button, Typography, Box, Link, Alert} from '@mui/material';
import {useNavigate} from 'react-router-dom';
import ApiService from '../../services/api';

const Register = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        firstname: '',
        lastname: '',
        company_name: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({...formData, [e.target.name]: e.target.value});
        setError('');
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        if (formData.password !== formData.confirmPassword) {
            setError('Passwords do not match');
            setLoading(false);
            return;
        }

        if (formData.password.length < 6) {
            setError('Password must be at least 6 characters long');
            setLoading(false);
            return;
        }

        try {
            const userData = {
                email: formData.email,
                firstname: formData.firstname,
                lastname: formData.lastname,
                company_name: formData.company_name,
                password: formData.password
            };

            await ApiService.register(userData);
            alert('Registration successful! Please login.');
            navigate('/login');
        } catch (error) {
            setError(error.message || 'Registration failed. Please try again.');
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
                            Register to Marynola LTD
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
                            name="firstname"
                            label="First Name"
                            value={formData.firstname}
                            onChange={handleChange}
                            required
                            disabled={loading}
                        />
                        <TextField
                            fullWidth
                            margin="normal"
                            name="lastname"
                            label="Last Name"
                            value={formData.lastname}
                            onChange={handleChange}
                            required
                            disabled={loading}
                        />
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
                            name="company_name"
                            label="Company Name"
                            value={formData.company_name}
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
                            helperText="Minimum 6 characters"
                        />
                        <TextField
                            fullWidth
                            margin="normal"
                            name="confirmPassword"
                            label="Confirm Password"
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
                            {loading ? 'Registering...' : 'Register'}
                        </Button>
                        <Box sx={{textAlign: 'center'}}>
                            <Link
                                component="button"
                                type="button"
                                variant="body2"
                                onClick={() => navigate('/login')}
                                sx={{textDecoration: 'none'}}
                                disabled={loading}
                            >
                                Already have an account? Login here
                            </Link>
                        </Box>
                    </form>
                </Paper>
            </Box>
        </Container>
    );
};

export default Register;
