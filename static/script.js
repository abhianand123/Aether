const state = {
    platform: null,
    mode: null,
    url: '',
    videoInfo: null,
    selectedQuality: null,
    downloadId: null,
    isDownloading: false
};

function init() {
    initButterflies();
    setupEventListeners();

    // Prevent accidental page refresh/close during download
    window.addEventListener('beforeunload', (e) => {
        if (state.isDownloading) {
            e.preventDefault();
            e.returnValue = ''; // Chrome requires returnValue to be set
        }
    });

    VanillaTilt.init(document.querySelectorAll(".glow-card"), {
        max: 15,
        speed: 400,
        glare: true,
        "max-glare": 0.2,
        scale: 1.05,
        gyroscope: true,
        gyroscopeMinAngleX: -45,
        gyroscopeMaxAngleX: 45,
        gyroscopeMinAngleY: -45,
        gyroscopeMaxAngleY: 45
    });

    VanillaTilt.init(document.querySelectorAll(".quality-option"), {
        max: 10,
        speed: 300,
        scale: 1.05,
        gyroscope: true
    });
}

function initButterflies() {
    const container = document.getElementById('bfyaContainer');
    if (!container) return;

    const main = document.createElement('div');
    main.id = 'bfyaMain';
    container.appendChild(main);

    const colors = ['#8b5cf6', '#06b6d4', '#ec4899', '#a855f7', '#ffffff'];
    const trail = [];

    function createTrailButterfly(x, y) {
        const butterfly = document.createElement('div');
        butterfly.className = 'bfyaButterfly bfyaTrail';

        const size = 30 + Math.random() * 20;
        const color = colors[Math.floor(Math.random() * colors.length)];

        butterfly.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            position: fixed;
            animation: bfyaFadeAway 2s ease-out forwards;
        `;

        butterfly.style.setProperty('--wing-color-1', color);
        butterfly.style.setProperty('--wing-color-2', color);
        butterfly.style.setProperty('--flap-duration', '0.3s');

        document.body.appendChild(butterfly);
        trail.push(butterfly);

        setTimeout(() => {
            butterfly.remove();
            const index = trail.indexOf(butterfly);
            if (index > -1) trail.splice(index, 1);
        }, 2000);
    }

    let lastSpawn = 0;
    document.addEventListener('mousemove', (e) => {
        const now = Date.now();
        if (now - lastSpawn > 100) {
            createTrailButterfly(e.clientX, e.clientY);
            lastSpawn = now;
        }
    });

    document.addEventListener('touchmove', (e) => {
        if (e.touches.length > 0) {
            const touch = e.touches[0];
            const now = Date.now();
            if (now - lastSpawn > 100) {
                createTrailButterfly(touch.clientX, touch.clientY);
                lastSpawn = now;
            }
        }
    }, { passive: true });
}

function setupEventListeners() {
    document.getElementById('ytCard').addEventListener('click', () => selectPlatform('youtube'));
    document.getElementById('instaCard').addEventListener('click', () => selectPlatform('instagram'));
    document.getElementById('musicCard').addEventListener('click', () => selectPlatform('music'));

    document.getElementById('singleCard').addEventListener('click', () => selectMode('single'));
    document.getElementById('playlistCard').addEventListener('click', () => selectMode('playlist'));

    document.getElementById('backToStep1').addEventListener('click', () => goToStep(1));
    document.getElementById('backToStep2').addEventListener('click', () => goToStep(2));

    document.getElementById('fetchBtn').addEventListener('click', fetchVideoInfo);
    document.getElementById('urlInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') fetchVideoInfo();
    });

    document.getElementById('downloadBtn').addEventListener('click', startDownload);
    document.getElementById('playlistDownloadBtn').addEventListener('click', startPlaylistDownload);
    document.getElementById('newDownloadBtn').addEventListener('click', resetApp);
    document.getElementById('retryBtn').addEventListener('click', resetApp);
}

function selectPlatform(platform) {
    state.platform = platform;

    const cards = document.querySelectorAll('.platform-card');
    cards.forEach(card => card.classList.add('selected-exit'));

    const urlInput = document.getElementById('urlInput');

    setTimeout(() => {
        if (platform === 'youtube') {
            document.getElementById('step2Title').textContent = 'Ready to download video';
            urlInput.placeholder = "Paste YouTube URL here...";
            document.getElementById('modeCards').classList.add('hidden');
            goToStep(3);
        } else if (platform === 'instagram') {
            document.getElementById('step2Title').textContent = 'Ready to download Instagram Reel';
            urlInput.placeholder = "Paste Instagram Reel URL here...";
            document.getElementById('modeCards').classList.add('hidden');
            goToStep(3);
        } else {
            document.getElementById('step2Title').textContent = 'What do you want to download?';
            // Music URL is input in step 3, so we can set it here or generic
            urlInput.placeholder = "Paste YouTube URL here...";
            document.getElementById('modeCards').classList.remove('hidden');
            document.getElementById('singleCard').querySelector('h3').textContent = 'Single Track';
            document.getElementById('singleCard').querySelector('p').textContent = 'Download one song as MP3';
            goToStep(2);
        }
    }, 200);
}

function selectMode(mode) {
    state.mode = mode;
    goToStep(3);
}

function goToStep(stepNum) {
    document.querySelectorAll('.step').forEach(step => step.classList.remove('active'));
    document.getElementById(`step${stepNum}`).classList.add('active');

    if (stepNum === 1) {
        state.platform = null;
        state.mode = null;
    }
    if (stepNum === 2) {
        state.mode = null;
    }
    if (stepNum === 3) {
        document.getElementById('urlInput').value = '';
        document.getElementById('videoInfo').classList.add('hidden');
        document.getElementById('playlistInfo').classList.add('hidden');
        state.url = '';
        state.videoInfo = null;
        state.selectedQuality = null;
    }
}

async function fetchVideoInfo() {
    const url = document.getElementById('urlInput').value.trim();
    if (!url) return;

    state.url = url;
    const fetchBtn = document.getElementById('fetchBtn');
    const fetchLoading = document.getElementById('fetchLoading');
    const urlContainer = document.querySelector('.url-input-container');

    fetchBtn.classList.add('loading');
    urlContainer.classList.add('hidden');
    fetchLoading.classList.remove('hidden');
    document.body.classList.add('loading-active');
    if (document.activeElement) {
        document.activeElement.blur();
    }

    try {
        const response = await fetch('/api/info', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.error) {
            alert(data.error);
            fetchBtn.classList.remove('loading');
            urlContainer.classList.remove('hidden');
            fetchLoading.classList.add('hidden');
            document.body.classList.remove('loading-active');
            return;
        }

        state.videoInfo = data;

        if (data.is_playlist) {
            showPlaylistInfo(data);
        } else {
            showVideoInfo(data);
        }

    } catch (error) {
        alert('Failed to fetch video info. Please check the URL.');
    }

    fetchBtn.classList.remove('loading');
    urlContainer.classList.remove('hidden');
    fetchLoading.classList.add('hidden');
    document.body.classList.remove('loading-active');
}

function showVideoInfo(data) {
    document.getElementById('videoInfo').classList.remove('hidden');
    document.getElementById('playlistInfo').classList.add('hidden');

    document.getElementById('thumbnail').src = data.thumbnail || '';
    document.getElementById('videoTitle').textContent = data.title;
    document.getElementById('channelName').textContent = data.channel;

    if (data.duration) {
        const mins = Math.floor(data.duration / 60);
        const secs = data.duration % 60;
        document.getElementById('duration').textContent = `${mins}:${secs.toString().padStart(2, '0')}`;
    } else {
        document.getElementById('duration').textContent = '';
    }

    const qualityGrid = document.getElementById('qualityGrid');
    qualityGrid.innerHTML = '';

    if (state.platform === 'youtube') {
        data.video_qualities.forEach((q, index) => {
            const option = createQualityOption(q.label, 'video', q.height, index === 0);
            qualityGrid.appendChild(option);
        });

        const bestAudioOption = createQualityOption('Best Audio (MP3)', 'audio', 'best', false);
        qualityGrid.appendChild(bestAudioOption);

    } else if (state.platform === 'instagram') {
        // Instagram usually doesn't return multiple qualities in the same way, or we just want simple options
        // We will offer "Best Video" and "Best Audio"
        const bestVideoOption = createQualityOption('Best Quality Video', 'video', 'best', true);
        qualityGrid.appendChild(bestVideoOption);

        const bestAudioOption = createQualityOption('Audio Only (MP3)', 'audio', 'best', false);
        qualityGrid.appendChild(bestAudioOption);

    } else {
        data.audio_qualities.forEach((q, index) => {
            const option = createQualityOption(q.label, 'audio', q.abr, index === 0);
            qualityGrid.appendChild(option);
        });
    }

    const firstOption = qualityGrid.querySelector('.quality-option');
    if (firstOption) {
        firstOption.classList.add('selected');
        state.selectedQuality = {
            type: firstOption.dataset.type,
            value: firstOption.dataset.value
        };
    }
}

function createQualityOption(label, type, value, isFirst) {
    const option = document.createElement('button');
    option.className = 'quality-option';
    option.dataset.type = type;
    option.dataset.value = value;

    option.innerHTML = `
        <div class="quality-label">${label}</div>
        <div class="quality-type">${type === 'video' ? 'Video' : 'Audio'}</div>
    `;

    option.addEventListener('click', () => selectQuality(option));

    return option;
}

function selectQuality(option) {
    document.querySelectorAll('.quality-option').forEach(opt => opt.classList.remove('selected'));
    option.classList.add('selected');

    state.selectedQuality = {
        type: option.dataset.type,
        value: option.dataset.value
    };
}

function showPlaylistInfo(data) {
    document.getElementById('videoInfo').classList.add('hidden');
    document.getElementById('playlistInfo').classList.remove('hidden');

    document.getElementById('playlistTitle').textContent = data.title;
    document.getElementById('playlistCount').textContent = `${data.count} tracks`;
}

async function startDownload() {
    if (!state.selectedQuality) return;

    let mode;
    if (state.selectedQuality.type === 'video') {
        if (state.selectedQuality.value === 'best') {
            mode = 'video_best';
        } else {
            mode = 'video_quality';
        }
    } else {
        if (state.selectedQuality.value === 'best') {
            mode = 'audio_best';
        } else {
            mode = 'audio_quality';
        }
    }

    await initiateDownload(mode, state.selectedQuality.value);
}

async function startPlaylistDownload() {
    await initiateDownload('playlist', null);
}

async function initiateDownload(mode, quality) {
    state.isDownloading = true; // Start blocking Refresh
    goToStep(4);

    document.querySelector('.progress-section').classList.remove('hidden');
    document.getElementById('completeSection').classList.add('hidden');
    document.getElementById('errorSection').classList.add('hidden');

    // Fix for blinking cursor
    if (document.activeElement) {
        document.activeElement.blur();
    }
    document.body.classList.add('loading-active');

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: state.url,
                mode: mode,
                quality: quality
            })
        });

        const data = await response.json();

        if (data.error) {
            showError(data.error);
            return;
        }

        state.downloadId = data.download_id;
        trackProgress(data.download_id);

    } catch (error) {
        state.isDownloading = false; // Stop blocking Refresh if init failed
        showError('Failed to start download');
    }
}

function trackProgress(downloadId) {
    const eventSource = new EventSource(`/api/progress/${downloadId}`);

    eventSource.onmessage = (event) => {
        const progress = JSON.parse(event.data);

        updateProgressUI(progress);

        if (progress.status === 'complete') {
            eventSource.close();

            // Trigger browser download
            const link = document.createElement('a');
            link.href = `/api/download_file/${downloadId}`;
            link.download = ''; // Browser will infer filename from Content-Disposition
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            showComplete();
        } else if (progress.status === 'error') {
            eventSource.close();
            showError(progress.message);
        }
    };

    eventSource.onerror = () => {
        eventSource.close();
    };
}

function updateProgressUI(progress) {
    const progressFill = document.querySelector('.progress-fill');
    const progressPercent = document.getElementById('progressPercent');
    const progressStatus = document.getElementById('progressStatus');
    const progressTitle = document.getElementById('progressTitle');

    const loaderGlitch = document.getElementById('loaderGlitch');
    const loaderHamster = document.getElementById('loaderHamster');
    const loaderBox = document.getElementById('loaderBox');
    const loaderGlow = document.getElementById('loaderGlow');

    loaderGlitch.classList.add('hidden');
    loaderHamster.classList.add('hidden');
    loaderBox.classList.add('hidden');
    loaderGlow.classList.add('hidden');

    progressFill.style.width = progress.percent + '%';
    progressPercent.textContent = Math.round(progress.percent) + '%';

    if (progress.status === 'downloading') {
        loaderHamster.classList.remove('hidden');
        progressTitle.textContent = 'Downloading...';
        let speedText = '';
        if (progress.speed) {
            const speedMB = (progress.speed / 1024 / 1024).toFixed(2);
            speedText = ` at ${speedMB} MB/s`;
        }
        progressStatus.textContent = `Downloading${speedText}...`;
    } else if (progress.status === 'processing') {
        loaderBox.classList.remove('hidden');
        progressTitle.textContent = 'Processing...';
        progressStatus.textContent = 'Converting and processing file...';
    } else if (progress.status === 'starting' || progress.status === 'waiting') {
        loaderGlitch.classList.remove('hidden');
        progressTitle.textContent = 'Starting...';
        progressStatus.textContent = 'Preparing download...';
    }
}

function showComplete() {
    state.isDownloading = false; // Stop blocking Refresh
    document.body.classList.remove('loading-active');
    document.querySelector('.progress-section').classList.add('hidden');
    document.getElementById('completeSection').classList.remove('hidden');
}

function showError(message) {
    state.isDownloading = false; // Stop blocking Refresh
    document.body.classList.remove('loading-active');
    document.querySelector('.progress-section').classList.add('hidden');
    document.getElementById('errorSection').classList.remove('hidden');
    document.getElementById('errorMessage').textContent = message;
}

function resetApp() {
    state.platform = null;
    state.mode = null;
    state.url = '';
    state.videoInfo = null;
    state.selectedQuality = null;
    state.downloadId = null;

    goToStep(1);
}

document.addEventListener('DOMContentLoaded', init);
