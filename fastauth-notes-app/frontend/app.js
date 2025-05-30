/**
 * MoodWise Notes App - Frontend JavaScript
 * 
 * This file contains shared functionality for the MoodWise Notes application
 * including authentication helpers, API calls, and utility functions.
 */

// Base API URL - update this if your backend is hosted elsewhere
const API_BASE_URL = '';

// Authentication helpers
const auth = {
    /**
     * Get the JWT token from localStorage
     * @returns {string|null} The JWT token or null if not found
     */
    getToken: function() {
        return localStorage.getItem('token');
    },
    
    /**
     * Check if the user is authenticated
     * @returns {boolean} True if authenticated, false otherwise
     */
    isAuthenticated: function() {
        return !!this.getToken();
    },
    
    /**
     * Logout the user by removing the token and redirecting to login page
     */
    logout: function() {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
    },
    
    /**
     * Redirect to login if not authenticated
     */
    requireAuth: function() {
        if (!this.isAuthenticated()) {
            window.location.href = 'login.html';
        }
    },
    
    /**
     * Redirect to dashboard if already authenticated
     */
    redirectIfAuthenticated: function() {
        if (this.isAuthenticated()) {
            window.location.href = 'dashboard.html';
        }
    }
};

// API helpers
const api = {
    /**
     * Get default headers including authorization if token exists
     * @param {boolean} includeContentType Whether to include Content-Type: application/json
     * @returns {Object} Headers object
     */
    headers: function(includeContentType = true) {
        const headers = {};
        
        if (includeContentType) {
            headers['Content-Type'] = 'application/json';
        }
        
        const token = auth.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        return headers;
    },
    
    /**
     * Make a GET request to the API
     * @param {string} endpoint The API endpoint
     * @returns {Promise} The fetch promise
     */
    get: async function(endpoint) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'GET',
            headers: this.headers(false)
        });
        
        // Handle 401 Unauthorized by logging out
        if (response.status === 401) {
            auth.logout();
            throw new Error('Authentication required');
        }
        
        return response;
    },
    
    /**
     * Make a POST request to the API
     * @param {string} endpoint The API endpoint
     * @param {Object} data The data to send
     * @returns {Promise} The fetch promise
     */
    post: async function(endpoint, data) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: this.headers(),
            body: JSON.stringify(data)
        });
        
        // Handle 401 Unauthorized by logging out
        if (response.status === 401) {
            auth.logout();
            throw new Error('Authentication required');
        }
        
        return response;
    },
    
    /**
     * Make a PUT request to the API
     * @param {string} endpoint The API endpoint
     * @param {Object} data The data to send
     * @returns {Promise} The fetch promise
     */
    put: async function(endpoint, data) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'PUT',
            headers: this.headers(),
            body: JSON.stringify(data)
        });
        
        // Handle 401 Unauthorized by logging out
        if (response.status === 401) {
            auth.logout();
            throw new Error('Authentication required');
        }
        
        return response;
    },
    
    /**
     * Make a DELETE request to the API
     * @param {string} endpoint The API endpoint
     * @returns {Promise} The fetch promise
     */
    delete: async function(endpoint) {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'DELETE',
            headers: this.headers(false)
        });
        
        // Handle 401 Unauthorized by logging out
        if (response.status === 401) {
            auth.logout();
            throw new Error('Authentication required');
        }
        
        return response;
    }
};

// Utility functions
const utils = {
    /**
     * Show an error message in the specified element
     * @param {string} message The error message
     * @param {HTMLElement} element The element to show the error in
     */
    showError: function(message, element) {
        element.textContent = message;
        element.style.display = 'block';
    },
    
    /**
     * Hide an error message element
     * @param {HTMLElement} element The element to hide
     */
    hideError: function(element) {
        element.textContent = '';
        element.style.display = 'none';
    },
    
    /**
     * Format a date string to a readable format
     * @param {string} dateString The ISO date string
     * @returns {string} Formatted date string
     */
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString();
    },
    
    /**
     * Escape HTML to prevent XSS
     * @param {string} unsafe The unsafe string
     * @returns {string} Escaped string
     */
    escapeHtml: function(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    },
    
    /**
     * Truncate a string to a specified length
     * @param {string} str The string to truncate
     * @param {number} length The maximum length
     * @returns {string} Truncated string
     */
    truncate: function(str, length) {
        if (str.length <= length) return str;
        return str.slice(0, length) + '...';
    }
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add logout functionality to all logout buttons
    const logoutButtons = document.querySelectorAll('[id="logout-btn"]');
    logoutButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            auth.logout();
        });
    });
});