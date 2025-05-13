document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;

    // --- Loading Animation ---
    const loadingOverlay = document.querySelector('.loading-overlay');
    if (loadingOverlay) {
        setTimeout(() => {
            loadingOverlay.style.opacity = '0';
            loadingOverlay.style.visibility = 'hidden';
            body.style.overflowY = 'auto'; // Allow scroll after load
        }, 2200); // Adjust timing based on animation length
    } else {
        body.style.overflowY = 'auto';
    }


    // --- Custom Cursor ---
    const cursor = document.querySelector('.custom-cursor');
    const linksAndButtons = document.querySelectorAll('a, button');

    if (cursor) { // Check if cursor element exists
        document.addEventListener('mousemove', e => {
            cursor.style.left = e.clientX + 'px';
            cursor.style.top = e.clientY + 'px';
        });

        linksAndButtons.forEach(el => {
            el.addEventListener('mouseenter', () => {
                cursor.style.width = '40px';
                cursor.style.height = '40px';
                // cursor.style.backgroundColor = 'var(--color-white)';
                // cursor.style.borderColor = 'var(--color-black)'; // Example hover effect
            });
            el.addEventListener('mouseleave', () => {
                cursor.style.width = '20px';
                cursor.style.height = '20px';
                // cursor.style.backgroundColor = 'transparent';
                // cursor.style.borderColor = 'var(--color-white)';
            });
        });
    }


    // --- Menu Toggle ---
    const menuToggle = document.querySelector('.menu-toggle');
    const menuClose = document.querySelector('.menu-close');
    const fullscreenMenu = document.querySelector('.fullscreen-menu');
    const menuLinks = document.querySelectorAll('.fullscreen-menu .menu-link');

    if (menuToggle && fullscreenMenu && menuClose) {
        menuToggle.addEventListener('click', () => {
            fullscreenMenu.classList.toggle('active');
            menuToggle.classList.toggle('active');
            body.style.overflowY = fullscreenMenu.classList.contains('active') ? 'hidden' : 'auto';
        });
        menuClose.addEventListener('click', () => {
            fullscreenMenu.classList.remove('active');
            menuToggle.classList.remove('active');
            body.style.overflowY = 'auto';
        });
        menuLinks.forEach(link => {
            link.addEventListener('click', () => {
                fullscreenMenu.classList.remove('active');
                menuToggle.classList.remove('active');
                body.style.overflowY = 'auto';
            });
        });
    }


    // --- Scroll-triggered Animations ---
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    const observerOptions = {
        root: null, // relative to document viewport
        rootMargin: '0px',
        threshold: 0.2 // 20% of item is visible
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                // observer.unobserve(entry.target); // Optional: stop observing after animation
            } else {
                // Optional: remove class to re-animate if scrolling up and then down again
                // entry.target.classList.remove('is-visible');
            }
        });
    }, observerOptions);

    animatedElements.forEach(el => {
        observer.observe(el);
    });
// --- Strategic Insight Simulator Logic ---
const industryButtons = document.querySelectorAll('.industry-btn');
const insightsArea = document.getElementById('insights-area');

const insightsData = {
    tech: {
        title: "Key Questions for AI EdTech:",
        points: [
            "How can personalized learning paths be dynamically adjusted by AI based on real-time student performance and engagement?",
            "What ethical frameworks are needed to govern AI-driven content generation and assessment in education?",
            "How can AI tools bridge the gap between theoretical knowledge and practical skill application for vocational training?"
        ]
    },
    fashion: {
        title: "Strategic Focus for Sustainable Fashion:",
        points: [
            "What innovative materials and production processes can drastically reduce the environmental footprint of apparel?",
            "How can circular economy models (e.g., rental, resale, recycling) be scaled effectively and profitably?",
            "How can technology enhance transparency and traceability throughout the fashion supply chain to build consumer trust?"
        ]
    },
    mobility: {
        title: "Exploring Urban Mobility Solutions:",
        points: [
            "How can integrated multi-modal transport platforms optimize for convenience, cost, and sustainability?",
            "What role will autonomous vehicles play in reshaping public vs. private transport in dense urban areas?",
            "How can data analytics and AI be used to predict and alleviate traffic congestion and improve infrastructure planning?"
        ]
    }
};

if (industryButtons.length > 0 && insightsArea) {
    industryButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            industryButtons.forEach(btn => btn.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');

            const selectedIndustry = this.dataset.industry;
            const data = insightsData[selectedIndustry];

            insightsArea.innerHTML = ''; // Clear previous insights

            if (data) {
                const titleEl = document.createElement('h4');
                titleEl.textContent = data.title;
                insightsArea.appendChild(titleEl);

                const ul = document.createElement('ul');
                data.points.forEach(point => {
                    const li = document.createElement('li');
                    li.textContent = point;
                    ul.appendChild(li);
                });
                insightsArea.appendChild(ul);
            } else {
                 insightsArea.innerHTML = '<p class="placeholder-insight"><em>No insights available for this selection.</em></p>';
            }
        });
    });
}
// Make sure this is the last closing curly brace for the DOMContentLoaded listener
});