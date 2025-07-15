# SAG AI Chatbot
This project implements an AI Chatbot capable of generating dashboard templates, summarizing data files, and querying a FIWARE instance. It leverages Langchain for multi-agent orchestration, Flask for the backend API, and a simple HTML/JavaScript frontend for interaction.

## Features
* Dashboard Template Generation: Generate dashboard templates based on user requests, utilizing data column information from uploaded files.

* Data Summarization: Summarize CSV or Excel data files, providing key insights and statistics.

* FIWARE Integration: Query FIWARE Orion for information such as parking spots and product details.

* File Uploads: Easily upload CSV, XLS, XLSX, and TXT files for analysis and summarization.

* Containerized Environment: Run the backend, frontend, FIWARE Orion, and MongoDB using Docker Compose for easy setup.

## Technologies Used
Backend: Python (Flask, Langchain, Pandas, Requests)

AI Model: OpenAI GPT-4o (via Langchain)

Database: MongoDB

FIWARE Components: FIWARE Orion Context Broker

Frontend: HTML, JavaScript, Tailwind CSS, Marked.js

Containerization: Docker, Docker Compose

File Descriptions
ai_agent.py: Contains the core AI logic using Langchain. It defines multiple agents (template generation, data summarization, FIWARE querying) and integrates them with various tools.

app.py: The Flask application that serves as the backend API. It handles file uploads to the mangodata folder and processes chat messages by interacting with the AI agent.

data_tools.py: Provides Python tools for data analysis, specifically extract_summary to get statistical information and extract_column_names to retrieve column headers from CSV and Excel files. These tools are used by the AI agent.

fiware_query_tool.py: Implements tools for querying a FIWARE Orion Context Broker instance. It includes functions to retrieve parking spot information and product details.

index.html: The frontend HTML file that provides the user interface for the chat application, including message display, input, and file upload functionalities.

populate_fiware.py: A utility script to populate your FIWARE Orion instance with initial parking and product data from JSON files.

docker-compose.yaml: Defines the Docker services required to run the application, including the FIWARE Orion Context Broker, MongoDB, and placeholders for your backend/frontend services.

Setup and Installation
Follow these steps to set up and run the SAG AI Chatbot on your local machine.

Prerequisites
Docker and Docker Compose installed.

Python 3.8+

An OpenAI API Key.

1. Clone the Repository
`git clone <repository_url>
cd <repository_directory>`
2. Set Up Environment Variables
Create a .env file in the root directory of the project and add your OpenAI API key:
`OPENAI_API_KEY="your_openai_api_key_here"`
If your FIWARE Orion instance is not at the default http://localhost:1026, you can also specify:
`ORION_URL="http://your_orion_ip:1026"
FIWARE_SERVICE="smart_data_service"
FIWARE_SERVICE_PATH="/data"`
3. Run Docker Compose (FIWARE and MongoDB)
Navigate to the directory containing docker-compose.yaml and start the services:
`docker-compose up -d`
This will spin up orion (FIWARE Orion Context Broker) and mongo (MongoDB) containers. Ensure they are running and healthy before proceeding. You can check their status with docker-compose ps.
4. Install Python Dependencies
It's recommended to use a virtual environment:
`docker-compose up -d`
`source venv/bin/activate # On Windows, use venv\Scripts\activate`
5. Populate FIWARE (Optional but Recommended)
You can use the populate_fiware.py script to add sample data to your Orion instance. You will be prompted to provide paths to parking and product data files (e.g., parking_data.json, product_data.json - these are not provided in the uploaded files but are assumed to exist for the script).
`python populate_fiware.py`
6. Run the Flask Application
`python app.py`
The Flask app will start, and you should see output indicating that the AI Agent is initialized and the upload folder exists.
7. Open the Frontend
Open index.html in your web browser. You should see the chat interface.
Usage
Upload a File: Use the "+" button to upload a CSV, XLS, or XLSX file. The file will be saved to the mangodata folder, and the chatbot will acknowledge the upload.
Summarize Data: After uploading a file, you can ask the chatbot to summarize it. For example: "summarize my_data.csv".
Generate Dashboard Template: Request a dashboard template. You can refer to the uploaded file, e.g., "generate a pie chart template for sales_data.xlsx showing sales by region".
Query FIWARE: Ask questions related to parking spots or products if you have populated your FIWARE instance. For example: "Find the closest free parking spot near latitude 34.733333, longitude 10.766667". or "What is the info about product 'Mango Fresh'?"
