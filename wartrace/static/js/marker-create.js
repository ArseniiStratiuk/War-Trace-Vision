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
  
  // Handle file upload
  document.getElementById('trigger-upload').addEventListener('click', function() {
    document.getElementById('media-upload').click();
  });
  
  document.getElementById('media-upload').addEventListener('change', function(e) {
    const files = e.target.files;
    
    if (files.length === 0) return;
    
    // Clear preview area
    const previewArea = document.getElementById('media-preview');
    previewArea.innerHTML = '';
    
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
        
        previewArea.appendChild(previewItem);
      };
      
      reader.readAsDataURL(file);
    }
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
  document.getElementById('create-marker-form').addEventListener('submit', function(e) {
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
        showNotification('Marker saved successfully!');
        // Redirect to marker detail page after 2 seconds
        setTimeout(() => {
          window.location.href = `/content/marker/${data.marker_id}/`;
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
