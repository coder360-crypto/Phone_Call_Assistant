# Phone Call Assistant

An AI-powered phone call assistant that automates appointment booking and other customer interactions over the phone.

## Features

- **Multi-platform Voice AI:** Supports Vapi, Retell, and Twilio for handling phone calls.
- **Flexible Scheduling:** Integrates with Google Calendar, Cal.com, and other CRMs.
- **Workflow Automation:** Connects to Make.com and Zapier to trigger custom workflows.
- **RESTful API:** Provides a comprehensive API for managing assistants, calls, and appointments.
- **Webhook Integration:** Handles incoming webhooks from various service providers.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites

- Python 3.8+
- `uv` (or `pip`) for package management
- A registered account with the voice AI, scheduling, and automation providers you intend to use.

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/phone-call-assistant.git
    cd phone-call-assistant
    ```

2.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**

    Using `uv`:
    ```bash
    uv pip install -r requirements.txt
    ```
    Or using `pip`:
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

1.  **Create a `.env` file:**

    Copy the example environment file to create your own configuration:
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file:**

    Open the `.env` file and fill in the required credentials and settings for the services you want to use.

    -   `SECRET_KEY`: **Important!** Change this to a long, random, and secure string.
    -   `VOICE_AI_PLATFORM`: Set this to your chosen voice AI provider (e.g., `vapi`).
    -   `SCHEDULING_PLATFORM`: Set this to your chosen scheduling provider (e.g., `google_calendar`).
    -   `AUTOMATION_PLATFORM`: Set this to your chosen automation provider (e.g., `makecom`).
    -   Fill in the API keys and other details for your chosen platforms.

3.  **Google Calendar Setup (if used):**

    If you are using Google Calendar, you will need to enable the API and create credentials.

    1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
    2.  Create a new project or select an existing one.
    3.  Enable the **Google Calendar API**.
    4.  Go to **Credentials**, click **Create Credentials**, and select **OAuth client ID**.
    5.  Choose **Desktop app** as the application type.
    6.  Download the JSON file and save it as `credentials.json` in the project root (or update `GOOGLE_CALENDAR_CREDENTIALS_PATH` in your `.env` file).

    The first time you run the application, you will be prompted to authorize access to your Google account in the browser.

### Running the Application

To start the FastAPI server, run the following command from the project root:

```bash
python app/main.py
```

The application will be available at `http://127.0.0.1:8000`.

## API Endpoints

The API includes endpoints for managing assistants, calls, scheduling, and more. A full API reference can be found in `docs/api_reference.md`.

-   `/health`: Health check endpoint.
-   `/config`: Get the current application configuration.
-   `/voice-ai/*`: Endpoints for interacting with the voice AI platform.
-   `/scheduling/*`: Endpoints for managing appointments and availability.
-   `/webhooks/*`: Endpoints for receiving webhooks from external services.

## Project Structure

```
.
├── app/                # Main application source code
│   ├── automation/     # Automation service integrations
│   ├── models/         # Pydantic data models
│   ├── scheduling/     # Scheduling service integrations
│   ├── utils/          # Utility functions
│   └── voice_ai/       # Voice AI service integrations
├── config/             # Configuration files
├── docs/               # Project documentation
├── scripts/            # Helper scripts
├── tests/              # Application tests
├── .env.example        # Example environment file
├── requirements.txt    # Python dependencies
└── README.md           # This file
```
