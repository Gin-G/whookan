// assets/js/dashboard.js

/**
 * Dashboard page functionality for WhoKan
 */

// Initialize dashboard data
async function initDashboard() {
    // Check authentication
    if (!requireAuth()) return;
    
    try {
        // Get current user from session storage or API
        let currentUser = getCurrentUser();
        if (!currentUser) {
            currentUser = await api.getCurrentUser();
            sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
        }
        
        // Update dashboard metrics
        document.getElementById('skills-count').textContent = currentUser.skills.length;
        document.getElementById('helped-count').textContent = currentUser.helped_count;
        document.getElementById('user-rank').textContent = computeRank(currentUser.helped_count);
        
        // Render skills
        renderDashboardSkills(currentUser.skills);
        
        // Fetch and render help requests
        await fetchHelpRequests();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        if (error.message === 'Unauthorized') {
            window.location.href = '/index.html';
        }
    }
}

// Render skills list for dashboard
function renderDashboardSkills(skills) {
    const skillsList = document.getElementById('dashboard-skills-list');
    const loadingIndicator = document.getElementById('skills-loading');
    
    if (loadingIndicator) {
        loadingIndicator.classList.add('hidden');
    }
    
    if (!skillsList) return;
    
    skillsList.innerHTML = '';
    
    if (!skills || skills.length === 0) {
        skillsList.innerHTML = '<p class="text-gray-500 text-center py-4">No skills added yet. <a href="profile.html" class="text-indigo-600 hover:text-indigo-500">Add some skills</a> to your profile.</p>';
        return;
    }
    
    skills.forEach(skill => {
        const skillElement = document.createElement('div');
        skillElement.className = 'bg-blue-100 px-3 py-1 rounded-full flex items-center mb-2 mr-2 inline-block';
        skillElement.innerHTML = `
            <span class="text-blue-800 text-sm">${skill.name}</span>
        `;
        skillsList.appendChild(skillElement);
    });
}

// Fetch help requests
async function fetchHelpRequests() {
    const requestsList = document.getElementById('help-requests-list');
    const loadingIndicator = document.getElementById('help-requests-loading');
    const noRequestsMessage = document.getElementById('no-help-requests');
    
    if (!requestsList || !loadingIndicator || !noRequestsMessage) return;
    
    try {
        const requests = await api.getHelpRequests();
        
        // Hide loading indicator
        loadingIndicator.classList.add('hidden');
        
        if (!requests || requests.length === 0) {
            noRequestsMessage.classList.remove('hidden');
            return;
        }
        
        // Show the list
        requestsList.classList.remove('hidden');
        requestsList.innerHTML = '';
        
        // Build cache of users and skills for display
        const usersCache = {};
        const skillsCache = {};
        
        // Get current user for help button functionality
        const currentUser = getCurrentUser();
        
        // Populate the list with requests
        requests.forEach(request => {
            const requestItem = document.createElement('li');
            requestItem.className = 'py-4 flex animate-fadeIn';
            
            let requesterName = 'Unknown User';
            let skillName = 'Unknown Skill';
            
            // Attempt to get requester name
            if (usersCache[request.requester_id]) {
                requesterName = usersCache[request.requester_id].name;
            }
            
            // Attempt to get skill name
            if (skillsCache[request.skill_id]) {
                skillName = skillsCache[request.skill_id].name;
            }
            
            requestItem.innerHTML = `
                <div class="ml-3 flex-1">
                    <p class="text-sm font-medium text-gray-900">${skillName}</p>
                    <p class="text-sm text-gray-500">${request.description}</p>
                    <p class="text-sm text-gray-500">Requested by ${requesterName} · ${formatDate(request.created_at)}</p>
                </div>
                <div class="ml-auto">
                    <button data-request-id="${request.id}" data-skill-id="${request.skill_id}" class="help-button inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-full shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500">
                        I can help
                    </button>
                </div>
            `;
            
            requestsList.appendChild(requestItem);
            
            // Fetch user and skill info if not in cache
            if (!usersCache[request.requester_id]) {
                fetchUserInfo(request.requester_id, usersCache, requestItem);
            }
            
            if (!skillsCache[request.skill_id]) {
                fetchSkillInfo(request.skill_id, skillsCache, requestItem);
            }
        });
        
        // Add event listeners to help buttons
        const helpButtons = document.querySelectorAll('.help-button');
        helpButtons.forEach(button => {
            button.addEventListener('click', () => {
                const requestId = button.getAttribute('data-request-id');
                const skillId = button.getAttribute('data-skill-id');
                offerHelp(requestId, skillId, currentUser.id);
            });
        });
    } catch (error) {
        console.error('Error fetching help requests:', error);
        loadingIndicator.classList.add('hidden');
        requestsList.innerHTML = `
            <div class="text-center py-4 text-red-500">
                <p>Error loading help requests. Please try again later.</p>
            </div>
        `;
    }
}

// Fetch user info for display
async function fetchUserInfo(userId, cache, element) {
    try {
        // This would be an API call in production
        // For now, just simulate with some example data
        cache[userId] = {
            id: userId,
            name: 'User ' + userId.substring(0, 4)
        };
        
        // Update the element
        const userElement = element.querySelector(`p:contains("Requested by")`);
        if (userElement) {
            userElement.textContent = `Requested by ${cache[userId].name} · ${formatDate(new Date())}`;
        }
    } catch (error) {
        console.error('Error fetching user info:', error);
    }
}

// Fetch skill info for display
async function fetchSkillInfo(skillId, cache, element) {
    try {
        // This would be an API call in production
        // For now, just simulate with some example data
        cache[skillId] = {
            id: skillId,
            name: 'Skill ' + skillId.substring(0, 4)
        };
        
        // Update the element
        const skillElement = element.querySelector('p.text-sm.font-medium');
        if (skillElement) {
            skillElement.textContent = cache[skillId].name;
        }
    } catch (error) {
        console.error('Error fetching skill info:', error);
    }
}

// Offer help for a request
async function offerHelp(requestId, skillId, helperId) {
    if (!confirm('Are you sure you want to offer help with this request?')) {
        return;
    }
    
    try {
        const confirmationData = {
            request_id: requestId,
            helper_id: helperId,
            skill_id: skillId
        };
        
        await api.confirmHelp(confirmationData);
        
        alert('Thank you for offering help! Your help count has been updated.');
        
        // Refresh the dashboard
        window.location.reload();
    } catch (error) {
        console.error('Error offering help:', error);
        alert('Failed to process your help offer. Please try again later.');
    }
}

// Initialize the dashboard page
document.addEventListener('DOMContentLoaded', initDashboard);