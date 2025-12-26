/**
 * Dynamic Icon Picker for Soundboard Website
 * Pulls the full FontAwesome 6 Free library dynamically.
 */
class IconPicker {
    constructor(targetInputId, previewIconId = null) {
        this.targetInput = document.getElementById(targetInputId);
        this.previewIcon = previewIconId ? document.getElementById(previewIconId) : null;
        this.modal = null;
        this.icons = [];
        this.categories = {};
        this.isLoading = false;
        this.init();
    }

    async init() {
        if (!this.targetInput) return;

        // Create modal structure early
        this.ensureModalExists();

        // Add click listener to target input
        this.targetInput.addEventListener('click', () => this.show());
        
        const btn = this.targetInput.parentElement.querySelector('.icon-picker-trigger');
        if (btn) {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.show();
            });
        }
    }

    async loadIcons() {
        if (this.icons.length > 0 || this.isLoading) return;
        
        this.isLoading = true;
        const grid = document.getElementById('iconGrid');
        grid.innerHTML = '<div class="col-12 text-center p-5"><div class="spinner-border text-primary"></div><p class="mt-2">Loading full icon library...</p></div>';

        try {
            // Fetching a comprehensive metadata file for FA6 Free
            // Using a reliable CDN source for the icons metadata
            const response = await fetch('https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/metadata/icons.json');
            const data = await response.json();
            
            this.icons = [];
            for (const [key, icon] of Object.entries(data)) {
                // Only include icons available in the Free set
                if (icon.free.includes('solid') || icon.free.includes('regular') || icon.free.includes('brands')) {
                    const style = icon.free.includes('solid') ? 'fas' : (icon.free.includes('brands') ? 'fab' : 'far');
                    this.icons.push({
                        name: icon.label,
                        class: `${style} fa-${key}`,
                        search: `${key} ${icon.label} ${icon.search?.terms?.join(' ') || ''}`.toLowerCase()
                    });
                }
            }
            
            this.renderGrid();
        } catch (err) {
            console.error("Failed to load icons:", err);
            grid.innerHTML = '<div class="col-12 text-center text-danger p-5">Failed to load icons. Please check your connection.</div>';
        } finally {
            this.isLoading = false;
        }
    }

    ensureModalExists() {
        let modalEl = document.getElementById('iconPickerModal');
        if (!modalEl) {
            const html = `
                <div class="modal fade" id="iconPickerModal" tabindex="-1" aria-hidden="true">
                    <div class="modal-dialog modal-xl modal-dialog-scrollable">
                        <div class="modal-content">
                            <div class="modal-header bg-light">
                                <h5 class="modal-title"><i class="fas fa-icons me-2"></i>Select an Icon</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="sticky-top bg-white pb-3" style="top: -1rem; z-index: 1020;">
                                    <div class="input-group shadow-sm">
                                        <span class="input-group-text bg-white border-end-0"><i class="fas fa-search text-muted"></i></span>
                                        <input type="text" class="form-control border-start-0 ps-0" id="iconSearchInput" placeholder="Search thousands of icons (e.g. music, dog, user, heart)..." autofocus>
                                    </div>
                                    <div id="search-stats" class="small text-muted mt-2 px-1"></div>
                                </div>
                                <div class="row row-cols-3 row-cols-sm-4 row-cols-md-6 row-cols-lg-8 g-2 mt-1" id="iconGrid">
                                    <!-- Icons will be rendered here -->
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', html);
            modalEl = document.getElementById('iconPickerModal');
            
            document.getElementById('iconSearchInput').addEventListener('input', (e) => {
                this.debouncedRender(e.target.value);
            });
        }
        this.modal = new bootstrap.Modal(modalEl);
    }

    debouncedRender(query) {
        if (this.timer) clearTimeout(this.debouncedTimer);
        this.debouncedTimer = setTimeout(() => this.renderGrid(query), 200);
    }

    renderGrid(query = '') {
        const grid = document.getElementById('iconGrid');
        const stats = document.getElementById('search-stats');
        
        if (!grid) return;
        
        grid.innerHTML = '';
        const lowerQuery = query.toLowerCase().trim();
        
        const filtered = lowerQuery === '' 
            ? this.icons.slice(0, 300) // Show first 300 icons by default
            : this.icons.filter(icon => icon.search.includes(lowerQuery));

        stats.textContent = lowerQuery === '' 
            ? `Showing popular icons. Search to see all ${this.icons.length} options.` 
            : `Found ${filtered.length} matches.`;

        if (filtered.length === 0) {
            grid.innerHTML = '<div class="col-12 text-center p-5 text-muted">No icons match your search.</div>';
            return;
        }

        const fragment = document.createDocumentFragment();
        filtered.forEach(icon => {
            const col = document.createElement('div');
            col.className = 'col text-center';
            col.innerHTML = `
                <div class="p-3 border rounded icon-option h-100 d-flex flex-column align-items-center justify-content-center bg-white" 
                     style="cursor: pointer; transition: all 0.2s;" 
                     data-class="${icon.class}" 
                     title="${icon.name}">
                    <i class="${icon.class} fa-2x mb-2 text-dark"></i>
                    <div class="text-truncate w-100" style="font-size: 0.65rem; color: #666;">${icon.name}</div>
                </div>
            `;
            
            const option = col.querySelector('.icon-option');
            option.addEventListener('mouseenter', () => option.classList.add('bg-light', 'border-primary', 'shadow-sm'));
            option.addEventListener('mouseleave', () => option.classList.remove('bg-light', 'border-primary', 'shadow-sm'));
            option.addEventListener('click', () => this.selectIcon(icon.class));
            
            fragment.appendChild(col);
        });
        
        grid.appendChild(fragment);
    }

    show() {
        this.modal.show();
        this.loadIcons();
        // Focus search input after modal opens
        setTimeout(() => {
            document.getElementById('iconSearchInput').focus();
        }, 500);
    }

    selectIcon(iconClass) {
        this.targetInput.value = iconClass;
        if (this.previewIcon) {
            this.previewIcon.className = iconClass;
        }
        this.targetInput.dispatchEvent(new Event('change'));
        this.modal.hide();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const pickers = document.querySelectorAll('[data-toggle="icon-picker"]');
    pickers.forEach(input => {
        const previewId = input.dataset.preview;
        new IconPicker(input.id, previewId);
    });
});