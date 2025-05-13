document.addEventListener('DOMContentLoaded', () => {
    // --- Contents Overlay Logic ---
    const openContentsButton = document.getElementById('openContentsButton');
    const closeContentsButton = document.getElementById('closeContentsButton');
    const contentsOverlay = document.getElementById('contentsOverlay');
    const contentsLinks = document.querySelectorAll('.contents-link');

    if (openContentsButton && contentsOverlay) {
        openContentsButton.addEventListener('click', () => {
            contentsOverlay.classList.add('active');
            document.body.style.overflow = 'hidden'; // Prevent background scroll
        });
    }

    if (closeContentsButton && contentsOverlay) {
        closeContentsButton.addEventListener('click', () => {
            contentsOverlay.classList.remove('active');
            document.body.style.overflow = '';
        });
    }

    // Close overlay when a link is clicked
    contentsLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (contentsOverlay) {
                contentsOverlay.classList.remove('active');
                document.body.style.overflow = '';
            }
            // Smooth scroll is handled by CSS 'scroll-behavior: smooth;'
            // but for JS-driven scroll to adjust for fixed header:
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                const headerOffset = document.querySelector('.main-header')?.offsetHeight || 70;
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                // Check if smooth scroll is supported, otherwise jump
                if ('scrollBehavior' in document.documentElement.style) {
                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                } else {
                    window.scrollTo(0, offsetPosition);
                }
            }
        });
    });

    // Close overlay if escape key is pressed
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && contentsOverlay && contentsOverlay.classList.contains('active')) {
            contentsOverlay.classList.remove('active');
            document.body.style.overflow = '';
        }
    });


    // --- Dynamic Year for Footer ---
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    // --- Placeholder for beyond.html ---
    // You can create a beyond.html and link to it.
    // For now, clicking "Beyond Work" will try to navigate to beyond.html
    // You'll need to create that file.
});

// Simple placeholder for beyond.html if you create it
// For now, just make an empty `beyond.html` file in the same directory,
// or modify the link in `index.html`
// Example `beyond.html`:
/*
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Beyond Work - Premkumar R</title>
    <link rel="stylesheet" href="style.css">
</head>
<body style="padding: 50px; text-align: center;">
    <h1>Beyond Work</h1>
    <p>This section is under construction. Come back soon!</p>
    <p><a href="index.html" style="font-family: var(--font-sans); color: var(--color-accent-ncert);">Back to Home</a></p>
</body>
</html>
*/