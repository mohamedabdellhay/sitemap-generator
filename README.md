# Sitemap Generator Tool

A web-based application for generating XML sitemaps for websites. This tool crawls a given website, collects URLs, and creates a sitemap file that can be downloaded. The application features a modern, responsive user interface with real-time logging and URL discovery tracking.

## Features

- **Website Crawling**: Crawls a website starting from a root URL to discover all accessible pages (up to a user-defined maximum).
- **Sitemap Generation**: Generates an XML sitemap file, with optional gzip compression.
- **Real-Time Logging**: Displays crawling logs in real-time using Server-Sent Events (SSE).
- **Dynamic URL Count**: Shows the number of URLs found during crawling in real-time.
- **Modern UI**: Clean, responsive design with a light overlay effect on the log box, icons, and interactive animations.
- **Performance Optimization**: Limits the number of log entries in the DOM to 100 to ensure smooth performance.
- **Customizable Crawling**: Allows users to configure maximum URLs, delay between requests, concurrent workers, and user agent.
- **Error Handling**: Displays errors clearly in the UI with detailed logging.

## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Icons**: Font Awesome
- **Logging**: Python `logging` module with file-based logs
- **Dependencies**: `sitemap_generator` (custom module), `flask`

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A modern web browser (Chrome, Firefox, Safari, etc.)

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/mohamedabdellhay/sitemap-generator.git
   cd sitemap-generator
   ```

2. **Create a Virtual Environment** (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:

   ```bash
   pip install flask
   ```

   _Note_: The `sitemap_generator` module is assumed to be a custom module. Ensure it is available in your project directory or install it if it's a third-party package.

4. **Ensure Project Structure**:
   The project should have the following structure:
   ```
   sitemap-generator/
   ├── app.py
   ├── templates/
   │   └── index.html
   ├── generated_sitemaps/
   └── app.log
   ```

## Usage

1. **Run the Application**:

   ```bash
   python app.py
   ```

   The app will start in debug mode on `http://127.0.0.1:5000`.

2. **Access the Web Interface**:
   Open your browser and navigate to `http://127.0.0.1:5000`.

3. **Generate a Sitemap**:

   - Enter the root URL of the website (e.g., `https://example.com`).
   - Configure optional settings (max URLs, delay, workers, user agent, compression).
   - Click "Generate Sitemap".
   - Watch real-time logs and the number of URLs found in the UI.
   - Once complete, download the generated sitemap file from the results section.

4. **View Logs**:
   - Logs are displayed in the UI with a light overlay effect for a modern look.
   - Logs are also saved to `app.log` for debugging.

## Configuration

The following settings can be adjusted in the UI:

- **Root URL**: The starting point for crawling (required).
- **Maximum URLs**: The maximum number of URLs to crawl (default: 1000).
- **Delay**: Time between requests in seconds (default: 1.0).
- **Concurrent Workers**: Number of parallel crawling threads (default: 5).
- **User Agent**: Custom user agent for crawling (default: `CustomCrawler/1.0`).
- **Compress**: Option to compress the sitemap file using gzip.

## Performance Notes

- The frontend limits log entries to 100 to prevent DOM performance issues.
- The log box uses `overflow: hidden` to ensure content stays within bounds.
- A light overlay effect is applied to the log box for a polished appearance.

## Limitations

- The current implementation updates the URL count only at the end of crawling. To enable real-time URL count updates, the `SitemapGenerator` module needs to support incremental URL reporting (e.g., via callbacks or yielding URLs).
- Log file (`app.log`) may grow large over time. Consider implementing log rotation for production use (e.g., using `logging.handlers.RotatingFileHandler`).
- The app is designed for single-user, local use. For production, additional security and scalability measures are needed.

## Future Improvements

- Add real-time progress bar based on the percentage of URLs crawled.
- Implement a "Stop Crawling" button to cancel ongoing crawls.
- Add a "Clear Logs" button to reset the log display.
- Enhance `SitemapGenerator` to support incremental URL count updates.
- Add support for multi-user sessions and authentication.
- Implement log rotation to manage `app.log` size.

## Troubleshooting

- **App doesn't start**: Ensure Flask is installed (`pip install flask`) and the project structure is correct.
- **No URLs found**: Check the root URL, ensure the site is accessible, and adjust the max URLs or delay settings.
- **Logs not appearing**: Verify that `app.log` is writable and the SSE connection is active.
- **Performance issues**: Confirm that `MAX_LOGS` is set to 100 in `index.html` to limit DOM size.

## Contributing

Contributions are welcome! Please:

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -m 'Add feature'`).
4. Push to the branch (`git push origin feature-name`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contact

For questions or feedback, please contact the project maintainer at [mohamedabdellhay1@gmail.com].
