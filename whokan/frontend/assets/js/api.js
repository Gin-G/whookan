// assets/js/api.js

/**
 * API Service for WhoKan frontend
 * Handles all communication with the backend API
 */

class ApiService {
    constructor(baseUrl = '/api/v1') {  
        this.baseUrl = baseUrl;
        this.token = localStorage.getItem('token');
    }

    /**
     * Set the authentication token
     * @param {string} token - JWT token
     */
    setToken(token) {
        this.token = token;
        localStorage.setItem('token', token);
    }

    /**
     * Clear the authentication token
     */
    clearToken() {
        this.token = null;
        localStorage.removeItem('token');
    }

    /**
     * Get authorization headers for API requests
     * @returns {Object} Headers with Authorization
     */
    getHeaders() {
        const headers = {
            'Content-Type': 'application/json'
        };

        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        return headers;
    }

    /**
     * Make a request to the API
     * @param {string} endpoint - API endpoint
     * @param {string} method - HTTP method
     * @param {Object} data - Request data
     * @returns {Promise} API response
     */
    async request(endpoint, method = 'GET', data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        
        const options = {
            method,
            headers: this.getHeaders(),
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            
            // Handle unauthorized responses
            if (response.status === 401) {
                this.clearToken();
                window.location.href = '/login.html';
                throw new Error('Unauthorized');
            }
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'API request failed');
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }

    /**
     * Login user and get access token
     * @param {string} email - User email
     * @param {string} password - User password
     * @returns {Promise} API response with token
     */
    async login(email, password) {
        const formData = new FormData();
        formData.append('username', email);
        formData.append('password', password);
        
        const response = await fetch(`${this.baseUrl}/auth/login`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Login failed');
        }
        
        const data = await response.json();
        this.setToken(data.access_token);
        return data;
    }

    /**
     * Register a new user
     * @param {Object} userData - User registration data
     * @returns {Promise} API response with user data
     */
    async register(userData) {
        return this.request('/users/', 'POST', userData);
    }

    /**
     * Get current user profile
     * @returns {Promise} API response with user data
     */
    async getCurrentUser() {
        return this.request('/users/me');
    }

    /**
     * Update current user profile
     * @param {Object} userData - User update data
     * @returns {Promise} API response with updated user data
     */
    async updateProfile(userData) {
        return this.request('/users/me', 'PUT', userData);
    }

    /**
     * Add a skill to user profile
     * @param {Object} skillData - Skill data
     * @returns {Promise} API response with updated user data
     */
    async addSkill(skillData) {
        return this.request('/users/me/skills', 'POST', skillData);
    }

    /**
     * Add multiple skills to user profile
     * @param {string} skillsText - Raw text with skills
     * @param {string} format - Format of the skills text (newline or csv)
     * @returns {Promise} API response with updated user data
     */
    async addSkillsBulk(skillsText, format = 'newline') {
        return this.request('/users/me/skills/bulk', 'POST', {
            skills: skillsText,
            format
        });
    }

    /**
     * Remove a skill from user profile
     * @param {string} skillId - ID of the skill to remove
     * @returns {Promise} API response with updated user data
     */
    async removeSkill(skillId) {
        return this.request(`/users/me/skills/${skillId}`, 'DELETE');
    }

    /**
     * Search users by skill
     * @param {string} skillTerm - Skill search term
     * @returns {Promise} API response with users data
     */
    async searchUsers(skillTerm) {
        return this.request(`/users/?skill=${encodeURIComponent(skillTerm)}`);
    }

    /**
     * Create a help request
     * @param {Object} requestData - Request data
     * @returns {Promise} API response with request data
     */
    async createHelpRequest(requestData) {
        return this.request('/help-requests', 'POST', requestData);
    }

    /**
     * Get all open help requests
     * @returns {Promise} API response with requests data
     */
    async getHelpRequests() {
        return this.request('/help-requests');
    }

    /**
     * Confirm help was provided
     * @param {Object} confirmationData - Confirmation data
     * @returns {Promise} API response with updated user data
     */
    async confirmHelp(confirmationData) {
        return this.request('/help-requests/confirm', 'POST', confirmationData);
    }
}

// Export the API service
const api = new ApiService();