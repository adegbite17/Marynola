import React, {useState} from 'react';
import {
    Container,
    Paper,
    TextField,
    Button,
    Typography,
    Box,
    Alert,
    FormControl,
    InputLabel,
    Select,
    MenuItem
} from '@mui/material';
import {useNavigate} from 'react-router-dom';
import ApiService from '../../services/api';

const AddStaff = () => {
    const navigate = useNavigate();
    const [formData, setFormData] = useState({
        firstname: '',
        lastname: '',
        national_insurance_number: '',
        home_address: '',
        telephone_number: '',
        employment_status: '',
        immigration_status: '',
        sex: '',
        date_of_birth: '',
        proof_of_id: null,
        visa_type: '',
        visa_sharecode: ''
    });
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        setFormData({...formData, [e.target.name]: e.target.value});
        setError('');
    };

    const handleFileChange = (e) => {
        setFormData({...formData, proof_of_id: e.target.files[0]});
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            // If there's a file, we need to send FormData, not JSON
            if (formData.proof_of_id) {
                const formDataToSend = new FormData();

                // Append all form fields to FormData
                Object.keys(formData).forEach(key => {
                    if (key === 'proof_of_id') {
                        formDataToSend.append(key, formData[key]);
                    } else if (formData[key] !== '' && formData[key] !== null) {
                        formDataToSend.append(key, formData[key]);
                    }
                });

                // Call API with FormData (you'll need to modify ApiService.addStaff to handle this)
                await ApiService.addStaff(formDataToSend, true); // Pass true flag for FormData
            } else {
                // No file, send JSON as before (but remove proof_of_id field)
                const {proof_of_id, ...dataWithoutFile} = formData;
                await ApiService.addStaff(dataWithoutFile);
            }

            alert('Staff member added successfully!');
            navigate('/dashboard');
        } catch (error) {
            setError(error.message || 'Failed to add staff member.');
        } finally {
            setLoading(false);
        }
    };


    return (
        <Container maxWidth="md">
            <Box sx={{mt: 4}}>
                <Paper elevation={3} sx={{p: 4}}>
                    <Typography variant="h4" gutterBottom>
                        Add New Staff Member
                    </Typography>

                    {error && (
                        <Alert severity="error" sx={{mb: 2}}>
                            {error}
                        </Alert>
                    )}

                    <form onSubmit={handleSubmit}>
                        <Box sx={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2}}>
                            <TextField
                                name="firstname"
                                label="First Name"
                                value={formData.firstname}
                                onChange={handleChange}
                                required
                                disabled={loading}
                            />
                            <TextField
                                name="lastname"
                                label="Last Name"
                                value={formData.lastname}
                                onChange={handleChange}
                                required
                                disabled={loading}
                            />
                        </Box>

                        <TextField
                            fullWidth
                            margin="normal"
                            name="national_insurance_number"
                            label="National Insurance Number"
                            value={formData.national_insurance_number}
                            onChange={handleChange}
                            required
                            disabled={loading}
                            placeholder="e.g., AB123456C"
                        />

                        <TextField
                            fullWidth
                            margin="normal"
                            name="home_address"
                            label="Home Address"
                            multiline
                            rows={2}
                            value={formData.home_address}
                            onChange={handleChange}
                            required
                            disabled={loading}
                        />

                        <TextField
                            fullWidth
                            margin="normal"
                            name="telephone_number"
                            label="Telephone Number"
                            value={formData.telephone_number}
                            onChange={handleChange}
                            required
                            disabled={loading}
                            placeholder="e.g., 07123456789"
                        />

                        <Box sx={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mt: 2}}>
                            <FormControl required disabled={loading}>
                                <InputLabel>Employment Status</InputLabel>
                                <Select
                                    name="employment_status"
                                    value={formData.employment_status}
                                    onChange={handleChange}
                                    label="Employment Status"
                                >
                                    <MenuItem value="Full-time">Full-time</MenuItem>
                                    <MenuItem value="Part-time">Part-time</MenuItem>
                                    <MenuItem value="Contract">Contract</MenuItem>
                                    <MenuItem value="Temporary">Temporary</MenuItem>
                                </Select>
                            </FormControl>

                            <FormControl required disabled={loading}>
                                <InputLabel>Sex</InputLabel>
                                <Select
                                    name="sex"
                                    value={formData.sex}
                                    onChange={handleChange}
                                    label="Sex"
                                >
                                    <MenuItem value="Male">Male</MenuItem>
                                    <MenuItem value="Female">Female</MenuItem>
                                    <MenuItem value="Other">Other</MenuItem>
                                </Select>
                            </FormControl>
                        </Box>

                        <TextField
                            fullWidth
                            margin="normal"
                            name="immigration_status"
                            label="Immigration Status"
                            value={formData.immigration_status}
                            onChange={handleChange}
                            required
                            disabled={loading}
                            placeholder="e.g., British Citizen, EU Citizen, Work Visa"
                        />

                        <Box sx={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mt: 2}}>
                            <TextField
                                name="visa_type"
                                label="Visa Type"
                                value={formData.visa_type}
                                onChange={handleChange}
                                disabled={loading}
                                placeholder="e.g., Work Visa, Student Visa"
                            />
                            <TextField
                                name="visa_sharecode"
                                label="Visa Sharecode"
                                value={formData.visa_sharecode}
                                onChange={handleChange}
                                disabled={loading}
                                placeholder="Enter visa sharecode"
                            />
                        </Box>

                        <TextField
                            fullWidth
                            margin="normal"
                            name="date_of_birth"
                            label="Date of Birth"
                            type="date"
                            value={formData.date_of_birth}
                            onChange={handleChange}
                            required
                            disabled={loading}
                            InputLabelProps={{shrink: true}}
                        />

                        <Box sx={{mt: 2}}>
                            <Typography variant="subtitle1" gutterBottom>
                                Proof of ID (Upload Image)
                            </Typography>
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleFileChange}
                                disabled={loading}
                                style={{marginBottom: '16px'}}
                            />
                            {formData.proof_of_id && (
                                <Typography variant="body2" color="textSecondary">
                                    Selected: {formData.proof_of_id.name}
                                </Typography>
                            )}
                        </Box>

                        <Box sx={{display: 'flex', gap: 2, mt: 3}}>
                            <Button
                                type="submit"
                                variant="contained"
                                disabled={loading}
                            >
                                {loading ? 'Adding...' : 'Add Staff'}
                            </Button>
                            <Button
                                variant="outlined"
                                onClick={() => navigate('/dashboard')}
                                disabled={loading}
                            >
                                Cancel
                            </Button>
                        </Box>
                    </form>
                </Paper>
            </Box>
        </Container>
    );
};

export default AddStaff;