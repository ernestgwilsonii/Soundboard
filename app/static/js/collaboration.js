/**
 * collaboration.js
 * Handles real-time synchronization for soundboards using Socket.IO.
 */

class CollaborationManager {
    constructor(boardId, currentUser) {
        this.boardId = boardId;
        this.currentUser = currentUser;
        this.socket = null;
        this.presenceContainer = document.getElementById('presence-list');
        this.statusBadge = document.getElementById('live-status-badge');
        this.activityList = document.getElementById('board-activity-log');
        this.isLocked = false;
    }

    init() {
        // Initialize Socket.IO connection
        this.socket = io();

        this.socket.on('connect', () => {
            console.log('Connected to collaboration server');
            this.updateStatus(true);
            this.joinBoard();
        });

        this.socket.on('disconnect', () => {
            console.log('Disconnected from collaboration server');
            this.updateStatus(false);
        });

        this.socket.on('presence_update', (users) => {
            this.renderPresence(users);
        });

        this.socket.on('board_updated', (data) => {
            console.log('Board updated by collaborator:', data);
            this.handleRemoteUpdate(data);
        });

        this.socket.on('slot_locked', (data) => {
            this.handleSlotLock(data.sound_id, data.user);
        });

        this.socket.on('slot_released', (data) => {
            this.handleSlotRelease(data.sound_id);
        });

        this.socket.on('update_sound_order', (data) => {
            this.handleRemoteReorder(data.sound_ids);
        });
    }

    joinBoard() {
        this.socket.emit('join_board', { board_id: this.boardId });
    }

    updateStatus(online) {
        if (this.statusBadge) {
            if (online) {
                this.statusBadge.classList.remove('bg-secondary');
                this.statusBadge.classList.add('bg-success');
                this.statusBadge.innerHTML = '<i class="fas fa-circle small"></i> Live';
            } else {
                this.statusBadge.classList.remove('bg-success');
                this.statusBadge.classList.add('bg-secondary');
                this.statusBadge.innerHTML = '<i class="fas fa-circle-notch fa-spin small"></i> Offline';
            }
        }
    }

    renderPresence(users) {
        if (!this.presenceContainer) return;

        this.presenceContainer.innerHTML = '';
        users.forEach(user => {
            const dot = document.createElement('span');
            dot.className = 'presence-user badge rounded-pill bg-light text-dark border me-1';
            dot.title = user.username;
            dot.innerHTML = `<i class="fas fa-user-circle"></i> ${user.username}`;
            
            if (this.currentUser && user.id === this.currentUser.id) {
                dot.classList.add('border-primary');
            }
            
            this.presenceContainer.appendChild(dot);
        });
    }

    logActivity(message) {
        if (!this.activityList) return;

        const entry = document.createElement('div');
        entry.className = 'activity-entry small border-bottom py-1 fade-in';
        const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        entry.innerHTML = `<span class="text-muted">[${now}]</span> ${message}`;
        
        this.activityList.prepend(entry);

        // Keep only last 10
        while (this.activityList.children.length > 10) {
            this.activityList.removeChild(this.activityList.lastChild);
        }
    }

    handleRemoteReorder(soundIds) {
        const list = document.getElementById('sounds-list');
        if (!list) return;

        // Reorder DOM elements
        const items = Array.from(list.children);
        soundIds.forEach(id => {
            const item = items.find(el => el.dataset.id == id);
            if (item) {
                list.appendChild(item);
            }
        });
    }

    handleRemoteUpdate(data) {
        let message = '';
        switch(data.action) {
            case 'sound_reordered':
                message = `${data.user} reordered sounds.`;
                break;
            case 'sound_uploaded':
                message = `${data.user} uploaded "${data.data.name}".`;
                break;
            case 'sound_deleted':
                message = `${data.user} deleted a sound.`;
                break;
            case 'sound_updated':
                message = `${data.user} updated "${data.data.name}".`;
                break;
            case 'board_metadata_updated':
                message = `${data.user} updated board settings.`;
                break;
        }

        if (message) {
            ux.toast(message);
            this.logActivity(message);
            
            // In a highly dynamic app, we'd use AJAX to refresh the specific part.
            // For now, we inform the user.
            if (ux.confirm) {
                // If they are on the edit page, we might want to refresh to see changes
                // But only if they aren't currently editing a sound settings modal
                const modal = document.getElementById('soundSettingsModal');
                const isModalOpen = modal && modal.classList.contains('show');
                
                if (!isModalOpen && window.location.pathname.includes('/edit/')) {
                    // console.log("Auto-refreshing view for synchronization...");
                    // location.reload(); 
                }
            }
        }
    }

    requestLock(soundId) {
        this.socket.emit('request_lock', { board_id: this.boardId, sound_id: soundId });
    }

    releaseLock(soundId) {
        this.socket.emit('release_lock', { board_id: this.boardId, sound_id: soundId });
    }

    handleSlotLock(soundId, username) {
        const item = document.querySelector(`.list-group-item[data-id="${soundId}"]`);
        if (item) {
            item.classList.add('list-group-item-warning');
            const btnGroup = item.querySelector('.btn-group');
            if (btnGroup) {
                const lockIndicator = document.createElement('span');
                lockIndicator.className = 'badge bg-warning text-dark me-2 slot-lock-indicator';
                lockIndicator.innerHTML = `<i class="fas fa-lock"></i> ${username} editing`;
                btnGroup.prepend(lockIndicator);
                
                // Disable settings button
                const settingsBtn = btnGroup.querySelector('button[title="Settings"]');
                if (settingsBtn) settingsBtn.disabled = true;
            }
        }
    }

    handleSlotRelease(soundId) {
        const item = document.querySelector(`.list-group-item[data-id="${soundId}"]`);
        if (item) {
            item.classList.remove('list-group-item-warning');
            const indicator = item.querySelector('.slot-lock-indicator');
            if (indicator) indicator.remove();
            
            const settingsBtn = item.querySelector('button[title="Settings"]');
            if (settingsBtn) settingsBtn.disabled = false;
        }
    }
}

// Global initialization helper
window.initCollaboration = (boardId, currentUser) => {
    const manager = new CollaborationManager(boardId, currentUser);
    manager.init();
    window.collabManager = manager;
};