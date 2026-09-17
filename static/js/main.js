// ------------------------------------------------------------------ //
// Video Modal                                                         //
// ------------------------------------------------------------------ //

// YouTube video ID - CHANGE THIS to use your own video
// Use only the video ID (the part after 'v=' in the URL)
// Example: For https://www.youtube.com/watch?v=VIDEO_ID, use 'VIDEO_ID'
const VIDEO_ID = '-Lt-ntUDj-g';

// Build YouTube embed URL with autoplay
const getYouTubeEmbedUrl = (videoId) => {
    return `https://www.youtube.com/embed/${videoId}?autoplay=1&rel=0`;
};

// Initialize video modal functionality
document.addEventListener('DOMContentLoaded', function() {
    const openBtn = document.getElementById('openVideoModal');
    const modal = document.getElementById('videoModal');
    const closeBtn = modal.querySelector('.video-modal-close');
    const backdrop = modal.querySelector('.video-modal-backdrop');
    const videoFrame = document.getElementById('videoFrame');

    // Open modal
    const openModal = () => {
        // Set video source with autoplay
        videoFrame.src = getYouTubeEmbedUrl(VIDEO_ID);

        // Show modal
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');

        // Prevent body scroll
        document.body.classList.add('modal-open');

        // Focus close button for accessibility
        closeBtn.focus();
    };

    // Close modal
    const closeModal = () => {
        // Stop video by removing src
        videoFrame.src = '';

        // Hide modal
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');

        // Restore body scroll
        document.body.classList.remove('modal-open');

        // Return focus to open button
        openBtn.focus();
    };

    // Event listeners
    if (openBtn) {
        openBtn.addEventListener('click', openModal);
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    // Close when clicking backdrop
    if (backdrop) {
        backdrop.addEventListener('click', closeModal);
    }

    // Close on Escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.classList.contains('is-open')) {
            closeModal();
        }
    });
});

