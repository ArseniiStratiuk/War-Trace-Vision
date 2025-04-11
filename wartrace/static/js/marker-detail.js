/**
 * Marker Detail JavaScript
 * Handles interactions on the marker detail page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize mini map
    const lat = parseFloat(document.getElementById('marker-coordinates').innerText.split(',')[0]);
    const lng = parseFloat(document.getElementById('marker-coordinates').innerText.split(',')[1]);
    
    const miniMap = L.map('mini-map', {
        zoomControl: false,
        attributionControl: false
    }).setView([lat, lng], 12);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19
    }).addTo(miniMap);
    
    // Add marker to mini map
    L.marker([lat, lng]).addTo(miniMap);
    
    // Make mini-map non-interactive
    miniMap.dragging.disable();
    miniMap.touchZoom.disable();
    miniMap.doubleClickZoom.disable();
    miniMap.scrollWheelZoom.disable();
    
    // Image gallery modal
    const modal = document.getElementById('image-modal');
    const modalImg = document.getElementById('modal-image');
    const modalCaption = document.getElementById('modal-caption');
    const closeBtn = document.getElementsByClassName('close')[0];
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');
    
    // Get all gallery images
    const galleryImages = document.querySelectorAll('.media-item .image-container img');
    let currentImageIndex = 0;
    const imageUrls = [];
    const imageCaptions = [];
    
    galleryImages.forEach((img, index) => {
        imageUrls.push(img.src);
        imageCaptions.push(img.alt || '');
        
        img.addEventListener('click', function() {
            currentImageIndex = index;
            openModal(this.src, this.alt);
        });
    });
    
    function openModal(src, caption) {
        modal.style.display = 'block';
        modalImg.src = src;
        modalCaption.innerHTML = caption;
        
        // Show/hide navigation buttons
        prevBtn.style.visibility = currentImageIndex > 0 ? 'visible' : 'hidden';
        nextBtn.style.visibility = currentImageIndex < imageUrls.length - 1 ? 'visible' : 'hidden';
    }
    
    // Close modal
    closeBtn.onclick = function() {
        modal.style.display = 'none';
    };
    
    // Navigation
    prevBtn.onclick = function() {
        if (currentImageIndex > 0) {
            currentImageIndex--;
            openModal(imageUrls[currentImageIndex], imageCaptions[currentImageIndex]);
        }
    };
    
    nextBtn.onclick = function() {
        if (currentImageIndex < imageUrls.length - 1) {
            currentImageIndex++;
            openModal(imageUrls[currentImageIndex], imageCaptions[currentImageIndex]);
        }
    };
    
    // Close modal when clicking outside the image
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    };
    
    // Handle comment submission
    const submitCommentBtn = document.querySelector('.submit-comment-btn');
    if (submitCommentBtn && !submitCommentBtn.disabled) {
        submitCommentBtn.addEventListener('click', function() {
            const commentText = document.getElementById('comment-text').value.trim();
            const markerId = window.location.pathname.split('/').filter(p => p).pop();
            
            if (!commentText) {
                alert('Коментар не може бути порожнім');
                return;
            }
            
            fetch(`/content/marker/${markerId}/comment/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    text: commentText
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Reload page to show new comment
                    location.reload();
                } else {
                    alert('Помилка: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error submitting comment:', error);
                alert('Помилка додавання коментаря');
            });
        });
    }
    
    // Handle comment upvotes
    const commentUpvoteButtons = document.querySelectorAll('.comment-upvote-btn');
    commentUpvoteButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const commentId = this.dataset.id;
            
            fetch(`/content/comment/${commentId}/upvote/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Update vote count
                    this.innerHTML = `
                        <svg viewBox="0 0 24 24">
                            <path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-1.91l-.01-.01L23 10z"/>
                        </svg>
                        ${data.votes}
                    `;
                } else {
                    alert('Помилка: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error upvoting comment:', error);
                alert('Помилка');
            });
        });
    });
    
    // Handle marker delete button
    const deleteBtn = document.querySelector('.delete-btn');
    if (deleteBtn) {
        deleteBtn.addEventListener('click', function() {
            const markerId = this.dataset.id;
            
            if (confirm('Ви впевнені, що хочете видалити цей маркер? Це не можна буде скасувати.')) {
                fetch(`/content/marker/${markerId}/delete/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.href = '/';
                    } else {
                        alert('Помилка: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error deleting marker:', error);
                    alert('Помилка видалення маркера');
                });
            }
        });
    }
    
    // Handle share button
    const shareBtn = document.querySelector('.share-btn');
    if (shareBtn) {
        shareBtn.addEventListener('click', function() {
            const url = this.dataset.url;
            
            if (navigator.share) {
                navigator.share({
                    title: document.getElementById('marker-title').innerText,
                    url: url
                }).catch((error) => console.error('Error sharing', error));
            } else {
                // Fallback for browsers that don't support the Share API
                navigator.clipboard.writeText(url).then(() => {
                    alert('URL скопійовано в буфер обміну');
                }, () => {
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = url;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    alert('URL скопійовано в буфер обміну');
                });
            }
        });
    }
    
    // Handle report button
    const reportBtn = document.querySelector('.report-btn');
    if (reportBtn) {
        reportBtn.addEventListener('click', function() {
            const markerId = this.dataset.id;
            const reason = prompt('Вкажіть причину скарги:');
            
            if (reason) {
                fetch(`/content/marker/${markerId}/report/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        reason: reason
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('Скаргу надіслано');
                    } else {
                        alert('Помилка: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error reporting marker:', error);
                    alert('Помилка надсилання скарги');
                });
            }
        });
    }
});
