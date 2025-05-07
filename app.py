from flask import Flask, render_template, request, jsonify, send_file, Response, redirect, url_for
import time
import json
import os
import logging
from datetime import datetime
from sitemap_generator import SitemapGenerator  
from urllib.parse import urlparse

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'last_work'
LOG_FILE = 'app.log'

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logging
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create upload folder
try:
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    logger.info(f"Created or verified upload folder: {app.config['UPLOAD_FOLDER']}")
except Exception as e:
    logger.error(f"Failed to create upload folder: {str(e)}")

# Test write permissions
try:
    test_path = os.path.join(app.config['UPLOAD_FOLDER'], 'test.txt')
    with open(test_path, 'w') as f:
        f.write('Test')
    logger.info(f"Test file created successfully: {test_path}")
    os.remove(test_path)
except Exception as e:
    logger.error(f"Failed to create test file: {str(e)}")

# Global variable for URL count
current_url_count = 0

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_sitemap():
    global current_url_count
    current_url_count = 0
    data = request.json
    root_url = data.get('root_url')
    logger.info(f"Received request to generate sitemap for {root_url}")

    try:
        generator = SitemapGenerator(
            root_url=root_url,
            max_urls=int(data.get('max_urls', 1000)),
            delay=float(data.get('delay', 1.0)),
            user_agent=data.get('user_agent', "CustomCrawler/1.0"),
            max_workers=int(data.get('max_workers', 5))
        )
        
        logger.info("Starting crawl...")
        urls = generator.crawl_site()
        
        if not urls:
            logger.error("No URLs found during crawling")
            return jsonify({"error": "No URLs found during crawling"}), 400
        
        logger.debug(f"URLs to include in sitemap: {urls}")
        
        # Generate filename from root URL and timestamp
        parsed_url = urlparse(root_url)
        domain = parsed_url.netloc.replace('.', '_')  # e.g., elghazawy_com
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{domain}_{timestamp}.xml"
        if data.get('compress', False):
            filename += '.gz'
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        logger.info(f"Generating sitemap: {output_path}")
        try:
            # Generate XML with dynamic changefreq and priority
            xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
            xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            for url in urls:
                # Determine changefreq and priority
                url_lower = url.lower()
                if url == root_url:
                    priority = '1.0'
                    changefreq = 'daily'
                    logger.debug(f"URL {url}: Root URL (priority={priority}, changefreq={changefreq})")
                elif 'sub-category' in url_lower:
                    priority = '0.9'
                    changefreq = 'weekly'
                    logger.debug(f"URL {url}: Sub-category (priority={priority}, changefreq={changefreq})")
                elif 'product' in url_lower:
                    priority = '0.8'
                    changefreq = 'weekly'
                    logger.debug(f"URL {url}: Product (priority={priority}, changefreq={changefreq})")
                else:
                    priority = '0.6'
                    changefreq = 'weekly'
                    logger.debug(f"URL {url}: Default (priority={priority}, changefreq={changefreq})")
                
                xml_content += '  <url>\n'
                xml_content += f'    <loc>{url}</loc>\n'
                xml_content += f'    <lastmod>{datetime.now().strftime("%Y-%m-%d")}</lastmod>\n'
                xml_content += f'    <changefreq>{changefreq}</changefreq>\n'
                xml_content += f'    <priority>{priority}</priority>\n'
                xml_content += '  </url>\n'
            xml_content += '</urlset>'
            
            # Write file (compressed or uncompressed)
            logger.info(f"Writing sitemap to: {output_path}")
            if data.get('compress', False):
                import gzip
                with gzip.open(output_path, 'wt', encoding='utf-8') as f:
                    f.write(xml_content)
            else:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(xml_content)
            
            if not os.path.exists(output_path):
                logger.error(f"Sitemap file not created: {output_path}")
                return jsonify({"error": f"Failed to create sitemap file: {output_path}"}), 500
            logger.info(f"Sitemap file created successfully: {output_path}")
        except Exception as e:
            logger.error(f"Error writing sitemap file: {str(e)}")
            return jsonify({"error": f"Failed to write sitemap file: {str(e)}"}), 500
        
        current_url_count = len(urls)
        logger.info(f"Sitemap generated with {current_url_count} URLs")
        return jsonify({
            "message": "Sitemap generated successfully",
            "filename": filename,
            "url_count": current_url_count,
            "redirect": url_for('sitemaps')
        })
    
    except Exception as e:
        logger.error(f"Error generating sitemap: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/download/<filename>')
def download_sitemap(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    logger.info(f"Attempting to download file: {file_path}")
    if not os.path.exists(file_path):
        logger.error(f"Download failed: File {file_path} not found")
        return jsonify({"error": "File not found"}), 404
    
    logger.info(f"Downloading file: {filename}")
    return send_file(file_path, as_attachment=True)

@app.route('/sitemaps')
def sitemaps():
    try:
        sitemaps = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.xml', '.xml.gz'))]
        return render_template('sitemaps.html', sitemaps=sitemaps)
    except Exception as e:
        logger.error(f"Error listing sitemaps: {str(e)}")
        return render_template('sitemaps.html', sitemaps=[], error=str(e))

@app.route('/generate-log')
def generate_log():
    global current_url_count
    def stream_logs():
        last_position = 0
        while True:
            try:
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    f.seek(last_position)
                    new_logs = f.read()
                    if new_logs:
                        url_count = current_url_count
                        for line in new_logs.splitlines():
                            if "URLs found" in line:
                                try:
                                    count = int(line.split('(')[1].split(' URLs found')[0])
                                    url_count = count
                                except (IndexError, ValueError):
                                    pass
                        yield f'data: {json.dumps({"log": new_logs, "url_count": url_count})}\n\n'
                    last_position = f.tell()
            except FileNotFoundError:
                yield f'data: {json.dumps({"log": "Log file not found", "url_count": current_url_count})}\n\n'
                break
            time.sleep(1)

    return Response(stream_logs(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)