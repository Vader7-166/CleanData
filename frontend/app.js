const fileInput = document.getElementById('fileInput');
const uploadArea = document.getElementById('uploadArea');
const fileNameDisplay = document.getElementById('fileName');
const processBtn = document.getElementById('processBtn');
const loader = document.getElementById('loader');
const resultArea = document.getElementById('resultArea');
const downloadLink = document.getElementById('downloadLink');
const resetBtn = document.getElementById('resetBtn');
const errorArea = document.getElementById('errorArea');
const errorMsg = document.getElementById('errorMsg');
const logList = document.getElementById('logList');
const progressLog = document.getElementById('progressLog');
const mainContainer = document.getElementById('mainContainer');
const previewThead = document.getElementById('previewThead');
const previewTbody = document.getElementById('previewTbody');

let selectedFile = null;
const API_BASE = "http://localhost:8000";

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
    if (e.dataTransfer.files.length) {
        handleFileSelection(e.dataTransfer.files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length) {
        handleFileSelection(e.target.files[0]);
    }
});

function handleFileSelection(file) {
    const validExts = ['.csv', '.xlsx', '.xls'];
    const hasValidExt = validExts.some(ext => file.name.toLowerCase().endsWith(ext));
    
    if (!hasValidExt) {
        showError("Invalid file type. Please upload CSV or Excel.");
        processBtn.disabled = true;
        fileNameDisplay.textContent = "";
        selectedFile = null;
        return;
    }
    
    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    processBtn.disabled = false;
    hideError();
}

function showError(msg) {
    errorMsg.textContent = msg;
    errorArea.classList.remove('hidden');
}

function hideError() {
    errorArea.classList.add('hidden');
}

function addLog(msg) {
    const li = document.createElement('li');
    li.textContent = `> ${msg}`;
    logList.appendChild(li);
    progressLog.scrollTop = progressLog.scrollHeight;
}

processBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    hideError();
    processBtn.disabled = true;
    processBtn.classList.add('hidden');
    uploadArea.classList.add('hidden');
    loader.classList.remove('hidden');
    logList.innerHTML = '';
    
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
        addLog("Uploading file...");
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Server Error Failed to upload.");
        }

        const data = await response.json();
        const jobId = data.job_id;
        addLog(`Upload successful. Job ID: ${jobId}`);

        // Connect to SSE stream
        const eventSource = new EventSource(`${API_BASE}/stream/${jobId}`);

        const handleStreamError = (msg) => {
            loader.classList.add('hidden');
            processBtn.classList.remove('hidden');
            uploadArea.classList.remove('hidden');
            processBtn.disabled = false;
            showError(msg);
        };

        eventSource.onmessage = async (e) => {
            try {
                const eventData = JSON.parse(e.data);
                
                if (eventData.event === 'progress') {
                    addLog(eventData.data);
                } 
                else if (eventData.event === 'done') {
                    addLog("Processing Complete!");
                    eventSource.close();
                    await showResults(jobId);
                }
                else if (eventData.event === 'error') {
                    eventSource.close();
                    handleStreamError(eventData.data);
                }
            } catch (err) {
                eventSource.close();
                handleStreamError("Error parsing progress stream data: " + err.message);
            }
        };

        eventSource.onerror = (err) => {
            eventSource.close();
            handleStreamError("Connection to progress stream lost.");
        };

    } catch (err) {
        loader.classList.add('hidden');
        processBtn.classList.remove('hidden');
        uploadArea.classList.remove('hidden');
        processBtn.disabled = false;
        showError(err.message);
    }
});

async function showResults(jobId) {
    try {
        const response = await fetch(`${API_BASE}/api/preview/${jobId}`);
        if (!response.ok) throw new Error("Failed to load preview.");
        const data = await response.json();
        const previewData = data.preview;

        // Render preview table
        previewThead.innerHTML = '';
        previewTbody.innerHTML = '';
        
        if (previewData && previewData.length > 0) {
            const cols = Object.keys(previewData[0]);
            
            // Header
            const trHead = document.createElement('tr');
            cols.forEach(col => {
                const th = document.createElement('th');
                th.textContent = col;
                trHead.appendChild(th);
            });
            previewThead.appendChild(trHead);

            // Body
            previewData.forEach(row => {
                const trBody = document.createElement('tr');
                cols.forEach(col => {
                    const td = document.createElement('td');
                    td.textContent = row[col];
                    trBody.appendChild(td);
                });
                previewTbody.appendChild(trBody);
            });
            
            mainContainer.classList.add('wide');
        }

        loader.classList.add('hidden');
        resultArea.classList.remove('hidden');
        
        downloadLink.href = `${API_BASE}/download/${jobId}`;

    } catch(err) {
        showError(err.message);
    }
}

resetBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = "";
    fileNameDisplay.textContent = "";
    resultArea.classList.add('hidden');
    uploadArea.classList.remove('hidden');
    processBtn.classList.remove('hidden');
    processBtn.disabled = true;
    mainContainer.classList.remove('wide');
});
