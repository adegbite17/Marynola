const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://marynola-2.onrender.com';


class ApiService {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const config = {
            ...options,
        };

        // Add auth token if available
        const token = localStorage.getItem('token');
        if (token) {
            config.headers = {
                ...config.headers,
                'Authorization': `Bearer ${token}`,
            };
        }

        // Only add Content-Type for non-FormData requests
        if (!(options.body instanceof FormData)) {
            config.headers = {
                'Content-Type': 'application/json',
                ...config.headers,
            };
        }

        try {
            const response = await fetch(url, config);

            if (!response.ok) {
                let errorMessage;
                try {
                    const errorData = await response.json();
                    console.error('API Error Response:', errorData);
                    errorMessage = errorData.message || errorData.error || `HTTP ${response.status}`;
                } catch {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }

                // Handle 401 differently for login vs authenticated routes
                if (response.status === 401) {
                    // Don't treat login failures as session expiration
                    if (endpoint === '/api/login') {
                        throw new Error(errorMessage);
                    } else {
                        // Only clear tokens for authenticated routes
                        localStorage.removeItem('token');
                        localStorage.removeItem('user');
                        throw new Error('Session expired. Please login again.');
                    }
                }

                throw new Error(errorMessage);
            }

            const data = await response.json();
            console.log(`API Response for ${endpoint}:`, data);
            return data;

        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }


    static async getStaffList() {
        try {
            const response = await this.request('/api/staff');

            // Handle various response formats
            if (Array.isArray(response)) {
                return response;
            } else if (response && Array.isArray(response.data)) {
                return response.data;
            } else if (response && Array.isArray(response.staff)) {
                return response.staff;
            } else if (response && Array.isArray(response.staffList)) {
                return response.staffList;
            } else {
                console.warn('Unexpected staff list response format:', response);
                return [];
            }
        } catch (error) {
            console.error('Error fetching staff list:', error);
            return [];
        }
    }

    static async register(userData) {
        return this.request('/api/register', {
            method: 'POST',
            body: JSON.stringify(userData),
        });
    }

    static async login(credentials) {
        return this.request('/api/login', {
            method: 'POST',
            body: JSON.stringify(credentials),
        });
    }

    static async logout() {
        try {
            await this.request('/api/logout', {
                method: 'POST',
            });
        } finally {
            localStorage.removeItem('token');
            localStorage.removeItem('user');
        }
    }

    static async forgotPassword(data) {
        const response = await fetch(`${API_BASE_URL}/api/forgot-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    static async resetPassword(data) {
        const response = await fetch(`${API_BASE_URL}/api/reset-password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    static async getStaff(id) {
        return this.request(`/api/staff/${id}`);
    }

    static async addStaff(staffData, isFormData = false) {
        const options = {
            method: 'POST',
        };

        if (isFormData) {
            options.body = staffData;
        } else {
            options.headers = {
                'Content-Type': 'application/json',
            };
            options.body = JSON.stringify(staffData);
        }

        return this.request('/api/staff', options);
    }

    static async addStaffWithFile(staffData) {
        const formData = new FormData();

        Object.keys(staffData).forEach(key => {
            if (staffData[key] !== null && staffData[key] !== undefined) {
                formData.append(key, staffData[key]);
            }
        });

        return this.request('/api/staff', {
            method: 'POST',
            body: formData,
        });
    }

    static async updateStaff(id, staffData) {
        const options = {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(staffData)
        };

        return this.request(`/api/staff/${id}`, options);
    }

    static async updateStaffWithFile(id, formData) {
        console.log('Updating staff with ID:', id);
        for (let pair of formData.entries()) {
            console.log('FormData entry:', pair[0], pair[1]);
        }

        const options = {
            method: 'PUT',
            body: formData
        };

        return this.request(`/api/staff/${id}/update-with-file`, options);
    }

    static async getDashboard() {
        try {
            const response = await this.request('/api/dashboard');

            let staffList = [];
            if (Array.isArray(response.staffList)) {
                staffList = response.staffList;
            } else if (Array.isArray(response.staff)) {
                staffList = response.staff;
            } else if (Array.isArray(response.data)) {
                staffList = response.data;
            } else if (Array.isArray(response)) {
                staffList = response;
            }

            return {
                totalStaff: response.totalStaff || response.total_staff || staffList.length || 0,
                staffList: staffList,
                ...response
            };
        } catch (error) {
            console.error('Error fetching dashboard:', error);
            return {totalStaff: 0, staffList: []};
        }
    }

    static async downloadStaffId(id) {
        const response = await fetch(`${API_BASE_URL}/api/staff/${id}/download-id`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to download ID');
        }

        return response.blob();
    }

    static async deleteStaff(id) {
        const options = {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        };

        return this.request(`/api/staff/${id}`, options);
    }

    // NEW SEARCH AND DOWNLOAD METHODS - PROPERLY FORMATTED
    static async searchStaff(query, employmentStatus = '') {
        const params = new URLSearchParams();
        if (query) params.append('q', query);
        if (employmentStatus) params.append('employment_status', employmentStatus);

        const response = await fetch(`${API_BASE_URL}/api/staff/search?${params}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'Content-Type': 'application/json',
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return response.json();
    }

    static async downloadStaffExcel() {
        const response = await fetch(`${API_BASE_URL}/api/staff/download`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'staff_list.xlsx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    static async getUserProfile() {
        return this.request('/api/profile');
    }

    static async updateProfile(profileData) {
        return this.request('/api/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData),
        });
    }
}

export default ApiService;