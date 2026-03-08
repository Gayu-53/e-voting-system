document.addEventListener('DOMContentLoaded', function () {
    // Mobile Nav Toggle
    var navToggle = document.getElementById('navToggle');
    var navMenu = document.getElementById('navMenu');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', function () {
            navMenu.classList.toggle('active');
        });

        document.addEventListener('click', function (e) {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navMenu.classList.remove('active');
            }
        });
    }

    // Auto dismiss flash messages after 8 seconds
    var flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(function (msg) {
        setTimeout(function () {
            msg.style.opacity = '0';
            msg.style.transform = 'translateY(-10px)';
            setTimeout(function () { msg.remove(); }, 300);
        }, 8000);
    });

    // Click to copy hash text
    document.querySelectorAll('.hash-text').forEach(function (elem) {
        elem.style.cursor = 'pointer';
        elem.title = 'Click to copy';
        elem.addEventListener('click', function () {
            var text = this.textContent.trim();
            if (navigator.clipboard) {
                navigator.clipboard.writeText(text);
            }
            var original = this.textContent;
            this.textContent = 'Copied!';
            this.style.color = '#00b894';
            var self = this;
            setTimeout(function () {
                self.textContent = original;
                self.style.color = '';
            }, 1500);
        });
    });

    // Block header click to expand/collapse
    document.querySelectorAll('.block-header').forEach(function (header) {
        header.addEventListener('click', function () {
            var body = this.nextElementSibling;
            if (body && body.classList.contains('block-body')) {
                if (body.style.display === 'none') {
                    body.style.display = 'block';
                } else {
                    body.style.display = 'none';
                }
            }
        });
    });

    console.log('E-Voting System Loaded - SHA-512 Blockchain');
});