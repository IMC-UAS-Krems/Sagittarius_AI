document.addEventListener('DOMContentLoaded', () => {
    const chatBox = document.getElementById('chat-box');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const csvFileInput = document.getElementById('csvFileInput');
    const uploadButton = document.getElementById('uploadButton');
    const uploadStatus = document.getElementById('uploadStatus');

    let lastUploadedFileName = null; // To keep track of the last uploaded file

    // Function to add a message to the chat box
    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', `${sender}-message`);
        messageDiv.textContent = message;
        chatBox.appendChild(messageDiv);
        chatBox.scrollTop = chatBox.scrollHeight; // Scroll to bottom
    }

    // Function to display upload status
    function setUploadStatus(message, type = 'info') {
        uploadStatus.textContent = message;
        uploadStatus.className = 'status-message ' + type;
        setTimeout(() => {
            uploadStatus.textContent = '';
            uploadStatus.className = 'status-message';
        }, 5000); // Clear message after 5 seconds
    }

    // Function to send message to backend
    async function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;

        addMessage(message, 'user');
        userInput.value = ''; // Clear input

        // Add a temporary loading message for better UX
        const loadingMessageDiv = document.createElement('div');
        loadingMessageDiv.classList.add('message', 'bot-message');
        loadingMessageDiv.textContent = '...typing...';
        chatBox.appendChild(loadingMessageDiv);
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            // Include the last uploaded filename in the chat request if available
            const payload = {
                message: message,
                last_uploaded_file: lastUploadedFileName
            };

            const response = await fetch('http://127.0.0.1:5000/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            // Remove loading message
            if (chatBox.contains(loadingMessageDiv)) {
                chatBox.removeChild(loadingMessageDiv);
            }

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.response || `HTTP error! status: ${response.status}`;
                console.error('Backend responded with an error:', errorMessage, response);
                addMessage(`Bot Error: ${errorMessage}`, 'bot');
                return;
            }

            const data = await response.json();
            addMessage(data.response, 'bot');
        } catch (error) {
            // Remove loading message on network error
            if (chatBox.contains(loadingMessageDiv)) {
                chatBox.removeChild(loadingMessageDiv);
            }
            console.error('Network or parsing error:', error);
            addMessage('Oops! Could not connect to the chatbot server. Please check if the backend is running.', 'bot');
        }
    }

    // Function to handle file upload
    async function uploadFile() {
        const file = csvFileInput.files[0];
        if (!file) {
            setUploadStatus('Please select a file first.', 'error');
            return;
        }

        setUploadStatus('Uploading...', 'info');

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://127.0.0.1:5000/upload', {
                method: 'POST',
                body: formData // No 'Content-Type' header needed for FormData; browser sets it
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorMessage = errorData.message || `HTTP error! status: ${response.status}`;
                throw new Error(errorMessage);
            }

            const data = await response.json();
            setUploadStatus(data.message, 'success');
            lastUploadedFileName = data.filename; // Store the filename for later use
            addMessage(`File "${data.filename}" uploaded successfully to 'mangodata' folder. You can now refer to it in your queries.`, 'bot');
            console.log('File uploaded:', data.filename);
        } catch (error) {
            setUploadStatus(`Upload failed: ${error.message}`, 'error');
            console.error('Upload error:', error);
        }
    }

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            sendMessage();
        }
    });
    uploadButton.addEventListener('click', uploadFile);

    // Initial message from bot
    addMessage("Hello! I'm your AI Chatbot. You can upload a file or ask me to generate a dashboard template or summarize a data file.", 'bot');
});