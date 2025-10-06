import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  InputAdornment,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { Download, Delete, Search, Add, GetApp } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import ApiService from '../../services/api';

const Dashboard = () => {
  const navigate = useNavigate();
  const [dashboardData, setDashboardData] = useState(null);
  const [staffList, setStaffList] = useState([]);
  const [filteredStaff, setFilteredStaff] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [searchLoading, setSearchLoading] = useState(false);
  const [downloadLoading, setDownloadLoading] = useState(null);
  const [excelDownloading, setExcelDownloading] = useState(false);
  const [deleteDialog, setDeleteDialog] = useState({
    open: false,
    staffId: null,
    staffName: ''
  });

  // Search states
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEmploymentStatus, setSelectedEmploymentStatus] = useState('');

  useEffect(() => {
    // Check authentication first
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login', { replace: true });
      return;
    }

    loadDashboardData();
  }, [navigate]);

  // Update filtered staff when staffList changes
  useEffect(() => {
    setFilteredStaff(staffList);
  }, [staffList]);

  const loadDashboardData = async () => {
    try {
      console.log('Loading dashboard data...');

      // Load dashboard data with proper error handling
      let dashboard = { company_name: 'Your Company' };
      let staff = [];

      try {
        dashboard = await ApiService.getDashboard();
        console.log('Dashboard API response:', dashboard);
      } catch (err) {
        console.warn('Dashboard endpoint failed:', err);
      }

      try {
        const staffResponse = await ApiService.getStaffList();
        console.log('Staff API response:', staffResponse);

        // Handle different response formats
        if (Array.isArray(staffResponse)) {
          staff = staffResponse;
        } else if (staffResponse && Array.isArray(staffResponse.data)) {
          staff = staffResponse.data;
        } else if (staffResponse && Array.isArray(staffResponse.staff)) {
          staff = staffResponse.staff;
        } else {
          console.warn('Staff response is not an array:', staffResponse);
          staff = [];
        }
      } catch (err) {
        console.warn('Staff list endpoint failed:', err);
        staff = [];
      }

      setDashboardData(dashboard);
      setStaffList(staff);
      setFilteredStaff(staff);
      console.log('Final state:', { dashboard, staff: staff.length });

    } catch (error) {
      console.error('Dashboard error:', error);
      setError(error.message || 'Failed to load dashboard data.');

      // Ensure staffList is still an array even on error
      setStaffList([]);
      setFilteredStaff([]);

      // If authentication fails, redirect to login
      if (error.message.includes('401') || error.message.includes('Session expired')) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login', { replace: true });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim() && !selectedEmploymentStatus) {
      // If no search criteria, show all staff
      setFilteredStaff(staffList);
      return;
    }

    setSearchLoading(true);
    try {
      const response = await ApiService.searchStaff(searchQuery, selectedEmploymentStatus);
      setFilteredStaff(response.staff || []);
      setError('');
    } catch (error) {
      console.error('Search error:', error);
      setError('Search failed. Please try again.');
      // Fall back to local filtering if API search fails
      handleLocalSearch();
    } finally {
      setSearchLoading(false);
    }
  };

  const handleLocalSearch = () => {
    let filtered = [...staffList];

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(staff =>
        staff.firstname?.toLowerCase().includes(query) ||
        staff.lastname?.toLowerCase().includes(query) ||
        staff.telephone_number?.includes(query) ||
        staff.national_insurance_number?.toLowerCase().includes(query)
      );
    }

    if (selectedEmploymentStatus) {
      filtered = filtered.filter(staff =>
        staff.employment_status === selectedEmploymentStatus
      );
    }

    setFilteredStaff(filtered);
  };

  const handleClearSearch = () => {
    setSearchQuery('');
    setSelectedEmploymentStatus('');
    setFilteredStaff(staffList);
  };

  const handleDownloadExcel = async () => {
    setExcelDownloading(true);
    try {
      await ApiService.downloadStaffExcel();
      setError('');
    } catch (error) {
      console.error('Excel download error:', error);
      setError('Failed to download Excel file. Please try again.');
    } finally {
      setExcelDownloading(false);
    }
  };

  const handleDownloadId = async (staffId, staffName) => {
    try {
      setDownloadLoading(staffId);
      const blob = await ApiService.downloadStaffId(staffId);

      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${staffName.replace(/\s+/g, '_')}_id_proof`;
      document.body.appendChild(a);
      a.click();

      // Cleanup
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

    } catch (error) {
      console.error('Download error:', error);
      setError('Failed to download ID proof. Please try again.');
    } finally {
      setDownloadLoading(null);
    }
  };

  const handleDeleteClick = (staffId, staffName) => {
    setDeleteDialog({
      open: true,
      staffId,
      staffName
    });
  };

  const handleDeleteConfirm = async () => {
    try {
      await ApiService.deleteStaff(deleteDialog.staffId);

      // Remove from both lists
      const updatedStaffList = staffList.filter(staff => staff.id !== deleteDialog.staffId);
      const updatedFilteredList = filteredStaff.filter(staff => staff.id !== deleteDialog.staffId);

      setStaffList(updatedStaffList);
      setFilteredStaff(updatedFilteredList);
      setDeleteDialog({ open: false, staffId: null, staffName: '' });
      setError(''); // Clear any previous errors

    } catch (error) {
      console.error('Delete error:', error);
      setError('Failed to delete staff member. Please try again.');
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ open: false, staffId: null, staffName: '' });
  };

  const handleLogout = async () => {
    try {
      await ApiService.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      navigate('/login', { replace: true });
    }
  };

  if (loading) {
    return (
      <Container>
        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>Loading Dashboard...</Typography>
        </Box>
      </Container>
    );
  }

  // Ensure staffList is always an array
  const safeStaffList = Array.isArray(staffList) ? staffList : [];
  const safeFilteredStaff = Array.isArray(filteredStaff) ? filteredStaff : [];

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
          <Typography variant="h4">Dashboard</Typography>
          <Button variant="outlined" onClick={handleLogout}>
            Logout
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: 3, mb: 4 }}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary">
                Total Staff
              </Typography>
              <Typography variant="h3" color="primary">
                {safeStaffList.length}
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary">
                Filtered Results
              </Typography>
              <Typography variant="h3" color="secondary">
                {safeFilteredStaff.length}
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" color="textSecondary">
                Company
              </Typography>
              <Typography variant="h6">
                {dashboardData?.company_name || 'Marynola'}
              </Typography>
            </CardContent>
          </Card>
        </Box>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => navigate('/add-staff')}
            size="large"
          >
            Add New Staff
          </Button>
          <Button
            variant="outlined"
            startIcon={excelDownloading ? <CircularProgress size={20} /> : <GetApp />}
            onClick={handleDownloadExcel}
            disabled={excelDownloading || safeStaffList.length === 0}
            size="large"
          >
            {excelDownloading ? 'Downloading...' : 'Download Excel'}
          </Button>
        </Box>

        {/* Search Section */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Search Staff
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', alignItems: 'center' }}>
              <TextField
                placeholder="Search by name, phone, or National Insurance Number..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search />
                    </InputAdornment>
                  ),
                }}
                sx={{ flex: 1, minWidth: 300 }}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              />
              <FormControl sx={{ minWidth: 180 }}>
                <InputLabel>Employment Status</InputLabel>
                <Select
                  value={selectedEmploymentStatus}
                  onChange={(e) => setSelectedEmploymentStatus(e.target.value)}
                  label="Employment Status"
                >
                  <MenuItem value="">All</MenuItem>
                  <MenuItem value="Full-time">Full-time</MenuItem>
                  <MenuItem value="Part-time">Part-time</MenuItem>
                  <MenuItem value="Contract">Contract</MenuItem>
                  <MenuItem value="Intern">Intern</MenuItem>
                  <MenuItem value="Temporary">Temporary</MenuItem>
                </Select>
              </FormControl>
              <Button
                variant="contained"
                onClick={handleSearch}
                disabled={searchLoading}
                sx={{ minWidth: 100 }}
              >
                {searchLoading ? <CircularProgress size={20} /> : 'Search'}
              </Button>
              <Button
                variant="outlined"
                onClick={handleClearSearch}
                disabled={searchLoading}
              >
                Clear
              </Button>
            </Box>
          </CardContent>
        </Card>

        <Typography variant="h5" gutterBottom sx={{ mt: 4 }}>
          Staff Members {safeFilteredStaff.length !== safeStaffList.length && `(${safeFilteredStaff.length} of ${safeStaffList.length})`}
        </Typography>

        {safeFilteredStaff.length === 0 ? (
          <Card>
            <CardContent>
              <Typography variant="body1" textAlign="center" color="textSecondary">
                {safeStaffList.length === 0
                  ? "No staff members added yet. Click \"Add New Staff\" to get started."
                  : "No staff members match your search criteria. Try adjusting your search terms."
                }
              </Typography>
            </CardContent>
          </Card>
        ) : (
          <Box sx={{ display: 'grid', gap: 2 }}>
            {safeFilteredStaff.map((staff, index) => (
              <Card key={staff.id || index}>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Box>
                      <Typography variant="h6">
                        {staff.firstname} {staff.lastname}
                      </Typography>
                      <Typography color="textSecondary">
                        {staff.employment_status}
                      </Typography>
                      <Typography variant="body2">
                        NIN: {staff.national_insurance_number}
                      </Typography>
                      <Typography variant="body2">
                        Phone: {staff.telephone_number}
                      </Typography>
                      <Typography variant="body2">
                        Address: {staff.home_address}
                      </Typography>
                      {staff.immigration_status && (
                        <Typography variant="body2">
                          Immigration Status: {staff.immigration_status}
                        </Typography>
                      )}
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      {/* Edit Button */}
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => navigate(`/edit-staff/${staff.id}`)}
                      >
                        Edit
                      </Button>

                      {/* Download ID Button */}
                      <IconButton
                        color="info"
                        onClick={() => handleDownloadId(staff.id, `${staff.firstname}_${staff.lastname}`)}
                        title="Download ID Proof"
                        disabled={downloadLoading === staff.id}
                      >
                        {downloadLoading === staff.id ? (
                          <CircularProgress size={20} />
                        ) : (
                          <Download />
                        )}
                      </IconButton>

                      {/* Delete Button */}
                      <IconButton
                        color="error"
                        onClick={() => handleDeleteClick(staff.id, `${staff.firstname} ${staff.lastname}`)}
                        title="Delete Staff"
                      >
                        <Delete />
                      </IconButton>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            ))}
          </Box>
        )}

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialog.open} onClose={handleDeleteCancel}>
          <DialogTitle>Confirm Delete</DialogTitle>
          <DialogContent>
            Are you sure you want to delete <strong>{deleteDialog.staffName}</strong>?
            This action cannot be undone and will permanently remove all their data.
          </DialogContent>
          <DialogActions>
            <Button onClick={handleDeleteCancel}>Cancel</Button>
            <Button
              onClick={handleDeleteConfirm}
              color="error"
              variant="contained"
            >
              Delete
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </Container>
  );
};

export default Dashboard;
