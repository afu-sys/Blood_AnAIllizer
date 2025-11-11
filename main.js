// Global variables
let currentUser = null;
let uploadedFiles = [];
let analysisResults = [];
let timelineData = [];

const API_BASE_URL = 'https://bloodanaillizer-production.up.railway.app/api';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeAnimations();
    initializeParticles();
    initializeTypedText();
    initializeFileUpload();
    initializeScrollAnimations();
    loadUserData();
});

// Initialize animations
function initializeAnimations() {
    // Animate feature cards on scroll
    const featureCards = document.querySelectorAll('.feature-card');
    featureCards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
        card.classList.add('fade-in-up');
    });
}

// Initialize floating particles
function initializeParticles() {
    const container = document.getElementById('particles-container');
    const particleCount = 50;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = Math.random() * 100 + '%';
        particle.style.animationDelay = Math.random() * 8 + 's';
        particle.style.animationDuration = (Math.random() * 4 + 6) + 's';
        container.appendChild(particle);
    }
}

// Initialize typed text animation
function initializeTypedText() {
    const typed = new Typed('#typed-text', {
        strings: [
            'MediLab Analytics',
            'AI-Powered Insights',
            'Health Intelligence',
            'Clinical Analysis'
        ],
        typeSpeed: 100,
        backSpeed: 50,
        backDelay: 2000,
        loop: true,
        showCursor: true,
        cursorChar: '|'
    });
}

// Initialize file upload functionality
function initializeFileUpload() {
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('border-blue-400', 'bg-blue-50');
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('border-blue-400', 'bg-blue-50');
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('border-blue-400', 'bg-blue-50');
        handleFiles(e.dataTransfer.files);
    });
    
    fileInput.addEventListener('change', (e) => {
        handleFiles(e.target.files);
    });
}

// Handle file uploads
function handleFiles(files) {
    const uploadedFilesContainer = document.getElementById('uploaded-files');
    
    Array.from(files).forEach(file => {
        if (file.type === 'application/pdf') {
            uploadedFiles.push(file);
            
            const fileElement = document.createElement('div');
            fileElement.className = 'flex items-center justify-between p-3 bg-gray-100 rounded-lg';
            fileElement.innerHTML = `
                <div class="flex items-center space-x-3">
                    <i class="fas fa-file-pdf text-red-500"></i>
                    <span class="text-sm font-medium">${file.name}</span>
                    <span class="text-xs text-gray-500">(${(file.size / 1024 / 1024).toFixed(2)} MB)</span>
                </div>
                <button onclick="removeFile(${uploadedFiles.length - 1})" class="text-red-500 hover:text-red-700">
                    <i class="fas fa-times"></i>
                </button>
            `;
            
            uploadedFilesContainer.appendChild(fileElement);
        }
    });
}

// Remove uploaded file
function removeFile(index) {
    uploadedFiles.splice(index, 1);
    refreshUploadedFiles();
}

// Refresh uploaded files display
function refreshUploadedFiles() {
    const container = document.getElementById('uploaded-files');
    container.innerHTML = '';
    
    uploadedFiles.forEach((file, index) => {
        const fileElement = document.createElement('div');
        fileElement.className = 'flex items-center justify-between p-3 bg-gray-100 rounded-lg';
        fileElement.innerHTML = `
            <div class="flex items-center space-x-3">
                <i class="fas fa-file-pdf text-red-500"></i>
                <span class="text-sm font-medium">${file.name}</span>
                <span class="text-xs text-gray-500">(${(file.size / 1024 / 1024).toFixed(2)} MB)</span>
            </div>
            <button onclick="removeFile(${index})" class="text-red-500 hover:text-red-700">
                <i class="fas fa-times"></i>
            </button>
        `;
        container.appendChild(fileElement);
    });
}

// Process reports
async function processReports() {
    if (uploadedFiles.length === 0) {
        showNotification('Please upload at least one PDF file', 'warning');
        return;
    }
    
    const reportDate = document.getElementById('report-date').value;
    if (!reportDate) {
        showNotification('Please select a report date', 'warning');
        return;
    }
    
    showLoading(true);
    
    try {
        // 2. Crear FormData para enviar los archivos
        const formData = new FormData();
        uploadedFiles.forEach(file => {
            formData.append('files', file);
        });
        formData.append('date', document.getElementById('report-date').value);

        // 3. Llamar a tu API real
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Error from API');
        }

        const data = await response.json();

        // 4. Usar los resultados de la API, no los mocks
        analysisResults = data.results;
        displayResults(data.results);
        updateTimeline(data.results, data.report_date);

        showNotification('Reports analyzed successfully!', 'success');

    } catch (error) {
        console.error('Error processing reports:', error);
        showNotification('Error processing reports. Please try again.', 'error');
    } finally {
        showLoading(false);
    }
}


// Generate mock analysis results
function generateMockResults() {
    const biomarkers = [
        { test: 'Glucose', value: 95, unit: 'mg/dL', refLow: 70, refHigh: 100, status: 'Normal' },
        { test: 'Cholesterol Total', value: 185, unit: 'mg/dL', refLow: 0, refHigh: 200, status: 'Normal' },
        { test: 'Hemoglobin', value: 14.2, unit: 'g/dL', refLow: 12, refHigh: 16, status: 'Normal' },
        { test: 'Platelets', value: 275, unit: 'K/uL', refLow: 150, refHigh: 400, status: 'Normal' },
        { test: 'White Blood Cells', value: 7.8, unit: 'K/uL', refLow: 4.5, refHigh: 11, status: 'Normal' },
        { test: 'Creatinine', value: 0.9, unit: 'mg/dL', refLow: 0.6, refHigh: 1.2, status: 'Normal' },
        { test: 'HDL Cholesterol', value: 52, unit: 'mg/dL', refLow: 40, refHigh: 60, status: 'Near' },
        { test: 'LDL Cholesterol', value: 115, unit: 'mg/dL', refLow: 0, refHigh: 100, status: 'High' }
    ];
    
    return biomarkers;
}

// Display analysis results
function displayResults(results) {
    const container = document.getElementById('results-container');
    
    const summary = calculateSummary(results);
    
    container.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div class="bg-green-100 border-l-4 border-green-500 p-4 rounded">
                <div class="text-2xl font-bold text-green-700">${summary.normal}</div>
                <div class="text-sm text-green-600">Normal</div>
            </div>
            <div class="bg-yellow-100 border-l-4 border-yellow-500 p-4 rounded">
                <div class="text-2xl font-bold text-yellow-700">${summary.near}</div>
                <div class="text-sm text-yellow-600">Borderline</div>
            </div>
            <div class="bg-red-100 border-l-4 border-red-500 p-4 rounded">
                <div class="text-2xl font-bold text-red-700">${summary.abnormal}</div>
                <div class="text-sm text-red-600">Abnormal</div>
            </div>
            <div class="bg-blue-100 border-l-4 border-blue-500 p-4 rounded">
                <div class="text-2xl font-bold text-blue-700">${summary.total}</div>
                <div class="text-sm text-blue-600">Total Tests</div>
            </div>
        </div>
        
        <div class="bg-white rounded-lg shadow overflow-hidden">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Test</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Value</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Reference Range</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                    ${results.map(result => `
                        <tr class="hover:bg-gray-50">
                            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${result.test}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${result.value} ${result.unit}</td>
                            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${result.refLow} - ${result.refHigh}</td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${getStatusColor(result.status)}">
                                    ${result.status}
                                </span>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
        
        <div class="mt-6 flex space-x-4">
            <button onclick="generatePDF('patient')" class="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                <i class="fas fa-download mr-2"></i>
                Download Patient Report
            </button>
            <button onclick="generatePDF('doctor')" class="flex-1 bg-green-600 text-white py-3 px-4 rounded-lg font-semibold hover:bg-green-700 transition-colors">
                <i class="fas fa-download mr-2"></i>
                Download Doctor Report
            </button>
        </div>
    `;
}

// Calculate summary statistics
function calculateSummary(results) {
    const summary = {
        normal: results.filter(r => r.status === 'Normal').length,
        near: results.filter(r => r.status === 'Near').length,
        abnormal: results.filter(r => r.status === 'Low' || r.status === 'High').length,
        total: results.length
    };
    return summary;
}

// Get status color class
function getStatusColor(status) {
    switch (status) {
        case 'Normal':
            return 'bg-green-100 text-green-800';
        case 'Near':
            return 'bg-yellow-100 text-yellow-800';
        case 'Low':
        case 'High':
            return 'bg-red-100 text-red-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}

// Update timeline
function updateTimeline(results, date) {
    const timelineItem = {
        date: date,
        results: results,
        summary: calculateSummary(results)
    };
    
    timelineData.push(timelineItem);
    timelineData.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    displayTimeline();
    updateChart();
}

// Display timeline
function displayTimeline() {
    const container = document.getElementById('timeline-items');
    
    container.innerHTML = timelineData.map((item, index) => `
        <div class="timeline-item flex items-center space-x-4 p-6 bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
            <div class="flex-shrink-0 w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                ${index + 1}
            </div>
            <div class="flex-1">
                <div class="flex items-center justify-between mb-2">
                    <h4 class="text-lg font-semibold text-gray-800">${new Date(item.date).toLocaleDateString()}</h4>
                    <span class="text-sm text-gray-500">${item.results.length} tests</span>
                </div>
                <div class="flex space-x-4 text-sm">
                    <span class="text-green-600">Normal: ${item.summary.normal}</span>
                    <span class="text-yellow-600">Borderline: ${item.summary.near}</span>
                    <span class="text-red-600">Abnormal: ${item.summary.abnormal}</span>
                </div>
            </div>
            <button onclick="viewTimelineDetails(${index})" class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                View Details
            </button>
        </div>
    `).join('');
    
    // Animate timeline items
    setTimeout(() => {
        document.querySelectorAll('.timeline-item').forEach(item => {
            item.classList.add('visible');
        });
    }, 100);
}

// Update chart
function updateChart() {
    const canvas = document.getElementById('timeline-chart');
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    if (timelineData.length < 2) return;
    
    // Simple line chart implementation
    const padding = 40;
    const width = canvas.width - 2 * padding;
    const height = canvas.height - 2 * padding;
    
    // Draw axes
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, canvas.height - padding);
    ctx.lineTo(canvas.width - padding, canvas.height - padding);
    ctx.stroke();
    
    // Draw data points
    const selectedBiomarker = document.getElementById('biomarker-select').value;
    const dataPoints = timelineData.map(item => {
        const biomarker = item.results.find(r => r.test.toLowerCase().includes(selectedBiomarker));
        return biomarker ? biomarker.value : null;
    }).filter(val => val !== null);
    
    if (dataPoints.length > 1) {
        const minVal = Math.min(...dataPoints);
        const maxVal = Math.max(...dataPoints);
        const range = maxVal - minVal || 1;
        
        ctx.strokeStyle = '#3b82f6';
        ctx.lineWidth = 3;
        ctx.beginPath();
        
        dataPoints.forEach((value, index) => {
            const x = padding + (index / (dataPoints.length - 1)) * width;
            const y = canvas.height - padding - ((value - minVal) / range) * height;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
            
            // Draw point
            ctx.fillStyle = '#3b82f6';
            ctx.beginPath();
            ctx.arc(x, y, 5, 0, 2 * Math.PI);
            ctx.fill();
        });
        
        ctx.stroke();
    }
}

// View timeline details
function viewTimelineDetails(index) {
    const item = timelineData[index];
    displayResults(item.results);
    document.getElementById('report-date').value = item.date;
    scrollToSection('dashboard');
}

// Generate PDF report
async function generatePDF(type) {
    showNotification(`${type.charAt(0).toUpperCase() + type.slice(1)} report generated successfully!`, 'success');
}

// Login functionality
function login() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        showNotification('Please enter username and password', 'warning');
        return;
    }
    
    // Simulate login
    currentUser = { username, name: username };
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    
    closeLoginModal();
    updateUserInterface();
    showNotification('Login successful!', 'success');
}

// Register functionality
function register() {
    const name = document.getElementById('reg-name').value;
    const email = document.getElementById('reg-email').value;
    const username = document.getElementById('reg-username').value;
    const password = document.getElementById('reg-password').value;
    
    if (!name || !email || !username || !password) {
        showNotification('Please fill in all fields', 'warning');
        return;
    }
    
    // Simulate registration
    currentUser = { username, name, email };
    localStorage.setItem('currentUser', JSON.stringify(currentUser));
    
    closeLoginModal();
    updateUserInterface();
    showNotification('Registration successful!', 'success');
}

// Update user interface
function updateUserInterface() {
    const navButton = document.querySelector('nav button');
    if (currentUser) {
        navButton.innerHTML = `<i class="fas fa-user mr-2"></i>${currentUser.name}`;
        navButton.onclick = logout;
    } else {
        navButton.innerHTML = 'Login';
        navButton.onclick = openLoginModal;
    }
}

// Logout functionality
function logout() {
    currentUser = null;
    localStorage.removeItem('currentUser');
    updateUserInterface();
    showNotification('Logged out successfully', 'success');
}

// Load user data
function loadUserData() {
    const savedUser = localStorage.getItem('currentUser');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        updateUserInterface();
    }
    
    // Load timeline data
    const savedTimeline = localStorage.getItem('timelineData');
    if (savedTimeline) {
        timelineData = JSON.parse(savedTimeline);
        displayTimeline();
        updateChart();
    }
}

// Save timeline data
function saveTimelineData() {
    localStorage.setItem('timelineData', JSON.stringify(timelineData));
}

// Modal functions
function openLoginModal() {
    document.getElementById('login-modal').classList.add('active');
}

function closeLoginModal() {
    document.getElementById('login-modal').classList.remove('active');
}

function showRegisterForm() {
    document.getElementById('login-form').classList.add('hidden');
    document.getElementById('register-form').classList.remove('hidden');
}

function showLoginForm() {
    document.getElementById('register-form').classList.add('hidden');
    document.getElementById('login-form').classList.remove('hidden');
}

// Utility functions
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    section.scrollIntoView({ behavior: 'smooth' });
}

function showLoading(show) {
    const indicator = document.getElementById('loading-indicator');
    if (show) {
        indicator.classList.remove('hidden');
    } else {
        indicator.classList.add('hidden');
    }
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `fixed top-20 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm transform transition-all duration-300 translate-x-full`;
    
    // Set notification style based on type
    switch (type) {
        case 'success':
            notification.classList.add('bg-green-500', 'text-white');
            break;
        case 'warning':
            notification.classList.add('bg-yellow-500', 'text-white');
            break;
        case 'error':
            notification.classList.add('bg-red-500', 'text-white');
            break;
        default:
            notification.classList.add('bg-blue-500', 'text-white');
    }
    
    notification.innerHTML = `
        <div class="flex items-center space-x-3">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.classList.remove('translate-x-full');
    }, 100);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.add('translate-x-full');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

function getNotificationIcon(type) {
    switch (type) {
        case 'success':
            return 'fa-check-circle';
        case 'warning':
            return 'fa-exclamation-triangle';
        case 'error':
            return 'fa-exclamation-circle';
        default:
            return 'fa-info-circle';
    }
}

// Initialize scroll animations
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    
    // Observe timeline items
    document.querySelectorAll('.timeline-item').forEach(item => {
        observer.observe(item);
    });
    
    // Observe feature cards
    document.querySelectorAll('.feature-card').forEach(card => {
        observer.observe(card);
    });
}

// Biomarker select change handler
document.addEventListener('DOMContentLoaded', function() {
    const biomarkerSelect = document.getElementById('biomarker-select');
    if (biomarkerSelect) {
        biomarkerSelect.addEventListener('change', updateChart);
    }
});

// Close modal when clicking outside
document.addEventListener('click', function(e) {
    const modal = document.getElementById('login-modal');
    if (e.target === modal) {
        closeLoginModal();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeLoginModal();
    }
});