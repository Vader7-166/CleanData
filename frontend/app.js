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

const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');

let selectedFile = null;

// Drag and drop setup
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

processBtn.addEventListener('click', async () => {
    if (!selectedFile) return;
    
    const user = usernameInput.value;
    const pass = passwordInput.value;
    
    if(!user || !pass) {
        showError("Please provide Username and Password.");
        return;
    }

    hideError();
    processBtn.disabled = true;
    processBtn.classList.add('hidden');
    uploadArea.classList.add('hidden');
    loader.classList.remove('hidden');
    document.getElementById('authSection').classList.add('hidden');

    const formData = new FormData();
    formData.append('file', selectedFile);

    const headers = new Headers();
    headers.append('Authorization', 'Basic ' + btoa(user + ':' + pass));

    try {
        // Change URL if deployed elsewhere
        const response = await fetch('http://localhost:8000/upload', {
            method: 'POST',
            body: formData,
            headers: headers
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Server Error Failed to process.");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        
        let outName = "cleaned_" + selectedFile.name;
        
        loader.classList.add('hidden');
        resultArea.classList.remove('hidden');
        downloadLink.href = url;
        downloadLink.download = outName;

    } catch (err) {
        loader.classList.add('hidden');
        processBtn.classList.remove('hidden');
        uploadArea.classList.remove('hidden');
        document.getElementById('authSection').classList.remove('hidden');
        processBtn.disabled = false;
        showError(err.message);
    }
});

resetBtn.addEventListener('click', () => {
    selectedFile = null;
    fileInput.value = "";
    fileNameDisplay.textContent = "";
    resultArea.classList.add('hidden');
    uploadArea.classList.remove('hidden');
    processBtn.classList.remove('hidden');
    document.getElementById('authSection').classList.remove('hidden');
    processBtn.disabled = true;
});
