import React, {useState, useEffect} from 'react';
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
import {useNavigate, useParams} from 'react-router-dom';
import ApiService from '../../services/api';

const EditStaff = () => {
    const navigate = useNavigate();
    const {id} = useParams();
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
    const [initialLoading, setInitialLoading] = useState(true);

    // In your EditStaff component
    useEffect(() => {
        const fetchStaffData = async () => {
            try {
                setInitialLoading(true)
                console.log("Fetching staff data for ID:", id);

                const response = await ApiService.getStaff(id);
                console.log('API response:', response); // Add this for debugging

                const staffData = response.staff;
                console.log('Extracted staff data:', staffData); // Add this for debugging
                // Pre-populate your form fields with existing data
                setFormData({
                    firstname: staffData.firstname || '',
                    lastname: staffData.lastname || '',
                    telephone_number: staffData.telephone_number || '',
                    employment_status: staffData.employment_status || '',
                    immigration_status: staffData.immigration_status || '',
                    sex: staffData.sex || '',
                    visa_type: staffData.visa_type || '',
                    visa_sharecode: staffData.visa_sharecode || '',
                    date_of_birth: staffData.date_of_birth || '',
                    home_address: staffData.home_address || '',
                    national_insurance_number: staffData.national_insurance_number || '',
                    // Don't pre-populate the file field
                    proof_of_id: staffData.proof_of_id || null
                });
                setError('');
            } catch (error) {
                console.error('Error fetching staff data:', error);
                setError('Failed to load staff data.');
            } finally {
                setInitialLoading(false);
            }
        };

        if (id) {
            fetchStaffData();
        }
    }, [id]);


    const handleChange = (e) => {
        setFormData({...formData, [e.target.name]: e.target.value});
        setError('');
    };

    const handleFileChange = (e) => {
        setFormData({...formData, proof_of_id: e.target.files[0]});
    };

    // In your form submission handler
    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            // Check if a file is selected for upload
            if (formData.proof_of_id && formData.proof_of_id instanceof File) {
                // Use FormData for file upload
                const form = new FormData();
                Object.keys(formData).forEach(key => {
                    if (formData[key] !== null && formData[key] !== undefined) {
                        form.append(key, formData[key]);
                    }
                });
                await ApiService.updateStaffWithFile(id, form);
            } else {
                // Use regular update without file
                const {proof_of_id, ...staffDataWithoutFile} = formData;
                await ApiService.updateStaff(id, staffDataWithoutFile);
            }

            navigate('/dashboard');
        } catch (error) {
            console.error('Update error:', error);
            setError('Failed to update staff member.');
        } finally {
            setLoading(false);
        }
    };


    if (initialLoading) {
        return (
            <Container maxWidth="md">
                <Box sx={{mt: 4, textAlign: 'center'}}>
                    <Typography>Loading staff data...</Typography>
                </Box>
            </Container>
        );
    }

    return (
        <Container maxWidth="md">
            <Box sx={{mt: 4}}>
                <Paper elevation={3} sx={{p: 4}}>
                    <Typography variant="h4" gutterBottom>
                        Edit Staff Member
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
                                Update Proof of ID (Upload New Image)
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
                                {loading ? 'Updating...' : 'Update Staff'}
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

export default EditStaff;
