/**
 * Marker editing functionality for War Trace Vision.
 * Handles map interactions, location selection, and form submission for existing markers.
 */

document.addEventListener('DOMContentLoaded', function() {
  // Get CSRF token for AJAX requests
  const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  // Get marker ID from URL
  const pathParts = window.location.pathname.split('/');
  const markerId = pathParts[pathParts.indexOf('marker') + 1];
  
  // Check if we're in explicit reprocessing mode from URL parameter
  const urlParams = new URLSearchParams(window.location.search);
  const isExplicitReprocessMode = urlParams.get('reprocess') === 'true';
  
  // Always treat as reprocessing mode even if not explicitly specified
  const isReprocessMode = true;
  
  // Add visual indication about reprocessing mode
  const statusElement = document.querySelector('.app-header .status');
  if (statusElement) {
    statusElement.textContent = isExplicitReprocessMode ? 
      'Наживо • Режим переобробки' :
      'Наживо • Режим редагування і оновлення';
  }
  
  // Update save button text
  const saveButton = document.getElementById('save-marker');
  if (saveButton) {
    saveButton.innerHTML = `
      <svg viewBox="0 0 24 24">
        <path d="M9 16.2L4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2z"/>
      </svg>
      Зберегти і оновити аналіз
    `;
  }
  
  // Always show the reprocessing hint
  const hintElement = document.getElementById('reprocessingHint');
  if (hintElement) {
    // Adjust the hint text based on whether it's explicit reprocessing
    if (isExplicitReprocessMode) {
      hintElement.innerHTML = '<strong>Режим переобробки:</strong> Після збереження змін, всі зображення маркера будуть заново оброблені з поточними моделями ШІ. Старі результати детекції будуть замінені.';
    } else {
      hintElement.innerHTML = '<strong>Оновлення аналізу:</strong> Після збереження змін, всі зображення маркера будуть оброблені з поточними моделями ШІ, якщо включені опції ШІ-аналізу.';
    }
    hintElement.classList.add('visible');
  }
  
  // Get coordinates from form
  const initialLat = parseFloat(document.getElementById('latitude').value);
  const initialLng = parseFloat(document.getElementById('longitude').value);
  
  // Initialize the map
  const mapContainer = document.getElementById('edit-map');
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
    const editPanel = document.querySelector('.edit-panel');
    if (editPanel) {
      editPanel.style.top = mapHeight + 'px';
    }
  };
  
  // Set initial height and adjust on resize
  adjustMapHeight();
  window.addEventListener('resize', adjustMapHeight);
  
  // Initialize map with the same options as the detail page for consistency
  const map = L.map('edit-map', {
    zoomControl: true,
    dragging: true,
    scrollWheelZoom: true
  }).setView([initialLat, initialLng], 15);
  
  // Attribution text
  const attributionText = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
  
  // More detailed standard layer - OpenStreetMap Humanitarian style for better detail
  const detailedLayer = L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
    attribution: attributionText,
    maxZoom: 19
  }).addTo(map);
  
  // Force map recalculation to ensure it renders properly
  setTimeout(function() {
    map.invalidateSize();
  }, 100);
  
  // Use the default Leaflet marker for simplicity and consistency
  // Variables to track selected location
  let selectedLocation = { lat: initialLat, lng: initialLng };
  let locationMarker = L.marker([initialLat, initialLng]).addTo(map);
  
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
      <span>Шир.: ${lat.toFixed(6)}, Дов.: ${lng.toFixed(6)}</span>
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
    
    // Create a new marker with the default Leaflet marker
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
  
  // Initialize uploadedFiles as empty array
  let uploadedFiles = [];

  // Handle file upload
  document.getElementById('trigger-upload').addEventListener('click', function() {
    document.getElementById('media-upload').click();
  });
  
  document.getElementById('media-upload').addEventListener('change', function(e) {
    const files = e.target.files;
    
    if (files.length === 0) return;
    
    // Add new files to existing uploadedFiles array
    const newFiles = Array.from(files).filter(file => 
      file.type.startsWith('image/') || file.type.startsWith('video/')
    );
    uploadedFiles = [...uploadedFiles, ...newFiles];
    
    // Refresh preview to add new files
    const mediaPreview = document.getElementById('media-preview');
    
    // Process and add each file to the preview
    newFiles.forEach(file => {
      const previewItem = document.createElement('div');
      previewItem.className = 'media-preview-item';
      
      // Add delete button for new files
      const deleteBtn = document.createElement('div');
      deleteBtn.className = 'media-delete-btn';
      deleteBtn.innerHTML = '✕';
      deleteBtn.onclick = function(e) {
        e.stopPropagation();
        const index = uploadedFiles.indexOf(file);
        if (index > -1) {
          uploadedFiles.splice(index, 1);
          previewItem.remove();
          updateFileInput();
        }
      };
      previewItem.appendChild(deleteBtn);
      
      // Create image preview based on file type
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
      
      mediaPreview.appendChild(previewItem);
    });
    
    // Update the file input to include all files
    updateFileInput();
    
    // Clear the input so the same files can be selected again if needed
    this.value = '';
  });
  
  function updateFileInput() {
    // Create a new DataTransfer object
    const dataTransfer = new DataTransfer();
    
    // Add all files to the DataTransfer object
    uploadedFiles.forEach(file => {
      dataTransfer.items.add(file);
    });
    
    // Set the new file list to the file input
    document.getElementById('media-upload').files = dataTransfer.files;
  }
  
  // Handle existing media delete buttons
  const mediaDeleteButtons = document.querySelectorAll('.media-delete-btn');
  mediaDeleteButtons.forEach(button => {
    button.addEventListener('click', function() {
      const fileId = this.dataset.id;
      const mediaItem = this.parentElement;
      
      if (confirm('Are you sure you want to delete this file?')) {
        fetch(`/content/marker/${markerId}/delete-media/${fileId}/`, {
          method: 'POST',
          headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
          }
        })
        .then(response => response.json())
        .then(data => {
          if (data.success) {
            mediaItem.remove();
            showNotification('File deleted successfully');
          } else {
            showNotification('Error: ' + data.message);
          }
        })
        .catch(error => {
          showNotification('Error deleting file: ' + error.message);
        });
      }
    });
  });
  
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
  document.getElementById('edit-marker-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    if (!selectedLocation) {
      showNotification('Please select a location on the map.');
      return;
    }
    
    // Using FormData to handle file uploads
    const formData = new FormData(this);
    
    // Add all the newly uploaded files
    if (uploadedFiles.length > 0) {
      // Remove any existing file input values
      if (formData.has('files')) {
        formData.delete('files');
      }
      
      // Add each file individually
      uploadedFiles.forEach(file => {
        formData.append('files', file);
      });
    }
    
    // AI options that require processing
    const aiOptionFields = [
      'object_detection',
      'camouflage_detection',
      'damage_assessment',
      'thermal_analysis'
    ];
    
    // Check if any AI options are enabled
    let hasAiOptions = false;
    
    // Process each AI option field and update FormData
    aiOptionFields.forEach(field => {
      const element = document.getElementById(`toggle-${field.replace('_', '-')}`);
      if (element) {
        const isChecked = element.checked;
        formData.set(field, isChecked);
        if (isChecked) {
          hasAiOptions = true;
        }
      }
    });
    
    // Always force reprocessing
    formData.append('force_reprocess', 'true');
    
    // Show warning for no AI options
    if (!hasAiOptions) {
      if (!confirm('Жодні опції ШІ-аналізу не вибрані. Продовжити без обробки ШІ?')) {
        return; // Stop submission if user cancels
      }
    }
    
    showNotification('Зберігаємо зміни маркера...');
    
    // Update the marker first
    fetch(`/content/marker/${markerId}/edit/submit/`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': csrftoken
      }
    })
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }
      return response.json();
    })
    .then(data => {
      if (data.success) {
        if (hasAiOptions) {
          showNotification('Маркер оновлено! Запускаємо обробку всіх зображень...');
          
          // Explicitly run AI processing for all images with current models
          return fetch(`/detection/api/markers/${markerId}/auto-process/`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrftoken
            },
            body: JSON.stringify({
              process_new_only: false,
              replace_existing: true
            })
          });
        } else {
          // No AI options selected, just redirect
          showNotification('Маркер оновлено (без обробки ШІ).');
          setTimeout(() => {
            window.location.href = data.redirect || `/content/marker/${markerId}/`;
          }, 1000);
          return null;
        }
      } else {
        throw new Error(data.message || 'Failed to update marker');
      }
    })
    .then(response => {
      if (response) {
        // This is the response from the AI processing API
        return response.json();
      }
      return null;
    })
    .then(processingData => {
      if (processingData) {
        if (processingData.success) {
          showNotification('Аналіз ШІ запущено. Результати будуть доступні незабаром.');
        } else {
          console.error('Processing error:', processingData);
          showNotification(`Помилка обробки: ${processingData.message || 'Невідома помилка'}`);
        }
        
        // Redirect to marker detail after AI processing is initiated
        setTimeout(() => {
          window.location.href = `/content/marker/${markerId}/`;
        }, 2000);
      }
      // If processingData is null, we've already redirected in the previous step
    })
    .catch(error => {
      console.error('Error in form submission:', error);
      showNotification('Помилка: ' + error.message);
    });
  });
  
  // Handle cancel button
  document.getElementById('cancel-edit').addEventListener('click', function() {
    if (confirm('Are you sure you want to cancel? All changes will be lost.')) {
      window.location.href = `/content/marker/${markerId}/`;
    }
  });
  
  // Handle back button
  document.getElementById('back-to-marker').addEventListener('click', function() {
    if (confirm('Go back to marker detail? Any unsaved changes will be lost.')) {
      window.location.href = `/content/marker/${markerId}/`;
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
