// Advanced Code Editor with Real-time Collaboration

class CodeCollabEditor {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            language: 'python',
            theme: 'default',
            fontSize: 14,
            readOnly: false,
            ...options
        };

        this.editor = null;
        this.socket = null;
        this.isCollaborating = false;

        this.init();
    }

    init() {
        this.createEditor();
        this.setupEventListeners();
        this.applyTheme();

        if (this.options.collaborationEnabled) {
            this.enableCollaboration();
        }
    }

    createEditor() {
        // Create editor HTML structure
        this.container.innerHTML = `
            <div class="code-editor-container">
                <div class="editor-header">
                    <div class="header-left">
                        <span class="file-info">
                            <i class="${this.getLanguageIcon()} me-2"></i>
                            <span class="filename">${this.options.filename || 'untitled'}</span>
                            <span class="badge bg-light text-dark ms-2">${this.options.language}</span>
                        </span>
                    </div>
                    <div class="header-right">
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-secondary" id="copy-code">
                                <i class="fas fa-copy"></i>
                            </button>
                            <button class="btn btn-outline-secondary" id="download-code">
                                <i class="fas fa-download"></i>
                            </button>
                            <button class="btn btn-outline-secondary" id="format-code">
                                <i class="fas fa-broom"></i>
                            </button>
                        </div>
                        <div class="collaboration-status ms-3">
                            <span id="connection-status" class="text-muted">
                                <i class="fas fa-circle"></i> Offline
                            </span>
                        </div>
                    </div>
                </div>
                <div class="editor-body">
                    <textarea id="code-textarea"
                              placeholder="Start coding..."
                              spellcheck="false"></textarea>
                    <div class="editor-status-bar">
                        <div class="status-left">
                            <span class="cursor-position">Line 1, Column 1</span>
                        </div>
                        <div class="status-right">
                            <span class="file-size">0 chars</span>
                        </div>
                    </div>
                </div>
                <div class="editor-sidebar" id="collaborators-sidebar">
                    <div class="sidebar-header">
                        <h6>Active Collaborators</h6>
                    </div>
                    <div class="sidebar-content" id="active-users">
                        <div class="empty-state">
                            <i class="fas fa-users text-muted"></i>
                            <small class="text-muted">No active collaborators</small>
                        </div>
                    </div>
                </div>
            </div>
        `;

        this.editor = document.getElementById('code-textarea');
        this.setupCodeEditor();
    }

    setupCodeEditor() {
        // Set initial content
        if (this.options.initialContent) {
            this.editor.value = this.options.initialContent;
        }

        // Apply syntax highlighting (basic)
        this.applySyntaxHighlighting();

        // Update status bar
        this.updateStatusBar();

        // Set up editor event listeners
        this.editor.addEventListener('input', this.debounce(() => {
            this.onContentChange();
            this.updateStatusBar();
        }, 300));

        this.editor.addEventListener('keyup', (e) => {
            this.updateCursorPosition();
        });

        this.editor.addEventListener('click', () => {
            this.updateCursorPosition();
        });

        // Set up control buttons
        this.setupControlButtons();
    }

    setupControlButtons() {
        // Copy code
        document.getElementById('copy-code').addEventListener('click', () => {
            this.copyCode();
        });

        // Download code
        document.getElementById('download-code').addEventListener('click', () => {
            this.downloadCode();
        });

        // Format code
        document.getElementById('format-code').addEventListener('click', () => {
            this.formatCode();
        });
    }

    setupEventListeners() {
        // Handle editor focus
        this.editor.addEventListener('focus', () => {
            this.container.classList.add('focused');
        });

        this.editor.addEventListener('blur', () => {
            this.container.classList.remove('focused');
        });

        // Handle keyboard shortcuts
        this.editor.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    }

    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + S to save
        if ((event.ctrlKey || event.metaKey) && event.key === 's') {
            event.preventDefault();
            this.saveCode();
        }

        // Tab key handling
        if (event.key === 'Tab') {
            event.preventDefault();
            this.insertTab();
        }
    }

    insertTab() {
        const start = this.editor.selectionStart;
        const end = this.editor.selectionEnd;

        // Insert tab at cursor position
        this.editor.value = this.editor.value.substring(0, start) + '    ' + this.editor.value.substring(end);

        // Move cursor
        this.editor.selectionStart = this.editor.selectionEnd = start + 4;

        // Trigger change event
        this.onContentChange();
    }

    onContentChange() {
        // Apply syntax highlighting
        this.applySyntaxHighlighting();

        // Send changes to collaborators
        if (this.isCollaborating && window.codeCollaboration) {
            window.codeCollaboration.sendChange(this.editor.value);
        }

        // Update file size
        this.updateFileSize();
    }

    applySyntaxHighlighting() {
        // Basic syntax highlighting (in a real app, use a library like Prism.js or Highlight.js)
        const code = this.editor.value;

        // This is a simplified version - in production, use a proper syntax highlighter
        if (this.options.language === 'python') {
            // Python-specific highlighting could go here
        } else if (this.options.language === 'javascript') {
            // JavaScript-specific highlighting
        }

        // For now, we'll just maintain the basic textarea
        // In a real implementation, you would replace the textarea with a div
        // and use a proper code editor library
    }

    updateStatusBar() {
        this.updateCursorPosition();
        this.updateFileSize();
    }

    updateCursorPosition() {
        const positionElement = document.querySelector('.cursor-position');
        if (positionElement) {
            const text = this.editor.value.substring(0, this.editor.selectionStart);
            const lines = text.split('\n');
            const line = lines.length;
            const column = lines[lines.length - 1].length + 1;
            positionElement.textContent = `Line ${line}, Column ${column}`;
        }
    }

    updateFileSize() {
        const sizeElement = document.querySelector('.file-size');
        if (sizeElement) {
            const size = this.editor.value.length;
            sizeElement.textContent = `${size} char${size !== 1 ? 's' : ''}`;
        }
    }

    enableCollaboration() {
        this.isCollaborating = true;

        if (window.codeCollaboration && this.options.projectId && this.options.fileId) {
            window.codeCollaboration.join(this.options.projectId, this.options.fileId);
        }
    }

    copyCode() {
        navigator.clipboard.writeText(this.editor.value).then(() => {
            this.showNotification('Code copied to clipboard!', 'success');
        });
    }

    downloadCode() {
        const filename = this.options.filename || 'code.txt';
        const blob = new Blob([this.editor.value], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    formatCode() {
        // Basic code formatting based on language
        const code = this.editor.value;
        let formatted = code;

        switch (this.options.language) {
            case 'python':
                // Basic Python formatting (indentation)
                formatted = this.formatPythonCode(code);
                break;
            case 'javascript':
                // Basic JS formatting
                formatted = this.formatJavascriptCode(code);
                break;
            default:
                // Just trim for other languages
                formatted = code.trim();
        }

        this.editor.value = formatted;
        this.onContentChange();
        this.showNotification('Code formatted!', 'success');
    }

    formatPythonCode(code) {
        // Very basic Python formatting
        return code.split('\n').map(line => {
            return line.trim() ? '    ' + line.trim() : '';
        }).join('\n');
    }

    formatJavascriptCode(code) {
        // Very basic JS formatting
        return code.split('\n').map(line => {
            return line.trim();
        }).join('\n');
    }

    saveCode() {
        // Save code to server
        if (this.options.onSave) {
            this.options.onSave(this.editor.value);
        }
        this.showNotification('Code saved!', 'success');
    }

    getLanguageIcon() {
        const icons = {
            'python': 'fab fa-python',
            'javascript': 'fab fa-js-square',
            'java': 'fab fa-java',
            'html': 'fab fa-html5',
            'css': 'fab fa-css3-alt',
            'cpp': 'fas fa-file-code',
            'c': 'fas fa-file-code'
        };
        return icons[this.options.language] || 'fas fa-file-code';
    }

    applyTheme() {
        // Apply CSS theme
        const themes = {
            'default': 'editor-theme-default',
            'dark': 'editor-theme-dark',
            'light': 'editor-theme-light'
        };

        this.container.classList.add(themes[this.options.theme] || themes.default);
    }

    showNotification(message, type = 'info') {
        // Use the global notification function or create one
        if (window.showNotification) {
            window.showNotification(message, type);
        } else {
            alert(message); // Fallback
        }
    }

    debounce(func, wait) {
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

    // Public methods
    getValue() {
        return this.editor.value;
    }

    setValue(value) {
        this.editor.value = value;
        this.onContentChange();
    }

    setLanguage(language) {
        this.options.language = language;
        this.applySyntaxHighlighting();
        // Update UI
        const badge = this.container.querySelector('.badge');
        if (badge) {
            badge.textContent = language;
        }
    }

    destroy() {
        // Cleanup
        if (this.socket) {
            this.socket.disconnect();
        }
    }
}

// Initialize editor when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const editorContainers = document.querySelectorAll('.code-editor');

    editorContainers.forEach(container => {
        const options = {
            language: container.dataset.language || 'python',
            filename: container.dataset.filename,
            initialContent: container.dataset.content,
            collaborationEnabled: container.dataset.collaboration === 'true',
            projectId: container.dataset.projectId,
            fileId: container.dataset.fileId
        };

        new CodeCollabEditor(container.id, options);
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CodeCollabEditor;
}
