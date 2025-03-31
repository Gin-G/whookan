/**
 * Authentication related functions for WhoKan
 */

// Handle login form submission
async function handleLogin(event) {
    event.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    
    if (!email || !password) {
        showError('Please enter both email and password.');
        return;
    }
    
    try {
        document.getElementById('login-button').disabled = true;
        document.getElementById('login-spinner').classList.remove('hidden');
        
        await api.login(email, password);
        
        // Redirect to dashboard on successful login
        window.location.href = '/dashboard.html';
    } catch (error) {
        showError(error.message || 'Login failed. Please check your credentials.');
    } finally {
        document.getElementById('login-button').disabled = false;
        document.getElementById('login-spinner').classList.add('hidden');
    }
}

// Handle registration form submission
async function handleRegister(event) {
    event.preventDefault();
    
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    const title = document.getElementById('title').value;
    const company = document.getElementById('company').value;
    
    if (!name || !email || !password) {
        showError('Please fill in all required fields.');
        return;
    }
    
    if (password !== confirmPassword) {
        showError('Passwords do not match.');
        return;
    }
    
    try {
        document.getElementById('register-button').disabled = true;
        document.getElementById('register-spinner').classList.remove('hidden');
        
        const userData = {
            name,
            email,
            password,
            title,
            company
        };
        
        await api.register(userData);
        
        // Show success message
        showSuccess('Registration successful! Redirecting to login page...');
        
        // Redirect to login page after a short delay
        setTimeout(() => {
            window.location.href = '/login.html';
        }, 2000);
    } catch (error) {
        showError(error.message || 'Registration failed. Please try again.');
    } finally {
        document.getElementById('register-button').disabled = false;
        document.getElementById('register-spinner').classList.add('hidden');
    }
}

// Initialize auth pages
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're on the login page
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        redirectIfAuthenticated();
        loginForm.addEventListener('submit', handleLogin);
    }
    
    // Check if we're on the register page
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        redirectIfAuthenticated();
        registerForm.addEventListener('submit', handleRegister);
    }
    
    // Handle logout buttons
    const logoutButtons = document.querySelectorAll('.logout-button');
    logoutButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            logout();
        });
    });
});