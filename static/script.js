document.addEventListener('DOMContentLoaded', function() {
    // Persistent Dark Mode Toggle
    const darkModeToggle = document.getElementById('darkModeToggle');
    if (darkModeToggle) {
        // Load dark mode state from localStorage
        const isDarkMode = localStorage.getItem('darkMode') === 'true';
        if (isDarkMode) {
            document.body.classList.add('dark-mode');
            darkModeToggle.querySelector('i').classList.remove('fa-moon');
            darkModeToggle.querySelector('i').classList.add('fa-sun');
        }

        darkModeToggle.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');
            const icon = this.querySelector('i');
            icon.classList.toggle('fa-moon');
            icon.classList.toggle('fa-sun');
            // Save state to localStorage
            const isNowDark = document.body.classList.contains('dark-mode');
            localStorage.setItem('darkMode', isNowDark);
        });
    }

    // Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
    }

    // Delete Card Confirmation & AJAX delete
    document.querySelectorAll('.delete-card').forEach(button => {
        button.addEventListener('click', function() {
            const cardId = this.getAttribute('data-card-id');
            if (confirm('Are you sure you want to delete this card?')) {
                fetch(`/delete_card/${cardId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error deleting card.');
                    }
                });
            }
        });
    });

    // Check Validity Button Logic
    document.querySelectorAll('.check-validity-btn').forEach(button => {
        button.addEventListener('click', () => {
            const cardExpiry = button.getAttribute('data-expiry');
            const resultDiv = button.closest('.card-body').querySelector('.validity-result');

            if (!cardExpiry || cardExpiry.length !== 7) {
                resultDiv.textContent = 'Invalid expiry format';
                resultDiv.style.color = '#dc3545';
                return;
            }

            const [mmStr, yyyyStr] = cardExpiry.split('/');
            const mm = parseInt(mmStr, 10);
            let yyyy = parseInt(yyyyStr, 10);
            if (isNaN(mm) || isNaN(yyyy) || mm < 1 || mm > 12) {
                resultDiv.textContent = 'Invalid expiry date';
                resultDiv.style.color = '#dc3545';
                return;
            }
            if (yyyy < 100) {
                yyyy += 2000;
            }
            const today = new Date();
            const expiryDate = new Date(yyyy, mm, 0);
            if (expiryDate >= today) {
                resultDiv.textContent = '✅ Card is valid';
                resultDiv.style.color = '#198754';
            } else {
                resultDiv.textContent = '❌ Invalid Card! Card has expired';
                resultDiv.style.color = '#dc3545';
            }
        });
    });

    // Developer Icon Click (on login page)
    const devIcon = document.getElementById('devIcon');
    if (devIcon) {
        devIcon.addEventListener('click', function() {
            window.location.href = '/dev_dashboard';
        });
    }
});
