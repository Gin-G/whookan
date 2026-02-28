// assets/js/search.js

/**
 * Search functionality for WhoKan
 */

// Initialize search page
async function initSearchPage() {
    // Check authentication
    if (!requireAuth()) return;
    
    // Set up search form
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', handleSearch);
    }
    
    // Set up help request modal
    setupHelpRequestModal();
}

// Handle search form submission
async function handleSearch(event) {
    event.preventDefault();
    
    const searchTerm = document.getElementById('search-term').value.trim();
    
    if (!searchTerm) {
        showError('Please enter a search term.');
        return;
    }
    
    // Show loading state
    document.getElementById('search-initial').classList.add('hidden');
    document.getElementById('search-no-results').classList.add('hidden');
    document.getElementById('search-results').classList.add('hidden');
    document.getElementById('search-loading').classList.remove('hidden');
    
    try {
        const results = await api.searchUsers(searchTerm);
        
        // Hide loading state
        document.getElementById('search-loading').classList.add('hidden');
        
        if (!results || results.length === 0) {
            // Show no results message
            document.getElementById('search-no-results').classList.remove('hidden');
            return;
        }
        
        // Show results
        renderSearchResults(results);
        document.getElementById('search-results').classList.remove('hidden');
    } catch (error) {
        // Hide loading state
        document.getElementById('search-loading').classList.add('hidden');
        document.getElementById('search-initial').classList.remove('hidden');
        showError(error.message || 'Error performing search. Please try again.');
    }
}

// Render search results
function renderSearchResults(users) {
    const resultsList = document.getElementById('search-results');
    if (!resultsList) return;
    
    resultsList.innerHTML = '';
    
    users.forEach(user => {
        const userElement = document.createElement('li');
        userElement.className = 'py-4 flex animate-fadeIn';
        userElement.innerHTML = `
            <div class="w-12 h-12 flex-shrink-0">
                <img class="h-12 w-12 rounded-full" src="/assets/img/placeholder-avatar.png" alt="User avatar">
            </div>
            <div class="ml-4 flex-1">
                <div class="flex items-center justify-between">
                    <h4 class="text-sm font-medium text-gray-900">${user.name}</h4>
                    <span class="text-sm text-green-600 font-medium">Helped <span>${user.helped_count}</span> people</span>
                </div>
                <p class="text-sm text-gray-500">${user.title || 'No title'} · ${user.company || 'No company'}</p>
                <div class="mt-2 flex flex-wrap gap-1">
                    ${user.skills.map(skill => {
                        const forumUrl = `/forum.html?skill_id=${encodeURIComponent(skill.id)}&skill_name=${encodeURIComponent(skill.name)}`;
                        const chatUrl = `/chat.html?skill_id=${encodeURIComponent(skill.id)}&skill_name=${encodeURIComponent(skill.name)}`;
                        return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800" data-skill-id="${skill.id}">
                            ${skill.name}
                            <a href="${forumUrl}" title="Forum" class="text-blue-500 hover:text-blue-700">📋</a>
                            <a href="${chatUrl}" title="Chat" class="text-blue-500 hover:text-blue-700">💬</a>
                        </span>`;
                    }).join('')}
                </div>
            </div>
            <div class="ml-2">
                <button data-user-id="${user.id}" class="request-help-button inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                    Request Help
                </button>
            </div>
        `;
        
        resultsList.appendChild(userElement);
    });
    
    // Add event listeners to help request buttons
    const requestButtons = document.querySelectorAll('.request-help-button');
    requestButtons.forEach(button => {
        button.addEventListener('click', () => {
            const userId = button.getAttribute('data-user-id');
            showHelpRequestModal(userId);
        });
    });
}

// Set up help request modal
function setupHelpRequestModal() {
    const modal = document.getElementById('help-request-modal');
    const closeButton = document.getElementById('close-request-modal');
    const form = document.getElementById('help-request-form');
    
    if (!modal || !closeButton || !form) return;
    
    // Close modal when clicking the close button
    closeButton.addEventListener('click', () => {
        modal.classList.add('hidden');
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.classList.add('hidden');
        }
    });
    
    // Handle form submission
    form.addEventListener('submit', handleHelpRequestSubmit);
}

// Show help request modal for a specific user
function showHelpRequestModal(userId) {
    const modal = document.getElementById('help-request-modal');
    const form = document.getElementById('help-request-form');
    const skillSelect = document.getElementById('skill-select');
    const helperNameElement = document.getElementById('helper-name');
    
    if (!modal || !form || !skillSelect || !helperNameElement) return;
    
    // Find the user in the search results
    const users = document.querySelectorAll('#search-results li');
    let selectedUser = null;
    
    users.forEach(userElement => {
        const button = userElement.querySelector('.request-help-button');
        if (button && button.getAttribute('data-user-id') === userId) {
            selectedUser = {
                id: userId,
                name: userElement.querySelector('h4').textContent,
                skills: []
            };
            
            // Get skills
            const skillElements = userElement.querySelectorAll('.bg-blue-100');
            skillElements.forEach(skillElement => {
                selectedUser.skills.push({
                    id: skillElement.getAttribute('data-skill-id'),
                    name: skillElement.textContent
                });
            });
        }
    });
    
    if (!selectedUser) {
        console.error('User not found:', userId);
        return;
    }
    
    // Update modal with user info
    helperNameElement.textContent = selectedUser.name;
    document.getElementById('helper-id').value = selectedUser.id;
    
    // Populate skill select
    skillSelect.innerHTML = '';
    selectedUser.skills.forEach(skill => {
        const option = document.createElement('option');
        option.value = skill.id;
        option.textContent = skill.name;
        skillSelect.appendChild(option);
    });
    
    // Show modal
    modal.classList.remove('hidden');
}

// Handle help request form submission
async function handleHelpRequestSubmit(event) {
    event.preventDefault();
    
    const helperId = document.getElementById('helper-id').value;
    const skillId = document.getElementById('skill-select').value;
    const description = document.getElementById('request-description').value.trim();
    
    if (!description) {
        alert('Please describe your request.');
        return;
    }
    
    const submitButton = document.getElementById('submit-request-button');
    submitButton.disabled = true;
    
    try {
        const requestData = {
            skill_id: skillId,
            description: description
        };
        
        await api.createHelpRequest(requestData);
        
        // Success
        document.getElementById('help-request-modal').classList.add('hidden');
        alert('Help request submitted successfully!');
        
        // Reset form
        document.getElementById('request-description').value = '';
    } catch (error) {
        console.error('Error submitting help request:', error);
        alert('Failed to submit help request. Please try again later.');
    } finally {
        submitButton.disabled = false;
    }
}

// Initialize the search page
document.addEventListener('DOMContentLoaded', initSearchPage);