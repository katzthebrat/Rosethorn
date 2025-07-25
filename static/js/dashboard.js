// RosethornBot Victorian Gothic Dashboard JavaScript

// Global state
let currentGuild = null;
let commandPreview = null;
let unsavedChanges = false;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    setupEventListeners();
    loadInitialData();
});

// Initialize dashboard components
function initializeDashboard() {
    console.log('🌹 Initializing Victorian Gothic Dashboard...');
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize modals
    initializeModals();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize auto-save
    initializeAutoSave();
    
    // Show welcome message
    showWelcomeMessage();
}

// Setup event listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', handleNavigation);
    });
    
    // Guild selector
    const guildSelector = document.getElementById('guild-selector');
    if (guildSelector) {
        guildSelector.addEventListener('change', handleGuildChange);
    }
    
    // Command editor
    const commandForm = document.getElementById('command-form');
    if (commandForm) {
        commandForm.addEventListener('submit', handleCommandSubmit);
        setupCommandEditor();
    }
    
    // Real-time preview
    const commandInputs = document.querySelectorAll('.command-input');
    commandInputs.forEach(input => {
        input.addEventListener('input', updateCommandPreview);
    });
    
    // File upload handling
    document.querySelectorAll('.file-upload').forEach(upload => {
        upload.addEventListener('change', handleFileUpload);
    });
    
    // Confirmation dialogs
    document.querySelectorAll('.confirm-action').forEach(button => {
        button.addEventListener('click', handleConfirmAction);
    });
    
    // Search functionality
    const searchInputs = document.querySelectorAll('.search-input');
    searchInputs.forEach(input => {
        input.addEventListener('input', debounce(handleSearch, 300));
    });
    
    // Theme toggle (if available)
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Window events
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('resize', handleWindowResize);
}

// Load initial data
function loadInitialData() {
    const guildId = getSelectedGuildId();
    if (guildId) {
        loadGuildData(guildId);
    }
    
    // Load dashboard statistics
    loadDashboardStats();
    
    // Start real-time updates
    startRealTimeUpdates();
}

// Handle navigation
function handleNavigation(event) {
    const link = event.target;
    const href = link.getAttribute('href');
    
    // Add loading state
    link.classList.add('loading');
    
    // Check for unsaved changes
    if (unsavedChanges) {
        event.preventDefault();
        showConfirmDialog(
            'Unsaved Changes',
            'You have unsaved changes. Do you want to save them before navigating away?',
            () => {
                saveCurrentChanges().then(() => {
                    window.location.href = href;
                });
            },
            () => {
                unsavedChanges = false;
                window.location.href = href;
            }
        );
    }
}

// Handle guild change
function handleGuildChange(event) {
    const guildId = event.target.value;
    if (guildId) {
        showLoading('Loading guild configuration...');
        loadGuildData(guildId);
    }
}

// Load guild data
async function loadGuildData(guildId) {
    try {
        const response = await fetch(`/api/guild/${guildId}/config`);
        const data = await response.json();
        
        if (response.ok) {
            currentGuild = data;
            updateGuildDisplay(data);
            loadGuildCommands(guildId);
            loadGuildStats(guildId);
        } else {
            showError('Failed to load guild data: ' + data.error);
        }
    } catch (error) {
        console.error('Error loading guild data:', error);
        showError('Network error while loading guild data');
    } finally {
        hideLoading();
    }
}

// Update guild display
function updateGuildDisplay(guild) {
    document.querySelectorAll('.guild-name').forEach(element => {
        element.textContent = guild.name;
    });
    
    // Update configuration form if present
    const configForm = document.getElementById('guild-config-form');
    if (configForm) {
        populateForm(configForm, guild);
    }
    
    // Update embed color preview
    const colorPreviews = document.querySelectorAll('.embed-color-preview');
    colorPreviews.forEach(preview => {
        preview.style.borderLeftColor = guild.embed_color;
    });
}

// Setup command editor
function setupCommandEditor() {
    const editor = document.getElementById('command-editor');
    if (!editor) return;
    
    // Syntax highlighting for command content
    const textareas = editor.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', function() {
            highlightSyntax(this);
            updateCommandPreview();
        });
        
        // Add line numbers
        addLineNumbers(textarea);
    });
    
    // Command type selector
    const typeSelector = document.getElementById('command-type');
    if (typeSelector) {
        typeSelector.addEventListener('change', handleCommandTypeChange);
    }
    
    // Embed toggle
    const embedToggle = document.getElementById('embed-toggle');
    if (embedToggle) {
        embedToggle.addEventListener('change', toggleEmbedOptions);
    }
}

// Handle command type change
function handleCommandTypeChange(event) {
    const type = event.target.value;
    const options = document.querySelectorAll('.command-option');
    
    options.forEach(option => {
        option.style.display = option.dataset.type === type ? 'block' : 'none';
    });
    
    updateCommandPreview();
}

// Toggle embed options
function toggleEmbedOptions(event) {
    const embedOptions = document.getElementById('embed-options');
    if (embedOptions) {
        embedOptions.style.display = event.target.checked ? 'block' : 'none';
    }
    updateCommandPreview();
}

// Update command preview
function updateCommandPreview() {
    const preview = document.getElementById('command-preview');
    if (!preview) return;
    
    const form = document.getElementById('command-form');
    const formData = new FormData(form);
    
    const commandData = {
        name: formData.get('name'),
        trigger: formData.get('trigger'),
        response: formData.get('response'),
        embed: formData.get('embed') === 'on',
        embed_title: formData.get('embed_title'),
        embed_description: formData.get('embed_description')
    };
    
    // Send preview request
    fetch('/api/commands/preview', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(commandData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            renderCommandPreview(preview, data.preview);
        }
    })
    .catch(error => {
        console.error('Preview error:', error);
    });
}

// Render command preview
function renderCommandPreview(container, preview) {
    container.innerHTML = '';
    
    if (preview.embed) {
        const embed = createEmbedElement(preview.embed);
        container.appendChild(embed);
    } else {
        const message = document.createElement('div');
        message.className = 'message-preview';
        message.textContent = preview.response;
        container.appendChild(message);
    }
}

// Create embed element
function createEmbedElement(embedData) {
    const embed = document.createElement('div');
    embed.className = 'embed-preview';
    embed.style.borderLeftColor = embedData.color || '#711417';
    
    if (embedData.title) {
        const title = document.createElement('div');
        title.className = 'embed-title';
        title.textContent = embedData.title;
        embed.appendChild(title);
    }
    
    if (embedData.description) {
        const description = document.createElement('div');
        description.className = 'embed-description';
        description.textContent = embedData.description;
        embed.appendChild(description);
    }
    
    return embed;
}

// Handle command submit
async function handleCommandSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const submitButton = form.querySelector('button[type="submit"]');
    
    // Show loading state
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Saving...';
    submitButton.disabled = true;
    
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.text();
        
        if (response.ok) {
            showSuccess('Command saved successfully! 🌹');
            unsavedChanges = false;
            
            // Reload commands list if on commands page
            if (window.location.pathname.includes('/commands')) {
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } else {
            showError('Failed to save command');
        }
    } catch (error) {
        console.error('Save error:', error);
        showError('Network error while saving command');
    } finally {
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    }
}

// Initialize tooltips
function initializeTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.classList.add('tooltip');
    });
}

// Initialize modals
function initializeModals() {
    const modals = document.querySelectorAll('.modal');
    const modalTriggers = document.querySelectorAll('[data-modal]');
    const modalCloses = document.querySelectorAll('.modal-close, [data-modal-close]');
    
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', function(e) {
            e.preventDefault();
            const modalId = this.dataset.modal;
            const modal = document.getElementById(modalId);
            if (modal) {
                showModal(modal);
            }
        });
    });
    
    modalCloses.forEach(close => {
        close.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                hideModal(modal);
            }
        });
    });
    
    // Close modal on backdrop click
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                hideModal(this);
            }
        });
    });
}

// Show modal
function showModal(modal) {
    modal.classList.add('show');
    document.body.style.overflow = 'hidden';
    
    // Focus management
    const firstFocusable = modal.querySelector('input, select, textarea, button');
    if (firstFocusable) {
        firstFocusable.focus();
    }
}

// Hide modal
function hideModal(modal) {
    modal.classList.remove('show');
    document.body.style.overflow = '';
}

// Initialize form validation
function initializeFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                clearFieldError(this);
                unsavedChanges = true;
            });
        });
    });
}

// Validate form
function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!validateField(input)) {
            isValid = false;
        }
    });
    
    return isValid;
}

// Validate field
function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    let isValid = true;
    let errorMessage = '';
    
    // Required validation
    if (field.hasAttribute('required') && !value) {
        isValid = false;
        errorMessage = 'This field is required';
    }
    
    // Type-specific validation
    if (value && type === 'email') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(value)) {
            isValid = false;
            errorMessage = 'Please enter a valid email address';
        }
    }
    
    if (value && type === 'url') {
        try {
            new URL(value);
        } catch {
            isValid = false;
            errorMessage = 'Please enter a valid URL';
        }
    }
    
    // Custom validation patterns
    const pattern = field.getAttribute('pattern');
    if (value && pattern) {
        const regex = new RegExp(pattern);
        if (!regex.test(value)) {
            isValid = false;
            errorMessage = field.getAttribute('data-error-message') || 'Invalid format';
        }
    }
    
    // Length validation
    const minLength = field.getAttribute('minlength');
    const maxLength = field.getAttribute('maxlength');
    
    if (value && minLength && value.length < parseInt(minLength)) {
        isValid = false;
        errorMessage = `Minimum ${minLength} characters required`;
    }
    
    if (value && maxLength && value.length > parseInt(maxLength)) {
        isValid = false;
        errorMessage = `Maximum ${maxLength} characters allowed`;
    }
    
    // Display validation result
    if (isValid) {
        clearFieldError(field);
    } else {
        showFieldError(field, errorMessage);
    }
    
    return isValid;
}

// Show field error
function showFieldError(field, message) {
    clearFieldError(field);
    
    field.classList.add('error');
    
    const errorElement = document.createElement('div');
    errorElement.className = 'field-error';
    errorElement.textContent = message;
    
    field.parentNode.appendChild(errorElement);
}

// Clear field error
function clearFieldError(field) {
    field.classList.remove('error');
    
    const errorElement = field.parentNode.querySelector('.field-error');
    if (errorElement) {
        errorElement.remove();
    }
}

// Initialize auto-save
function initializeAutoSave() {
    let autoSaveTimer = null;
    
    document.addEventListener('input', function(e) {
        if (e.target.matches('.auto-save')) {
            clearTimeout(autoSaveTimer);
            autoSaveTimer = setTimeout(() => {
                autoSave();
            }, 2000); // Auto-save after 2 seconds of inactivity
        }
    });
}

// Auto-save functionality
async function autoSave() {
    const form = document.querySelector('form[data-auto-save]');
    if (!form) return;
    
    const formData = new FormData(form);
    
    try {
        const response = await fetch('/api/auto-save', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showAutoSaveIndicator();
        }
    } catch (error) {
        console.error('Auto-save error:', error);
    }
}

// Show auto-save indicator
function showAutoSaveIndicator() {
    const indicator = document.getElementById('auto-save-indicator');
    if (indicator) {
        indicator.style.opacity = '1';
        setTimeout(() => {
            indicator.style.opacity = '0';
        }, 2000);
    }
}

// File upload handling
function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const maxSize = 5 * 1024 * 1024; // 5MB
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    
    if (file.size > maxSize) {
        showError('File size must be less than 5MB');
        event.target.value = '';
        return;
    }
    
    if (!allowedTypes.includes(file.type)) {
        showError('Only image files are allowed');
        event.target.value = '';
        return;
    }
    
    // Show preview
    const reader = new FileReader();
    reader.onload = function(e) {
        showImagePreview(e.target.result, event.target);
    };
    reader.readAsDataURL(file);
}

// Show image preview
function showImagePreview(src, input) {
    const preview = input.parentNode.querySelector('.image-preview');
    if (preview) {
        preview.src = src;
        preview.style.display = 'block';
    }
}

// Handle confirm actions
function handleConfirmAction(event) {
    event.preventDefault();
    
    const action = event.target.dataset.action;
    const message = event.target.dataset.confirmMessage || 'Are you sure?';
    const title = event.target.dataset.confirmTitle || 'Confirm Action';
    
    showConfirmDialog(title, message, () => {
        // Proceed with action
        if (action === 'delete') {
            performDeleteAction(event.target);
        } else if (action === 'reset') {
            performResetAction(event.target);
        } else {
            // Generic form submission
            const form = event.target.closest('form');
            if (form) {
                form.submit();
            }
        }
    });
}

// Perform delete action
async function performDeleteAction(button) {
    const url = button.getAttribute('href') || button.dataset.url;
    
    try {
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.ok) {
            showSuccess('Item deleted successfully');
            
            // Remove from DOM
            const row = button.closest('tr, .card, .item');
            if (row) {
                row.remove();
            }
        } else {
            showError('Failed to delete item');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showError('Network error while deleting');
    }
}

// Handle search
function handleSearch(event) {
    const query = event.target.value.toLowerCase();
    const searchTarget = event.target.dataset.searchTarget;
    const items = document.querySelectorAll(searchTarget);
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        const match = text.includes(query);
        item.style.display = match ? '' : 'none';
    });
    
    // Update search results count
    const visibleItems = Array.from(items).filter(item => item.style.display !== 'none');
    updateSearchResults(visibleItems.length, items.length);
}

// Update search results
function updateSearchResults(visible, total) {
    const counter = document.querySelector('.search-results-count');
    if (counter) {
        counter.textContent = `Showing ${visible} of ${total} results`;
    }
}

// Show notifications
function showSuccess(message) {
    showNotification(message, 'success');
}

function showError(message) {
    showNotification(message, 'error');
}

function showInfo(message) {
    showNotification(message, 'info');
}

function showWarning(message) {
    showNotification(message, 'warning');
}

// Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Add to container
    let container = document.getElementById('notifications');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notifications';
        container.className = 'notifications-container';
        document.body.appendChild(container);
    }
    
    container.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
    
    // Animate in
    requestAnimationFrame(() => {
        notification.classList.add('show');
    });
}

// Show confirm dialog
function showConfirmDialog(title, message, onConfirm, onCancel) {
    const modal = document.createElement('div');
    modal.className = 'modal confirm-modal show';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <h3>${title}</h3>
                <button class="modal-close">×</button>
            </div>
            <div class="modal-body">
                <p>${message}</p>
            </div>
            <div class="modal-footer">
                <button class="btn btn-secondary cancel-btn">Cancel</button>
                <button class="btn btn-danger confirm-btn">Confirm</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
    
    // Event handlers
    const confirmBtn = modal.querySelector('.confirm-btn');
    const cancelBtn = modal.querySelector('.cancel-btn');
    const closeBtn = modal.querySelector('.modal-close');
    
    function cleanup() {
        modal.remove();
        document.body.style.overflow = '';
    }
    
    confirmBtn.addEventListener('click', () => {
        cleanup();
        if (onConfirm) onConfirm();
    });
    
    cancelBtn.addEventListener('click', () => {
        cleanup();
        if (onCancel) onCancel();
    });
    
    closeBtn.addEventListener('click', cleanup);
    
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            cleanup();
            if (onCancel) onCancel();
        }
    });
}

// Loading states
function showLoading(message = 'Loading...') {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.querySelector('.loading-message').textContent = message;
        loader.style.display = 'flex';
    }
}

function hideLoading() {
    const loader = document.getElementById('page-loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

// Utility functions
function debounce(func, wait) {
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

function getSelectedGuildId() {
    const selector = document.getElementById('guild-selector');
    return selector ? selector.value : null;
}

function populateForm(form, data) {
    Object.keys(data).forEach(key => {
        const field = form.querySelector(`[name="${key}"]`);
        if (field) {
            if (field.type === 'checkbox') {
                field.checked = data[key];
            } else {
                field.value = data[key];
            }
        }
    });
}

// Handle window events
function handleBeforeUnload(event) {
    if (unsavedChanges) {
        event.preventDefault();
        event.returnValue = 'You have unsaved changes. Are you sure you want to leave?';
        return event.returnValue;
    }
}

function handleWindowResize() {
    // Adjust layouts on resize
    const tables = document.querySelectorAll('.table-responsive');
    tables.forEach(table => {
        if (window.innerWidth < 768) {
            table.classList.add('mobile-view');
        } else {
            table.classList.remove('mobile-view');
        }
    });
}

// Start real-time updates
function startRealTimeUpdates() {
    // Update timestamps
    setInterval(updateTimestamps, 60000); // Every minute
    
    // Update stats
    setInterval(loadDashboardStats, 300000); // Every 5 minutes
}

// Update timestamps
function updateTimestamps() {
    const timestamps = document.querySelectorAll('[data-timestamp]');
    timestamps.forEach(element => {
        const timestamp = parseInt(element.dataset.timestamp);
        const timeAgo = getTimeAgo(timestamp);
        element.textContent = timeAgo;
    });
}

// Get time ago string
function getTimeAgo(timestamp) {
    const now = Date.now();
    const diff = now - timestamp;
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
        return `${days} day${days > 1 ? 's' : ''} ago`;
    } else if (hours > 0) {
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else if (minutes > 0) {
        return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    } else {
        return 'Just now';
    }
}

// Load dashboard stats
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        if (response.ok) {
            updateStatsDisplay(stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Update stats display
function updateStatsDisplay(stats) {
    Object.keys(stats).forEach(key => {
        const element = document.querySelector(`[data-stat="${key}"]`);
        if (element) {
            animateCounter(element, parseInt(stats[key]));
        }
    });
}

// Animate counter
function animateCounter(element, target) {
    const current = parseInt(element.textContent) || 0;
    const increment = (target - current) / 20;
    let count = current;
    
    const timer = setInterval(() => {
        count += increment;
        if ((increment > 0 && count >= target) || (increment < 0 && count <= target)) {
            count = target;
            clearInterval(timer);
        }
        element.textContent = Math.floor(count).toLocaleString();
    }, 50);
}

// Show welcome message
function showWelcomeMessage() {
    const isFirstVisit = !localStorage.getItem('dashboard_visited');
    
    if (isFirstVisit) {
        setTimeout(() => {
            showInfo('Welcome to the RosethornBot Victorian Gothic Dashboard! 🌹');
            localStorage.setItem('dashboard_visited', 'true');
        }, 1000);
    }
}

// Save current changes
async function saveCurrentChanges() {
    const form = document.querySelector('form[data-auto-save]');
    if (!form) return;
    
    const formData = new FormData(form);
    
    try {
        const response = await fetch(form.action, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            unsavedChanges = false;
            showSuccess('Changes saved successfully');
        } else {
            throw new Error('Save failed');
        }
    } catch (error) {
        console.error('Save error:', error);
        throw error;
    }
}

// Export functions for global access
window.RosethornDashboard = {
    showSuccess,
    showError,
    showInfo,
    showWarning,
    showLoading,
    hideLoading,
    showModal,
    hideModal,
    showConfirmDialog,
    updateCommandPreview
};

console.log('🌹 RosethornBot Dashboard JavaScript loaded successfully');
