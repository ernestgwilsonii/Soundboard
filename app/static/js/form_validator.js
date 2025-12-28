/**
 * Real-Time Form Validator for Soundboard Website
 */
class FormValidator {
    constructor(formId) {
        this.form = document.getElementById(formId);
        if (!this.form) return;
        this.init();
    }

    init() {
        // Find relevant fields
        this.usernameInput = this.form.querySelector('input[name="username"]');
        this.emailInput = this.form.querySelector('input[name="email"]');
        this.passwordInput = this.form.querySelector('input[name="password"]');
        this.boardNameInput = this.form.querySelector('input[name="name"]');
        
        if (this.usernameInput) {
            this.usernameInput.addEventListener('input', (e) => this.checkAvailability('username', e.target.value));
        }
        if (this.emailInput) {
            this.emailInput.addEventListener('input', (e) => this.checkAvailability('email', e.target.value));
        }
        if (this.passwordInput) {
            this.setupPasswordMeter();
        }
        if (this.boardNameInput) {
            this.boardNameInput.addEventListener('input', (e) => this.checkBoardAvailability(e.target.value));
        }
    }

    async checkBoardAvailability(value) {
        if (!value || value.length < 2) return;
        try {
            const response = await fetch(`/soundboard/check-name?name=${encodeURIComponent(value)}`);
            const data = await response.json();
            this.setFieldStatus(this.boardNameInput, data.available);
        } catch (err) {
            console.error("Board name check failed:", err);
        }
    }

    async checkAvailability(field, value) {
        if (!value || value.length < 3) return;

        const parent = this.usernameInput.parentElement;
        try {
            const response = await fetch(`/auth/check-availability?${field}=${encodeURIComponent(value)}`);
            const data = await response.json();
            
            this.setFieldStatus(field === 'username' ? this.usernameInput : this.emailInput, data.available);
        } catch (err) {
            console.error("Availability check failed:", err);
        }
    }

    setFieldStatus(input, isAvailable) {
        if (isAvailable) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
        }
    }

    setupPasswordMeter() {
        const meterContainer = document.createElement('div');
        meterContainer.className = 'progress mt-2';
        meterContainer.style.height = '5px';
        meterContainer.innerHTML = '<div id="password-strength-bar" class="progress-bar" role="progressbar" style="width: 0%"></div>';
        
        const text = document.createElement('div');
        text.id = 'password-strength-text';
        text.className = 'small text-muted mt-1';
        text.textContent = 'Password strength';

        this.passwordInput.parentElement.appendChild(meterContainer);
        this.passwordInput.parentElement.appendChild(text);

        this.passwordInput.addEventListener('input', (e) => {
            const strength = this.calculatePasswordStrength(e.target.value);
            const bar = document.getElementById('password-strength-bar');
            const label = document.getElementById('password-strength-text');
            
            const levels = [
                { width: '25%', color: 'bg-danger', text: 'Weak' },
                { width: '50%', color: 'bg-warning', text: 'Fair' },
                { width: '75%', color: 'bg-info', text: 'Good' },
                { width: '100%', color: 'bg-success', text: 'Strong' }
            ];

            if (e.target.value.length === 0) {
                bar.style.width = '0%';
                label.textContent = 'Password strength';
                return;
            }

            const level = levels[Math.min(strength, 3)];
            bar.style.width = level.width;
            bar.className = 'progress-bar ' + level.color;
            label.textContent = 'Strength: ' + level.text;
        });
    }

    calculatePasswordStrength(password) {
        let score = 0;
        if (password.length > 6) score++;
        if (password.length > 10) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/[0-9]/.test(password)) score++;
        if (/[^A-Za-z0-9]/.test(password)) score++;
        return Math.floor(score / 1.5); // Normalize to 0-3
    }
}

document.addEventListener('DOMContentLoaded', () => {
    // Initialize on Signup form
    new FormValidator('signup-form');
});
