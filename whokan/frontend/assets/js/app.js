/**
 * Main application script for WhoKan
 * This file contains common functions and utilities for the frontend
 */

// Check if user is authenticated
function isAuthenticated() {
    return localStorage.getItem('token') !== null;
}

// Redirect to login if not authenticated
function requireAuth() {
    if (!isAuthenticated()) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

// Redirect to dashboard if already authenticated
function redirectIfAuthenticated() {
    if (isAuthenticated()) {
        window.location.href = '/dashboard.html';
        return true;
    }
    return false;
}

// Show error message
function showError(message, elementId = 'error-message') {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorElement.classList.add('hidden');
        }, 5000);
    } else {
        console.error(message);
    }
}

// Show success message
function showSuccess(message, elementId = 'success-message') {
    const successElement = document.getElementById(elementId);
    if (successElement) {
        successElement.textContent = message;
        successElement.classList.remove('hidden');
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            successElement.classList.add('hidden');
        }, 5000);
    } else {
        console.log(message);
    }
}

// Compute user rank based on help count
function computeRank(helpCount) {
    if (helpCount === 0) return 'Newcomer';
    if (helpCount < 5) return 'Helper';
    if (helpCount < 10) return 'Skilled';
    if (helpCount < 20) return 'Expert';
    return 'Master';
}

// Format date to locale string
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

// Include HTML components
function includeHTML() {
    const includes = document.getElementsByTagName('include');
    
    Array.from(includes).forEach(async include => {
        const file = include.getAttribute('src');
        try {
            const response = await fetch(file);
            if (response.ok) {
                const html = await response.text();
                include.insertAdjacentHTML('afterend', html);
            } else {
                include.insertAdjacentHTML('afterend', `Error loading ${file}`);
            }
        } catch (error) {
            include.insertAdjacentHTML('afterend', `Error: ${error.message}`);
        } finally {
            include.remove();
        }
    });
}

// Execute when DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    includeHTML();
    
    // Initialize current user if applicable
    if (isAuthenticated()) {
        initCurrentUser();
    }
});

// Initialize current user data
async function initCurrentUser() {
    try {
        // Set loading state if needed
        
        const currentUser = await api.getCurrentUser();
        
        // Store in session storage for easy access across pages
        sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
        
        // Update UI elements with user data
        const userNameElements = document.querySelectorAll('.current-user-name');
        userNameElements.forEach(element => {
            element.textContent = currentUser.name;
        });
        
        // Dispatch event for components that need current user data
        const event = new CustomEvent('userLoaded', { detail: currentUser });
        document.dispatchEvent(event);
        
        return currentUser;
    } catch (error) {
        console.error('Error initializing user:', error);
        // If error is auth-related, redirect to login
        if (error.message === 'Unauthorized') {
            window.location.href = '/login.html';
        }
        return null;
    }
}

// Get current user data
function getCurrentUser() {
    const userData = sessionStorage.getItem('currentUser');
    return userData ? JSON.parse(userData) : null;
}

// Handle logout
function logout() {
    api.clearToken();
    sessionStorage.removeItem('currentUser');
    window.location.href = '/login.html';
}