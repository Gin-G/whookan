/**
 * Skills management functions for WhoKan
 */

// Handle adding a new skill
async function addSkill(event) {
    event.preventDefault();
    
    const skillName = document.getElementById('skill-name').value.trim();
    const skillDescription = document.getElementById('skill-description')?.value.trim();
    
    if (!skillName) {
        showError('Please enter a skill name.', 'skill-error-message');
        return;
    }
    
    try {
        document.getElementById('add-skill-button').disabled = true;
        
        const skillData = {
            name: skillName,
            description: skillDescription || ''
        };
        
        const updatedUser = await api.addSkill(skillData);
        
        // Update user data in session storage
        sessionStorage.setItem('currentUser', JSON.stringify(updatedUser));
        
        // Show success message
        showSuccess('Skill added successfully!', 'skill-success-message');
        
        // Clear the input fields
        document.getElementById('skill-name').value = '';
        if (document.getElementById('skill-description')) {
            document.getElementById('skill-description').value = '';
        }
        
        // Refresh the skills list
        renderSkillsList(updatedUser.skills);
    } catch (error) {
        showError(error.message || 'Failed to add skill.', 'skill-error-message');
    } finally {
        document.getElementById('add-skill-button').disabled = false;
    }
}

// Handle bulk import of skills
async function importSkillsBulk(event) {
    event.preventDefault();
    
    const skillsText = document.getElementById('bulk-skills').value.trim();
    const format = document.querySelector('input[name="format"]:checked').value;
    
    if (!skillsText) {
        showError('Please enter skills to import.', 'skill-error-message');
        return;
    }
    
    try {
        document.getElementById('import-skills-button').disabled = true;
        
        const updatedUser = await api.addSkillsBulk(skillsText, format);
        
        // Update user data in session storage
        sessionStorage.setItem('currentUser', JSON.stringify(updatedUser));
        
        // Show success message
        showSuccess('Skills imported successfully!', 'skill-success-message');
        
        // Clear the textarea
        document.getElementById('bulk-skills').value = '';
        
        // Refresh the skills list
        renderSkillsList(updatedUser.skills);
        
        // Close the modal if we're using one
        const modal = document.getElementById('import-skills-modal');
        if (modal && typeof modal.close === 'function') {
            modal.close();
        } else if (modal) {
            modal.classList.add('hidden');
        }
    } catch (error) {
        showError(error.message || 'Failed to import skills.', 'skill-error-message');
    } finally {
        document.getElementById('import-skills-button').disabled = false;
    }
}

// Handle removing a skill
async function removeSkill(skillId) {
    if (!confirm('Are you sure you want to remove this skill?')) {
        return;
    }
    
    try {
        const updatedUser = await api.removeSkill(skillId);
        
        // Update user data in session storage
        sessionStorage.setItem('currentUser', JSON.stringify(updatedUser));
        
        // Show success message
        showSuccess('Skill removed successfully!', 'skill-success-message');
        
        // Refresh the skills list
        renderSkillsList(updatedUser.skills);
    } catch (error) {
        showError(error.message || 'Failed to remove skill.', 'skill-error-message');
    }
}

// Render skills list
function renderSkillsList(skills) {
    const skillsList = document.getElementById('skills-list');
    if (!skillsList) return;
    
    skillsList.innerHTML = '';
    
    if (!skills || skills.length === 0) {
        skillsList.innerHTML = '<p class="text-gray-500 text-center py-4">No skills added yet.</p>';
        return;
    }
    
    skills.forEach(skill => {
        const skillElement = document.createElement('div');
        skillElement.className = 'bg-blue-100 px-3 py-1 rounded-full flex items-center mb-2 mr-2 inline-block';
        skillElement.innerHTML = `
            <span class="text-blue-800 text-sm">${skill.name}</span>
            <button type="button" class="ml-2 text-blue-500 hover:text-blue-700" data-skill-id="${skill.id}">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
            </button>
        `;
        skillsList.appendChild(skillElement);
        
        // Add event listener to remove button
        const removeButton = skillElement.querySelector('button');
        removeButton.addEventListener('click', () => removeSkill(skill.id));
    });
}

// Toggle bulk import modal
function toggleImportModal() {
    const modal = document.getElementById('import-skills-modal');
    if (modal.classList.contains('hidden')) {
        modal.classList.remove('hidden');
    } else {
        modal.classList.add('hidden');
    }
}

// Initialize skills page
document.addEventListener('DOMContentLoaded', () => {
    // Handle user loaded event
    document.addEventListener('userLoaded', (e) => {
        const currentUser = e.detail;
        renderSkillsList(currentUser.skills);
    });
    
    // Check if we're on the profile page
    const skillsForm = document.getElementById('skill-form');
    if (skillsForm) {
        requireAuth();
        skillsForm.addEventListener('submit', addSkill);
        
        // Initial render of skills list if user data is available
        const currentUser = getCurrentUser();
        if (currentUser) {
            renderSkillsList(currentUser.skills);
        }
    }
    
    // Check if we have a bulk import form
    const bulkImportForm = document.getElementById('bulk-import-form');
    if (bulkImportForm) {
        bulkImportForm.addEventListener('submit', importSkillsBulk);
    }
    
    // Handle import button
    const importButton = document.getElementById('show-import-modal');
    if (importButton) {
        importButton.addEventListener('click', toggleImportModal);
    }
    
    // Handle close modal button
    const closeModalButton = document.getElementById('close-import-modal');
    if (closeModalButton) {
        closeModalButton.addEventListener('click', toggleImportModal);
    }
});