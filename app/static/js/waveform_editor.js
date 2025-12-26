/**
 * Waveform Editor component for Soundboard Website
 * Uses WaveSurfer.js to provide visual audio trimming.
 */
class WaveformEditor {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;

        this.startInput = document.getElementById(options.startInputId || 'modal-start');
        this.endInput = document.getElementById(options.endInputId || 'modal-end');
        this.playBtn = document.getElementById(options.playBtnId || 'modal-play-btn');
        
        this.wavesurfer = null;
        this.wsRegions = null;
        this.activeRegion = null;
        
        this.init();
    }

    init() {
        // Initialize WaveSurfer
        this.wavesurfer = WaveSurfer.create({
            container: this.container,
            waveColor: '#0d6efd',
            progressColor: '#0a58ca',
            cursorColor: '#ff00ff',
            barWidth: 2,
            barRadius: 3,
            responsive: true,
            height: 100,
            normalize: true
        });

        // Initialize Regions plugin
        this.wsRegions = this.wavesurfer.registerPlugin(WaveSurfer.Regions.create());

        // Handle region updates
        this.wsRegions.on('region-updated', (region) => {
            this.activeRegion = region;
            if (this.startInput) this.startInput.value = region.start.toFixed(3);
            if (this.endInput) this.endInput.value = region.end.toFixed(3);
        });

        // Loop functionality for preview
        this.wavesurfer.on('finish', () => {
            if (this.wavesurfer.isPlaying()) {
                this.wavesurfer.stop();
            }
        });
    }

    async load(url, startTime = 0, endTime = null) {
        if (!this.wavesurfer) return;

        // Clear existing regions
        this.wsRegions.clearRegions();

        // Load audio
        await this.wavesurfer.load(url);

        this.wavesurfer.once('ready', () => {
            const duration = this.wavesurfer.getDuration();
            const start = parseFloat(startTime) || 0;
            const end = (parseFloat(endTime) && endTime > start) ? parseFloat(endTime) : duration;

            // Create initial trimming region
            this.activeRegion = this.wsRegions.addRegion({
                start: start,
                end: end,
                color: 'rgba(13, 110, 253, 0.2)',
                drag: true,
                resize: true
            });

            // Update inputs
            if (this.startInput) this.startInput.value = start.toFixed(3);
            if (this.endInput) this.endInput.value = end.toFixed(3);
        });
    }

    playPause() {
        if (!this.wavesurfer) return;
        
        if (this.activeRegion) {
            this.activeRegion.play();
        } else {
            this.wavesurfer.playPause();
        }
    }

    stop() {
        if (this.wavesurfer) this.wavesurfer.stop();
    }

    destroy() {
        if (this.wavesurfer) {
            this.wavesurfer.destroy();
            this.wavesurfer = null;
        }
    }
}
