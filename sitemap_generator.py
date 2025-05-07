import requests
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin, urlparse
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
import os
import time
import re
import gzip
from typing import List, Set, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SitemapGenerator:
    def __init__(self, root_url: str, max_urls: int = 1000, delay: float = 1.0, 
                 user_agent: str = "CustomCrawler/1.0", max_workers: int = 5):
        """
        Initialize the sitemap generator.
        
        Args:
            root_url: The root URL of the website to crawl
            max_urls: Maximum number of URLs to crawl (default: 1000)
            delay: Delay between requests in seconds (default: 1.0)
            user_agent: User agent string for requests (default: "CustomCrawler/1.0")
            max_workers: Maximum number of concurrent workers (default: 5)
        """
        self.root_url = self._normalize_url(root_url)
        self.max_urls = max_urls
        self.delay = delay
        self.user_agent = user_agent
        self.max_workers = max_workers
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create a requests session with custom headers."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        return session
        
    def _normalize_url(self, url: str) -> str:
        """Normalize URL by removing fragments and query parameters."""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"
    
    def is_valid_url(self, url: str) -> bool:
        """Check if the URL is valid and belongs to the root domain."""
        parsed_root = urlparse(self.root_url)
        parsed_url = urlparse(url)
        
        # Check if URL belongs to the root domain
        if parsed_url.netloc != parsed_root.netloc:
            return False
        
        # Exclude non-HTML resources
        non_html_extensions = r'\.(jpg|jpeg|png|gif|pdf|css|js|woff|woff2|ttf|ico|svg|zip|mp4|mp3)(\?.*)?$'
        if re.search(non_html_extensions, parsed_url.path, re.IGNORECASE):
            return False
        
        # Ensure URL uses http or https
        return parsed_url.scheme in ['http', 'https']
    
    def can_fetch_url(self, url: str, user_agent: Optional[str] = None) -> bool:
        """Check if the URL is allowed to be crawled according to robots.txt."""
        if user_agent is None:
            user_agent = self.user_agent
            
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        try:
            rp = RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            return rp.can_fetch(user_agent, url)
        except Exception as e:
            logger.warning(f"Could not parse robots.txt at {robots_url}: {e}")
            return True
    
    def _extract_links(self, url: str) -> Set[str]:
        """Extract all valid links from a page."""
        links = set()
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                normalized_url = self._normalize_url(absolute_url)
                
                if self.is_valid_url(normalized_url):
                    links.add(normalized_url)
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
        
        return links
    
    def crawl_site(self) -> List[str]:
        """Crawl the website starting from root_url and return a list of URLs."""
        crawled_urls = set()
        to_crawl = {self.root_url}
        visited = set()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while to_crawl and len(crawled_urls) < self.max_urls:
                futures = {}
                
                # Submit current batch of URLs for processing
                for url in to_crawl:
                    if url not in visited:
                        visited.add(url)
                        futures[executor.submit(self._process_url, url)] = url
                
                # Process completed futures
                for future in as_completed(futures):
                    url = futures[future]
                    try:
                        new_links = future.result()
                        
                        if url in crawled_urls:
                            continue
                            
                        if self.is_valid_url(url):
                            crawled_urls.add(url)
                            logger.info(f"Crawled: {url} ({len(crawled_urls)} URLs found)")
                            
                            # Add new links to the queue
                            for link in new_links:
                                if link not in visited and link not in to_crawl:
                                    to_crawl.add(link)
                    
                    except Exception as e:
                        logger.error(f"Error processing {url}: {e}")
                
                # Remove processed URLs from the queue
                to_crawl -= visited
                
                # Be polite: wait between batches
                time.sleep(self.delay)
        
        return sorted(crawled_urls)
    
    def _process_url(self, url: str) -> Set[str]:
        """Process a single URL and return discovered links."""
        if not self.can_fetch_url(url):
            logger.info(f"Skipping {url} (disallowed by robots.txt)")
            return set()
        
        return self._extract_links(url)
    def _determine_priority(self, url: str) -> str:
        """
        Determine priority based on URL pattern.
        
        Rules:
        1. High priority pages (priority = 1)
        2. Sub-category pages (priority = 0.9)
        3. Product pages (priority = 0.8)
        4. Other pages (priority = 0.6)
        """
  
        high_priority_pages = [
        "https://elghazawy.com/ar/", 
        "https://elghazawy.com/ar/sub-category/mobile-tablet",
        "https://elghazawy.com/ar/sub-category/computing",
        "https://elghazawy.com/ar/sub-category/home-appliances",
        "https://elghazawy.com/ar/sub-category/health-beauty",
        "https://elghazawy.com/ar/sub-category/electronics",
        "https://elghazawy.com/ar/sub-category/televisions",
        "https://elghazawy.com/ar/sub-category/kitchen-home",
        "https://elghazawy.com/ar/sub-category/stationery",
        "https://elghazawy.com/ar/sub-category/toys-baby",
        "https://elghazawy.com/ar/sub-category/fitness-supplies",
        "https://elghazawy.com/ar/sub-category/maintenance-tools",
        "https://elghazawy.com/ar/sub-category/electricity-connectors",
        "https://elghazawy.com/ar/sub-category/bags",
        "https://elghazawy.com/ar/sub-category/Fashion-",
        ]  
        
        # check if the URL matches any high-priority patterns
        for pattern in high_priority_pages:
            if re.search(pattern, url, re.IGNORECASE):
                return "1.0"
        
        #check if the URL matches any sub-category patterns
        if re.search(r'/sub-category/|/category/', url, re.IGNORECASE):
            return "0.9"
        
        #check if the URL matches any product patterns
        if re.search(r'/product/|/item/', url, re.IGNORECASE):
            return "0.8"
        
        # Default priority for other pages
        return "0.6"

    def generate_sitemap(self, urls: List[str], output_file: str = "sitemap.xml", 
                        compress: bool = False) -> str:
        """
        Generate a sitemap.xml file from a list of URLs with custom priorities.
        
        Args:
            urls: List of URLs to include in the sitemap
            output_file: Output file name (default: "sitemap.xml")
            compress: Whether to gzip compress the output (default: False)
            
        Returns:
            Path to the generated sitemap file
        """
        if not urls:
            raise ValueError("No URLs provided for sitemap generation")
        
        # Current date for lastmod
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Create XML structure
        urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        
        for url in urls:
            url_elem = SubElement(urlset, "url")
            SubElement(url_elem, "loc").text = url
            SubElement(url_elem, "lastmod").text = today
            

            priority = self._determine_priority(url)
            SubElement(url_elem, "priority").text = priority
            

            if priority == "1.0":
                changefreq = "daily"
            elif priority == "0.9":
                changefreq = "weekly"
            else:
                changefreq = "monthly"
                
            SubElement(url_elem, "changefreq").text = changefreq
        
    # def generate_sitemap(self, urls: List[str], output_file: str = "sitemap.xml", 
    #                     compress: bool = False) -> str:
    #     """
    #     Generate a sitemap.xml file from a list of URLs.
        
    #     Args:
    #         urls: List of URLs to include in the sitemap
    #         output_file: Output file name (default: "sitemap.xml")
    #         compress: Whether to gzip compress the output (default: False)
            
    #     Returns:
    #         Path to the generated sitemap file
    #     """
    #     if not urls:
    #         raise ValueError("No URLs provided for sitemap generation")
        
    #     # Current date for lastmod
    #     today = datetime.now().strftime("%Y-%m-%d")
        
    #     # Create XML structure
    #     urlset = Element("urlset", xmlns="http://www.sitemaps.org/schemas/sitemap/0.9")
        
    #     for url in urls:
    #         url_elem = SubElement(urlset, "url")
    #         SubElement(url_elem, "loc").text = url
    #         SubElement(url_elem, "lastmod").text = today
    #         SubElement(url_elem, "changefreq").text = "weekly"
    #         SubElement(url_elem, "priority").text = "0.5"
        
    #     # Convert to string and prettify
    #     rough_string = tostring(urlset, "utf-8")
    #     reparsed = minidom.parseString(rough_string)
    #     pretty_xml = reparsed.toprettyxml(indent="    ")
        
    #     # Save to file
    #     with open(output_file, "w", encoding="utf-8") as f:
    #         f.write(pretty_xml)
        
    #     if compress:
    #         self._compress_file(output_file)
    #         output_file += ".gz"
        
    #     logger.info(f"Sitemap saved to {output_file}")
    #     return output_file
    

    def _compress_file(self, filepath: str) -> None:
        """Compress a file using gzip."""
        with open(filepath, 'rb') as f_in:
            with gzip.open(f"{filepath}.gz", 'wb') as f_out:
                f_out.writelines(f_in)
        os.remove(filepath)

def main():
    # Configuration
    root_url = "https://elghazawy.com/ar"  # Your site's root domain
    max_urls = 1000  # Maximum number of URLs to crawl
    delay = 1.0  # Delay between requests (in seconds)
    output_file = "sitemap.xml"  # Output file name
# High-priority pages to include in the sitemap
    # high_property = 1.0  # Priority for high-priority pages
    # low_property = 0.5  # Priority for other pages
    try:
        # Initialize and run crawler
        generator = SitemapGenerator(root_url=root_url, max_urls=max_urls, delay=delay)
        logger.info(f"Starting crawl from {root_url}...")
        urls = generator.crawl_site()
        
        # Generate sitemap
        if urls:
            logger.info(f"Found {len(urls)} URLs. Generating sitemap...")
            generator.generate_sitemap(urls, output_file, compress=True)
        else:
            logger.warning("No URLs found. Sitemap not generated.")
            
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)



if __name__ == "__main__":
    main()