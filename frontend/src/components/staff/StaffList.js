import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Box,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  CircularProgress
} from '@mui/material';
import { Edit, Download, Delete, Add } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import ApiService from '../../services/api';

const StaffList = () => {
  const navigate = useNavigate();
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [deleteDialog, setDeleteDialog] = useState({
    open: false,
    staffId: null,
    staffName: ''
  });
  const [downloadLoading, setDownloadLoading] = useState(null);

  useEffect(() => {
    fetchStaff();
  }, []);

  const fetchStaff = async () => {
    try {
      setLoading(true);
      const data = await ApiService.getStaffList();
      setStaffList(data);
      setError('');
    } catch (error) {
      console.error('Error fetching staff:', error);
      setError('Failed to load staff list');
    } finally {
      setLoading(false);
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

      // Remove from local state
      setStaffList(staffList.filter(staff => staff.id !== deleteDialog.staffId));
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

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4" gutterBottom>
            Staff Management
          </Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => navigate('/add-staff')}
          >
            Add New Staff
          </Button>
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
            {error}
          </Alert>
        )}

        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Phone</TableCell>
                <TableCell>Employment Status</TableCell>
                <TableCell>Immigration Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {staffList.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center">
                    No staff members found
                  </TableCell>
                </TableRow>
              ) : (
                staffList.map((staff) => (
                  <TableRow key={staff.id}>
                    <TableCell>{`${staff.firstname} ${staff.lastname}`}</TableCell>
                    <TableCell>{staff.telephone_number}</TableCell>
                    <TableCell>{staff.employment_status}</TableCell>
                    <TableCell>{staff.immigration_status}</TableCell>
                    <TableCell align="center">
                      {/* Edit Button */}
                      <IconButton
                        color="primary"
                        onClick={() => navigate(`/edit-staff/${staff.id}`)}
                        title="Edit Staff"
                        size="small"
                        sx={{ mr: 1 }}
                      >
                        <Edit />
                      </IconButton>

                      {/* Download ID Button */}
                      <IconButton
                        color="info"
                        onClick={() => handleDownloadId(staff.id, `${staff.firstname}_${staff.lastname}`)}
                        title="Download ID Proof"
                        size="small"
                        disabled={downloadLoading === staff.id}
                        sx={{ mr: 1 }}
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
                        size="small"
                      >
                        <Delete />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

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

export default StaffList;
