/**
 * API Client para el Sistema de Reclutamiento
 * Maneja todas las llamadas HTTP al backend Django
 */

class RecruitmentAPI {
    constructor() {
        this.baseURL = 'http://localhost:8000/api';
        this.token = localStorage.getItem('authToken');
    }

    // Configuración de headers por defecto
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json',
        };
        
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }
        
        return headers;
    }

    // Método genérico para hacer peticiones
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: this.getHeaders(),
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            if (!response.ok) {
                if (response.status === 401) {
                    this.handleUnauthorized();
                    throw new Error('No autorizado');
                }
                throw new Error(`Error ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    // Manejo de token expirado
    handleUnauthorized() {
        localStorage.removeItem('authToken');
        window.location.href = '/login';
    }

    // Autenticación
    async login(email, password) {
        const response = await this.request('/auth/token/', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        
        if (response.access) {
            this.token = response.access;
            localStorage.setItem('authToken', this.token);
            localStorage.setItem('refreshToken', response.refresh);
        }
        
        return response;
    }

    // Refresh token
    async refreshToken() {
        const refreshToken = localStorage.getItem('refreshToken');
        if (!refreshToken) throw new Error('No refresh token available');
        
        const response = await this.request('/auth/token/refresh/', {
            method: 'POST',
            body: JSON.stringify({ refresh: refreshToken })
        });
        
        this.token = response.access;
        localStorage.setItem('authToken', this.token);
        return response;
    }

    // Dashboard - Estadísticas generales
    async getDashboardStats() {
        return await this.request('/dashboard/stats/');
    }

    // Procesos de Reclutamiento
    async getProcesses(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        const endpoint = queryParams ? `/profiles/?${queryParams}` : '/profiles/';
        return await this.request(endpoint);
    }

    async getProcessById(id) {
        return await this.request(`/profiles/${id}/`);
    }

    async createProcess(data) {
        return await this.request('/profiles/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateProcess(id, data) {
        return await this.request(`/profiles/${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    async deleteProcess(id) {
        return await this.request(`/profiles/${id}/`, {
            method: 'DELETE'
        });
    }

    // Candidatos
    async getCandidates(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        const endpoint = queryParams ? `/candidates/?${queryParams}` : '/candidates/';
        return await this.request(endpoint);
    }

    async getCandidateById(id) {
        return await this.request(`/candidates/${id}/`);
    }

    async createCandidate(data) {
        return await this.request('/candidates/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async updateCandidate(id, data) {
        return await this.request(`/candidates/${id}/`, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // Evaluaciones
    async getEvaluations(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        const endpoint = queryParams ? `/evaluations/?${queryParams}` : '/evaluations/';
        return await this.request(endpoint);
    }

    async getEvaluationById(id) {
        return await this.request(`/evaluations/${id}/`);
    }

    async createEvaluation(data) {
        return await this.request('/evaluations/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    async getPendingApprovals() {
        return await this.request('/evaluations/?status=pending_approval');
    }

    async approveCandidate(evaluationId) {
        return await this.request(`/evaluations/${evaluationId}/approve/`, {
            method: 'POST'
        });
    }

    async rejectCandidate(evaluationId, reason) {
        return await this.request(`/evaluations/${evaluationId}/reject/`, {
            method: 'POST',
            body: JSON.stringify({ reason })
        });
    }

    // Clientes
    async getClients(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        const endpoint = queryParams ? `/clients/?${queryParams}` : '/clients/';
        return await this.request(endpoint);
    }

    async getClientById(id) {
        return await this.request(`/clients/${id}/`);
    }

    async createClient(data) {
        return await this.request('/clients/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Equipo (Usuarios)
    async getTeamMembers() {
        return await this.request('/accounts/users/');
    }

    async getTeamMemberById(id) {
        return await this.request(`/accounts/users/${id}/`);
    }

    async createTeamMember(data) {
        return await this.request('/accounts/users/', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Documentos
    async getDocuments(filters = {}) {
        const queryParams = new URLSearchParams(filters).toString();
        const endpoint = queryParams ? `/documents/api/generated/?${queryParams}` : '/documents/api/generated/';
        return await this.request(endpoint);
    }

    async generateDocument(templateId, data) {
        return await this.request('/documents/api/generated/generate/', {
            method: 'POST',
            body: JSON.stringify({
                template_id: templateId,
                ...data
            })
        });
    }

    async getDocumentTemplates() {
        return await this.request('/documents/api/templates/');
    }

    async getDocumentStatistics() {
        return await this.request('/documents/api/generated/statistics/');
    }

    // Reportes
    async getReports(type = 'monthly') {
        return await this.request(`/reports/?type=${type}`);
    }

    async generateReport(type, filters = {}) {
        return await this.request('/reports/generate/', {
            method: 'POST',
            body: JSON.stringify({
                type,
                filters
            })
        });
    }

    // Actividad reciente
    async getRecentActivity(limit = 10) {
        return await this.request(`/accounts/users/activity/?limit=${limit}`);
    }

    // Notificaciones
    async getNotifications() {
        return await this.request('/notifications/');
    }

    async markNotificationAsRead(id) {
        return await this.request(`/notifications/${id}/mark_read/`, {
            method: 'POST'
        });
    }

    // Upload de archivos (CV)
    async uploadCV(file, candidateId = null) {
        const formData = new FormData();
        formData.append('file', file);
        if (candidateId) {
            formData.append('candidate_id', candidateId);
        }

        return await fetch(`${this.baseURL}/candidates/upload-cv/`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.token}`
            },
            body: formData
        }).then(response => {
            if (!response.ok) throw new Error('Upload failed');
            return response.json();
        });
    }

    // Análisis de IA
    async analyzeCV(candidateId) {
        return await this.request(`/candidates/${candidateId}/analyze/`, {
            method: 'POST'
        });
    }

    async getAIAnalysisHistory(candidateId) {
        return await this.request(`/candidates/${candidateId}/ai-analysis/`);
    }
}

// Utilidades para manejo de datos
class DataUtils {
    static formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    static formatDateTime(dateString) {
        return new Date(dateString).toLocaleString('es-ES', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    static formatCurrency(amount, currency = 'MXN') {
        return new Intl.NumberFormat('es-MX', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }

    static getStatusColor(status) {
        const statusColors = {
            'active': 'bg-green-100 text-green-800',
            'activo': 'bg-green-100 text-green-800',
            'pending': 'bg-yellow-100 text-yellow-800',
            'pendiente': 'bg-yellow-100 text-yellow-800',
            'paused': 'bg-gray-100 text-gray-800',
            'pausado': 'bg-gray-100 text-gray-800',
            'completed': 'bg-blue-100 text-blue-800',
            'completado': 'bg-blue-100 text-blue-800',
            'rejected': 'bg-red-100 text-red-800',
            'rechazado': 'bg-red-100 text-red-800'
        };
        return statusColors[status.toLowerCase()] || 'bg-gray-100 text-gray-800';
    }

    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static generateAvatar(name) {
        return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=random&size=32`;
    }
}

// Notificaciones Toast
class NotificationManager {
    static show(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-sm transform transition-all duration-300 translate-x-full`;
        
        const colors = {
            success: 'bg-green-500 text-white',
            error: 'bg-red-500 text-white',
            warning: 'bg-yellow-500 text-black',
            info: 'bg-blue-500 text-white'
        };
        
        notification.className += ` ${colors[type]}`;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 10);
        
        // Auto remove
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, duration);
    }

    static success(message) {
        this.show(message, 'success');
    }

    static error(message) {
        this.show(message, 'error');
    }

    static warning(message) {
        this.show(message, 'warning');
    }

    static info(message) {
        this.show(message, 'info');
    }
}

// Exportar para uso global
window.RecruitmentAPI = RecruitmentAPI;
window.DataUtils = DataUtils;
window.NotificationManager = NotificationManager;