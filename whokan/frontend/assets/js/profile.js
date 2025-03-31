// assets/js/profile.js

/**
 * Profile management functionality for WhoKan
 */

// Initialize profile page
async function initProfilePage() {
    // Check authentication
    if (!requireAuth()) return;
    
    try {
        // Get current user from session storage or API
        let currentUser = getCurrentUser();
        if (!currentUser) {
            currentUser = await api.getCurrentUser();
            sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
        }
        
        // Populate profile form
        populateProfileForm(currentUser);
        
        // Set up form submission
        const profileForm = document.getElementById('profile-form');
        if (profileForm) {
            profileForm.addEventListener('submit', handleProfileUpdate);
        }
    } catch (error) {
        console.error('Error initializing profile page:', error);
        if (error.message === 'Unauthorized') {
            window.location.href = '/index.html';
        }
    }
}

// Populate profile form with user data
function populateProfileForm(user) {
    document.getElementById('full-name').value = user.name || '';
    document.getElementById('job-title').value = user.title || '';
    document.getElementById('company').value = user.company || '';
    document.getElementById('email-address').value = user.email || '';
}

// Handle profile form submission
async function handleProfileUpdate(event) {
    event.preventDefault();
    
    const name = document.getElementById('full-name').value.trim();
    const title = document.getElementById('job-title').value.trim();
    const company = document.getElementById('company').value.trim();
    
    if (!name) {
        showError('Please enter your name.');
        return;
    }
    
    const updateData = {
        name,
        title,
        company
    };
    
    try {
        document.getElementById('save-profile-button').disabled = true;
        
        const updatedUser = await api.updateProfile(updateData);
        
        // Update session storage
        sessionStorage.setItem('currentUser', JSON.stringify(updatedUser));
        
        // Show success message
        showSuccess('Profile updated successfully!');
        
        // Update user display name in navbar
        const userNameElements = document.querySelectorAll('.current-user-name');
        userNameElements.forEach(element => {
            element.textContent = updatedUser.name;
        });
    } catch (error) {
        showError(error.message || 'Failed to update profile. Please try again.');
    } finally {
        document.getElementById('save-profile-button').disabled = false;
    }
}

// Initialize the profile page
document.addEventListener('DOMContentLoaded', initProfilePage);