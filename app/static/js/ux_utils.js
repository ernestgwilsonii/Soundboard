/**
 * UX Utilities - Global Dialog System
 * Replaces native alert() and confirm() with modern SweetAlert2 dialogs.
 */

window.ux = {
    /**
     * Display a modern alert dialog.
     * @param {string} title 
     * @param {string} text 
     * @param {string} icon - 'success', 'error', 'warning', 'info', 'question'
     */
    alert: function(title, text = '', icon = 'info') {
        return Swal.fire({
            title: title,
            text: text,
            icon: icon,
            confirmButtonColor: '#0d6efd'
        });
    },

    /**
     * Display a modern confirmation dialog.
     * @param {string} title 
     * @param {string} text 
     * @param {string} confirmText 
     * @param {string} icon 
     * @returns {Promise<boolean>}
     */
    confirm: async function(title, text = '', confirmText = 'Yes, proceed', icon = 'warning') {
        const result = await Swal.fire({
            title: title,
            text: text,
            icon: icon,
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: confirmText
        });
        return result.isConfirmed;
    },

    /**
     * Success toast (top right)
     */
    toast: function(title, icon = 'success') {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: 3000,
            timerProgressBar: true
        });
        Toast.fire({
            icon: icon,
            title: title
        });
    }
};

// Optional: Override global window.alert if we want to catch legacy calls
// window.alert = (msg) => ux.alert(msg);
