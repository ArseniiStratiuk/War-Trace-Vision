// Initialize map
const map = L.map('map', {
  zoomControl: false  // Disable default zoom controls
}).setView([48.3794, 31.1656], 6);

// Set attributions with more relevant text for this project
const attributionText = '© OpenStreetMap contributors | Платформа аналізу зображень для документування війни';

// Regular map layer - OpenStreetMap with custom attribution
const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: attributionText,
  maxZoom: 19
});

// More detailed standard layer - OpenStreetMap Humanitarian style for better detail
const detailedLayer = L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
  attribution: attributionText,
  maxZoom: 19
}).addTo(map);

// Satellite layer with appropriate attribution
const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
  attribution: attributionText + ' | Супутникові знімки від Esri',
  maxZoom: 19
});

// Labels layer for satellite mode
const labelsLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_only_labels/{z}/{x}/{y}{r}.png', {
  attribution: attributionText,
  maxZoom: 19,
  pane: 'shadowPane'  // Place labels above the satellite imagery
});

// Add scale control
L.control.scale({
  imperial: false,
  position: 'bottomleft'
}).addTo(map);

// Layer for all markers
const markers = L.layerGroup().addTo(map);

// Layer for drawing features
const drawnItems = new L.FeatureGroup().addTo(map);

// Helper function to truncate text
function truncateText(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// Ukrainian translations for marker tooltips
const translations = {
  confidence: 'Достовірність',
  date: 'Дата',
  source: 'Джерело',
  by: 'Автор',
  verified: 'Перевірено',
  unverified: 'Неперевірено',
  aiDetected: 'ШІ виявлено',
  // Drawing and measurement translations
  draw: {
    toolbar: {
      actions: {
        title: 'Скасувати малювання',
        text: 'Скасувати'
      },
      finish: {
        title: 'Завершити малювання',
        text: 'Завершити'
      },
      undo: {
        title: 'Видалити останню намальовану точку',
        text: 'Видалити останню точку'
      },
      buttons: {
        polyline: 'Намалювати лінію',
        polygon: 'Намалювати полігон',
        rectangle: 'Намалювати прямокутник',
        circle: 'Намалювати коло',
        marker: 'Додати точку',
        circlemarker: 'Додати круглу точку'
      }
    },
    handlers: {
      circle: {
        tooltip: {
          start: 'Клікніть та потягніть, щоб намалювати коло'
        },
        radius: 'Радіус'
      },
      circlemarker: {
        tooltip: {
          start: 'Клікніть, щоб розмістити круглу точку'
        }
      },
      marker: {
        tooltip: {
          start: 'Клікніть, щоб розмістити точку'
        }
      },
      polygon: {
        tooltip: {
          start: 'Клікніть, щоб почати малювати фігуру',
          cont: 'Клікніть, щоб продовжити малювання фігури',
          end: 'Клікніть на першу точку, щоб замкнути фігуру'
        }
      },
      polyline: {
        tooltip: {
          start: 'Клікніть, щоб почати малювати лінію',
          cont: 'Клікніть, щоб продовжити малювання лінії',
          end: 'Клікніть на останню точку, щоб завершити лінію'
        }
      },
      rectangle: {
        tooltip: {
          start: 'Клікніть та потягніть, щоб намалювати прямокутник'
        }
      },
      simpleshape: {
        tooltip: {
          end: 'Відпустіть кнопку миші, щоб завершити малювання'
        }
      }
    }
  },
  measure: {
    start: 'Почати вимірювання',
    startArea: 'Вимірювання площі',
    startLine: 'Вимірювання відстані',
    complete: 'Завершити вимірювання',
    area: 'Площа',
    distance: 'Відстань',
    kilometers: 'км',
    meters: 'м',
    squareKilometers: 'км²',
    hectares: 'га'
  }
};

// Function to create marker with proper tooltip and thumbnail
function createMarker(item) {
  const markerClass = `marker-${item.category}`;
  
  const icon = L.divIcon({
    className: markerClass,
    iconSize: [12, 12]
  });
  
  const marker = L.marker([item.lat, item.lng], {
    icon: icon
  });
  
  const verificationStatus = item.verification === 'verified' ? 
    `<span class="status-verified">${translations.verified}</span>` : 
    (item.verification === 'ai-detected' ? 
      `<span class="status-ai-detected">${translations.aiDetected}</span>` : 
      `<span class="status-unverified">${translations.unverified}</span>`);
  
  // Truncate description to 60 characters
  const truncatedDescription = truncateText(item.description, 60);
  
  // Truncate source to 30 characters
  const truncatedSource = truncateText(item.source, 30);

  // Get category name in Ukrainian
  const categoryNames = {
    'infrastructure': 'Інфраструктура',
    'military': 'Військові об\'єкти',
    'hazard': 'Небезпечна зона',
    'residential': 'Житлові будинки'
  };
  
  const categoryName = categoryNames[item.category] || item.category;
  
  // Add thumbnail to tooltip if available
  const thumbnailHtml = item.thumbnail ? 
    `<div class="marker-thumbnail"><img src="${item.thumbnail}" alt="Мініатюра"></div>` :
    '';
  
  const tooltipContent = `
    <div class="tooltip">
      ${thumbnailHtml}
      <div class="tooltip-header">
        <h3 class="tooltip-title">${item.title}</h3>
        <div class="tooltip-meta">
          ${verificationStatus}
          <span class="category-tag">${categoryName}</span>
        </div>
      </div>
      <p class="truncated-text" title="${item.description}">${truncatedDescription}</p>
      <p class="confidence">${translations.confidence}: ${item.confidence}</p>
      <p class="date" title="${translations.date}: ${item.date}">${translations.date}: ${item.date}</p>
      <p class="source" title="${translations.source}: ${item.source}">${translations.source}: ${truncatedSource}</p>
      <p class="user">${translations.by}: ${item.user}</p>
    </div>
  `;
  
  marker.bindTooltip(tooltipContent, {
    permanent: false,
    direction: 'top',
    offset: [0, -10],
    opacity: 1
  });
  
  // Add click handler to view marker details - fix URL path to match actual URL configuration
  marker.on('click', function() {
    window.location.href = `/content/marker/${item.id}/`;
  });
  
  return marker;
}

// Store the current markers data
let currentMarkersData = [];

// Function to load markers via AJAX
function loadMarkers() {
  // Show loading indicator in status
  document.querySelector('.app-header .status').textContent = 'Завантаження маркерів...';
  
  // Make AJAX request to the marker_api endpoint - fix URL to match Django URL structure
  fetch('/content/api/markers/')
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        // Store the complete markers data
        currentMarkersData = data.markers || [];
        
        // Clear existing markers
        markers.clearLayers();
        
        // Add new markers from the API response
        if (currentMarkersData.length > 0) {
            currentMarkersData.forEach(item => {
                const marker = createMarker(item);
                marker.addTo(markers);
            });
            
            // Update status to show number of markers
            document.querySelector('.app-header .status').textContent = 
                `Наживо • ${currentMarkersData.length} маркерів завантажено`;
        } else {
            // No markers found
            document.querySelector('.app-header .status').textContent = 
                'Наживо • Немає доступних маркерів';
        }
    })
    .catch(error => {
        console.error('Error loading markers:', error);
        document.querySelector('.app-header .status').textContent = 
            'Помилка завантаження маркерів';
    });
}

// Function to filter markers locally using the stored data
function filterMarkers() {
  // Get filter values
  const categoryFilter = document.getElementById('filter-category').value;
  const verificationFilter = document.getElementById('filter-verification').value;
  const startDateFilter = document.getElementById('filter-start-date').value;
  const endDateFilter = document.getElementById('filter-end-date').value;
  
  // Show filtering status
  document.querySelector('.app-header .status').textContent = 'Фільтрація маркерів...';
  
  // Clear existing markers
  markers.clearLayers();
  
  // Apply filters to current data
  const filteredMarkers = currentMarkersData.filter(item => {
    // Check category filter
    if (categoryFilter && item.category !== categoryFilter) {
      return false;
    }
    
    // Check verification filter
    if (verificationFilter && item.verification !== verificationFilter) {
      return false;
    }
    
    // Check date range
    if (startDateFilter || endDateFilter) {
      const itemDate = new Date(item.date);
      
      if (startDateFilter) {
        const startDate = new Date(startDateFilter);
        if (itemDate < startDate) {
          return false;
        }
      }
      
      if (endDateFilter) {
        const endDate = new Date(endDateFilter);
        // Set time to end of day for inclusive end date
        endDate.setHours(23, 59, 59, 999);
        if (itemDate > endDate) {
          return false;
        }
      }
    }
    
    // All filters passed
    return true;
  });
  
  // Add filtered markers
  if (filteredMarkers.length > 0) {
    filteredMarkers.forEach(item => {
      const marker = createMarker(item);
      marker.addTo(markers);
    });
    
    // Update status to show filtered results
    document.querySelector('.app-header .status').textContent = 
      `Наживо • ${filteredMarkers.length} маркерів відображено`;
  } else {
    // No markers match the filter
    document.querySelector('.app-header .status').textContent = 
      'Жоден маркер не відповідає фільтрам';
  }
  
  // Close the filter panel
  document.querySelector('.filter-panel').style.display = 'none';
}

// Variables to track UI state
let isDarkMode = false;
let isSatelliteMode = false;
let isLegendVisible = false;
let isAiPanelVisible = false;
let isDrawControlActive = false;
let drawControl = null;
let isMeasureActive = false;
let measureControl = null;
let isMenuExpanded = false;

// Function to initialize draw control with proper Ukrainian translations
function initDrawControl() {
  if (drawControl) {
    map.removeControl(drawControl);
  }
  
  // Override default Leaflet.draw translations with Ukrainian
  if (L.drawLocal) {
    // Actions
    L.drawLocal.draw.toolbar.actions.title = translations.draw.toolbar.actions.title;
    L.drawLocal.draw.toolbar.actions.text = translations.draw.toolbar.actions.text;
    L.drawLocal.draw.toolbar.finish.title = translations.draw.toolbar.finish.title;
    L.drawLocal.draw.toolbar.finish.text = translations.draw.toolbar.finish.text;
    L.drawLocal.draw.toolbar.undo.title = translations.draw.toolbar.undo.title;
    L.drawLocal.draw.toolbar.undo.text = translations.draw.toolbar.undo.text;
    
    // Buttons
    L.drawLocal.draw.toolbar.buttons.polyline = translations.draw.toolbar.buttons.polyline;
    L.drawLocal.draw.toolbar.buttons.polygon = translations.draw.toolbar.buttons.polygon;
    L.drawLocal.draw.toolbar.buttons.rectangle = translations.draw.toolbar.buttons.rectangle;
    L.drawLocal.draw.toolbar.buttons.circle = translations.draw.toolbar.buttons.circle;
    L.drawLocal.draw.toolbar.buttons.marker = translations.draw.toolbar.buttons.marker;
    L.drawLocal.draw.toolbar.buttons.circlemarker = translations.draw.toolbar.buttons.circlemarker;
    
    // Handlers tooltips
    L.drawLocal.draw.handlers.circle.tooltip.start = translations.draw.handlers.circle.tooltip.start;
    L.drawLocal.draw.handlers.circle.radius = translations.draw.handlers.circle.radius;
    L.drawLocal.draw.handlers.circlemarker.tooltip.start = translations.draw.handlers.circlemarker.tooltip.start;
    L.drawLocal.draw.handlers.marker.tooltip.start = translations.draw.handlers.marker.tooltip.start;
    L.drawLocal.draw.handlers.polygon.tooltip.start = translations.draw.handlers.polygon.tooltip.start;
    L.drawLocal.draw.handlers.polygon.tooltip.cont = translations.draw.handlers.polygon.tooltip.cont;
    L.drawLocal.draw.handlers.polygon.tooltip.end = translations.draw.handlers.polygon.tooltip.end;
    L.drawLocal.draw.handlers.polyline.tooltip.start = translations.draw.handlers.polyline.tooltip.start;
    L.drawLocal.draw.handlers.polyline.tooltip.cont = translations.draw.handlers.polyline.tooltip.cont;
    L.drawLocal.draw.handlers.polyline.tooltip.end = translations.draw.handlers.polyline.tooltip.end;
    L.drawLocal.draw.handlers.rectangle.tooltip.start = translations.draw.handlers.rectangle.tooltip.start;
    L.drawLocal.draw.handlers.simpleshape.tooltip.end = translations.draw.handlers.simpleshape.tooltip.end;
    
    // Edit tooltips
    L.drawLocal.edit = L.drawLocal.edit || {};
    L.drawLocal.edit.toolbar = L.drawLocal.edit.toolbar || {};
    L.drawLocal.edit.toolbar.buttons = L.drawLocal.edit.toolbar.buttons || {};
    L.drawLocal.edit.toolbar.buttons.edit = 'Редагувати шари';
    L.drawLocal.edit.toolbar.buttons.editDisabled = 'Немає шарів для редагування';
    L.drawLocal.edit.toolbar.buttons.remove = 'Видалити шари';
    L.drawLocal.edit.toolbar.buttons.removeDisabled = 'Немає шарів для видалення';
  }
  
  // Initialize draw control with our options
  drawControl = new L.Control.Draw({
    position: 'topright',
    draw: {
      polyline: {
        shapeOptions: {
          color: '#f357a1',
          weight: 3
        }
      },
      polygon: {
        allowIntersection: false,
        drawError: {
          color: '#e1e100',
          message: '<strong>Помилка:</strong> форми не можуть перетинатися!'
        },
        shapeOptions: {
          color: '#3388ff',
          fillOpacity: 0.3
        }
      },
      circle: {
        shapeOptions: {
          color: '#ff6600',
          fillOpacity: 0.3
        }
      },
      rectangle: {
        shapeOptions: {
          color: '#ff4444',
          fillOpacity: 0.3
        }
      }
    },
    edit: {
      featureGroup: drawnItems,
      poly: {
        allowIntersection: false
      }
    }
  });
  
  // Register event handlers for drawing
  map.on(L.Draw.Event.CREATED, function(event) {
    const layer = event.layer;
    drawnItems.addLayer(layer);
    
    // If the shape has getLatLngs (polygons, polylines)
    if (layer.getLatLngs) {
      console.log('Shape coordinates:', JSON.stringify(layer.getLatLngs()));
    } 
    // Else if it's a circle
    else if (layer.getRadius) {
      console.log('Circle at:', JSON.stringify(layer.getLatLng()), 'with radius:', layer.getRadius());
    }
    // Otherwise it's a marker
    else if (layer.getLatLng) {
      console.log('Marker at:', JSON.stringify(layer.getLatLng()));
    }
    
    // Export the complete feature collection
    const geojson = drawnItems.toGeoJSON();
    console.log('Full GeoJSON:', JSON.stringify(geojson));
    
    // Here you would typically send this data to the server
    // fetch('/content/api/save-drawing/', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(geojson)
    // });
  });
  
  map.on(L.Draw.Event.EDITED, function(event) {
    const layers = event.layers;
    console.log('Edited layers:', layers.toGeoJSON());
  });
  
  map.on(L.Draw.Event.DELETED, function(event) {
    const layers = event.layers;
    console.log('Deleted layers:', layers.toGeoJSON());
  });
  
  return drawControl;
}

// Function to initialize measure control
function initMeasureControl() {
  // Prepare custom language strings
  const measureLocalization = {
    startPrompt: translations.measure.start,
    continuePrompt: '',
    clearPrompt: translations.measure.complete,
    measureArea: translations.measure.startArea,
    measureLine: translations.measure.startLine,
    primaryLengthUnit: translations.measure.kilometers,
    secondaryLengthUnit: translations.measure.meters,
    primaryAreaUnit: translations.measure.squareKilometers,
    secondaryAreaUnit: translations.measure.hectares,
    activeColor: '#3388ff',
    completedColor: '#ff7800'
  };
  
  // Create measure control with custom options
  return L.control.measure({
    primaryLengthUnit: 'kilometers',
    secondaryLengthUnit: 'meters',
    primaryAreaUnit: 'sqkilometers', 
    secondaryAreaUnit: 'hectares',
    activeColor: measureLocalization.activeColor,
    completedColor: measureLocalization.completedColor,
    position: 'topright',
    localization: measureLocalization,
    captureZIndex: 10000
  });
}

// Function to toggle enhanced navigation menu
function toggleEnhancedMenu() {
  const toolbar = document.querySelector('.toolbar');
  isMenuExpanded = !isMenuExpanded;
  
  if (isMenuExpanded) {
    toolbar.classList.add('expanded');
    
    // Create the enhanced menu if it doesn't exist
    if (!document.querySelector('.enhanced-menu')) {
      const menuHTML = `
        <div class="enhanced-menu">
          <div class="menu-header">
            <h3>War Trace Vision</h3>
            <button class="close-menu-btn">&times;</button>
          </div>
          <div class="menu-sections">
            <div class="menu-section">
              <h4>Карта</h4>
              <ul>
                <li><a href="/maps/" class="active">Інтерактивна карта</a></li>
                <li><a href="/content/marker/create/">Додати маркер</a></li>
                <li><a href="/detection/">ШІ аналіз</a></li>
              </ul>
            </div>
            <div class="menu-section">
              <h4>Обліковий запис</h4>
              <ul>
                <li><a href="/auth/login/">Вхід</a></li>
                <li><a href="/auth/register/">Реєстрація</a></li>
                <li><a href="/auth/personal/">Особистий кабінет</a></li>
                <li><a href="/auth/logout/">Вихід</a></li>
              </ul>
            </div>
            <div class="menu-section">
              <h4>Волонтерство</h4>
              <ul>
                <li><a href="/search/">Запити на допомогу</a></li>
                <li><a href="/content/">Контент</a></li>
              </ul>
            </div>
          </div>
        </div>
      `;
      
      toolbar.insertAdjacentHTML('beforeend', menuHTML);
      
      // Add event listener to close menu button
      document.querySelector('.close-menu-btn').addEventListener('click', function(e) {
        e.stopPropagation();
        toggleEnhancedMenu();
      });
    } else {
      document.querySelector('.enhanced-menu').style.display = 'block';
    }
  } else {
    toolbar.classList.remove('expanded');
    const enhancedMenu = document.querySelector('.enhanced-menu');
    if (enhancedMenu) {
      enhancedMenu.style.display = 'none';
    }
  }
}

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
  // Initial status indicator
  document.querySelector('.app-header .status').innerHTML = '<span class="spinner"></span> Ініціалізація...';
  
  // Initial marker load
  loadMarkers();
  
  // Set up auto-refresh every 60 seconds
  setInterval(loadMarkers, 60000);
  
  // Set up connection status check
  setInterval(() => {
    // Check connectivity
    const isOnline = navigator.onLine;
    const statusElement = document.querySelector('.app-header .status');
    
    if (!isOnline) {
      statusElement.innerHTML = '<span style="color: red;">⚠ Офлайн</span>';
    }
  }, 30000);

  // Filter panel toggle
  document.getElementById('filter-btn').addEventListener('click', function() {
    document.querySelector('.filter-panel').style.display = 'block';
  });

  document.getElementById('close-filter').addEventListener('click', function() {
    document.querySelector('.filter-panel').style.display = 'none';
  });

  // Apply filters
  document.getElementById('apply-filters').addEventListener('click', filterMarkers);

  // Reset filters
  document.getElementById('reset-filters').addEventListener('click', function() {
    // Clear all filter inputs
    document.getElementById('filter-category').value = '';
    document.getElementById('filter-verification').value = '';
    document.getElementById('filter-start-date').value = '';
    document.getElementById('filter-end-date').value = '';
    
    // Reset to show all markers
    markers.clearLayers();
    currentMarkersData.forEach(item => {
      const marker = createMarker(item);
      marker.addTo(markers);
    });
    
    // Update status
    document.querySelector('.app-header .status').textContent = 
      `Наживо • ${currentMarkersData.length} маркерів відображено`;
    
    // Close the filter panel
    document.querySelector('.filter-panel').style.display = 'none';
  });

  // Add "Add Marker" button functionality
  document.getElementById('marker-btn').addEventListener('click', function() {
    window.location.href = '/content/marker/create/';
  });

  // Toggle dark mode
  document.getElementById('dark-mode-btn').addEventListener('click', function() {
    isDarkMode = !isDarkMode;
    document.body.classList.toggle('dark-mode', isDarkMode);
    
    // Update the dark mode button icon
    this.innerHTML = isDarkMode ? 
      '<svg viewBox="0 0 24 24"><path d="M10 2c-1.82 0-3.53.5-5 1.35C7.99 5.08 10 8.3 10 12s-2.01 6.92-5 8.65C6.47 21.5 8.18 22 10 22c5.52 0 10-4.48 10-10S15.52 2 10 2z"/></svg>' : 
      '<svg viewBox="0 0 24 24"><path d="M20 8.69V4h-4.69L12 .69 8.69 4H4v4.69L.69 12 4 15.31V20h4.69L12 23.31 15.31 20H20v-4.69L23.31 12 20 8.69zM12 18c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6zm0-10c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4-1.79-4-4-4z"/></svg>';
  });
  
  // Toggle satellite mode
  document.getElementById('satellite-btn').addEventListener('click', function() {
    isSatelliteMode = !isSatelliteMode;
    
    if (isSatelliteMode) {
      map.removeLayer(detailedLayer);
      map.removeLayer(osmLayer);
      satelliteLayer.addTo(map);
      labelsLayer.addTo(map);
    } else {
      map.removeLayer(satelliteLayer);
      map.removeLayer(labelsLayer);
      detailedLayer.addTo(map);
    }
    
    // Update button state
    this.classList.toggle('active', isSatelliteMode);
  });
  
  // Toggle legend visibility
  document.getElementById('legend-btn').addEventListener('click', function() {
    isLegendVisible = !isLegendVisible;
    document.querySelector('.map-legend').style.display = isLegendVisible ? 'block' : 'none';
  });
  
  // Zoom controls
  document.getElementById('zoom-in-btn').addEventListener('click', function() {
    map.zoomIn();
  });
  
  document.getElementById('zoom-out-btn').addEventListener('click', function() {
    map.zoomOut();
  });
  
  // AI analysis panel toggle (if it exists)
  const aiBtn = document.getElementById('ai-btn');
  if (aiBtn) {
    aiBtn.addEventListener('click', function() {
      // Either toggle panel or redirect to detection page
      const aiPanel = document.querySelector('.ai-analysis-panel');
      if (aiPanel) {
        isAiPanelVisible = !isAiPanelVisible;
        aiPanel.style.display = isAiPanelVisible ? 'block' : 'none';
      } else {
        window.location.href = '/detection/';
      }
    });
  }
  
  // Close AI panel if it exists
  const closeAiPanel = document.getElementById('close-ai-panel');
  if (closeAiPanel) {
    closeAiPanel.addEventListener('click', function() {
      isAiPanelVisible = false;
      document.querySelector('.ai-analysis-panel').style.display = 'none';
    });
  }
  
  // Draw mode button - Updated with real Leaflet.Draw functionality
  document.getElementById('draw-btn').addEventListener('click', function() {
    isDrawControlActive = !isDrawControlActive;
    
    if (isDrawControlActive) {
      try {
        // Check if Leaflet.Draw is available by testing for a key component
        if (typeof L.Control.Draw === 'function') {
          // If we're activating drawing, first deactivate measuring if active
          if (isMeasureActive && measureControl) {
            map.removeControl(measureControl);
            document.getElementById('ruler-btn').classList.remove('active');
            isMeasureActive = false;
          }
          
          // Initialize and add draw control
          drawControl = initDrawControl();
          map.addControl(drawControl);
          this.classList.add('active');
          
          // Show toast notification with instructions
          showToast('Режим малювання активовано. Використовуйте панель інструментів у верхньому правому куті карти.');
        } else {
          console.error("Leaflet.Draw not found. Make sure the library is loaded.");
          alert("Режим малювання недоступний. Необхідно підключити бібліотеку Leaflet.Draw.");
          isDrawControlActive = false;
        }
      } catch (e) {
        console.error("Error initializing draw control:", e);
        isDrawControlActive = false;
      }
    } else {
      // Remove draw control if active
      if (drawControl) {
        map.removeControl(drawControl);
        this.classList.remove('active');
      }
    }
  });
  
  // Measurement tool - Updated with real Leaflet-Measure functionality
  document.getElementById('ruler-btn').addEventListener('click', function() {
    isMeasureActive = !isMeasureActive;
    
    if (isMeasureActive) {
      try {
        // If we're activating measuring, first deactivate drawing if active
        if (isDrawControlActive && drawControl) {
          map.removeControl(drawControl);
          document.getElementById('draw-btn').classList.remove('active');
          isDrawControlActive = false;
        }
        
        // Initialize and add measure control
        measureControl = initMeasureControl();
        map.addControl(measureControl);
        this.classList.add('active');
        
        // Show toast notification with instructions
        showToast('Режим вимірювання активовано. Клікніть на карту, щоб почати вимірювання.');
      } catch (e) {
        console.error("Error initializing measure control:", e);
        isMeasureActive = false;
        alert("Інструмент вимірювання недоступний. Перевірте підключення бібліотеки.");
      }
    } else {
      // Remove measurement control if active
      if (measureControl) {
        map.removeControl(measureControl);
        this.classList.remove('active');
      }
    }
  });
  
  // Search functionality
  document.getElementById('search-btn').addEventListener('click', function() {
    const searchPanel = document.createElement('div');
    searchPanel.className = 'search-panel';
    searchPanel.innerHTML = `
      <div class="search-header">
        <h3>Пошук за місцем</h3>
        <button class="close-search">&times;</button>
      </div>
      <div class="search-content">
        <input type="text" id="search-input" placeholder="Введіть назву міста чи адресу">
        <button id="execute-search">Пошук</button>
      </div>
    `;
    
    document.body.appendChild(searchPanel);
    
    document.querySelector('.close-search').addEventListener('click', function() {
      document.body.removeChild(searchPanel);
    });
    
    document.getElementById('execute-search').addEventListener('click', function() {
      const query = document.getElementById('search-input').value.trim();
      if (query) {
        // Use Nominatim for geocoding
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=1`)
          .then(response => response.json())
          .then(data => {
            if (data && data.length > 0) {
              const location = data[0];
              map.setView([location.lat, location.lon], 13);
              
              // Add a temporary marker
              const tempMarker = L.marker([location.lat, location.lon])
                .addTo(map)
                .bindTooltip(`${location.display_name}`, {
                  permanent: false,
                  direction: 'top'
                });
              
              // Remove the search panel
              document.body.removeChild(searchPanel);
              
              // Remove the marker after 5 seconds
              setTimeout(() => {
                map.removeLayer(tempMarker);
              }, 5000);
            } else {
              alert('Місце не знайдено. Спробуйте інший пошуковий запит.');
            }
          })
          .catch(error => {
            console.error('Error searching location:', error);
            alert('Помилка під час пошуку. Спробуйте пізніше.');
          });
      }
    });
  });
  
  // Layer control
  document.getElementById('layers-btn').addEventListener('click', function() {
    // Create a simple layer control panel
    const layerPanel = document.createElement('div');
    layerPanel.className = 'layer-panel';
    layerPanel.innerHTML = `
      <div class="layer-header">
        <h3>Шари карти</h3>
        <button class="close-layers">&times;</button>
      </div>
      <div class="layer-content">
        <div class="layer-item">
          <input type="radio" name="base-layer" id="layer-detailed" ${!isSatelliteMode ? 'checked' : ''}>
          <label for="layer-detailed">Стандартна карта</label>
        </div>
        <div class="layer-item">
          <input type="radio" name="base-layer" id="layer-satellite" ${isSatelliteMode ? 'checked' : ''}>
          <label for="layer-satellite">Супутникові знімки</label>
        </div>
        <div class="layer-divider"></div>
        <h4>Додаткові шари</h4>
        <div class="layer-item">
          <input type="checkbox" id="layer-markers" checked>
          <label for="layer-markers">Маркери</label>
        </div>
        <div class="layer-item">
          <input type="checkbox" id="layer-drawings" checked>
          <label for="layer-drawings">Позначки</label>
        </div>
      </div>
    `;
    
    document.body.appendChild(layerPanel);
    
    // Close button
    document.querySelector('.close-layers').addEventListener('click', function() {
      document.body.removeChild(layerPanel);
    });
    
    // Layer change events
    document.getElementById('layer-detailed').addEventListener('change', function() {
      if (this.checked && isSatelliteMode) {
        isSatelliteMode = false;
        map.removeLayer(satelliteLayer);
        map.removeLayer(labelsLayer);
        detailedLayer.addTo(map);
        document.getElementById('satellite-btn').classList.remove('active');
      }
    });
    
    document.getElementById('layer-satellite').addEventListener('change', function() {
      if (this.checked && !isSatelliteMode) {
        isSatelliteMode = true;
        map.removeLayer(detailedLayer);
        map.removeLayer(osmLayer);
        satelliteLayer.addTo(map);
        labelsLayer.addTo(map);
        document.getElementById('satellite-btn').classList.add('active');
      }
    });
    
    document.getElementById('layer-markers').addEventListener('change', function() {
      if (this.checked) {
        markers.addTo(map);
      } else {
        map.removeLayer(markers);
      }
    });
    
    document.getElementById('layer-drawings').addEventListener('change', function() {
      if (this.checked) {
        drawnItems.addTo(map);
      } else {
        map.removeLayer(drawnItems);
      }
    });
  });
  
  // Try to get user location if available
  try {
    navigator.geolocation.getCurrentPosition(function(position) {
      const userIcon = L.divIcon({
        className: 'user-location',
        iconSize: [20, 20]
      });
      
      L.marker([position.coords.latitude, position.coords.longitude], {
        icon: userIcon
      }).addTo(map).bindTooltip("Ваше місцезнаходження", {
        permanent: false,
        direction: 'top'
      });
    }, function() {
      // Geolocation error or denied
      console.log("Геолокація недоступна або відхилена");
    });
  } catch (e) {
    console.log("Геолокація не підтримується");
  }
  
  // Add menu button functionality - enhanced version
  document.querySelector('.menu-button').addEventListener('click', toggleEnhancedMenu);
});

// Add CSS for enhanced menu and other new UI components
document.addEventListener('DOMContentLoaded', function() {
  const style = document.createElement('style');
  style.textContent = `
    .toolbar.expanded {
      width: 300px;
      overflow-y: auto;
    }
    
    .enhanced-menu {
      width: 100%;
      padding: 0;
    }
    
    .menu-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 15px;
      border-bottom: 1px solid rgba(0,0,0,0.1);
      margin-bottom: 15px;
    }
    
    .menu-header h3 {
      margin: 0;
      font-size: 16px;
    }
    
    .close-menu-btn {
      background: none;
      border: none;
      font-size: 22px;
      cursor: pointer;
      color: #666;
    }
    
    .dark-mode .close-menu-btn {
      color: #ddd;
    }
    
    .menu-sections {
      padding: 0 15px;
    }
    
    .menu-section {
      margin-bottom: 20px;
    }
    
    .menu-section h4 {
      font-size: 14px;
      margin-bottom: 8px;
      color: #555;
    }
    
    .dark-mode .menu-section h4 {
      color: #bbb;
    }
    
    .menu-section ul {
      list-style: none;
      padding: 0;
      margin: 0;
    }
    
    .menu-section ul li {
      margin-bottom: 5px;
    }
    
    .menu-section ul li a {
      display: block;
      padding: 8px 10px;
      color: #333;
      text-decoration: none;
      border-radius: 4px;
      font-size: 14px;
      transition: background-color 0.2s;
    }
    
    .dark-mode .menu-section ul li a {
      color: #eee;
    }
    
    .menu-section ul li a:hover,
    .menu-section ul li a.active {
      background-color: rgba(0,0,0,0.05);
    }
    
    .dark-mode .menu-section ul li a:hover,
    .dark-mode .menu-section ul li a.active {
      background-color: rgba(255,255,255,0.1);
    }
    
    .tooltip-header {
      display: flex;
      flex-direction: column;
      margin-bottom: 8px;
    }
    
    .tooltip-title {
      font-size: 14px;
      margin: 0 0 5px 0;
      min-height: 18px;
    }
    
    .tooltip-meta {
      display: flex;
      align-items: center;
      gap: 5px;
      margin-bottom: 8px;
    }
    
    .category-tag {
      display: inline-block;
      background: #e0e0e0;
      color: #333;
      padding: 2px 5px;
      border-radius: 3px;
      font-size: 10px;
    }
    
    .dark-mode .category-tag {
      background: #555;
      color: #ddd;
    }
    
    .search-panel,
    .layer-panel {
      position: absolute;
      top: 120px;
      right: 15px;
      width: 280px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.2);
      z-index: 1000;
      overflow: hidden;
    }
    
    .dark-mode .search-panel,
    .dark-mode .layer-panel {
      background: #333;
      color: #fff;
    }
    
    .search-header,
    .layer-header {
      display: flex;
      justify-content: space-between;
      padding: 10px 15px;
      border-bottom: 1px solid #eee;
    }
    
    .dark-mode .search-header,
    .dark-mode .layer-header {
      border-bottom: 1px solid #555;
    }
    
    .search-header h3,
    .layer-header h3 {
      margin: 0;
      font-size: 16px;
    }
    
    .close-search,
    .close-layers {
      background: none;
      border: none;
      font-size: 20px;
      cursor: pointer;
    }
    
    .dark-mode .close-search,
    .dark-mode .close-layers {
      color: #ddd;
    }
    
    .search-content,
    .layer-content {
      padding: 15px;
    }
    
    #search-input {
      width: 100%;
      padding: 8px;
      margin-bottom: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
    }
    
    .dark-mode #search-input {
      background: #444;
      border: 1px solid #666;
      color: #fff;
    }
    
    #execute-search {
      width: 100%;
      padding: 8px;
      background: #1976D2;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
    
    .layer-item {
      display: flex;
      align-items: center;
      margin-bottom: 8px;
    }
    
    .layer-item input {
      margin-right: 8px;
    }
    
    .layer-divider {
      height: 1px;
      background: #eee;
      margin: 10px 0;
    }
    
    .dark-mode .layer-divider {
      background: #555;
    }
    
    .layer-content h4 {
      font-size: 14px;
      margin: 10px 0;
    }
    
    .marker-military,
    .marker-infrastructure,
    .marker-hazard,
    .marker-residential {
      border-radius: 50%;
      width: 12px !important;
      height: 12px !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    
    @media (max-width: 768px) {
      .toolbar.expanded {
        width: 100%;
        left: 0;
        bottom: 0;
        top: auto;
        height: 60%;
        border-radius: 15px 15px 0 0;
      }
      
      .toolbar.expanded .enhanced-menu {
        height: 100%;
        display: flex;
        flex-direction: column;
      }
      
      .menu-sections {
        flex: 1;
        overflow-y: auto;
      }
      
      .search-panel,
      .layer-panel {
        width: 90%;
        max-width: 350px;
        left: 50%;
        transform: translateX(-50%);
        right: auto;
      }
    }
    
    /* Toast notification */
    .toast-notification {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background-color: rgba(0, 0, 0, 0.7);
      color: white;
      padding: 10px 20px;
      border-radius: 4px;
      font-size: 14px;
      z-index: 2000;
      opacity: 0;
      transition: opacity 0.3s;
    }
    
    .toast-notification.show {
      opacity: 1;
    }
    
    /* Drawing and measuring controls */
    .leaflet-draw-toolbar a {
      background-color: #fff;
      border-radius: 4px;
      box-shadow: 0 1px 5px rgba(0,0,0,0.4);
    }
    
    .dark-mode .leaflet-draw-toolbar a {
      background-color: #444;
      filter: invert(100%) hue-rotate(180deg) brightness(95%) contrast(90%);
    }
    
    .dark-mode .leaflet-draw-tooltip {
      background-color: #444;
      color: #fff;
      border: 1px solid #777;
    }
    
    /* Fix measure control in dark mode */
    .dark-mode .leaflet-control-measure a,
    .dark-mode .leaflet-control-measure-interaction {
      background-color: #444;
      color: #fff;
    }
    
    .dark-mode .leaflet-control-measure a.start {
      background-color: #6ABF59;
      color: #fff;
    }
    
    .dark-mode .leaflet-control-measure a.start:hover {
      background-color: #7BCA6B;
    }
    
    .button-active {
      background-color: #6ABF59 !important;
    }
    
    /* Fix ruler button active state */
    .toolbar button.active {
      background-color: rgba(0, 0, 0, 0.2);
    }
    
    .dark-mode .toolbar button.active {
      background-color: rgba(255, 255, 255, 0.2);
    }
  `;
  
  document.head.appendChild(style);
});

// Helper function to show toast notifications
function showToast(message, duration = 3000) {
  // Remove any existing toast
  const existingToast = document.querySelector('.toast-notification');
  if (existingToast) {
    document.body.removeChild(existingToast);
  }
  
  // Create new toast
  const toast = document.createElement('div');
  toast.className = 'toast-notification';
  toast.textContent = message;
  document.body.appendChild(toast);
  
  // Show toast (delay for CSS transition)
  setTimeout(() => toast.classList.add('show'), 10);
  
  // Hide and remove toast after duration
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => {
      if (toast.parentNode) {
        document.body.removeChild(toast);
      }
    }, 300); // wait for fade out animation
  }, duration);
}
