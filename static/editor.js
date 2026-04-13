/* ─── Pinedit Editor — Live Preview + Preset Management ──────────────────── */

(function () {
    'use strict';

    // ─── State ──────────────────────────────────────────────────────────
    let originalFiles = [];      // Raw File objects for batch export
    let currentFileIndex = 0;    // Which file is being previewed
    let currentFile = null;      // Current File blob for preview requests
    let presets = window.__presets || {};
    let activePreset = null;
    let previewTimeout = null;
    let isProcessing = false;

    // ─── DOM References ─────────────────────────────────────────────────
    const uploadZone = document.getElementById('upload-zone');
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('preview-container');
    const previewImage = document.getElementById('preview-image');
    const previewLoading = document.getElementById('preview-loading');
    const presetsGrid = document.getElementById('presets-grid');
    const batchStrip = document.getElementById('batch-strip');
    const btnExport = document.getElementById('btn-export');
    const btnReset = document.getElementById('btn-reset');
    const btnSavePreset = document.getElementById('btn-save-preset');
    const modalOverlay = document.getElementById('modal-overlay');
    const exportOverlay = document.getElementById('export-overlay');
    const presetNameInput = document.getElementById('preset-name-input');
    const modalCancel = document.getElementById('modal-cancel');
    const modalSave = document.getElementById('modal-save');
    const btnChangePhoto = document.getElementById('btn-change-photo');
    const btnSettings = document.getElementById('btn-settings');
    const settingsOverlay = document.getElementById('settings-overlay');

    // ─── Initialization ─────────────────────────────────────────────────

    function init() {
        renderPresets();
        setupUpload();
        setupSliders();
        setupShapeBlurControls();
        setupGroupToggles();
        setupButtons();
        setupSettings();
    }

    // ─── Upload Handling ────────────────────────────────────────────────

    function setupUpload() {
        uploadZone.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', handleFiles);

        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });
        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });
        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFiles();
            }
        });
    }

    function handleFiles() {
        const files = Array.from(fileInput.files);
        if (!files.length) return;

        originalFiles = files;
        currentFileIndex = 0;
        currentFile = files[0];

        // Show preview, hide upload zone
        uploadZone.style.display = 'none';
        previewContainer.style.display = 'flex';
        btnExport.disabled = false;
        btnSavePreset.disabled = false;

        // Show batch strip if multiple files
        if (files.length > 1) {
            batchStrip.style.display = 'flex';
            renderBatchStrip();
        } else {
            batchStrip.style.display = 'none';
        }

        // Load first image preview (show original first, then apply edits)
        showOriginalPreview(files[0]);
        requestPreview();
    }

    function showOriginalPreview(file) {
        // Use createObjectURL for faster initial display
        const url = URL.createObjectURL(file);
        previewImage.src = url;
    }

    function renderBatchStrip() {
        batchStrip.innerHTML = '';
        const count = originalFiles.length;
        const cardData = []; // store cards to position after all loaded

        originalFiles.forEach((file, idx) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const card = document.createElement('div');
                card.className = 'batch-card' + (idx === currentFileIndex ? ' active' : '');

                // Calculate fan arc: cards curve upward toward center
                const centerIdx = (count - 1) / 2;
                const offset = idx - centerIdx;
                const rotation = offset * (count > 8 ? 4 : 6); // degrees, tighter for more cards
                const lift = -Math.pow(offset, 2) * (count > 8 ? 2 : 3); // parabolic lift (negative = up)
                const zIdx = count - Math.abs(Math.round(offset)); // center cards on top

                card.style.transform = `rotate(${rotation}deg) translateY(${lift}px)`;
                card.style.zIndex = zIdx;

                const img = document.createElement('img');
                img.src = e.target.result;
                card.appendChild(img);

                // Photo number label
                const label = document.createElement('span');
                label.className = 'batch-card-label';
                label.textContent = idx + 1;
                card.appendChild(label);

                card.addEventListener('click', () => {
                    currentFileIndex = idx;
                    currentFile = originalFiles[idx];
                    batchStrip.querySelectorAll('.batch-card').forEach((c, i) => {
                        c.classList.toggle('active', i === idx);
                    });
                    showOriginalPreview(currentFile);
                    requestPreview();
                });

                // Insert in order (FileReader is async so we use data-index)
                card.dataset.index = idx;
                insertCardInOrder(card);
            };
            reader.readAsDataURL(file);
        });

        // Counter badge
        const counter = document.createElement('div');
        counter.className = 'batch-counter';
        counter.textContent = `${count} photos`;
        batchStrip.appendChild(counter);
    }

    function insertCardInOrder(card) {
        const idx = parseInt(card.dataset.index);
        const existing = batchStrip.querySelectorAll('.batch-card');
        let inserted = false;
        for (const el of existing) {
            if (parseInt(el.dataset.index) > idx) {
                batchStrip.insertBefore(card, el);
                inserted = true;
                break;
            }
        }
        if (!inserted) {
            // Insert before the counter badge
            const counter = batchStrip.querySelector('.batch-counter');
            if (counter) {
                batchStrip.insertBefore(card, counter);
            } else {
                batchStrip.appendChild(card);
            }
        }
    }

    // ─── Slider Controls ────────────────────────────────────────────────

    function setupSliders() {
        document.querySelectorAll('.slider-row').forEach(row => {
            const input = row.querySelector('input[type="range"]');
            const display = row.querySelector('.slider-value');

            input.addEventListener('input', () => {
                display.textContent = formatValue(input.value, row.dataset.step);
                schedulePreview();
            });

            // Double-click to reset to default
            input.addEventListener('dblclick', () => {
                input.value = row.dataset.default;
                display.textContent = formatValue(row.dataset.default, row.dataset.step);
                schedulePreview();
            });
        });
    }

    function formatValue(val, step) {
        const num = parseFloat(val);
        if (step && parseFloat(step) < 1) {
            return num.toFixed(2);
        }
        return Math.round(num).toString();
    }

    function getParams() {
        const params = {};
        document.querySelectorAll('.slider-row').forEach(row => {
            const input = row.querySelector('input[type="range"]');
            params[row.dataset.param] = parseFloat(input.value);
        });
        // Shape blur button-group values
        const shapePicker = document.getElementById('shape-picker');
        const modeToggle = document.getElementById('mode-toggle');
        if (shapePicker) params.shape_blur_shape = parseInt(shapePicker.dataset.value);
        if (modeToggle) params.shape_blur_invert = parseInt(modeToggle.dataset.value);
        return params;
    }

    function setParams(params) {
        document.querySelectorAll('.slider-row').forEach(row => {
            const key = row.dataset.param;
            if (key in params) {
                const input = row.querySelector('input[type="range"]');
                const display = row.querySelector('.slider-value');
                input.value = params[key];
                display.textContent = formatValue(params[key], row.dataset.step);
            }
        });
        // Shape blur button-group values
        if ('shape_blur_shape' in params) {
            setShapePicker(parseInt(params.shape_blur_shape));
        }
        if ('shape_blur_invert' in params) {
            setModeToggle(parseInt(params.shape_blur_invert));
        }
    }

    function resetParams() {
        document.querySelectorAll('.slider-row').forEach(row => {
            const input = row.querySelector('input[type="range"]');
            const display = row.querySelector('.slider-value');
            input.value = row.dataset.default;
            display.textContent = formatValue(row.dataset.default, row.dataset.step);
        });
        setShapePicker(0);
        setModeToggle(1);
    }

    // ─── Shape Blur Controls ─────────────────────────────────────────────

    function setupShapeBlurControls() {
        // Shape picker buttons
        const shapePicker = document.getElementById('shape-picker');
        if (shapePicker) {
            shapePicker.querySelectorAll('.shape-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    setShapePicker(parseInt(btn.dataset.shape));
                    schedulePreview();
                });
            });
        }

        // Mode toggle buttons
        const modeToggle = document.getElementById('mode-toggle');
        if (modeToggle) {
            modeToggle.querySelectorAll('.mode-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    setModeToggle(parseInt(btn.dataset.mode));
                    schedulePreview();
                });
            });
        }

        // Drag on preview to position shape blur
        setupShapeDrag();
    }

    function setupShapeDrag() {
        let dragging = false;

        function isShapeBlurActive() {
            const row = document.querySelector('.slider-row[data-param="shape_blur"]');
            if (!row) return false;
            return parseFloat(row.querySelector('input[type="range"]').value) > 0;
        }

        function updatePositionFromEvent(e) {
            const rect = previewImage.getBoundingClientRect();
            const x = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
            const y = Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100));

            // Update sliders
            const xRow = document.querySelector('.slider-row[data-param="shape_blur_x"]');
            const yRow = document.querySelector('.slider-row[data-param="shape_blur_y"]');
            if (xRow) {
                const input = xRow.querySelector('input[type="range"]');
                const display = xRow.querySelector('.slider-value');
                input.value = Math.round(x);
                display.textContent = Math.round(x);
            }
            if (yRow) {
                const input = yRow.querySelector('input[type="range"]');
                const display = yRow.querySelector('.slider-value');
                input.value = Math.round(y);
                display.textContent = Math.round(y);
            }
            schedulePreview();
        }

        previewImage.addEventListener('mousedown', (e) => {
            if (!isShapeBlurActive()) return;
            e.preventDefault();
            dragging = true;
            previewImage.style.cursor = 'crosshair';
            updatePositionFromEvent(e);
        });

        document.addEventListener('mousemove', (e) => {
            if (!dragging) return;
            e.preventDefault();
            updatePositionFromEvent(e);
        });

        document.addEventListener('mouseup', () => {
            if (dragging) {
                dragging = false;
                previewImage.style.cursor = '';
            }
        });
    }

    function setShapePicker(value) {
        const picker = document.getElementById('shape-picker');
        if (!picker) return;
        picker.dataset.value = value;
        picker.querySelectorAll('.shape-btn').forEach(btn => {
            btn.classList.toggle('active', parseInt(btn.dataset.shape) === value);
        });
    }

    function setModeToggle(value) {
        const toggle = document.getElementById('mode-toggle');
        if (!toggle) return;
        toggle.dataset.value = value;
        toggle.querySelectorAll('.mode-btn').forEach(btn => {
            btn.classList.toggle('active', parseInt(btn.dataset.mode) === value);
        });
    }

    // ─── Group Toggles ──────────────────────────────────────────────────

    function setupGroupToggles() {
        document.querySelectorAll('.adj-group-toggle').forEach(btn => {
            btn.addEventListener('click', () => {
                btn.classList.toggle('active');
            });
        });
    }

    // ─── Live Preview ───────────────────────────────────────────────────

    function schedulePreview() {
        if (previewTimeout) clearTimeout(previewTimeout);
        previewTimeout = setTimeout(requestPreview, 300);
    }

    function requestPreview() {
        if (!currentFile || isProcessing) return;

        isProcessing = true;
        previewLoading.style.display = 'flex';

        const params = getParams();
        const formData = new FormData();
        formData.append('image', currentFile);

        for (const [key, val] of Object.entries(params)) {
            formData.append(key, val);
        }

        fetch('/preview', {
            method: 'POST',
            body: formData,
        })
        .then(res => res.json())
        .then(data => {
            if (data.image) {
                previewImage.src = data.image;
            }
        })
        .catch(err => console.error('Preview error:', err))
        .finally(() => {
            isProcessing = false;
            previewLoading.style.display = 'none';
        });
    }

    // ─── Presets ─────────────────────────────────────────────────────────

    function renderPresets() {
        presetsGrid.innerHTML = '';

        // "None" preset card
        const noneCard = createPresetCard('None', null, true);
        presetsGrid.appendChild(noneCard);

        for (const [name, data] of Object.entries(presets)) {
            const card = createPresetCard(name, data, false);
            presetsGrid.appendChild(card);
        }
    }

    function createPresetCard(name, data, isNone) {
        const card = document.createElement('div');
        card.className = 'preset-card' + (isNone && !activePreset ? ' active' : '') +
                         (!isNone && activePreset === name ? ' active' : '');

        // Cover
        const coverDiv = document.createElement('div');
        if (!isNone && data && data.cover) {
            const coverImg = document.createElement('img');
            coverImg.src = data.cover;
            coverImg.className = 'preset-card-cover';
            coverDiv.appendChild(coverImg);
        } else {
            coverDiv.className = 'preset-card-cover placeholder';
            if (isNone) {
                coverDiv.textContent = '○';
            } else {
                // Generate a warm gradient placeholder based on preset name
                const hue = hashCode(name) % 40 + 10; // warm hue range
                coverDiv.style.background = `linear-gradient(135deg, hsl(${hue}, 60%, 88%) 0%, hsl(${hue + 15}, 50%, 78%) 100%)`;
                coverDiv.textContent = name.charAt(0).toUpperCase();
            }
        }
        card.appendChild(coverDiv);

        // Info
        const info = document.createElement('div');
        info.className = 'preset-card-info';
        const nameEl = document.createElement('div');
        nameEl.className = 'preset-card-name';
        nameEl.textContent = name;
        info.appendChild(nameEl);

        card.appendChild(info);

        // Delete button on all presets except "None"
        if (!isNone && data) {
            const delBtn = document.createElement('button');
            delBtn.className = 'preset-card-delete';
            delBtn.textContent = '\u00d7';
            delBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                deletePreset(name);
            });
            card.appendChild(delBtn);
        }

        // Click to apply
        card.addEventListener('click', () => {
            if (isNone) {
                activePreset = null;
                resetParams();
            } else if (data && data.params) {
                activePreset = name;
                setParams(data.params);
            }
            // Update active state
            presetsGrid.querySelectorAll('.preset-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');

            if (currentFile) {
                requestPreview();
            }
        });

        return card;
    }

    function hashCode(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash |= 0;
        }
        return Math.abs(hash);
    }

    function deletePreset(name) {
        fetch(`/delete-preset/${encodeURIComponent(name)}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                presets = data.presets;
                if (activePreset === name) activePreset = null;
                renderPresets();
            });
    }

    // ─── Buttons ────────────────────────────────────────────────────────

    function setupButtons() {
        // Reset
        btnReset.addEventListener('click', () => {
            activePreset = null;
            resetParams();
            presetsGrid.querySelectorAll('.preset-card').forEach(c => c.classList.remove('active'));
            presetsGrid.querySelector('.preset-card')?.classList.add('active');
            if (currentFile) requestPreview();
        });

        // Change photos
        btnChangePhoto.addEventListener('click', () => {
            // Reset file input so same file can be re-selected
            fileInput.value = '';

            // Reset state
            originalFiles = [];
            currentFileIndex = 0;
            currentFile = null;

            // Show upload zone, hide preview
            uploadZone.style.display = 'flex';
            previewContainer.style.display = 'none';
            batchStrip.style.display = 'none';
            btnExport.disabled = true;
            btnSavePreset.disabled = true;
        });

        // Export
        btnExport.addEventListener('click', handleExport);

        // Save preset
        btnSavePreset.addEventListener('click', () => {
            modalOverlay.style.display = 'flex';
            presetNameInput.value = '';
            presetNameInput.focus();
        });

        modalCancel.addEventListener('click', () => {
            modalOverlay.style.display = 'none';
        });

        modalSave.addEventListener('click', handleSavePreset);

        presetNameInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') handleSavePreset();
            if (e.key === 'Escape') modalOverlay.style.display = 'none';
        });

        // Close modal on overlay click
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) modalOverlay.style.display = 'none';
        });
    }

    function handleSavePreset() {
        const name = presetNameInput.value.trim();
        if (!name) return;

        // Get current preview image as cover art
        const coverData = previewImage.src.startsWith('data:') ? previewImage.src : null;

        const payload = {
            name: name,
            params: getParams(),
            cover: coverData,
        };

        fetch('/save-preset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        })
        .then(res => res.json())
        .then(data => {
            presets = data.presets;
            activePreset = name;
            renderPresets();
            modalOverlay.style.display = 'none';
        });
    }

    function handleExport() {
        if (!originalFiles.length) return;

        exportOverlay.style.display = 'flex';
        const progressFill = document.getElementById('progress-fill');
        const exportStatus = document.getElementById('export-status');

        progressFill.style.width = '30%';
        exportStatus.textContent = `Processing ${originalFiles.length} photo${originalFiles.length > 1 ? 's' : ''} at full resolution...`;

        const formData = new FormData();
        const params = getParams();

        for (const file of originalFiles) {
            formData.append('images', file);
        }
        for (const [key, val] of Object.entries(params)) {
            formData.append(key, val);
        }

        progressFill.style.width = '60%';

        fetch('/export', {
            method: 'POST',
            body: formData,
        })
        .then(res => {
            progressFill.style.width = '90%';
            return res.blob();
        })
        .then(blob => {
            progressFill.style.width = '100%';
            exportStatus.textContent = 'Done! Starting download...';

            // Trigger download
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'pinedit_export.zip';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            setTimeout(() => {
                exportOverlay.style.display = 'none';
                progressFill.style.width = '0%';
            }, 1000);
        })
        .catch(err => {
            console.error('Export error:', err);
            exportStatus.textContent = 'Export failed. Please try again.';
            setTimeout(() => {
                exportOverlay.style.display = 'none';
                progressFill.style.width = '0%';
            }, 2000);
        });
    }

    // ─── Settings ────────────────────────────────────────────────────────

    function setupSettings() {
        const formatSelect = document.getElementById('setting-format');
        const qualitySlider = document.getElementById('setting-quality');
        const qualityVal = document.getElementById('setting-quality-val');
        const exportPathInput = document.getElementById('setting-export-path');
        const btnBrowse = document.getElementById('btn-browse-folder');
        const btnClear = document.getElementById('btn-clear-path');
        const btnSaveSettings = document.getElementById('settings-save');
        const btnClose = document.getElementById('settings-close');

        // Quality slider label
        qualitySlider.addEventListener('input', () => {
            qualityVal.textContent = qualitySlider.value;
        });

        // Open settings
        btnSettings.addEventListener('click', () => {
            // Load current settings
            fetch('/settings')
                .then(r => r.json())
                .then(s => {
                    formatSelect.value = s.export_format || 'jpg';
                    qualitySlider.value = s.export_quality || 95;
                    qualityVal.textContent = qualitySlider.value;
                    exportPathInput.value = s.export_path || '';
                    exportPathInput.placeholder = s.export_path ? '' : 'Browser download (default)';
                    settingsOverlay.style.display = 'flex';
                });
        });

        // Close
        btnClose.addEventListener('click', () => {
            settingsOverlay.style.display = 'none';
        });
        settingsOverlay.addEventListener('click', (e) => {
            if (e.target === settingsOverlay) settingsOverlay.style.display = 'none';
        });

        // Browse folder
        btnBrowse.addEventListener('click', () => {
            fetch('/browse-folder', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.path) {
                        exportPathInput.value = data.path;
                        exportPathInput.placeholder = '';
                    }
                });
        });

        // Clear path
        btnClear.addEventListener('click', () => {
            exportPathInput.value = '';
            exportPathInput.placeholder = 'Browser download (default)';
        });

        // Save
        btnSaveSettings.addEventListener('click', () => {
            const settings = {
                export_format: formatSelect.value,
                export_quality: parseInt(qualitySlider.value),
                export_path: exportPathInput.value.trim(),
            };
            fetch('/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(settings),
            })
            .then(r => r.json())
            .then(() => {
                settingsOverlay.style.display = 'none';
            });
        });
    }

    // ─── Start ──────────────────────────────────────────────────────────
    init();
})();
