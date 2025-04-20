/**
 * Marker creation functionality for War Trace Vision.
 * Handles map interactions, location selection, and form submission for new markers.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Get CSRF token for AJAX requests
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  // Set the current date as default date
  const today = new Date();
  document.getElementById('marker-date').value = today.toISOString().split('T')[0];
  
  // Initialize the map
  const mapContainer = document.getElementById('create-map');
  if (!mapContainer) {
    console.error('Map container not found');
    return;
  }
  
  // Responsive map height - match the detail page style
  const adjustMapHeight = () => {
    const viewportHeight = window.innerHeight;
    const mapHeight = Math.max(Math.min(viewportHeight * 0.3, 300), 200);
    mapContainer.style.height = mapHeight + 'px';
    
    // Adjust panel top position to match map height
    const createPanel = document.querySelector('.create-panel');
    if (createPanel) {
      createPanel.style.top = mapHeight + 'px';
    }
  };
  
  // Set initial height and adjust on resize
  adjustMapHeight();
  window.addEventListener('resize', adjustMapHeight);
  
  // Initialize the map with zoomControl similar to detail page
  const map = L.map('create-map', {
    zoomControl: true,
    dragging: true,
    scrollWheelZoom: true
  }).setView([49.0139, 31.2858], 6);
  
  // Attribution text
  const attributionText = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
  
  // More detailed standard layer - OpenStreetMap Humanitarian style for better detail
  const detailedLayer = L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
    attribution: attributionText,
    maxZoom: 19
  }).addTo(map);
  
  // Force a map size recalculation after initialization to fix display issues
  setTimeout(function() {
    map.invalidateSize();
  }, 100);
  
  // Variables to track selected location
  let selectedLocation = null;
  let locationMarker = null;
  
  /**
   * Updates the coordinates display in the UI.
   * @param {number} lat - Latitude value
   * @param {number} lng - Longitude value
   */
  function updateCoordinatesDisplay(lat, lng) {
    document.getElementById('selected-coordinates').innerHTML = `
      <svg viewBox="0 0 24 24">
        <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
      </svg>
      <span>Lat: ${lat.toFixed(6)}, Lng: ${lng.toFixed(6)}</span>
    `;
    
    // Update hidden form fields
    document.getElementById('latitude').value = lat;
    document.getElementById('longitude').value = lng;
  }
  
  /**
   * Sets a marker at the specified coordinates.
   * @param {number} lat - Latitude value
   * @param {number} lng - Longitude value
   */
  function setMarkerAt(lat, lng) {
    // Remove previous marker if it exists
    if (locationMarker) {
      map.removeLayer(locationMarker);
    }
    
    // Create a new marker
    locationMarker = L.marker([lat, lng]).addTo(map);
    
    // Store selected location
    selectedLocation = { lat, lng };
    
    // Update coordinates display
    updateCoordinatesDisplay(lat, lng);
    
    // Center map on the location
    map.setView([lat, lng], 15);
  }
  
  // Handle map click
  map.on('click', function(e) {
    if (document.getElementById('use-map-click').classList.contains('active')) {
      setMarkerAt(e.latlng.lat, e.latlng.lng);
    }
  });
  
  // Handle location options
  const locationOptions = document.querySelectorAll('.location-option');
  locationOptions.forEach(option => {
    option.addEventListener('click', function() {
      // Remove active class from all options
      locationOptions.forEach(opt => {
        opt.classList.remove('active');
      });
      
      // Add active class to clicked option
      this.classList.add('active');
      
      // Show/hide coordinates input
      document.getElementById('coords-input').style.display = 
        this.id === 'use-coordinates' ? 'block' : 'none';
      
      // Handle current location option
      if (this.id === 'use-current-location') {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            function(position) {
              setMarkerAt(position.coords.latitude, position.coords.longitude);
            },
            function(error) {
              showNotification('Could not get your location: ' + error.message);
            }
          );
        } else {
          showNotification('Geolocation is not supported by this browser.');
        }
      }
    });
  });
  
  // Handle coordinates input
  document.getElementById('go-to-coords').addEventListener('click', function() {
    const lat = parseFloat(document.getElementById('lat-input').value);
    const lng = parseFloat(document.getElementById('lng-input').value);
    
    if (isNaN(lat) || isNaN(lng)) {
      showNotification('Please enter valid coordinates.');
      return;
    }
    
    setMarkerAt(lat, lng);
  });
  
  // Simple file management - modified for single file only
  let uploadedFiles = [];
  
  // Handle file upload
  document.getElementById('trigger-upload').addEventListener('click', function() {
    document.getElementById('media-upload').click();
  });
  
  document.getElementById('media-upload').addEventListener('change', function(e) {
    const files = e.target.files;
    
    if (files.length === 0) return;
    
    // Only take the first file
    const file = files[0];
    
    // Ensure it's an image file
    if (!file.type.startsWith('image/')) {
      showNotification('Будь ласка, завантажте тільки файли зображень');
      return;
    }
    
    // Replace any existing files
    uploadedFiles = [file];
    
    // Refresh preview
    refreshPreview();
    
    // Update the file input
    updateFileInput();
    
    // Clear the input so the same file can be selected again if needed
    this.value = '';
  });

  function refreshPreview() {
    const previewArea = document.getElementById('media-preview');
    previewArea.innerHTML = '';
    
    if (uploadedFiles.length === 0) {
      previewArea.innerHTML = '<div class="empty-media-message">Немає вибраних файлів</div>';
      return;
    }
    
    uploadedFiles.forEach((file, index) => {
      const previewItem = document.createElement('div');
      previewItem.className = 'media-preview-item';
      previewItem.dataset.index = index;
      
      // Add delete button
      const deleteBtn = document.createElement('div');
      deleteBtn.className = 'media-delete-btn';
      deleteBtn.innerHTML = '✕';
      deleteBtn.onclick = function(e) {
        e.stopPropagation();
        uploadedFiles.splice(index, 1);
        refreshPreview();
        updateFileInput();
      };
      previewItem.appendChild(deleteBtn);
      
      // Create preview thumbnail based on file type
      if (file.type.startsWith('image/')) {
        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        previewItem.appendChild(img);
      } else if (file.type.startsWith('video/')) {
        const video = document.createElement('video');
        video.src = URL.createObjectURL(file);
        video.controls = true;
        previewItem.appendChild(video);
      }
      
      previewArea.appendChild(previewItem);
    });
  }

  function updateFileInput() {
    // Create a new DataTransfer object
    const dataTransfer = new DataTransfer();
    
    // Add the file to the DataTransfer object (if any)
    if (uploadedFiles.length > 0) {
      dataTransfer.items.add(uploadedFiles[0]);
    }
    
    // Set the new file list to the file input
    document.getElementById('media-upload').files = dataTransfer.files;
  }
  
  // Handle category selection
  const categoryOptions = document.querySelectorAll('.category-option');
  categoryOptions.forEach(option => {
    option.addEventListener('click', function() {
      categoryOptions.forEach(opt => {
        opt.classList.remove('active');
      });
      this.classList.add('active');
      
      // Update hidden input with selected category
      document.getElementById('marker-category').value = this.dataset.category;
    });
  });
  
  // Handle visibility selection
  const visibilityOptions = document.querySelectorAll('.visibility-option');
  visibilityOptions.forEach(option => {
    option.addEventListener('click', function() {
      visibilityOptions.forEach(opt => {
        opt.classList.remove('active');
      });
      this.classList.add('active');
      
      // Update hidden input with selected visibility
      document.getElementById('marker-visibility').value = this.dataset.visibility;
    });
  });
  
  // Handle form submission
  document.getElementById('create-marker-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    if (!document.getElementById('latitude').value || !document.getElementById('longitude').value) {
      showNotification('Будь ласка, виберіть місце на карті');
      return;
    }
    
    // Show saving notification
    showNotification('Збереження маркера...');
    
    // Using FormData to handle file uploads
    const formData = new FormData(this);
    
    // Prepare AI detection options using the correct field names for the backend model
    formData.set('object_detection', document.getElementById('toggle-object-detection').checked);
    formData.set('camouflage_detection', document.getElementById('toggle-camouflage').checked);
    formData.set('damage_assessment', false); // Hidden option
    formData.set('thermal_analysis', false);  // Hidden option
    
    // Ensure file is included
    if (uploadedFiles.length > 0) {
      // Remove any existing file input values
      if (formData.has('files')) {
        formData.delete('files');
      }
      
      // Add the file
      formData.append('files', uploadedFiles[0]);
    } else {
      showNotification('Будь ласка, завантажте зображення для аналізу');
      return;
    }
    
    // Send AJAX request to create marker
    fetch('/content/marker/create/submit/', {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': csrftoken
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        // Check if there are any AI options enabled and files to process
        const hasAiOptions = 
          document.getElementById('toggle-object-detection').checked || 
          document.getElementById('toggle-camouflage').checked ||
          document.getElementById('toggle-damage').checked ||
          document.getElementById('toggle-thermal').checked;
        
        const uploadedFilesCount = document.querySelectorAll('.media-preview-item').length;
        
        if (hasAiOptions && uploadedFilesCount > 0) {
          showNotification('Маркер збережено! Починаємо обробку зображень...');
          
          // Trigger AI processing by calling process_marker API
          fetch(`/detection/api/markers/${data.marker_id}/auto-process/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({}) // Empty body as options are already set on the marker
          })
          .then(response => response.json())
          .then(processingData => {
            if (processingData.success) {
              showNotification('ШІ-аналіз запущено. Результати будуть доступні на сторінці маркера.');
            } else {
              console.error('Processing error:', processingData);
              showNotification(`Помилка обробки: ${processingData.message || 'Невідома помилка'}`);
            }
            
            // Always redirect to marker detail page
            setTimeout(() => {
              window.location.href = `/content/marker/${data.marker_id}/`;
            }, 2000);
          })
          .catch(error => {
            console.error('Error triggering AI processing:', error);
            showNotification('Помилка обробки зображень. Маркер був збережений, але ШІ-аналіз не був виконаний.');
            
            // Still redirect to the marker page
            setTimeout(() => {
              window.location.href = `/content/marker/${data.marker_id}/`;
            }, 2000);
          });
        } else {
          showNotification('Маркер успішно збережено!');
          // Redirect to marker detail page after short delay
          setTimeout(() => {
            window.location.href = `/content/marker/${data.marker_id}/`;
          }, 1500);
        }
      } else {
        showNotification('Помилка: ' + data.message);
      }
    })
    .catch(error => {
      showNotification('Помилка: ' + error.message);
    });
  });
  
  // Handle cancel button
  document.getElementById('cancel-marker').addEventListener('click', function() {
    if (confirm('Are you sure you want to cancel? All entered data will be lost.')) {
      window.location.href = '/content/';
    }
  });
  
  // Handle back button
  document.getElementById('back-to-map').addEventListener('click', function() {
    if (confirm('Go back to map? Any unsaved changes will be lost.')) {
      window.location.href = '/content/';
    }
  });
  
  /**
   * Displays a notification message to the user.
   * @param {string} message - The message to display
   */
  function showNotification(message) {
    const notification = document.getElementById('notification');
    document.getElementById('notification-message').textContent = message;
    
    notification.classList.add('show');
    
    setTimeout(function() {
      notification.classList.remove('show');
    }, 3000);
  }
});
