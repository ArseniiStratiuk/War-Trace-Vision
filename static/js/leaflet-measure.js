(function (factory) {
  if (typeof define === 'function' && define.amd) {
    // AMD
    define(['leaflet'], factory);
  } else if (typeof module !== 'undefined') {
    // Node/CommonJS
    module.exports = factory(require('leaflet'));
  } else {
    // Browser globals
    if (typeof window.L === 'undefined') {
      throw new Error('Leaflet must be loaded first');
    }
    factory(window.L);
  }
}(function (L) {
  // Import DOM utilities simplified for our use case
  const dom = {
    selectOne: function(selector, el) {
      if (!el) {
        el = document;
      }
      return el.querySelector(selector);
    },
    selectAll: function(selector, el) {
      if (!el) {
        el = document;
      }
      return Array.prototype.slice.call(el.querySelectorAll(selector));
    },
    hide: function(el) {
      if (el) {
        el.setAttribute('style', 'display:none;');
        return el;
      }
    },
    show: function(el) {
      if (el) {
        el.removeAttribute('style');
        return el;
      }
    }
  };

  const MeasureControl = L.Control.extend({
    options: {
      position: 'topleft',
      primaryLengthUnit: 'kilometers',
      secondaryLengthUnit: 'meters',
      primaryAreaUnit: 'sqkilometers',
      secondaryAreaUnit: 'hectares',
      activeColor: '#3388ff',
      completedColor: '#ff7800',
      localization: {
        startPrompt: 'Click to start measuring',
        continuePrompt: 'Click to continue measuring',
        clearPrompt: 'Click to clear measurement',
        measureArea: 'Measure area',
        measureLine: 'Measure distance',
        primaryLengthUnit: 'km',
        secondaryLengthUnit: 'm',
        primaryAreaUnit: 'km²',
        secondaryAreaUnit: 'ha'
      },
      captureZIndex: 10000
    },

    initialize: function (options) {
      L.Util.setOptions(this, options);
      this._layer = null;
      this._isActive = false;
      this._isAreaMode = false;
      this._points = [];
      this._tooltips = [];
      this._currentTooltip = null;
      this._resultTooltip = null;
      this._measureLayer = null;
      this._measurePath = null;
    },

    onAdd: function (map) {
      this._map = map;
      this._container = L.DomUtil.create('div', 'leaflet-control-measure');
      
      // Create measure button
      this._measureButton = L.DomUtil.create('a', '', this._container);
      this._measureButton.href = '#';
      this._measureButton.title = this.options.localization.startPrompt;
      this._measureButton.innerHTML = '&#8212;';
      
      // Create measure dropdown
      this._createDropdown();

      L.DomEvent
        .on(this._measureButton, 'click', L.DomEvent.stopPropagation)
        .on(this._measureButton, 'click', L.DomEvent.preventDefault)
        .on(this._measureButton, 'click', this._toggleDropdown, this);

      L.DomEvent
        .on(document, 'mousedown', this._onDocumentMouseDown, this);

      return this._container;
    },
    
    _createDropdown: function() {
      this._dropdown = L.DomUtil.create('div', 'leaflet-control-measure-dropdown', this._container);
      dom.hide(this._dropdown);
      
      // Line measuring option
      this._lineOption = L.DomUtil.create('a', 'leaflet-control-measure-option', this._dropdown);
      this._lineOption.href = '#';
      this._lineOption.innerHTML = this.options.localization.measureLine;
      
      // Area measuring option
      this._areaOption = L.DomUtil.create('a', 'leaflet-control-measure-option', this._dropdown);
      this._areaOption.href = '#';
      this._areaOption.innerHTML = this.options.localization.measureArea;
      
      L.DomEvent
        .on(this._lineOption, 'click', L.DomEvent.stopPropagation)
        .on(this._lineOption, 'click', L.DomEvent.preventDefault)
        .on(this._lineOption, 'click', this._startLineMeasurement, this);
      
      L.DomEvent
        .on(this._areaOption, 'click', L.DomEvent.stopPropagation)
        .on(this._areaOption, 'click', L.DomEvent.preventDefault)
        .on(this._areaOption, 'click', this._startAreaMeasurement, this);
    },
    
    _toggleDropdown: function() {
      if (this._isActive) {
        this._stopMeasurement();
      } else {
        if (dom.selectOne('.leaflet-control-measure-dropdown', this._container).style.display === 'none') {
          dom.show(this._dropdown);
        } else {
          dom.hide(this._dropdown);
        }
      }
    },
    
    _onDocumentMouseDown: function(e) {
      if (!this._container.contains(e.target)) {
        dom.hide(this._dropdown);
      }
    },
    
    _startLineMeasurement: function() {
      this._isAreaMode = false;
      this._startMeasurement();
      dom.hide(this._dropdown);
    },
    
    _startAreaMeasurement: function() {
      this._isAreaMode = true;
      this._startMeasurement();
      dom.hide(this._dropdown);
    },
    
    _startMeasurement: function() {
      this._isActive = true;
      this._points = [];
      this._clearMeasurement();
      
      // Create measurement layer
      this._measureLayer = L.layerGroup().addTo(this._map);
      
      // Update button appearance
      L.DomUtil.addClass(this._measureButton, 'start');
      this._measureButton.innerHTML = '&#10006;';
      this._measureButton.title = this.options.localization.clearPrompt;
      
      // Add map listeners
      this._map.on('click', this._onMapClick, this);
      this._map.on('mousemove', this._onMapMouseMove, this);
      
      // Create current tooltip
      this._createTooltip();
    },
    
    _stopMeasurement: function() {
      this._isActive = false;
      
      // Remove button appearance
      L.DomUtil.removeClass(this._measureButton, 'start');
      this._measureButton.innerHTML = '&#8212;';
      this._measureButton.title = this.options.localization.startPrompt;
      
      // Remove listeners
      this._map.off('click', this._onMapClick, this);
      this._map.off('mousemove', this._onMapMouseMove, this);
      
      // Clear measurements
      this._clearMeasurement();
    },
    
    _clearMeasurement: function() {
      if (this._measureLayer) {
        this._measureLayer.clearLayers();
      }
      
      if (this._tooltips.length) {
        this._tooltips.forEach(tooltip => {
          this._map.removeLayer(tooltip);
        });
        this._tooltips = [];
      }
      
      if (this._currentTooltip) {
        this._map.removeLayer(this._currentTooltip);
        this._currentTooltip = null;
      }
      
      if (this._resultTooltip) {
        this._map.removeLayer(this._resultTooltip);
        this._resultTooltip = null;
      }
      
      this._points = [];
      this._measurePath = null;
    },
    
    _createTooltip: function(position) {
      const tooltip = L.marker(position || [0, 0], {
        icon: L.divIcon({
          className: 'leaflet-measure-tooltip',
          iconSize: [0, 0],
          iconAnchor: [0, 0]
        }),
        interactive: false,
        zIndexOffset: this.options.captureZIndex
      });
      
      if (position) {
        tooltip.addTo(this._map);
      }
      
      return tooltip;
    },
    
    _onMapClick: function(e) {
      const latlng = e.latlng;
      this._points.push(latlng);
      
      // Add point marker
      L.circleMarker(latlng, {
        color: this.options.activeColor,
        radius: 4,
        fillOpacity: 0.7,
        className: this._points.length === 1 ? 'leaflet-measure-point-first' : 'leaflet-measure-point'
      }).addTo(this._measureLayer);
      
      if (this._points.length === 1) {
        // First point
        this._updateTooltip(latlng, this.options.localization.continuePrompt);
      } else {
        // Drawing segment
        const prevPoint = this._points[this._points.length - 2];
        const line = L.polyline([prevPoint, latlng], {
          color: this.options.activeColor,
          weight: 2,
          className: 'leaflet-measure-path'
        }).addTo(this._measureLayer);
        
        // If we're measuring areas and have at least 3 points, draw polygon
        if (this._isAreaMode && this._points.length >= 3) {
          if (this._polygon) {
            this._measureLayer.removeLayer(this._polygon);
          }
          
          this._polygon = L.polygon(this._points, {
            color: this.options.activeColor,
            weight: 2,
            fillOpacity: 0.2,
            className: 'leaflet-measure-polygon'
          }).addTo(this._measureLayer);
          
          // Show area
          this._updateResult();
        } else if (!this._isAreaMode) {
          // Update distance for line
          this._updateResult();
        }
      }
    },
    
    _onMapMouseMove: function(e) {
      const latlng = e.latlng;
      
      if (this._points.length > 0) {
        // Show dynamic measuring line
        const points = [...this._points, latlng];
        
        if (this._tempLine) {
          this._measureLayer.removeLayer(this._tempLine);
        }
        
        if (this._isAreaMode && points.length >= 3) {
          // For area, show polygon
          if (this._tempPolygon) {
            this._measureLayer.removeLayer(this._tempPolygon);
          }
          
          this._tempPolygon = L.polygon(points, {
            color: this.options.activeColor,
            weight: 1,
            dashArray: '5,5',
            fillOpacity: 0.1,
            className: 'leaflet-measure-temp-polygon'
          }).addTo(this._measureLayer);
          
          // And last segment
          this._tempLine = L.polyline([this._points[this._points.length - 1], latlng], {
            color: this.options.activeColor,
            weight: 1,
            dashArray: '5,5',
            className: 'leaflet-measure-temp-path'
          }).addTo(this._measureLayer);
        } else {
          // For line, show line segment
          this._tempLine = L.polyline([this._points[this._points.length - 1], latlng], {
            color: this.options.activeColor,
            weight: 1,
            dashArray: '5,5',
            className: 'leaflet-measure-temp-path'
          }).addTo(this._measureLayer);
        }
        
        // Update tooltip position
        if (this._currentTooltip) {
          this._currentTooltip.setLatLng(latlng);
        }
      }
    },
    
    _updateTooltip: function(position, text) {
      if (this._currentTooltip) {
        this._map.removeLayer(this._currentTooltip);
      }
      
      this._currentTooltip = this._createTooltip(position);
      this._currentTooltip.getElement().innerHTML = text;
    },
    
    _updateResult: function() {
      let result = '';
      let position;
      
      if (this._isAreaMode && this._points.length >= 3) {
        // Calculate area
        const area = this._calculateArea(this._points);
        result = this._formatArea(area);
        position = this._getPolygonCenter(this._points);
      } else if (!this._isAreaMode && this._points.length >= 2) {
        // Calculate length
        const length = this._calculateLength(this._points);
        result = this._formatLength(length);
        position = this._points[this._points.length - 1];
      } else {
        return;
      }
      
      if (this._resultTooltip) {
        this._map.removeLayer(this._resultTooltip);
      }
      
      this._resultTooltip = this._createTooltip(position);
      this._resultTooltip.getElement().innerHTML = '<span class="leaflet-measure-result">' + result + '</span>';
      this._tooltips.push(this._resultTooltip);
    },
    
    _calculateLength: function(points) {
      let length = 0;
      for (let i = 1; i < points.length; i++) {
        length += points[i-1].distanceTo(points[i]);
      }
      return length;
    },
    
    _calculateArea: function(points) {
      return L.GeometryUtil.geodesicArea(points);
    },
    
    _getPolygonCenter: function(points) {
      let x = 0, y = 0;
      for (const point of points) {
        x += point.lat;
        y += point.lng;
      }
      return L.latLng(x / points.length, y / points.length);
    },
    
    _formatLength: function(length) {
      let formattedLength;
      
      if (length >= 1000) {
        // Primary unit: kilometers
        formattedLength = (length / 1000).toFixed(2) + ' ' + this.options.localization.primaryLengthUnit;
        
        // Add secondary unit
        formattedLength += ' (' + Math.round(length) + ' ' + this.options.localization.secondaryLengthUnit + ')';
      } else {
        // Use meters
        formattedLength = Math.round(length) + ' ' + this.options.localization.secondaryLengthUnit;
      }
      
      return formattedLength;
    },
    
    _formatArea: function(area) {
      let formattedArea;
      
      if (area >= 1000000) {
        // Primary unit: sq kilometers
        formattedArea = (area / 1000000).toFixed(2) + ' ' + this.options.localization.primaryAreaUnit;
        
        // Add secondary unit (hectares)
        formattedArea += ' (' + (area / 10000).toFixed(2) + ' ' + this.options.localization.secondaryAreaUnit + ')';
      } else {
        // Use sq meters or hectares depending on size
        if (area >= 10000) {
          formattedArea = (area / 10000).toFixed(2) + ' ' + this.options.localization.secondaryAreaUnit;
        } else {
          formattedArea = Math.round(area) + ' m²';
        }
      }
      
      return formattedArea;
    }
  });

  // Helper for geodesic calculations
  L.GeometryUtil = L.extend(L.GeometryUtil || {}, {
    geodesicArea: function(latLngs) {
      let area = 0,
          len = latLngs.length,
          d2r = Math.PI / 180;
          
      if (len < 3) {
        return area;
      }
      
      for (let i = 0; i < len; i++) {
        const p1 = latLngs[i],
              p2 = latLngs[(i + 1) % len];
              
        area += ((p2.lng - p1.lng) * d2r) * (2 + Math.sin(p1.lat * d2r) + Math.sin(p2.lat * d2r));
      }
      
      area = area * 6378137 * 6378137 / 2.0;
      return Math.abs(area);
    }
  });

  L.control.measure = function(options) {
    return new MeasureControl(options);
  };

  return L;
}));
