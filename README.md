# War Trace Vision

<p align="center">
  <img src="logo.jpg" alt="War Trace Vision Logo" width="200"/>
</p>

<p align="center">
  <a href="https://war-trace-vision.onrender.com/">
    <img src="https://img.shields.io/badge/Render-deployed-brightgreen?logo=render" alt="Deployment Status">
  </a>
  <a href="https://opensource.org/licenses/MIT">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  </a>
</p>

**War Trace Vision** is an online platform for documenting war-related destruction using both AI-powered analysis and user collaboration. The system processes uploaded by users imagery to detect people, vehicles, weapons and other objects of interest with deep learning (YOLO) and OpenCV. Users can manually describe, and comment detected areas, ensuring comprehensive documentation. Built with Django and an interactive Leaflet map, the project aims to support humanitarian missions, post-war reconstruction, and historical records by combining Computer Vision with community-driven verification.

**Live Deployment:** [war-trace-vision.onrender.com](https://war-trace-vision.onrender.com/)

**Key Technologies:** Python, Django, JavaScript, Leaflet.js, HTML, CSS, YOLO, OpenCV, SQLite

## User Journey & Platform Usage

### Account Management

#### Registration & Login
1. From the main map screen, access the side menu by clicking the hamburger icon in the top left
2. Navigate to Account section and click "Реєстрація" (Registration)
3. Fill in the registration form with your details:
   - Username
   - Email
   - First Name
   - Last Name
   - Password
4. Select your user category (volunteer, soldier)
5. After registration, return to the side menu and select "Вхід" (Login) to access your account

#### Personal Profile
- View your profile by clicking "Особистий кабінет" (Personal Account) in the side menu
- From your profile page, you can:
  - View your contact information
  - Edit profile settings via the gear icon
  - View your markers and soldier requests
  - Create new soldier requests (if applicable)
  - Log out of your account

### Interactive Map Navigation

#### Main Interface Controls
- **Pan**: Click and drag anywhere on the map
- **Zoom**: Use the + and - buttons on the right side or your mouse wheel
- **Menu**: Access site-wide navigation via the hamburger icon (≡) in the top left
- **Current Status**: View connection status in the top header bar

#### Map Tools (Left Toolbar)
- **Add Marker** (pin icon): Create a new marker at a specific location
- **Draw** (pencil icon): Draw shapes and areas on the map
- **Measure** (ruler icon): Calculate distances and areas
- **Search** (magnifying glass): Find specific locations by name
- **Filter** (funnel icon): Filter markers by various criteria
- **Layers** (stacked layers icon): Switch between map types and overlays

#### Map Settings (Bottom Right)
- **Satellite View**: Toggle between standard map and satellite imagery
- **Dark Mode**: Switch between light and dark themes

### Working with Markers

#### Adding Markers
1. Click the marker (pin) icon in the left toolbar
2. Select the marker location either by:
   - Clicking directly on the map
   - Entering coordinates manually in the form
   - Using your location
3. Complete the marker form with:
   - Title and detailed description
   - Date of observation
   - Source information
   - Category selection (military, infrastructure, hazard, residential)
   - Supporting media (photos only)
4. Choose visibility settings (public or private)
5. Toggle AI analysis options if desired
6. Click "Зберегти" (Save) to create the marker

#### Marker Details
When viewing a marker's details, you'll see:
- Map location context at the top
- Title and verification status
- Description and category information
- Location coordinates and observation date
- Media gallery with uploaded photos/videos
- AI analysis results (if available)
- Community comments and voting section

You can also:
- Edit the marker (if you have permission)
- Share the marker via URL
- Report inaccurate information
- Request AI analysis (if you have permission)

#### Media Management
- Add photos and videos to markers from the detail page
- View media in fullscreen by clicking thumbnails
- Navigate between multiple media files with arrow buttons
- See AI detection overlays on analyzed images

### AI Analysis Features

#### Requesting Analysis
1. From a marker's detail page, click "Запустити ШІ аналіз" (Run AI Analysis)
2. Select desired detection types:
   - COCO Object detection (equipment, vehicles, personnel)
   - Military Object detection (camouflaged soldiers, military vehicles etc.)
   - Other AI options are currently under development
3. Click "Почати обробку" (Start Processing)
4. Monitor the progress bar during processing

#### Viewing Analysis Results
- After processing completes, you'll be redirected to the results page
- The results display:
  - Detection summary statistics
  - Original images with detection overlays
  - Detailed list of detected objects with confidence scores
  - Classification details for each detection

### Community Features

#### Comments System
- Add comments on any marker from the detail page
- View community discussions about the marker
- Upvote helpful comments

#### Verification System
- Qualified experts can verify marker information
- Filter markers based on verification status

### Volunteer Section

#### Request Management
- Create assistance requests from your personal profile page
- View existing requests in your profile's archive section
- Track request status (in progress, completed)

#### Communication
- Send and receive messages related to volunteer requests
- View chat history from the volunteer section

### Mobile Responsiveness
The platform automatically adapts to different screen sizes:
- On smaller screens, the menu expands to full width at the bottom
- Controls are reorganized for touch interaction
- All features remain accessible on mobile devices

## Interface Languages
The platform interface is available in Ukrainian, with certain technical terms and notifications appearing in English.
