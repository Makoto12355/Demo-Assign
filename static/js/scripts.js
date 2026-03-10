/* Dynamic back button with smooth transition */
document.addEventListener('DOMContentLoaded', function() {
    const backButton = document.querySelector('.btn-back');
    
    if (backButton) {
        backButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Add fade-out effect
            document.body.style.opacity = '0';
            document.body.style.transition = 'opacity 0.5s ease-out';
            
            // Navigate after animation
            setTimeout(function() {
                window.location.href = backButton.href;
            }, 300);
        });
    }
});

/* Add smooth fade-in effect when page loads */
window.addEventListener('load', function() {
    document.body.style.opacity = '0';
    document.body.style.transition = 'opacity 0.5s ease-in';
    
    setTimeout(function() {
        document.body.style.opacity = '1';
    }, 100);
});

/* Smooth scroll behavior */
document.documentElement.style.scrollBehavior = 'smooth';
