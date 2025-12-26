/**
 * Reusable Icon Picker for Soundboard Website
 */
class IconPicker {
    constructor(targetInputId, previewIconId = null) {
        this.targetInput = document.getElementById(targetInputId);
        this.previewIcon = previewIconId ? document.getElementById(previewIconId) : null;
        this.modal = null;
        this.icons = [];
        this.init();
    }

    async init() {
        if (!this.targetInput) return;

        // Load icons if not already loaded
        if (this.icons.length === 0) {
            try {
                const response = await fetch('/static/icons.json');
                this.icons = await response.json();
            } catch (err) {
                console.error("Failed to load icons:", err);
                return;
            }
        }

        // Create modal if it doesn't exist
        this.ensureModalExists();

        // Add click listener to target input or a button
        this.targetInput.addEventListener('click', () => this.show());
        
        // If there's a button next to it, maybe trigger on that too
        const btn = this.targetInput.nextElementSibling;
        if (btn && btn.classList.contains('icon-picker-trigger')) {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.show();
            });
        }
    }

    ensureModalExists() {
        let modalEl = document.getElementById('iconPickerModal');
        if (!modalEl) {
            const html = `
                <div class="modal fade" id="iconPickerModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog modal-lg">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Select an Icon</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="mb-3">
                                    <input type="text" class="form-control" id="iconSearchInput" placeholder="Search icons...">
                                </div>
                                <div class="row row-cols-4 row-cols-md-6 g-3" id="iconGrid" style="max-height: 400px; overflow-y: auto;">
                                    <!-- Icons will be rendered here -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', html);
            modalEl = document.getElementById('iconPickerModal');
            
            // Add search listener
            document.getElementById('iconSearchInput').addEventListener('input', (e) => {
                this.renderGrid(e.target.value);
            });
        }
        this.modal = new bootstrap.Modal(modalEl);
    }

    renderGrid(query = '') {
        const grid = document.getElementById('iconGrid');
        grid.innerHTML = '';
        
        const filtered = this.icons.filter(icon => 
            icon.name.toLowerCase().includes(query.toLowerCase()) || 
            icon.class.toLowerCase().includes(query.toLowerCase())
        );

        filtered.forEach(icon => {
            const col = document.createElement('div');
            col.className = 'col text-center';
            col.innerHTML = `
                <div class="p-2 border rounded icon-option" style="cursor: pointer;" data-class="${icon.class}">
                    <i class="${icon.class} fa-2x mb-1"></i>
                    <div class="tiny text-muted" style="font-size: 0.7rem;">${icon.name}</div>
                </div>
            `;
            col.querySelector('.icon-option').addEventListener('click', () => {
                this.selectIcon(icon.class);
            });
            grid.appendChild(col);
        });
    }

    show() {
        this.renderGrid();
        this.modal.show();
    }

    selectIcon(iconClass) {
        this.targetInput.value = iconClass;
        if (this.previewIcon) {
            this.previewIcon.className = iconClass;
        }
        // Trigger change event for form handling
        this.targetInput.dispatchEvent(new Event('change'));
        this.modal.hide();
    }
}

// Auto-initialize if elements exist with specific data attributes
document.addEventListener('DOMContentLoaded', () => {
    const pickers = document.querySelectorAll('[data-toggle="icon-picker"]');
    pickers.forEach(input => {
        const previewId = input.dataset.preview;
        new IconPicker(input.id, previewId);
    });
});
