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
  
  // Handle file upload
  document.getElementById('trigger-upload').addEventListener('click', function() {
    document.getElementById('media-upload').click();
  });
  
  document.getElementById('media-upload').addEventListener('change', function(e) {
    const files = e.target.files;
    
    if (files.length === 0) return;
    
    // Display each selected file
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const reader = new FileReader();
      
      reader.onload = function(event) {
        const previewItem = document.createElement('div');
        previewItem.className = 'media-preview-item';
        
        if (file.type.startsWith('image/')) {
          const img = document.createElement('img');
          img.src = event.target.result;
          previewItem.appendChild(img);
        } else if (file.type.startsWith('video/')) {
          const video = document.createElement('video');
          video.src = event.target.result;
          video.controls = true;
          previewItem.appendChild(video);
        }
        
        document.getElementById('media-preview').appendChild(previewItem);
      };
      
      reader.readAsDataURL(file);
    }
  });
  
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
    
    // Add latitude and longitude from selectedLocation
    formData.set('latitude', selectedLocation.lat);
    formData.set('longitude', selectedLocation.lng);
    
    // Ensure boolean fields are properly handled
    const booleanFields = [
      'object_detection', 
      'military_detection', 
      'damage_assessment', 
      'emergency_recognition',
      'request_verification'
    ];
    
    booleanFields.forEach(field => {
      if (!formData.has(field)) {
        formData.append(field, 'false');
      }
    });
    
    // Send AJAX request to update marker
    fetch(`/content/marker/${markerId}/edit/submit/`, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': csrftoken
      }
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        showNotification('Marker updated successfully!');
        // Redirect to marker detail page after 2 seconds
        setTimeout(() => {
          window.location.href = data.redirect || `/content/marker/${markerId}/`;
        }, 1000);
      } else {
        showNotification('Error: ' + data.message);
      }
    })
    .catch(error => {
      showNotification('Error: ' + error.message);
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
