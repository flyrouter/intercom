#!/bin/sh
echo "Content-type: text/html; charset=utf-8"
echo ""

cat << 'EOFH'
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Управление бэкапами</title>
    <link rel="stylesheet" href="/a/bootstrap.min.css">
    <style>
        body { background: #f5f5f5; padding: 20px; }
        .container { max-width: 900px; margin: 0 auto; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        .btn-primary { background: #1976d2; color: white; }
        .btn-success { background: #4caf50; color: white; }
        .btn-danger { background: #f44336; color: white; }
        .btn-warning { background: #ff9800; color: white; }
        .btn-info { background: #17a2b8; color: white; }
        .btn-secondary { background: #6c757d; color: white; }
        
        .backup-list { max-height: 400px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; }
        .backup-item { 
            padding: 15px; 
            border-bottom: 1px solid #eee; 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            transition: background-color 0.2s;
        }
        .backup-item:hover { background: #f8f9fa; }
        .backup-item:last-child { border-bottom: none; }
        
        .status { 
            padding: 15px; 
            border-radius: 4px; 
            margin: 15px 0;
            font-weight: 500;
        }
        .status.success { 
            background: #d4edda; 
            color: #155724; 
            border-left: 4px solid #28a745;
        }
        .status.error { 
            background: #f8d7da; 
            color: #721c24; 
            border-left: 4px solid #dc3545;
        }
        .status.info { 
            background: #d1ecf1; 
            color: #0c5460; 
            border-left: 4px solid #17a2b8;
        }
        .status.warning { 
            background: #fff3cd; 
            color: #856404; 
            border-left: 4px solid #ffc107;
        }
        
        .loader {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .storage-info {
            background: #e9ecef;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
            font-family: monospace;
        }
        
        .storage-option {
            display: flex;
            align-items: center;
            padding: 15px;
            margin: 10px 0;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .storage-option:hover {
            border-color: #1976d2;
            background: #f8f9fa;
        }
        
        .storage-option.selected {
            border-color: #1976d2;
            background: #e3f2fd;
        }
        
        .storage-option.disabled {
            opacity: 0.6;
            cursor: not-allowed;
            background: #f8f9fa;
        }
        
        .storage-option.disabled:hover {
            border-color: #dee2e6;
        }
        
        .storage-option input[type="radio"] {
            margin-right: 15px;
            transform: scale(1.2);
        }
        
        .storage-icon {
            font-size: 24px;
            margin-right: 15px;
        }
        
        .storage-details {
            flex: 1;
        }
        
        .storage-name {
            font-weight: bold;
            font-size: 16px;
        }
        
        .storage-path {
            color: #666;
            font-size: 12px;
        }
        
        .storage-space {
            color: #28a745;
            font-size: 12px;
        }
        
        .storage-error {
            color: #dc3545;
            font-size: 12px;
        }
        
        .button-group {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 20px;
        }
        
        .file-size {
            font-size: 12px;
            color: #6c757d;
        }
        
        .backup-date {
            font-weight: bold;
            color: #495057;
        }
        
        .component-selector {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }
        
        .component-item {
            padding: 8px;
            border-bottom: 1px solid #dee2e6;
        }
        
        .component-item:last-child {
            border-bottom: none;
        }
        
        .upload-area {
            border: 2px dashed #1976d2;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            background: #f8f9fa;
            cursor: pointer;
            transition: all 0.3s;
            margin: 20px 0;
        }
        
        .upload-area:hover {
            background: #e3f2fd;
            border-color: #0d47a1;
        }
        
        .upload-area.dragover {
            background: #bbdefb;
            border-color: #0d47a1;
        }
        
        .upload-progress {
            margin-top: 15px;
            display: none;
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #f0f0f0;
            border-radius: 10px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: #1976d2;
            width: 0%;
            transition: width 0.3s;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">💾 Управление бэкапами</h1>
        
        <!-- Кнопки управления -->
        <div class="card">
            <h3 class="mb-3">Действия</h3>
            <div class="button-group">
                <button class="btn btn-primary" onclick="createBackup()">
                    <span class="btn-icon">📀</span> Создать бэкап
                </button>
                <button class="btn btn-info" onclick="scanStorage()">
                    <span class="btn-icon">🔍</span> Сканировать устройства
                </button>
                <button class="btn btn-secondary" onclick="loadBackups()">
                    <span class="btn-icon">🔄</span> Обновить список
                </button>
            </div>
            <div id="actionStatus" class="status" style="display: none;"></div>
        </div>

        <!-- Выбор места хранения -->
        <div class="card">
            <h3 class="mb-3">💿 Место хранения бэкапов</h3>
            <div id="storageOptions" class="storage-options">
                <div class="text-center py-3">
                    <div class="loader"></div>
                    <p class="mt-2 text-muted">Поиск доступных устройств...</p>
                </div>
            </div>
            <div id="selectedStorageInfo" class="storage-info mt-3" style="display: none;"></div>
        </div>

        <!-- Загрузка бэкапа -->
        <div class="card">
            <h3 class="mb-3">📤 Загрузить бэкап</h3>
            <div class="upload-area" id="uploadArea">
                <span class="storage-icon">📁</span>
                <p>Нажмите или перетащите файл бэкапа сюда</p>
                <p class="text-muted small">Поддерживаются форматы .tar и .tar.gz</p>
                <input type="file" id="fileInput" style="display: none;" accept=".tar,.tar.gz,.tgz">
            </div>
            <div id="uploadProgress" class="upload-progress">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <p class="text-center mt-2" id="progressText">Загрузка...</p>
            </div>
            <div id="uploadStatus" class="status" style="display: none;"></div>
        </div>

        <!-- Выбор компонентов для бэкапа -->
        <div class="card">
            <h3 class="mb-3">📦 Выбор компонентов для бэкапа</h3>
            <div class="component-selector">
                <div class="component-item">
                    <input type="checkbox" id="backup_cgi" checked> 
                    <label for="backup_cgi"><strong>CGI скрипты</strong> - все наши страницы (/var/www/cgi-bin/p/*.cgi)</label>
                </div>
                <div class="component-item">
                    <input type="checkbox" id="backup_baresip" checked> 
                    <label for="backup_baresip"><strong>SIP конфиги</strong> - аккаунты и настройки (/etc/baresip/)</label>
                </div>
                <div class="component-item">
                    <input type="checkbox" id="backup_keys" checked> 
                    <label for="backup_keys"><strong>База ключей</strong> - все RFID и QR ключи (/etc/door_keys.conf)</label>
                </div>
                <div class="component-item">
                    <input type="checkbox" id="backup_scripts" checked> 
                    <label for="backup_scripts"><strong>Скрипты монитора</strong> - door_monitor.sh, start_baresip.sh</label>
                </div>
                <div class="component-item">
                    <input type="checkbox" id="backup_init" checked> 
                    <label for="backup_init"><strong>Init скрипты</strong> - автозапуск (/etc/init.d/S99door)</label>
                </div>
                <div class="component-item">
                    <input type="checkbox" id="backup_majestic" checked> 
                    <label for="backup_majestic"><strong>Majestic конфиг</strong> - настройки камеры (/etc/majestic.yaml)</label>
                </div>
                <div class="component-item">
                    <input type="checkbox" id="backup_uart" checked> 
                    <label for="backup_uart"><strong>UART настройки</strong> - rc.local и параметры последовательного порта</label>
                </div>
            </div>
            <div class="button-group">
                <button class="btn btn-sm btn-success" onclick="selectAll(true)">Выбрать все</button>
                <button class="btn btn-sm btn-warning" onclick="selectAll(false)">Снять все</button>
            </div>
        </div>

        <!-- Список бэкапов -->
        <div class="card">
            <h3 class="mb-3">📋 Существующие бэкапы</h3>
            <div id="backupList" class="backup-list">
                <div class="text-center py-4">
                    <div class="loader"></div>
                    <p class="mt-2 text-muted">Загрузка списка бэкапов...</p>
                </div>
            </div>
            <div class="mt-3 text-muted small">
                * Хранятся последние 10 бэкапов, старые удаляются автоматически
            </div>
        </div>
    </div>

    <script>
        let selectedStorage = null;
        let currentBackupComponents = {
            cgi: true,
            baresip: true,
            keys: true,
            scripts: true,
            init: true,
            majestic: true,
            uart: true
        };
        
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        
        // Настройка drag & drop
        uploadArea.addEventListener('click', () => fileInput.click());
        
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) uploadBackup(file);
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files[0]) uploadBackup(e.target.files[0]);
        });
        
        function showStatus(elementId, message, type) {
            const status = document.getElementById(elementId);
            status.className = 'status ' + type;
            status.innerHTML = message;
            status.style.display = 'block';
            
            if (type === 'success') {
                setTimeout(() => {
                    status.style.display = 'none';
                }, 5000);
            }
        }
        
        function selectAll(select) {
            document.getElementById('backup_cgi').checked = select;
            document.getElementById('backup_baresip').checked = select;
            document.getElementById('backup_keys').checked = select;
            document.getElementById('backup_scripts').checked = select;
            document.getElementById('backup_init').checked = select;
            document.getElementById('backup_majestic').checked = select;
            document.getElementById('backup_uart').checked = select;
            updateComponents();
        }
        
        function updateComponents() {
            currentBackupComponents = {
                cgi: document.getElementById('backup_cgi').checked,
                baresip: document.getElementById('backup_baresip').checked,
                keys: document.getElementById('backup_keys').checked,
                scripts: document.getElementById('backup_scripts').checked,
                init: document.getElementById('backup_init').checked,
                majestic: document.getElementById('backup_majestic').checked,
                uart: document.getElementById('backup_uart').checked
            };
        }
        
        document.getElementById('backup_cgi').addEventListener('change', updateComponents);
        document.getElementById('backup_baresip').addEventListener('change', updateComponents);
        document.getElementById('backup_keys').addEventListener('change', updateComponents);
        document.getElementById('backup_scripts').addEventListener('change', updateComponents);
        document.getElementById('backup_init').addEventListener('change', updateComponents);
        document.getElementById('backup_majestic').addEventListener('change', updateComponents);
        document.getElementById('backup_uart').addEventListener('change', updateComponents);
        
        function scanStorage() {
            const storageDiv = document.getElementById('storageOptions');
            storageDiv.innerHTML = '<div class="text-center py-3"><div class="loader"></div><p class="mt-2 text-muted">Поиск устройств...</p></div>';
            
            fetch('/cgi-bin/p/backup_api.cgi?action=scan_storage')
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success' && data.devices && data.devices.length > 0) {
                        let html = '';
                        data.devices.forEach((device, index) => {
                            const isSelected = (selectedStorage && selectedStorage.path === device.path) || (index === 0 && device.available && !selectedStorage);
                            const selectedClass = isSelected ? 'selected' : '';
                            const disabledClass = device.available ? '' : 'disabled';
                            const checked = isSelected ? 'checked' : '';
                            const disabled = device.available ? '' : 'disabled';
                            
                            html += `
                                <div class="storage-option ${selectedClass} ${disabledClass}" onclick="${device.available ? 'selectStorage(\'' + device.path + '\', \'' + device.name + '\', \'' + device.mount + '\', \'' + device.free + '\')' : ''}">
                                    <input type="radio" name="storage" value="${device.path}" ${checked} ${disabled} onclick="event.stopPropagation()">
                                    <span class="storage-icon">${device.icon}</span>
                                    <div class="storage-details">
                                        <div class="storage-name">${device.name}</div>
                                        <div class="storage-path">${device.mount || 'Не примонтировано'}</div>
                                        ${device.available 
                                            ? '<div class="storage-space">Свободно: ' + device.free + '</div>'
                                            : '<div class="storage-error">⚠️ ' + (device.error || 'Недоступно') + '</div>'
                                        }
                                    </div>
                                </div>
                            `;
                            
                            if (isSelected && device.available) {
                                selectedStorage = {
                                    path: device.path,
                                    name: device.name,
                                    mount: device.mount,
                                    free: device.free
                                };
                            }
                        });
                        storageDiv.innerHTML = html;
                        
                        if (selectedStorage) {
                            updateStorageInfo();
                            loadBackups();
                        } else {
                            const firstAvailable = data.devices.find(d => d.available);
                            if (firstAvailable) {
                                // Находим DOM элемент первого доступного устройства и вызываем клик
                                const firstRadio = document.querySelector('.storage-option:not(.disabled) input[type="radio"]');
                                if (firstRadio) {
                                    firstRadio.click();
                                }
                            }
                        }
                    } else {
                        storageDiv.innerHTML = '<div class="text-center py-3 text-warning">⚠️ Нет доступных устройств хранения</div>';
                    }
                })
                .catch(error => {
                    storageDiv.innerHTML = '<div class="text-center py-3 text-danger">❌ Ошибка сканирования</div>';
                    console.error('Scan error:', error);
                });
        }
        
        function selectStorage(path, name, mount, free) {
            document.querySelectorAll('.storage-option').forEach(opt => {
                opt.classList.remove('selected');
            });
            event.currentTarget.classList.add('selected');
            
            const radio = event.currentTarget.querySelector('input[type="radio"]');
            radio.checked = true;
            
            selectedStorage = { path, name, mount, free };
            
            updateStorageInfo();
            loadBackups();
        }
        
        function updateStorageInfo() {
            if (!selectedStorage) return;
            
            const infoDiv = document.getElementById('selectedStorageInfo');
            infoDiv.style.display = 'block';
            infoDiv.innerHTML = `
                <strong>Выбрано устройство:</strong> ${selectedStorage.name}<br>
                <strong>Путь:</strong> ${selectedStorage.mount}/backups/<br>
                <strong>Свободно:</strong> ${selectedStorage.free}
            `;
        }
        
        function uploadBackup(file) {
            if (!selectedStorage) {
                showStatus('uploadStatus', '⚠️ Сначала выберите место хранения', 'warning');
                return;
            }
            
            // Показываем прогресс
            const progress = document.getElementById('uploadProgress');
            const progressFill = document.getElementById('progressFill');
            const progressText = document.getElementById('progressText');
            progress.style.display = 'block';
            progressFill.style.width = '0%';
            progressText.textContent = 'Подготовка...';
            
            const formData = new FormData();
            formData.append('backup', file);
            
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable) {
                    const percent = (e.loaded / e.total) * 100;
                    progressFill.style.width = percent + '%';
                    progressText.textContent = `Загрузка: ${Math.round(percent)}%`;
                }
            });
            
            xhr.addEventListener('load', () => {
                progress.style.display = 'none';
                if (xhr.status === 200) {
                    try {
                        const response = JSON.parse(xhr.responseText);
                        if (response.status === 'success') {
                            showStatus('uploadStatus', 
                                `✅ ${response.message} (${response.size})`, 'success');
                            loadBackups();
                        } else {
                            showStatus('uploadStatus', `❌ ${response.message}`, 'error');
                        }
                    } catch (e) {
                        showStatus('uploadStatus', `❌ Ошибка ответа сервера`, 'error');
                    }
                } else {
                    showStatus('uploadStatus', `❌ Ошибка загрузки (${xhr.status})`, 'error');
                }
            });
            
            xhr.addEventListener('error', () => {
                progress.style.display = 'none';
                showStatus('uploadStatus', '❌ Ошибка соединения', 'error');
            });
            
            xhr.open('POST', '/cgi-bin/p/upload_final.cgi?storage=' + encodeURIComponent(selectedStorage.path));
            xhr.send(formData);
        }
        
        function createBackup() {
            if (!selectedStorage) {
                showStatus('actionStatus', '⚠️ Выберите место для сохранения бэкапа', 'warning');
                return;
            }
            
            updateComponents();
            
            const components = [];
            if (currentBackupComponents.cgi) components.push('cgi');
            if (currentBackupComponents.baresip) components.push('baresip');
            if (currentBackupComponents.keys) components.push('keys');
            if (currentBackupComponents.scripts) components.push('scripts');
            if (currentBackupComponents.init) components.push('init');
            if (currentBackupComponents.majestic) components.push('majestic');
            if (currentBackupComponents.uart) components.push('uart');
            
            if (components.length === 0) {
                showStatus('actionStatus', '⚠️ Выберите хотя бы один компонент', 'warning');
                return;
            }
            
            const status = document.getElementById('actionStatus');
            status.className = 'status info';
            status.innerHTML = '<div class="loader"></div> Создание бэкапа...';
            status.style.display = 'block';
            
            fetch('/cgi-bin/p/backup_api.cgi?action=create_backup&storage=' + 
                  encodeURIComponent(selectedStorage.path) + 
                  '&components=' + components.join(','))
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        showStatus('actionStatus', 
                            `✅ Бэкап создан: ${data.file} (${data.size})`, 'success');
                        loadBackups();
                    } else {
                        showStatus('actionStatus', `❌ ${data.message}`, 'error');
                    }
                })
                .catch(error => {
                    showStatus('actionStatus', `❌ Ошибка: ${error}`, 'error');
                });
        }
        
        function loadBackups() {
            if (!selectedStorage) {
                document.getElementById('backupList').innerHTML = '<div class="text-center py-4 text-muted">📭 Сначала выберите устройство</div>';
                return;
            }
            
            const listDiv = document.getElementById('backupList');
            listDiv.innerHTML = '<div class="text-center py-4"><div class="loader"></div><p class="mt-2 text-muted">Загрузка...</p></div>';
            
            fetch('/cgi-bin/p/backup_api.cgi?action=list_backups&storage=' + encodeURIComponent(selectedStorage.path))
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        if (!data.backups || data.backups.length === 0) {
                            listDiv.innerHTML = '<div class="text-center py-4 text-muted">📭 Нет сохраненных бэкапов</div>';
                            return;
                        }
                        
                        let html = '';
                        data.backups.forEach(backup => {
                            const dateStr = backup.date.replace(/_/g, ' ');
                            const displayDate = dateStr.substring(0, 4) + '-' + 
                                                dateStr.substring(4, 6) + '-' + 
                                                dateStr.substring(6, 8) + ' ' + 
                                                dateStr.substring(9, 11) + ':' + 
                                                dateStr.substring(11, 13) + ':' + 
                                                dateStr.substring(13, 15);
                            
                            html += '<div class="backup-item">' +
                                '<div>' +
                                '<div class="backup-date">📅 ' + displayDate + '</div>' +
                                '<div class="file-size">📁 ' + backup.file + '</div>' +
                                '<div class="file-size">💾 Размер: ' + backup.size + '</div>' +
                                '</div>' +
                                '<div class="btn-group-vertical">' +
                                '<button class="btn btn-info btn-sm" onclick="downloadBackup(\'' + backup.file + '\')">📥 Скачать</button>' +
                                '<button class="btn btn-success btn-sm" onclick="restoreBackup(\'' + backup.file + '\')">⟲ Восстановить</button>' +
                                '<button class="btn btn-danger btn-sm" onclick="deleteBackup(\'' + backup.file + '\')">🗑️ Удалить</button>' +
                                '</div>' +
                                '</div>';
                        });
                        listDiv.innerHTML = html;
                    } else {
                        listDiv.innerHTML = '<div class="text-center py-4 text-danger">❌ Ошибка загрузки</div>';
                    }
                })
                .catch(error => {
                    listDiv.innerHTML = '<div class="text-center py-4 text-danger">❌ Ошибка соединения</div>';
                });
        }
        
        function downloadBackup(file) {
            if (!selectedStorage) return;
            
            const form = document.createElement('form');
            form.method = 'GET';
            form.action = '/cgi-bin/p/backup_api.cgi';
            form.style.display = 'none';
            
            const actionInput = document.createElement('input');
            actionInput.type = 'hidden';
            actionInput.name = 'action';
            actionInput.value = 'download_backup';
            
            const storageInput = document.createElement('input');
            storageInput.type = 'hidden';
            storageInput.name = 'storage';
            storageInput.value = selectedStorage.path;
            
            const fileInput = document.createElement('input');
            fileInput.type = 'hidden';
            fileInput.name = 'file';
            fileInput.value = file;
            
            form.appendChild(actionInput);
            form.appendChild(storageInput);
            form.appendChild(fileInput);
            document.body.appendChild(form);
            form.submit();
            document.body.removeChild(form);
        }
        
        function restoreBackup(file) {
            if (!selectedStorage) return;
            
            if (!confirm('⚠️ Восстановить бэкап ' + file + '?\n\nЭто перезапишет текущие файлы!\nПосле восстановления рекомендуется перезагрузить камеру.')) return;
            
            showStatus('actionStatus', 
                '<div class="loader"></div> Восстановление...', 'info');
            
            fetch('/cgi-bin/p/backup_api.cgi?action=restore_backup&storage=' + 
                  encodeURIComponent(selectedStorage.path) + 
                  '&file=' + encodeURIComponent(file))
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        showStatus('actionStatus', 
                            '✅ ' + data.message + '<br><small>Рекомендуется перезагрузить</small>', 
                            'success');
                    } else {
                        showStatus('actionStatus', '❌ ' + data.message, 'error');
                    }
                    loadBackups();
                })
                .catch(error => {
                    showStatus('actionStatus', '❌ Ошибка: ' + error, 'error');
                });
        }
        
        function deleteBackup(file) {
            if (!selectedStorage) return;
            
            if (!confirm('🗑️ Удалить бэкап ' + file + '?')) return;
            
            fetch('/cgi-bin/p/backup_api.cgi?action=delete_backup&storage=' + 
                  encodeURIComponent(selectedStorage.path) + 
                  '&file=' + encodeURIComponent(file))
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        showStatus('actionStatus', '✅ ' + data.message, 'success');
                        loadBackups();
                    } else {
                        showStatus('actionStatus', '❌ ' + data.message, 'error');
                    }
                })
                .catch(error => {
                    showStatus('actionStatus', '❌ Ошибка: ' + error, 'error');
                });
        }
        
        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            scanStorage();
            updateComponents();
        });
        
        // Автообновление списка
        setInterval(loadBackups, 30000);
    </script>
</body>
</html>
EOFH
