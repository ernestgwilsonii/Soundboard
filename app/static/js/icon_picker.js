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

        // Start loading icons in background immediately
        this.loadIcons();

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
        
        // Try to load from cache first
        const cached = localStorage.getItem('fa_icons_cache');
        if (cached) {
            try {
                this.icons = JSON.parse(cached);
                console.log("Loaded icons from cache");
                return; // Ready to go
            } catch (e) {
                localStorage.removeItem('fa_icons_cache');
            }
        }

        this.isLoading = true;
        try {
            const response = await fetch('https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/metadata/icons.json');
            const data = await response.json();
            
            this.icons = [];
            for (const [key, icon] of Object.entries(data)) {
                if (icon.free.includes('solid') || icon.free.includes('regular') || icon.free.includes('brands')) {
                    const style = icon.free.includes('solid') ? 'fas' : (icon.free.includes('brands') ? 'fab' : 'far');
                    this.icons.push({
                        name: icon.label,
                        class: `${style} fa-${key}`,
                        search: `${key} ${icon.label} ${icon.search?.terms?.join(' ') || ''}`.toLowerCase()
                    });
                }
            }
            
            // Save to cache for next time
            localStorage.setItem('fa_icons_cache', JSON.stringify(this.icons));
        } catch (err) {
            console.error("Failed to load icons:", err);
        } finally {
            this.isLoading = false;
        }
    }

    ensureModalExists() {
        let modalEl = document.getElementById('iconPickerModal');
        if (!modalEl) {
            const html = `
                <div class="modal fade" id="iconPickerModal" tabindex="-1" aria-hidden="true" style="z-index: 1060;">
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
                                        <input type="text" class="form-control border-start-0 ps-0" id="iconSearchInput" placeholder="Search thousands of icons..." autofocus>
                                    </div>
                                    <div id="search-stats" class="small text-muted mt-2 px-1"></div>
                                </div>
                                <div class="row row-cols-3 row-cols-sm-4 row-cols-md-6 row-cols-lg-8 g-2 mt-1" id="iconGrid">
                                    <div class="col-12 text-center p-5"><div class="spinner-border text-primary"></div><p class="mt-2">Loading icon library...</p></div>
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

    show() {
        this.modal.show();
        if (this.icons.length === 0) {
            this.loadIcons().then(() => this.renderGrid());
        } else {
            this.renderGrid();
        }
        // Focus search input
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