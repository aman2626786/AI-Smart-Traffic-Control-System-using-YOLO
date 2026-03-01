// DOM Elements
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const loading = document.getElementById('loading');
const errorMessage = document.getElementById('errorMessage');
const errorText = document.getElementById('errorText');
const resultsSection = document.getElementById('resultsSection');
const uploadAnotherBtn = document.getElementById('uploadAnotherBtn');

// Mode elements
const imageModeBtn = document.getElementById('imageModeBtn');
const videoModeBtn = document.getElementById('videoModeBtn');
const uploadIcon = document.getElementById('uploadIcon');
const uploadTitle = document.getElementById('uploadTitle');
const uploadSubtitle = document.getElementById('uploadSubtitle');

// Result elements
const annotatedImage = document.getElementById('annotatedImage');
const imageResultCard = document.getElementById('imageResultCard');
const videoResultCard = document.getElementById('videoResultCard');
const processedVideo = document.getElementById('processedVideo');
const videoSource = document.getElementById('videoSource');
const downloadVideoBtn = document.getElementById('downloadVideoBtn');
const totalVehicles = document.getElementById('totalVehicles');
const totalLabel = document.getElementById('totalLabel');
const carsCount = document.getElementById('carsCount');
const trucksCount = document.getElementById('trucksCount');
const carsCard = document.getElementById('carsCard');
const trucksCard = document.getElementById('trucksCard');
const avgConfidence = document.getElementById('avgConfidence');
const confidenceLabel = document.getElementById('confidenceLabel');
const trafficLight = document.getElementById('trafficLight');
const lightDuration = document.getElementById('lightDuration');
const decisionReason = document.getElementById('decisionReason');

// Current mode
let currentMode = 'image';
let currentVideoUrl = null;

// Event Listeners
uploadBtn.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);
uploadAnotherBtn.addEventListener('click', resetUI);
imageModeBtn.addEventListener('click', () => switchMode('image'));
videoModeBtn.addEventListener('click', () => switchMode('video'));
downloadVideoBtn.addEventListener('click', downloadVideo);

// Drag and drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
});

uploadArea.addEventListener('click', (e) => {
    if (e.target !== uploadBtn) {
        fileInput.click();
    }
});

function switchMode(mode) {
    currentMode = mode;
    
    if (mode === 'image') {
        imageModeBtn.classList.add('active');
        videoModeBtn.classList.remove('active');
        fileInput.accept = 'image/jpeg,image/png';
        uploadIcon.textContent = '📁';
        uploadTitle.textContent = 'Drop your image here or click to browse';
        uploadSubtitle.textContent = 'Supports JPEG and PNG (max 10MB)';
        uploadBtn.textContent = 'Choose Image';
    } else {
        videoModeBtn.classList.add('active');
        imageModeBtn.classList.remove('active');
        fileInput.accept = 'video/mp4,video/avi,video/mov,video/mkv';
        uploadIcon.textContent = '🎥';
        uploadTitle.textContent = 'Drop your video here or click to browse';
        uploadSubtitle.textContent = 'Supports MP4, AVI, MOV, MKV (max 100MB)';
        uploadBtn.textContent = 'Choose Video';
    }
    
    resetUI();
}

function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        handleFile(file);
    }
}

async function handleFile(file) {
    if (currentMode === 'image') {
        await handleImageUpload(file);
    } else {
        await handleVideoUpload(file);
    }
}

async function handleImageUpload(file) {
    const validTypes = ['image/jpeg', 'image/png'];
    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please upload a JPEG or PNG image.');
        return;
    }

    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('File too large. Maximum size is 10MB.');
        return;
    }

    hideError();
    resultsSection.style.display = 'none';
    loading.style.display = 'block';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/detect', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Detection failed');
        }

        const data = await response.json();
        loading.style.display = 'none';
        displayImageResults(data);

    } catch (error) {
        loading.style.display = 'none';
        showError(error.message || 'An error occurred while processing the image.');
    }
}

async function handleVideoUpload(file) {
    const validTypes = ['video/mp4', 'video/avi', 'video/x-msvideo', 'video/quicktime', 'video/x-matroska'];
    if (!validTypes.includes(file.type)) {
        showError('Invalid file type. Please upload MP4, AVI, MOV, or MKV video.');
        return;
    }

    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
        showError('Video too large. Maximum size is 100MB.');
        return;
    }

    hideError();
    resultsSection.style.display = 'none';
    loading.style.display = 'block';
    loading.querySelector('p').textContent = 'Processing video... This may take a few minutes.';

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/detect-video', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Video processing failed');
        }

        const data = await response.json();
        loading.style.display = 'none';
        loading.querySelector('p').textContent = 'Analyzing image...';
        displayVideoResults(data);

    } catch (error) {
        loading.style.display = 'none';
        loading.querySelector('p').textContent = 'Analyzing image...';
        showError(error.message || 'An error occurred while processing the video.');
    }
}

function displayImageResults(data) {
    imageResultCard.style.display = 'block';
    videoResultCard.style.display = 'none';
    carsCard.style.display = 'flex';
    trucksCard.style.display = 'flex';
    
    annotatedImage.src = data.annotated_image;
    totalVehicles.textContent = data.total_vehicles;
    totalLabel.textContent = 'Total Vehicles';
    carsCount.textContent = data.cars;
    trucksCount.textContent = data.trucks;
    avgConfidence.textContent = `${Math.round(data.average_confidence * 100)}%`;
    confidenceLabel.textContent = 'Avg Confidence';

    const decision = data.traffic_decision;
    lightDuration.textContent = `${capitalizeFirst(decision.light)} - ${decision.duration} seconds`;
    decisionReason.textContent = decision.reason;

    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function displayVideoResults(data) {
    imageResultCard.style.display = 'none';
    videoResultCard.style.display = 'block';
    carsCard.style.display = 'none';
    trucksCard.style.display = 'none';
    
    currentVideoUrl = data.download_url;
    videoSource.src = currentVideoUrl;
    processedVideo.load();
    
    totalVehicles.textContent = data.average_vehicle_count;
    totalLabel.textContent = 'Avg Vehicles';
    avgConfidence.textContent = `${data.total_frames} frames`;
    confidenceLabel.textContent = 'Total Frames';

    const decision = data.traffic_decision;
    lightDuration.textContent = `${capitalizeFirst(decision.light)} - ${decision.duration} seconds`;
    decisionReason.textContent = decision.reason;

    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function downloadVideo() {
    if (currentVideoUrl) {
        window.open(currentVideoUrl, '_blank');
    }
}

function showError(message) {
    errorText.textContent = message;
    errorMessage.style.display = 'flex';
}

function hideError() {
    errorMessage.style.display = 'none';
}

function resetUI() {
    fileInput.value = '';
    resultsSection.style.display = 'none';
    imageResultCard.style.display = 'block';
    videoResultCard.style.display = 'none';
    carsCard.style.display = 'flex';
    trucksCard.style.display = 'flex';
    hideError();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function capitalizeFirst(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}
