/**
 * Waveform Editor component for Soundboard Website
 * Uses WaveSurfer.js to provide visual audio trimming.
 */
class WaveformEditor {
    constructor(containerId, options = {}) {
        this.containerId = containerId;
        this.container = document.getElementById(containerId);
        this.options = options;
        
        this.startInput = document.getElementById(options.startInputId || 'modal-start');
        this.endInput = document.getElementById(options.endInputId || 'modal-end');
        
        this.wavesurfer = null;
        this.wsRegions = null;
        this.activeRegion = null;
        this.isRegionPlayback = false;
    }

    /**
     * Completely (re)initializes the WaveSurfer instance.
     */
    init() {
        if (this.wavesurfer) {
            try { this.wavesurfer.destroy(); } catch(e) {}
        }

        this.container.innerHTML = '';

        this.wavesurfer = WaveSurfer.create({
            container: this.container,
            waveColor: '#ffcccc',
            progressColor: '#28a745',
            cursorColor: '#ff00ff',
            barWidth: 2,
            height: 100,
            normalize: true,
            fillParent: true,
            minPxPerSec: 100
        });

        this.wsRegions = this.wavesurfer.registerPlugin(WaveSurfer.Regions.create());

        this.wsRegions.enableDragSelection({
            color: 'rgba(40, 167, 69, 0.3)',
        });

        this.wsRegions.on('region-created', (region) => {
            this.wsRegions.getRegions().forEach(r => {
                if (r !== region) r.remove();
            });
            this.activeRegion = region;
        });

        this.wsRegions.on('region-updated', (region) => {
            this.activeRegion = region;
            if (this.startInput) this.startInput.value = region.start.toFixed(3);
            if (this.endInput) this.endInput.value = region.end.toFixed(3);
        });

        this.wavesurfer.on('timeupdate', (currentTime) => {
            if (this.isRegionPlayback && this.activeRegion) {
                if (currentTime >= this.activeRegion.end - 0.05) { 
                    this.wavesurfer.pause();
                    this.wavesurfer.setTime(this.activeRegion.start);
                    this.isRegionPlayback = false;
                }
            }
        });
    }

    async load(url, startTime = 0, endTime = null) {
        this.init();
        
        this.wavesurfer.on('ready', () => {
            const duration = this.wavesurfer.getDuration();
            const start = parseFloat(startTime) || 0;
            const end = (parseFloat(endTime) && endTime > start && endTime <= duration) ? parseFloat(endTime) : duration;
            
            this.createRegion(start, end);
            this.wavesurfer.zoom(100);
        });

        await this.wavesurfer.load(url);
    }

    createRegion(start, end) {
        if (!this.wsRegions) return;
        this.wsRegions.clearRegions();
        this.activeRegion = this.wsRegions.addRegion({
            start: start,
            end: end,
            color: 'rgba(40, 167, 69, 0.3)',
            drag: true,
            resize: true
        });
        
        if (this.startInput) this.startInput.value = start.toFixed(3);
        if (this.endInput) this.endInput.value = end.toFixed(3);
    }

    reset() {
        if (!this.wavesurfer) return;
        this.createRegion(0, this.wavesurfer.getDuration());
    }

    playPause() {
        if (!this.wavesurfer || !this.wavesurfer.decodedData) return;
        
        if (this.wavesurfer.isPlaying()) {
            this.wavesurfer.pause();
        } else {
            if (this.activeRegion) {
                this.isRegionPlayback = true;
                this.wavesurfer.setTime(this.activeRegion.start);
                this.activeRegion.play();
            } else {
                this.wavesurfer.play();
            }
        }
    }

    stop() {
        if (this.wavesurfer) {
            try { this.wavesurfer.stop(); } catch(e) {}
            this.isRegionPlayback = false;
        }
    }
}