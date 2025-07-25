// Gothic Command Editor with Syntax Highlighting and Live Preview
class GothicCommandEditor {
    constructor() {
        this.currentCommand = null;
        this.embedPreview = null;
        this.syntaxRules = this.initSyntaxRules();
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupEmbedEditor();
        this.setupAutoSave();
        this.loadTemplates();
    }

    setupEventListeners() {
        // Command list interactions
        document.addEventListener('click', (e) => {
            if (e.target.matches('.command-item')) {
                this.selectCommand(e.target.dataset.commandId);
            }
            
            if (e.target.matches('.btn-new-command')) {
                this.createNewCommand();
            }
            
            if (e.target.matches('.btn-delete-command')) {
                this.deleteCommand(e.target.dataset.commandId);
            }
            
            if (e.target.matches('.btn-duplicate-command')) {
                this.duplicateCommand(e.target.dataset.commandId);
            }
        });

        // Editor interactions
        document.addEventListener('input', (e) => {
            if (e.target.matches('.command-editor')) {
                this.handleContentChange(e.target);
            }
            
            if (e.target.matches('.embed-field')) {
                this.updateEmbedPreview();
            }
        });

        // Template selection
        document.addEventListener('change', (e) => {
            if (e.target.matches('.template-selector')) {
                this.loadTemplate(e.target.value);
            }
        });

        // Save command
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-save-command')) {
                this.saveCommand();
            }
        });

        // Import/Export
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-export-commands')) {
                this.exportCommands();
            }
            
            if (e.target.matches('.btn-import-commands')) {
                this.importCommands();
            }
        });
    }

    initSyntaxRules() {
        return {
            // Discord mentions
            userMention: /<@!?\d+>/g,
            roleMention: /<@&\d+>/g,
            channelMention: /<#\d+>/g,
            
            // Variables
            variable: /\{([^}]+)\}/g,
            
            // Discord formatting
            bold: /\*\*([^*]+)\*\*/g,
            italic: /\*([^*]+)\*/g,
            underline: /__([^_]+)__/g,
            strikethrough: /~~([^~]+)~~/g,
            code: /`([^`]+)`/g,
            codeBlock: /```([^`]+)```/g,
            
            // Gothic emojis
            gothicEmoji: /🌹|🥀|🕯️|🌙|⭐|🗝️|👑|💎|🖤|⚰️|💀/g
        };
    }

    setupEmbedEditor() {
        const embedContainer = document.querySelector('.embed-editor');
        if (!embedContainer) return;

        // Create embed form
        embedContainer.innerHTML = `
            <div class="embed-form gothic-border">
                <h4>🎨 Gothic Embed Designer</h4>
                
                <div class="form-group">
                    <label class="form-label">Title</label>
                    <input type="text" class="form-control embed-field" data-field="title" 
                           placeholder="Enter embed title...">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Description</label>
                    <textarea class="form-control embed-field" data-field="description" rows="4"
                              placeholder="Enter embed description..."></textarea>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Color</label>
                    <div class="color-picker-group">
                        <input type="color" class="form-control embed-field" data-field="color" value="#711417">
                        <span class="color-label">Gothic Red (#711417)</span>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Fields</label>
                    <div class="embed-fields-container">
                        <button type="button" class="btn btn-primary btn-add-field">Add Field</button>
                    </div>
                </div>
                
                <div class="form-group">
                    <label class="form-label">Footer Text</label>
                    <input type="text" class="form-control embed-field" data-field="footer" 
                           placeholder="🌹 RosethornBot - Gothic Excellence">
                </div>
                
                <div class="form-group">
                    <label class="form-label">Thumbnail URL</label>
                    <input type="url" class="form-control embed-field" data-field="thumbnail" 
                           placeholder="https://example.com/image.png">
                </div>
            </div>
            
            <div class="embed-preview-container">
                <h4>📱 Discord Preview</h4>
                <div class="embed-preview"></div>
            </div>
        `;

        this.setupEmbedFieldManager();
        this.updateEmbedPreview();
    }

    setupEmbedFieldManager() {
        document.addEventListener('click', (e) => {
            if (e.target.matches('.btn-add-field')) {
                this.addEmbedField();
            }
            
            if (e.target.matches('.btn-remove-field')) {
                this.removeEmbedField(e.target.closest('.embed-field-item'));
            }
        });
    }

    addEmbedField() {
        const container = document.querySelector('.embed-fields-container');
        const fieldItem = document.createElement('div');
        fieldItem.className = 'embed-field-item';
        fieldItem.innerHTML = `
            <div class="field-inputs">
                <input type="text" class="form-control embed-field" data-field="fieldName" 
                       placeholder="Field name">
                <textarea class="form-control embed-field" data-field="fieldValue" 
                          placeholder="Field value" rows="2"></textarea>
                <label class="field-inline">
                    <input type="checkbox" class="embed-field" data-field="fieldInline"> Inline
                </label>
                <button type="button" class="btn btn-danger btn-sm btn-remove-field">Remove</button>
            </div>
        `;
        
        container.insertBefore(fieldItem, container.querySelector('.btn-add-field'));
        this.updateEmbedPreview();
    }

    removeEmbedField(fieldItem) {
        fieldItem.remove();
        this.updateEmbedPreview();
    }

    handleContentChange(editor) {
        // Apply syntax highlighting
        this.applySyntaxHighlighting(editor);
        
        // Auto-save
        this.scheduleAutoSave();
        
        // Update character count
        this.updateCharacterCount(editor);
    }

    applySyntaxHighlighting(editor) {
        const content = editor.value;
        const highlightedContent = this.highlightSyntax(content);
        
        // Create highlighted overlay
        let overlay = editor.parentElement.querySelector('.syntax-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.className = 'syntax-overlay';
            editor.parentElement.appendChild(overlay);
        }
        
        overlay.innerHTML = highlightedContent;
    }

    highlightSyntax(content) {
        let highlighted = this.escapeHtml(content);
        
        // Apply highlighting rules
        Object.entries(this.syntaxRules).forEach(([type, regex]) => {
            highlighted = highlighted.replace(regex, (match) => {
                return `<span class="syntax-${type}">${match}</span>`;
            });
        });
        
        return highlighted;
    }

    updateEmbedPreview() {
        const embedData = this.getEmbedData();
        const preview = document.querySelector('.embed-preview');
        
        if (!preview) return;
        
        // Send to server for preview generation
        fetch('/api/embed-preview', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(embedData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                preview.innerHTML = data.html;
            }
        })
        .catch(error => {
            console.error('Embed preview error:', error);
            preview.innerHTML = '<div class="preview-error">Preview unavailable</div>';
        });
    }

    getEmbedData() {
        const embedData = {};
        
        // Get basic fields
        document.querySelectorAll('.embed-field').forEach(field => {
            const fieldName = field.dataset.field;
            const value = field.type === 'checkbox' ? field.checked : field.value;
            
            if (value && fieldName) {
                if (fieldName.startsWith('field')) {
                    // Handle embed fields separately
                    return;
                }
                embedData[fieldName] = value;
            }
        });
        
        // Get embed fields
        const fields = [];
        document.querySelectorAll('.embed-field-item').forEach(item => {
            const name = item.querySelector('[data-field="fieldName"]').value;
            const value = item.querySelector('[data-field="fieldValue"]').value;
            const inline = item.querySelector('[data-field="fieldInline"]').checked;
            
            if (name && value) {
                fields.push({ name, value, inline });
            }
        });
        
        if (fields.length > 0) {
            embedData.fields = fields;
        }
        
        return embedData;
    }

    loadTemplates() {
        const templates = [
            {
                name: 'Gothic Welcome',
                data: {
                    title: '🌹 Welcome to Our Gothic Manor',
                    description: 'Welcome, {user}, to our Victorian realm! May your journey here be filled with roses and thorns alike.',
                    color: '#711417',
                    footer: '🕯️ Welcome to the Gothic Community',
                    fields: [
                        {
                            name: '📜 Getting Started',
                            value: '• Read our rules and guidelines\n• Introduce yourself in the welcome chamber\n• Explore our Gothic channels',
                            inline: false
                        }
                    ]
                }
            },
            {
                name: 'Announcement Template',
                data: {
                    title: '📢 Gothic Manor Announcement',
                    description: '{announcement_text}',
                    color: '#711417',
                    footer: '🌹 RosethornBot - Victorian Excellence',
                    fields: [
                        {
                            name: '📅 Date',
                            value: '{date}',
                            inline: true
                        },
                        {
                            name: '👑 Announced By',
                            value: '{moderator}',
                            inline: true
                        }
                    ]
                }
            },
            {
                name: 'Event Notification',
                data: {
                    title: '🎭 Gothic Manor Event',
                    description: 'Join us for a magnificent Gothic gathering!',
                    color: '#711417',
                    footer: '🕯️ See you in the Gothic halls',
                    fields: [
                        {
                            name: '📅 When',
                            value: '{event_date}',
                            inline: true
                        },
                        {
                            name: '📍 Where',
                            value: '{event_location}',
                            inline: true
                        },
                        {
                            name: '🎪 What to Expect',
                            value: '{event_description}',
                            inline: false
                        }
                    ]
                }
            }
        ];
        
        const selector = document.querySelector('.template-selector');
        if (selector) {
            templates.forEach(template => {
                const option = document.createElement('option');
                option.value = JSON.stringify(template.data);
                option.textContent = template.name;
                selector.appendChild(option);
            });
        }
    }

    loadTemplate(templateData) {
        if (!templateData) return;
        
        try {
            const data = JSON.parse(templateData);
            
            // Fill basic fields
            Object.entries(data).forEach(([key, value]) => {
                if (key === 'fields') return;
                
                const field = document.querySelector(`[data-field="${key}"]`);
                if (field) {
                    field.value = value;
                }
            });
            
            // Clear existing fields
            document.querySelectorAll('.embed-field-item').forEach(item => item.remove());
            
            // Add template fields
            if (data.fields) {
                data.fields.forEach(field => {
                    this.addEmbedField();
                    const fieldItem = document.querySelector('.embed-field-item:last-of-type');
                    fieldItem.querySelector('[data-field="fieldName"]').value = field.name;
                    fieldItem.querySelector('[data-field="fieldValue"]').value = field.value;
                    fieldItem.querySelector('[data-field="fieldInline"]').checked = field.inline || false;
                });
            }
            
            this.updateEmbedPreview();
            window.gothicDashboard.showNotification('Template loaded with Gothic elegance! 🌹', 'success');
        } catch (error) {
            console.error('Template loading error:', error);
            window.gothicDashboard.showNotification('Failed to load template', 'error');
        }
    }

    setupAutoSave() {
        this.autoSaveTimeout = null;
    }

    scheduleAutoSave() {
        clearTimeout(this.autoSaveTimeout);
        this.autoSaveTimeout = setTimeout(() => {
            this.autoSave();
        }, 30000); // Auto-save every 30 seconds
    }

    autoSave() {
        if (!this.currentCommand) return;
        
        const commandData = this.getCommandData();
        localStorage.setItem(`autosave_command_${this.currentCommand}`, JSON.stringify(commandData));
        
        // Show subtle auto-save indicator
        const indicator = document.querySelector('.autosave-indicator');
        if (indicator) {
            indicator.textContent = 'Auto-saved';
            indicator.style.opacity = '1';
            setTimeout(() => {
                indicator.style.opacity = '0';
            }, 2000);
        }
    }

    async selectCommand(commandId) {
        try {
            const response = await fetch(`/api/commands/${commandId}`);
            const command = await response.json();
            
            this.currentCommand = commandId;
            this.loadCommandIntoEditor(command);
            
            // Highlight selected command
            document.querySelectorAll('.command-item').forEach(item => {
                item.classList.remove('active');
            });
            document.querySelector(`[data-command-id="${commandId}"]`).classList.add('active');
            
        } catch (error) {
            console.error('Error loading command:', error);
            window.gothicDashboard.showNotification('Failed to load command', 'error');
        }
    }

    loadCommandIntoEditor(command) {
        // Load command content
        const contentEditor = document.querySelector('.command-editor');
        if (contentEditor) {
            contentEditor.value = command.content;
            this.handleContentChange(contentEditor);
        }
        
        // Load embed data if present
        if (command.embed_data) {
            this.loadEmbedData(command.embed_data);
        }
        
        // Load command name
        const nameField = document.querySelector('[name="command_name"]');
        if (nameField) {
            nameField.value = command.name;
        }
    }

    loadEmbedData(embedData) {
        // Clear existing fields
        document.querySelectorAll('.embed-field-item').forEach(item => item.remove());
        
        // Load basic embed properties
        Object.entries(embedData).forEach(([key, value]) => {
            if (key === 'fields') return;
            
            const field = document.querySelector(`[data-field="${key}"]`);
            if (field) {
                field.value = value;
            }
        });
        
        // Load embed fields
        if (embedData.fields) {
            embedData.fields.forEach(field => {
                this.addEmbedField();
                const fieldItem = document.querySelector('.embed-field-item:last-of-type');
                fieldItem.querySelector('[data-field="fieldName"]').value = field.name;
                fieldItem.querySelector('[data-field="fieldValue"]').value = field.value;
                fieldItem.querySelector('[data-field="fieldInline"]').checked = field.inline || false;
            });
        }
        
        this.updateEmbedPreview();
    }

    getCommandData() {
        const contentEditor = document.querySelector('.command-editor');
        const nameField = document.querySelector('[name="command_name"]');
        
        return {
            name: nameField ? nameField.value : '',
            content: contentEditor ? contentEditor.value : '',
            embed_data: this.getEmbedData(),
            guild_id: window.gothicDashboard.currentGuild
        };
    }

    async saveCommand() {
        if (!this.currentCommand && !this.validateNewCommand()) {
            return;
        }
        
        const commandData = this.getCommandData();
        
        try {
            const url = this.currentCommand ? 
                `/api/commands?id=${this.currentCommand}` : 
                '/api/commands';
            const method = this.currentCommand ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(commandData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                window.gothicDashboard.showNotification(result.message, 'success');
                
                // Clear auto-save
                if (this.currentCommand) {
                    localStorage.removeItem(`autosave_command_${this.currentCommand}`);
                }
                
                // Refresh command list
                this.refreshCommandList();
            } else {
                window.gothicDashboard.showNotification(result.error, 'error');
            }
        } catch (error) {
            console.error('Error saving command:', error);
            window.gothicDashboard.showNotification('Failed to save command', 'error');
        }
    }

    validateNewCommand() {
        const nameField = document.querySelector('[name="command_name"]');
        const contentEditor = document.querySelector('.command-editor');
        
        if (!nameField || !nameField.value.trim()) {
            window.gothicDashboard.showNotification('Command name is required', 'error');
            return false;
        }
        
        if (!contentEditor || !contentEditor.value.trim()) {
            window.gothicDashboard.showNotification('Command content is required', 'error');
            return false;
        }
        
        return true;
    }

    createNewCommand() {
        this.currentCommand = null;
        
        // Clear editor
        const contentEditor = document.querySelector('.command-editor');
        const nameField = document.querySelector('[name="command_name"]');
        
        if (contentEditor) contentEditor.value = '';
        if (nameField) nameField.value = '';
        
        // Clear embed editor
        document.querySelectorAll('.embed-field').forEach(field => {
            if (field.type === 'checkbox') {
                field.checked = false;
            } else {
                field.value = '';
            }
        });
        
        document.querySelectorAll('.embed-field-item').forEach(item => item.remove());
        
        // Reset color to gothic default
        const colorField = document.querySelector('[data-field="color"]');
        if (colorField) {
            colorField.value = '#711417';
        }
        
        this.updateEmbedPreview();
        
        // Clear selection
        document.querySelectorAll('.command-item').forEach(item => {
            item.classList.remove('active');
        });
        
        window.gothicDashboard.showNotification('Ready to create new Gothic command 🌹', 'info');
    }

    async deleteCommand(commandId) {
        if (!confirm('Are you sure you want to delete this Gothic command? This action cannot be undone.')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/commands?id=${commandId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                window.gothicDashboard.showNotification(result.message, 'success');
                this.refreshCommandList();
                
                if (this.currentCommand === commandId) {
                    this.createNewCommand();
                }
            } else {
                window.gothicDashboard.showNotification(result.error, 'error');
            }
        } catch (error) {
            console.error('Error deleting command:', error);
            window.gothicDashboard.showNotification('Failed to delete command', 'error');
        }
    }

    async duplicateCommand(commandId) {
        try {
            const response = await fetch(`/api/commands/${commandId}`);
            const command = await response.json();
            
            // Create new command with duplicated data
            this.createNewCommand();
            
            // Load duplicated data
            const nameField = document.querySelector('[name="command_name"]');
            if (nameField) {
                nameField.value = `${command.name}_copy`;
            }
            
            this.loadCommandIntoEditor(command);
            
            window.gothicDashboard.showNotification('Command duplicated! Make your changes and save. 🌹', 'info');
        } catch (error) {
            console.error('Error duplicating command:', error);
            window.gothicDashboard.showNotification('Failed to duplicate command', 'error');
        }
    }

    async refreshCommandList() {
        try {
            const response = await fetch(`/api/commands?guild_id=${window.gothicDashboard.currentGuild}`);
            const commands = await response.json();
            
            const container = document.querySelector('.commands-list');
            if (container) {
                container.innerHTML = commands.map(cmd => `
                    <div class="command-item" data-command-id="${cmd.id}">
                        <div class="command-info">
                            <div class="command-name">${cmd.name}</div>
                            <div class="command-meta">Uses: ${cmd.uses} | Updated: ${new Date(cmd.updated_at).toLocaleDateString()}</div>
                        </div>
                        <div class="command-actions">
                            <button class="btn btn-sm btn-primary btn-duplicate-command" data-command-id="${cmd.id}">📋</button>
                            <button class="btn btn-sm btn-danger btn-delete-command" data-command-id="${cmd.id}">🗑️</button>
                        </div>
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error refreshing command list:', error);
        }
    }

    updateCharacterCount(editor) {
        const counter = editor.parentElement.querySelector('.character-count');
        if (counter) {
            const count = editor.value.length;
            const limit = editor.getAttribute('maxlength') || 2000;
            counter.textContent = `${count}/${limit}`;
            
            if (count > limit * 0.9) {
                counter.classList.add('warning');
            } else {
                counter.classList.remove('warning');
            }
        }
    }

    exportCommands() {
        fetch(`/api/commands?guild_id=${window.gothicDashboard.currentGuild}`)
            .then(response => response.json())
            .then(commands => {
                const dataStr = JSON.stringify(commands, null, 2);
                const dataBlob = new Blob([dataStr], {type: 'application/json'});
                
                const link = document.createElement('a');
                link.href = URL.createObjectURL(dataBlob);
                link.download = `gothic_commands_${new Date().toISOString().split('T')[0]}.json`;
                link.click();
                
                window.gothicDashboard.showNotification('Commands exported successfully! 📜', 'success');
            })
            .catch(error => {
                console.error('Export error:', error);
                window.gothicDashboard.showNotification('Failed to export commands', 'error');
            });
    }

    importCommands() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.json';
        
        input.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const commands = JSON.parse(e.target.result);
                    this.processImportedCommands(commands);
                } catch (error) {
                    window.gothicDashboard.showNotification('Invalid JSON file', 'error');
                }
            };
            reader.readAsText(file);
        };
        
        input.click();
    }

    async processImportedCommands(commands) {
        if (!Array.isArray(commands)) {
            window.gothicDashboard.showNotification('Invalid command format', 'error');
            return;
        }
        
        let imported = 0;
        let errors = 0;
        
        for (const command of commands) {
            try {
                const response = await fetch('/api/commands', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        ...command,
                        guild_id: window.gothicDashboard.currentGuild
                    })
                });
                
                if (response.ok) {
                    imported++;
                } else {
                    errors++;
                }
            } catch (error) {
                errors++;
            }
        }
        
        window.gothicDashboard.showNotification(
            `Import complete: ${imported} commands imported, ${errors} errors`, 
            errors > 0 ? 'warning' : 'success'
        );
        
        this.refreshCommandList();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize command editor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.command-editor-container')) {
        window.gothicCommandEditor = new GothicCommandEditor();
    }
});
