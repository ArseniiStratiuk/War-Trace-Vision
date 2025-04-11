// Basic JavaScript for handling marker processing

document.addEventListener('DOMContentLoaded', function() {
    // Get CSRF token for AJAX requests
    function getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    // Process single file button
    const processFileButtons = document.querySelectorAll('.process-file-btn:not(.processed)');
    processFileButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            const fileId = this.getAttribute('data-id');
            this.disabled = true;
            this.innerHTML = 'Processing...';
            
            fetch(`/detection/file/${fileId}/process/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.innerHTML = 'Processed';
                    this.classList.add('processed');
                    // Reload page to show results
                    window.location.reload();
                } else {
                    this.disabled = false;
                    this.innerHTML = 'Error: ' + data.message;
                    alert('Processing error: ' + data.message);
                }
            })
            .catch(error => {
                this.disabled = false;
                this.innerHTML = 'Error';
                console.error('Error processing file:', error);
            });
        });
    });

    // Process all files button
    const processAllButton = document.getElementById('process-all-files-btn');
    if (processAllButton) {
        processAllButton.addEventListener('click', function() {
            const markerId = window.location.pathname.split('/').filter(p => p).pop();
            this.disabled = true;
            this.innerHTML = 'Processing all files...';
            
            fetch(`/detection/marker/${markerId}/process/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.innerHTML = 'All files processed';
                    // Reload page to show results
                    window.location.reload();
                } else {
                    this.disabled = false;
                    this.innerHTML = 'Process all files';
                    alert('Processing error: ' + data.message);
                }
            })
            .catch(error => {
                this.disabled = false;
                this.innerHTML = 'Process all files';
                console.error('Error processing files:', error);
            });
        });
    }

    // Media upload functionality
    const mediaForm = document.getElementById('add-media-form');
    const mediaInput = document.getElementById('media-file-input');
    const mediaTrigger = document.getElementById('add-media-trigger');
    
    if (mediaTrigger && mediaInput) {
        mediaTrigger.addEventListener('click', function() {
            mediaInput.click();
        });
        
        mediaInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                const markerId = window.location.pathname.split('/').filter(Boolean).pop();
                const formData = new FormData(mediaForm);
                
                mediaTrigger.disabled = true;
                mediaTrigger.textContent = 'Uploading...';
                
                fetch(`/content/marker/${markerId}/add-media/`, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': getCsrfToken()
                    }
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload(); // Refresh to show new files
                    } else {
                        mediaTrigger.disabled = false;
                        mediaTrigger.textContent = 'Add Media';
                        alert('Upload error: ' + data.message);
                    }
                })
                .catch(error => {
                    mediaTrigger.disabled = false;
                    mediaTrigger.textContent = 'Add Media';
                    console.error('Error uploading files:', error);
                });
            }
        });
    }

    // Comment submission
    const commentForm = document.querySelector('.comment-form');
    if (commentForm) {
        const submitButton = commentForm.querySelector('.submit-comment-btn');
        const commentText = document.getElementById('comment-text');
        
        if (submitButton && !submitButton.disabled) {
            submitButton.addEventListener('click', function() {
                if (!commentText.value.trim()) {
                    alert('Comment cannot be empty');
                    return;
                }
                
                const markerId = window.location.pathname.split('/').filter(Boolean).pop();
                
                fetch(`/content/marker/${markerId}/comment/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCsrfToken(),
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        text: commentText.value.trim()
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        window.location.reload(); // Refresh to show new comment
                    } else {
                        alert('Error: ' + data.message);
                    }
                })
                .catch(error => {
                    console.error('Error submitting comment:', error);
                });
            });
        }
    }
});
