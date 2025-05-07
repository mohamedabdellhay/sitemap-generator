from flask import Flask, render_template, request, jsonify, send_file, Response
import time
import json
import os
import logging
from datetime import datetime
from sitemap_generator import SitemapGenerator  

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'generated_sitemaps'
LOG_FILE = 'app.log'  # File to store logs

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),  # Write logs to app.log
        logging.StreamHandler()  # Also output to console
    ]
)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_sitemap():
    data = request.json
    logger.info(f"Received request to generate sitemap for {data.get('root_url')}")

    try:
        # Initialize sitemap generator
        generator = SitemapGenerator(
            root_url=data['root_url'],
            max_urls=int(data.get('max_urls', 1000)),
            delay=float(data.get('delay', 1.0)),
            user_agent=data.get('user_agent', "CustomCrawler/1.0"),
            max_workers=int(data.get('max_workers', 5))
        )
        
        # Crawl and collect URLs
        logger.info("Starting crawl...")
        urls = generator.crawl_site()
        
        if not urls:
            logger.error("No URLs found during crawling")
            return jsonify({"error": "No URLs found during crawling"}), 400
        
        # Generate sitemap file
        filename = f"sitemap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logger.info(f"Generating sitemap: {filename}")
        generator.generate_sitemap(
            urls=urls,
            output_file=output_path,
            compress=data.get('compress', False)
        )
        
        logger.info(f"Sitemap generated with {len(urls)} URLs")
        return jsonify({
            "message": "Sitemap generated successfully",
            "filename": filename,
            "url_count": len(urls)
        })
    
    except Exception as e:
        logger.error(f"Error generating sitemap: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_sitemap(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        logger.error(f"Download failed: File {filename} not found")
        return jsonify({"error": "File not found"}), 404
    
    logger.info(f"Downloading file: {filename}")
    return send_file(file_path, as_attachment=True)

@app.route('/generate-log')
def generate_log():
    def stream_logs():
        last_position = 0
        while True:
            try:
                # Open the log file and seek to the last known position
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_logs = f.read()
                    if new_logs:
                        # Send new log lines to the client
                        yield f'data: {json.dumps({"log": new_logs})}\n\n'
                    last_position = f.tell()  # Update the last read position
            except FileNotFoundError:
                yield f'data: {json.dumps({"log": "Log file not found"})}\n\n'
                break

            # Sleep briefly to avoid overloading the server
            time.sleep(1)

    return Response(stream_logs(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)