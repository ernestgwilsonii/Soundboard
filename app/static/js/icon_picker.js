/**
 * Dynamic Icon Picker for Soundboard Website
 * Pulls the full FontAwesome 6 Free library dynamically.
 */

// Shared global state to avoid redundant fetches across multiple instances
const IconLibrary = {
    icons: [],
    isLoading: false,
    loadPromise: null,

    async fetchIcons() {
        if (this.icons.length > 0) return this.icons;
        if (this.loadPromise) return this.loadPromise;

        this.loadPromise = (async () => {
            // Try cache first
            const cached = localStorage.getItem('fa_icons_cache_v2');
            if (cached) {
                try {
                    this.icons = JSON.parse(cached);
                    console.log("Loaded icons from cache");
                    return this.icons;
                } catch (e) {
                    localStorage.removeItem('fa_icons_cache_v2');
                }
            }

            this.isLoading = true;
            try {
                // Fetch official FA6 metadata
                const response = await fetch('https://raw.githubusercontent.com/FortAwesome/Font-Awesome/6.x/metadata/icons.json');
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                
                const processed = [];
                for (const [key, icon] of Object.entries(data)) {
                    if (icon.free && (icon.free.includes('solid') || icon.free.includes('regular') || icon.free.includes('brands'))) {
                        const style = icon.free.includes('solid') ? 'fas' : (icon.free.includes('brands') ? 'fab' : 'far');
                        processed.push({
                            name: icon.label,
                            class: `${style} fa-${key}`,
                            search: `${key} ${icon.label} ${icon.search?.terms?.join(' ') || ''}`.toLowerCase()
                        });
                    }
                }
                
                this.icons = processed;
                localStorage.setItem('fa_icons_cache_v2', JSON.stringify(this.icons));
                return this.icons;
            } catch (err) {
                console.error("Failed to load icons from GitHub:", err);
                throw err;
            } finally {
                this.isLoading = false;
            }
        })();

        return this.loadPromise;
    }
};

class IconPicker {
    constructor(targetInputId, previewIconId = null) {
        this.targetInput = document.getElementById(targetInputId);
        this.previewIcon = previewIconId ? document.getElementById(previewIconId) : null;
        this.modal = null;
        this.debouncedTimer = null;
        this.init();
    }

    init() {
        if (!this.targetInput) return;

        this.ensureModalExists();

        // Start loading in background immediately
        IconLibrary.fetchIcons().catch(err => {
            const grid = document.getElementById('iconGrid');
            if (grid) grid.innerHTML = `<div class="col-12 text-center text-danger p-5">Error: ${err.message}</div>`;
        });

        // Add trigger listeners
        this.targetInput.addEventListener('click', () => this.show());
        
        const parent = this.targetInput.parentElement;
        const btn = parent ? parent.querySelector('.icon-picker-trigger') : null;
        if (btn) {
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
                <div class="modal fade" id="iconPickerModal" tabindex="-1" aria-hidden="true" style="z-index: 1070;">
                    <div class="modal-dialog modal-xl modal-dialog-scrollable">
                        <div class="modal-content">
                            <div class="modal-header bg-light">
                                <h5 class="modal-title"><i class="fas fa-icons me-2 text-primary"></i>Select an Icon</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body">
                                <div class="sticky-top bg-white pb-3" style="top: -1rem; z-index: 1020;">
                                    <div class="input-group shadow-sm">
                                        <span class="input-group-text bg-white border-end-0"><i class="fas fa-search text-muted"></i></span>
                                        <input type="text" class="form-control border-start-0 ps-0" id="iconSearchInput" placeholder="Search icons (e.g. music, dog, brand)..." autofocus>
                                    </div>
                                    <div id="search-stats" class="small text-muted mt-2 px-1"></div>
                                </div>
                                <div class="row row-cols-3 row-cols-sm-4 row-cols-md-6 row-cols-lg-8 g-2 mt-1" id="iconGrid">
                                    <div class="col-12 text-center p-5">
                                        <div class="spinner-border text-primary"></div>
                                        <p class="mt-2 text-muted">Loading library...</p>
                                    </div>
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
        if (this.debouncedTimer) clearTimeout(this.debouncedTimer);
        this.debouncedTimer = setTimeout(() => this.renderGrid(query), 150);
    }

    async renderGrid(query = '') {
        const grid = document.getElementById('iconGrid');
        const stats = document.getElementById('search-stats');
        if (!grid) return;

        // Ensure data is ready
        let icons = [];
        try {
            icons = await IconLibrary.fetchIcons();
        } catch (err) {
            grid.innerHTML = `<div class="col-12 text-center text-danger p-5">Failed to load icons: ${err.message}</div>`;
            return;
        }

        grid.innerHTML = '';
        const lowerQuery = query.toLowerCase().trim();
        
        const filtered = lowerQuery === '' 
            ? icons.slice(0, 200) // Initial set
            : icons.filter(icon => icon.search.includes(lowerQuery));

        stats.textContent = lowerQuery === '' 
            ? `Displaying popular icons. Search to see all ${icons.length} options.` 
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
                     style="cursor: pointer; transition: all 0.2s; min-height: 90px; border-width: 2px !important;" 
                     data-class="${icon.class}" 
                     title="${icon.name}">
                    <div class="icon-wrapper d-flex align-items-center justify-content-center mb-2" style="height: 40px;">
                        <i class="${icon.class} fa-2x text-dark"></i>
                    </div>
                    <div class="text-truncate w-100 px-1" style="font-size: 0.7rem; color: #555; font-weight: 500;">${icon.name}</div>
                </div>
            `;
            
            const option = col.querySelector('.icon-option');
            option.addEventListener('mouseenter', () => {
                option.style.borderColor = 'var(--bs-primary)';
                option.style.backgroundColor = '#f8f9ff';
                option.querySelector('i').classList.add('text-primary');
            });
            option.addEventListener('mouseleave', () => {
                option.style.borderColor = '';
                option.style.backgroundColor = '';
                option.querySelector('i').classList.remove('text-primary');
            });
            option.addEventListener('click', () => this.selectIcon(icon.class));
            fragment.appendChild(col);
        });
        
        grid.appendChild(fragment);
    }

    async show() {
        this.modal.show();
        await this.renderGrid(document.getElementById('iconSearchInput').value);
        setTimeout(() => {
            document.getElementById('iconSearchInput').focus();
        }, 300);
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

// Global initialization
document.addEventListener('DOMContentLoaded', () => {
    // Delegation or individual attachment
    const initPickers = () => {
        const pickers = document.querySelectorAll('[data-toggle="icon-picker"]');
        pickers.forEach(input => {
            if (!input.dataset.pickerInitialized) {
                const previewId = input.dataset.preview;
                new IconPicker(input.id, previewId);
                input.dataset.pickerInitialized = "true";
            }
        });
    };

    initPickers();
    
    // If we add sounds dynamically (not yet implemented but good for future), we'd call initPickers again
});
