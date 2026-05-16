document.addEventListener('DOMContentLoaded', function () {

    // ═══════════════════════════════════════════════════════
    // THEME TOGGLE  (moon ↔ sun, persisted in localStorage)
    // ═══════════════════════════════════════════════════════
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon   = document.getElementById('themeIcon');

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        if (themeIcon) {
            // moon icon when currently dark (click to go light)
            // sun  icon when currently light (click to go dark)
            if (theme === 'dark') {
                themeIcon.className = 'fas fa-moon';
                if (themeToggle) themeToggle.title = 'Switch to light mode';
            } else {
                themeIcon.className = 'fas fa-sun';
                if (themeToggle) themeToggle.title = 'Switch to dark mode';
            }
        }
    }

    // On load: set correct icon for whatever theme is active
    const savedTheme = localStorage.getItem('theme') || 'dark';
    applyTheme(savedTheme);

    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            const current = document.documentElement.getAttribute('data-theme') || 'dark';
            applyTheme(current === 'dark' ? 'light' : 'dark');
        });
    }

    // ═══════════════════════════════════════════════════════
    // PASSWORD EYE TOGGLE
    // ═══════════════════════════════════════════════════════
    document.querySelectorAll('.pw-eye').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const input    = document.getElementById(targetId);
            if (!input) return;

            const isHidden = input.type === 'password';
            input.type = isHidden ? 'text' : 'password';

            // Swap icon
            const icon = this.querySelector('i');
            if (icon) {
                icon.className = isHidden ? 'fas fa-eye-slash' : 'fas fa-eye';
            }

            // Keep focus on the input
            input.focus();
        });
    });

    // ═══════════════════════════════════════════════════════
    // SIDEBAR TOGGLE
    // ═══════════════════════════════════════════════════════
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar       = document.querySelector('.sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });
        document.addEventListener('click', function (e) {
            if (sidebar.classList.contains('open') &&
                !sidebar.contains(e.target) &&
                !sidebarToggle.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }

    // ═══════════════════════════════════════════════════════
    // CARD NUMBER FORMATTING  (live XXXX XXXX XXXX XXXX)
    // ═══════════════════════════════════════════════════════
    const numberInput = document.getElementById('number');
    if (numberInput) {
        numberInput.setAttribute('type', 'text');
        numberInput.setAttribute('inputmode', 'numeric');
        numberInput.setAttribute('maxlength', '19');
        numberInput.setAttribute('autocomplete', 'cc-number');
        numberInput.setAttribute('placeholder', '0000 0000 0000 0000');

        numberInput.addEventListener('input', function () {
            let val       = this.value.replace(/\D/g, '').substring(0, 16);
            this.value    = val.replace(/(.{4})/g, '$1 ').trim();
        });

        numberInput.addEventListener('keydown', function (e) {
            if ([8,9,27,13,46,37,38,39,40].includes(e.keyCode)) return;
            if ((e.ctrlKey || e.metaKey) && [65,67,86,88].includes(e.keyCode)) return;
            if (!/[0-9]/.test(e.key)) e.preventDefault();
        });

        // Strip spaces & Luhn-check before submit
        const form = numberInput.closest('form');
        if (form) {
            form.addEventListener('submit', function (e) {
                const raw = numberInput.value.replace(/\s/g, '');
                if (!luhnCheck(raw) || raw.length !== 16) {
                    e.preventDefault();
                    showCardError('Invalid card number. Please enter a valid 16-digit card number.');
                    return;
                }
                numberInput.value = raw;
            });
        }

        // Live Luhn feedback on blur
        numberInput.addEventListener('blur', function () {
            const raw = this.value.replace(/\s/g, '');
            clearCardFeedback();
            if (raw.length === 0) return;
            if (raw.length === 16 && luhnCheck(raw)) {
                setCardFeedback('✓ Valid card number', '#34d399', '#34d399', '0 0 0 3px rgba(52,211,153,0.12)');
            } else {
                showCardError('Invalid card number. Please check and re-enter.');
            }
        });

        numberInput.addEventListener('focus', clearCardFeedback);
    }

    function luhnCheck(num) {
        if (!/^\d+$/.test(num)) return false;
        let sum = 0, alt = false;
        for (let i = num.length - 1; i >= 0; i--) {
            let n = parseInt(num[i], 10);
            if (alt) { n *= 2; if (n > 9) n -= 9; }
            sum += n;
            alt = !alt;
        }
        return sum % 10 === 0;
    }

    function clearCardFeedback() {
        const el = document.querySelector('.card-number-feedback');
        if (el) el.remove();
        if (numberInput) { numberInput.style.borderColor = ''; numberInput.style.boxShadow = ''; }
    }

    function setCardFeedback(msg, textColor, borderColor, shadow) {
        clearCardFeedback();
        const el = document.createElement('div');
        el.className = 'card-number-feedback';
        el.style.cssText = `color:${textColor};font-family:var(--font-mono);font-size:0.75rem;margin-top:6px;letter-spacing:0.04em;`;
        el.textContent = msg;
        numberInput.parentNode.appendChild(el);
        numberInput.style.borderColor = borderColor;
        numberInput.style.boxShadow   = shadow;
    }

    function showCardError(msg) {
        setCardFeedback('✗ ' + msg, '#f87171', '#f87171', '0 0 0 3px rgba(248,113,113,0.15)');
        setTimeout(clearCardFeedback, 4000);
    }

    // ═══════════════════════════════════════════════════════
    // DELETE CARD  (AJAX with fade-out)
    // ═══════════════════════════════════════════════════════
    document.querySelectorAll('.delete-card').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const cardId = this.getAttribute('data-card-id');
            if (!confirm('Delete this card permanently?')) return;
            fetch(`/delete_card/${cardId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    const col = this.closest('.col');
                    if (col) {
                        col.style.transition = 'opacity 0.3s, transform 0.3s';
                        col.style.opacity    = '0';
                        col.style.transform  = 'scale(0.95)';
                        setTimeout(() => col.remove(), 300);
                    } else { location.reload(); }
                } else { alert('Error deleting card.'); }
            });
        });
    });

    // ═══════════════════════════════════════════════════════
    // CHECK CARD VALIDITY  (client-side expiry check)
    // ═══════════════════════════════════════════════════════
    document.querySelectorAll('.check-validity-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const expiry    = this.getAttribute('data-expiry');
            const resultDiv = this.closest('.card-body').querySelector('.validity-result');
            if (!expiry || expiry.length < 6) {
                resultDiv.textContent  = '✗ Invalid expiry format';
                resultDiv.style.color  = '#f87171';
                return;
            }
            const [mmStr, yyyyStr] = expiry.split('/');
            const mm   = parseInt(mmStr,  10);
            let   yyyy = parseInt(yyyyStr, 10);
            if (isNaN(mm) || isNaN(yyyy) || mm < 1 || mm > 12) {
                resultDiv.textContent = '✗ Invalid expiry date';
                resultDiv.style.color = '#f87171';
                return;
            }
            if (yyyy < 100) yyyy += 2000;
            const expiryDate = new Date(yyyy, mm, 0);
            if (expiryDate >= new Date()) {
                resultDiv.textContent = '✓ Card is valid';
                resultDiv.style.color = '#34d399';
            } else {
                resultDiv.textContent = '✗ Card has expired';
                resultDiv.style.color = '#f87171';
            }
        });
    });

    // ═══════════════════════════════════════════════════════
    // LANDING PAGE TABS
    // ═══════════════════════════════════════════════════════
    document.querySelectorAll('.tab-button').forEach(function (tab) {
        tab.addEventListener('click', function () {
            const target = this.dataset.tab;
            document.querySelectorAll('.tab-button').forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            document.querySelectorAll('.tab-panel').forEach(p => {
                p.classList.toggle('active', p.id === target);
            });
        });
    });

    // ═══════════════════════════════════════════════════════
    // PASSWORD STRENGTH BAR  (register tab)
    // ═══════════════════════════════════════════════════════
    const strengthFill = document.getElementById('pwStrengthFill');
    const regPw        = document.getElementById('reg_password');
    if (strengthFill && regPw) {
        regPw.addEventListener('input', function () {
            const v = this.value;
            let score = 0;
            if (v.length >= 8)                           score++;
            if (/[A-Z]/.test(v))                         score++;
            if (/[a-z]/.test(v))                         score++;
            if (/\d/.test(v))                            score++;
            if (/[!@#$%^&*(),.?":{}|<>]/.test(v))       score++;
            const colours = ['#f87171','#f87171','#fbbf24','#34d399','#34d399'];
            strengthFill.style.width      = (score * 20) + '%';
            strengthFill.style.background = colours[score - 1] || '#f87171';
        });
    }

});