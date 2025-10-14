// CodeCollab - Main JavaScript File

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    initializeTooltips();

    // Initialize real-time notifications
    initializeNotifications();

    // Initialize search functionality
    initializeSearch();

    // Initialize code collaboration if on editor page
    if (document.getElementById('code-editor')) {
        initializeCodeCollaboration();
    }
}

function initializeTooltips() {
    // Initialize Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeNotifications() {
    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
}

function initializeSearch() {
    // Live search functionality
    const searchInput = document.querySelector('input[type="search"]');
    if (searchInput) {
        let searchTimeout;

        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (this.value.length >= 2 || this.value.length === 0) {
                    this.form.submit();
                }
            }, 500);
        });
    }
}

// Real-time collaboration functions
function initializeCodeCollaboration() {
    // Connect to SocketIO server
    const socket = io();

    // Collaboration state
    let collaborationState = {
        projectId: null,
        fileId: null,
        isConnected: false,
        activeUsers: new Set()
    };

    // Socket event handlers
    socket.on('connect', function() {
        collaborationState.isConnected = true;
        updateConnectionStatus(true);
    });

    socket.on('disconnect', function() {
        collaborationState.isConnected = false;
        updateConnectionStatus(false);
    });

    socket.on('user_joined_project', function(data) {
        addActiveUser(data.username, data.avatar_url);
        showNotification(`${data.username} joined the project`, 'info');
    });

    socket.on('user_joined_file', function(data) {
        addActiveUser(data.username, data.avatar_url);
    });

    socket.on('user_disconnected', function(data) {
        removeActiveUser(data.username);
        showNotification(`${data.username} left`, 'warning');
    });

    socket.on('code_updated', function(data) {
        if (data.file_id === collaborationState.fileId) {
            updateCodeContent(data.content, data.updated_by);
        }
    });

    // Join collaboration room
    function joinCollaboration(projectId, fileId) {
        collaborationState.projectId = projectId;
        collaborationState.fileId = fileId;

        socket.emit('join_editor', {
            project_id: projectId,
            file_id: fileId
        });
    }

    // Send code changes
    function sendCodeChange(content) {
        if (collaborationState.isConnected && collaborationState.fileId) {
            socket.emit('code_change', {
                file_id: collaborationState.fileId,
                content: content
            });
        }
    }

    // Update connection status UI
    function updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            statusElement.className = connected ? 'text-success' : 'text-danger';
            statusElement.innerHTML = connected ?
                '<i class="fas fa-circle"></i> Connected' :
                '<i class="fas fa-circle"></i> Disconnected';
        }
    }

    // Add active user to UI
    function addActiveUser(username, avatarUrl) {
        collaborationState.activeUsers.add(username);
        updateActiveUsersList();
    }

    // Remove user from active users
    function removeActiveUser(username) {
        collaborationState.activeUsers.delete(username);
        updateActiveUsersList();
    }

    // Update active users list in UI
    function updateActiveUsersList() {
        const usersList = document.getElementById('active-users');
        if (usersList) {
            usersList.innerHTML = '';
            collaborationState.activeUsers.forEach(username => {
                const userElement = document.createElement('div');
                userElement.className = 'active-user';
                userElement.innerHTML = `
                    <i class="fas fa-circle text-success me-2"></i>
                    <span>${username}</span>
                `;
                usersList.appendChild(userElement);
            });
        }
    }

    // Show notification
    function showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Add to notifications container
        const container = document.getElementById('notifications-container') || document.body;
        container.appendChild(notification);

        // Auto-remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }

    // Update code content from remote changes
    function updateCodeContent(content, updatedBy) {
        const editor = document.getElementById('code-editor');
        if (editor && editor.value !== content) {
            editor.value = content;

            // Show who made the change
            showNotification(`${updatedBy} updated the code`, 'info');
        }
    }

    // Expose functions to global scope for use in other files
    window.codeCollaboration = {
        join: joinCollaboration,
        sendChange: sendCodeChange,
        socket: socket
    };
}

// File operations
function downloadFile(filename, content) {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(content));
    element.setAttribute('download', filename);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showNotification('Copied to clipboard!', 'success');
    }, function(err) {
        console.error('Could not copy text: ', err);
    });
}

// Utility functions
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        debounce,
        formatFileSize,
        downloadFile,
        copyToClipboard
    };
}
