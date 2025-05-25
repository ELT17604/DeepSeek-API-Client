# DeepSeek Web App

DeepSeek Web App is a web-based client for interacting with the DeepSeek API. This application allows users to input their API key, select models, and view outputs rendered in Markdown format.

## Project Structure

The project is organized as follows:

```
deepseek-web-app
├── static
│   ├── css
│   │   └── style.css          # Styles for the application
│   ├── js
│   │   ├── app.js             # Main JavaScript file for user interactions
│   │   ├── markdown.js         # Markdown rendering functions
│   │   └── crypto.js           # API key encryption and decryption
│   └── fonts
│       └── consolas.woff2     # Web font for code blocks
├── templates
│   └── index.html             # Main HTML file for the application
├── src
│   ├── app.py                 # Entry point for the Flask application
│   ├── models
│   │   └── deepseek_client.py  # Client model for DeepSeek API interaction
│   ├── utils
│   │   ├── encryption.py       # Encryption and decryption functions
│   │   └── storage.py          # API key storage and loading functions
│   └── routes
│       ├── __init__.py        # Initializes the routes module
│       ├── api.py             # API-related routes
│       └── chat.py            # Chat functionality routes
├── requirements.txt            # Required Python libraries and dependencies
├── config.py                   # Application configuration settings
├── run.py                      # Script to start the Flask application
└── README.md                   # Project documentation and usage instructions
```

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd deepseek-web-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Start the application:
   ```
   python run.py
   ```

2. Open your web browser and navigate to `http://localhost:5000`.

3. Enter your API key in the provided input field and click "初始化" to initialize the client.

4. Select a model from the dropdown menu to interact with the DeepSeek API.

5. View the output rendered in Markdown format in the output section.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for details.