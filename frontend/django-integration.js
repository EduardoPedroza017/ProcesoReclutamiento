/**
 * Django Integration Module
 * Handles Django-specific API calls, CSRF tokens, and Django REST Framework integration
 */

class DjangoAPI {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.csrfToken = null;
        this.init();
    }

    async init() {
        await this.getCsrfToken();
    }

    // Get CSRF token from Django
    async getCsrfToken() {
        try {
            const response = await fetch(`${this.baseURL}/csrf/`, {
                credentials: 'include'
            });
            const data = await response.json();
            this.csrfToken = data.csrfToken;
            
            // Also try to get from cookie
            if (!this.csrfToken) {
                this.csrfToken = this.getCsrfTokenFromCookie();
            }
        } catch (error) {
            console.warn('Could not get CSRF token:', error);
        }
    }

    getCsrfTokenFromCookie() {
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrftoken') {
                return decodeURIComponent(value);
            }
        }
        return null;
    }

    // Get default headers for Django requests
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        if (this.csrfToken) {
            headers['X-CSRFToken'] = this.csrfToken;
        }

        if (includeAuth) {
            const token = localStorage.getItem('authToken');
            if (token) {
                headers['Authorization'] = `Bearer ${token}`;
            }
        }

        return headers;
    }

    // Generic API request method
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            credentials: 'include',
            headers: this.getHeaders(),
            ...options
        };

        // Merge headers
        if (options.headers) {
            config.headers = { ...config.headers, ...options.headers };
        }

        try {
            const response = await fetch(url, config);
            
            if (response.status === 401) {
                // Token expired, try to refresh
                await this.refreshToken();
                // Retry original request
                config.headers = this.getHeaders();
                const retryResponse = await fetch(url, config);
                return this.handleResponse(retryResponse);
            }

            return this.handleResponse(response);
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    async handleResponse(response) {
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || errorData.message || 'Request failed');
        }

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return response;
    }

    // Authentication
    async login(username, password) {
        const response = await this.request('/api/accounts/login/', {
            method: 'POST',
            body: JSON.stringify({ username, password })
        });
        
        // Store tokens
        if (response.access_token) {
            localStorage.setItem('authToken', response.access_token);
            localStorage.setItem('refreshToken', response.refresh_token);
            localStorage.setItem('user', JSON.stringify(response.user));
        }
        
        return response;
    }

    async refreshToken() {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) {
            throw new Error('No refresh token available');
        }

        try {
            const response = await this.request('/api/accounts/token/refresh/', {
                method: 'POST',
                body: JSON.stringify({ refresh: refreshToken })
            });
            
            localStorage.setItem('authToken', response.access);
            return response;
        } catch (error) {
            // Refresh failed, redirect to login
            localStorage.clear();
            window.location.href = '/login.html';
            throw error;
        }
    }

    async logout() {
        try {
            await this.request('/api/accounts/logout/', { method: 'POST' });
        } catch (error) {
            console.warn('Logout request failed:', error);
        } finally {
            localStorage.clear();
            window.location.href = '/login.html';
        }
    }

    // Dashboard & Stats
    async getDashboardStats() {
        return this.request('/api/dashboard/stats/');
    }

    async getRecentActivity(limit = 10) {
        return this.request(`/api/dashboard/activity/?limit=${limit}`);
    }

    // Candidates
    async getCandidates(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/api/candidates/?${params}`);
    }

    async getCandidate(id) {
        return this.request(`/api/candidates/${id}/`);
    }

    async createCandidate(data) {
        return this.request('/api/candidates/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateCandidate(id, data) {
        return this.request(`/api/candidates/${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteCandidate(id) {
        return this.request(`/api/candidates/${id}/`, {
            method: 'DELETE'
        });
    }

    // Processes
    async getProcesses(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/api/processes/?${params}`);
    }

    async getProcess(id) {
        return this.request(`/api/processes/${id}/`);
    }

    async createProcess(data) {
        return this.request('/api/processes/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateProcess(id, data) {
        return this.request(`/api/processes/${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // Clients
    async getClients(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/api/clients/?${params}`);
    }

    async getClient(id) {
        return this.request(`/api/clients/${id}/`);
    }

    async createClient(data) {
        return this.request('/api/clients/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Profiles
    async getProfiles(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/api/profiles/?${params}`);
    }

    async getProfile(id) {
        return this.request(`/api/profiles/${id}/`);
    }

    // Approvals
    async getPendingApprovals() {
        return this.request('/api/approvals/pending/');
    }

    async approveCandidate(candidateId, notes = '') {
        return this.request(`/api/approvals/approve/`, {
            method: 'POST',
            body: JSON.stringify({
                candidate_id: candidateId,
                notes: notes
            })
        });
    }

    async rejectCandidate(candidateId, reason = '') {
        return this.request(`/api/approvals/reject/`, {
            method: 'POST',
            body: JSON.stringify({
                candidate_id: candidateId,
                reason: reason
            })
        });
    }

    // File uploads
    async uploadFile(file, endpoint = '/api/documents/upload/') {
        const formData = new FormData();
        formData.append('file', file);

        return this.request(endpoint, {
            method: 'POST',
            headers: {
                // Don't set Content-Type, let browser set it with boundary
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: formData
        });
    }

    // Reports
    async generateReport(type, filters = {}) {
        const params = new URLSearchParams({ type, ...filters }).toString();
        return this.request(`/api/reports/generate/?${params}`);
    }

    async downloadReport(reportId) {
        const response = await this.request(`/api/reports/${reportId}/download/`, {
            method: 'GET'
        });
        
        // Handle file download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = `report_${reportId}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    // Notifications
    async getNotifications(unreadOnly = false) {
        const params = unreadOnly ? '?unread_only=true' : '';
        return this.request(`/api/notifications/${params}`);
    }

    async markNotificationAsRead(notificationId) {
        return this.request(`/api/notifications/${notificationId}/mark_read/`, {
            method: 'POST'
        });
    }

    // Search
    async search(query, filters = {}) {
        return this.request('/api/search/', {
            method: 'POST',
            body: JSON.stringify({
                query: query,
                filters: filters
            })
        });
    }

    // User management
    async getUsers(filters = {}) {
        const params = new URLSearchParams(filters).toString();
        return this.request(`/api/accounts/users/?${params}`);
    }

    async getUserProfile() {
        return this.request('/api/accounts/profile/');
    }

    async updateUserProfile(data) {
        return this.request('/api/accounts/profile/', {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // AI Services
    async analyzeCV(file) {
        const formData = new FormData();
        formData.append('cv_file', file);

        return this.request('/api/ai_services/analyze_cv/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('authToken')}`
            },
            body: formData
        });
    }

    async matchCandidates(processId) {
        return this.request('/api/ai_services/match_candidates/', {
            method: 'POST',
            body: JSON.stringify({ process_id: processId })
        });
    }
}

/**
 * Django Forms Helper
 * Utilities for working with Django forms and validation
 */
class DjangoForms {
    static validateForm(formData, rules) {
        const errors = {};
        
        for (const [field, validators] of Object.entries(rules)) {
            const value = formData[field];
            
            for (const validator of validators) {
                const error = validator(value);
                if (error) {
                    errors[field] = errors[field] || [];
                    errors[field].push(error);
                }
            }
        }
        
        return Object.keys(errors).length > 0 ? errors : null;
    }

    static validators = {
        required: (value) => {
            if (!value || value.toString().trim() === '') {
                return 'Este campo es requerido';
            }
            return null;
        },
        
        email: (value) => {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (value && !emailRegex.test(value)) {
                return 'Formato de email inválido';
            }
            return null;
        },
        
        minLength: (min) => (value) => {
            if (value && value.length < min) {
                return `Mínimo ${min} caracteres`;
            }
            return null;
        },
        
        maxLength: (max) => (value) => {
            if (value && value.length > max) {
                return `Máximo ${max} caracteres`;
            }
            return null;
        },
        
        numeric: (value) => {
            if (value && isNaN(Number(value))) {
                return 'Debe ser un número válido';
            }
            return null;
        },
        
        phone: (value) => {
            const phoneRegex = /^\+?[\d\s\-\(\)]+$/;
            if (value && !phoneRegex.test(value)) {
                return 'Formato de teléfono inválido';
            }
            return null;
        }
    };
}

/**
 * WebSocket Manager for real-time features
 */
class DjangoWebSocket {
    constructor(url = 'ws://localhost:8000/ws/') {
        this.url = url;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectInterval = 1000;
        this.listeners = {};
    }

    connect() {
        try {
            this.socket = new WebSocket(this.url);
            
            this.socket.onopen = (event) => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                this.emit('connected', event);
            };
            
            this.socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                this.emit('message', data);
                
                // Emit specific event types
                if (data.type) {
                    this.emit(data.type, data);
                }
            };
            
            this.socket.onclose = (event) => {
                console.log('WebSocket disconnected');
                this.emit('disconnected', event);
                this.handleReconnect();
            };
            
            this.socket.onerror = (error) => {
                console.error('WebSocket error:', error);
                this.emit('error', error);
            };
            
        } catch (error) {
            console.error('Failed to connect WebSocket:', error);
            this.handleReconnect();
        }
    }

    handleReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`);
            setTimeout(() => this.connect(), this.reconnectInterval * this.reconnectAttempts);
        }
    }

    send(data) {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify(data));
        } else {
            console.warn('WebSocket not connected');
        }
    }

    on(event, callback) {
        if (!this.listeners[event]) {
            this.listeners[event] = [];
        }
        this.listeners[event].push(callback);
    }

    off(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
        }
    }

    emit(event, data) {
        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback(data));
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }
    }
}

/**
 * Django Integration Utilities
 */
class DjangoUtils {
    // Convert Django model data to frontend format
    static formatModelData(data, modelType) {
        switch (modelType) {
            case 'candidate':
                return {
                    id: data.id,
                    name: `${data.first_name} ${data.last_name}`,
                    email: data.email,
                    phone: data.phone,
                    skills: data.skills ? data.skills.split(',') : [],
                    experience: data.experience_years,
                    status: data.status,
                    createdAt: new Date(data.created_at),
                    updatedAt: new Date(data.updated_at)
                };
                
            case 'process':
                return {
                    id: data.id,
                    title: data.title,
                    description: data.description,
                    status: data.status,
                    client: data.client_name,
                    requirements: data.requirements ? JSON.parse(data.requirements) : {},
                    createdAt: new Date(data.created_at),
                    deadline: data.deadline ? new Date(data.deadline) : null
                };
                
            default:
                return data;
        }
    }

    // Convert frontend data to Django format
    static formatForDjango(data, modelType) {
        switch (modelType) {
            case 'candidate':
                const [firstName, ...lastNameParts] = data.name.split(' ');
                return {
                    first_name: firstName,
                    last_name: lastNameParts.join(' '),
                    email: data.email,
                    phone: data.phone,
                    skills: Array.isArray(data.skills) ? data.skills.join(',') : data.skills,
                    experience_years: data.experience
                };
                
            case 'process':
                return {
                    title: data.title,
                    description: data.description,
                    requirements: JSON.stringify(data.requirements),
                    deadline: data.deadline ? data.deadline.toISOString().split('T')[0] : null
                };
                
            default:
                return data;
        }
    }

    // Handle Django validation errors
    static formatDjangoErrors(errors) {
        const formatted = {};
        
        for (const [field, messages] of Object.entries(errors)) {
            if (Array.isArray(messages)) {
                formatted[field] = messages.join(', ');
            } else if (typeof messages === 'string') {
                formatted[field] = messages;
            } else {
                formatted[field] = 'Error de validación';
            }
        }
        
        return formatted;
    }

    // Date formatting for Django
    static formatDateForDjango(date) {
        if (!date) return null;
        
        if (typeof date === 'string') {
            date = new Date(date);
        }
        
        return date.toISOString();
    }

    // Parse Django datetime
    static parseDjangoDate(dateString) {
        if (!dateString) return null;
        return new Date(dateString);
    }
}

// Export for use in other modules
window.DjangoAPI = DjangoAPI;
window.DjangoForms = DjangoForms;
window.DjangoWebSocket = DjangoWebSocket;
window.DjangoUtils = DjangoUtils;