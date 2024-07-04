import os
import requests
from bs4 import BeautifulSoup
import sqlite3
from flask import Flask, render_template_string, send_from_directory
from urllib.parse import urljoin, urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def download_asset(url, folder):
    try:
        os.makedirs(folder, exist_ok=True)
        local_filename = os.path.join(folder, os.path.basename(urlparse(url).path))
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        logging.info(f"Downloaded asset {url} to {local_filename}")
        return local_filename
    except Exception as e:
        logging.error(f"Failed to download asset {url}: {e}")
        return url

def fetch_and_save_page(url, db_path, asset_folder='static'):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        logging.info(f"Fetched HTML content for {url}")
        print(soup.prettify())  # Debug print

        for tag in soup.find_all(['img', 'link', 'script']):
            if tag.name == 'img' and tag.get('src'):
                asset_url = urljoin(url, tag['src'])
                local_path = download_asset(asset_url, asset_folder)
                tag['src'] = local_path
            elif tag.name == 'link' and tag.get('href'):
                asset_url = urljoin(url, tag['href'])
                local_path = download_asset(asset_url, asset_folder)
                tag['href'] = local_path
            elif tag.name == 'script' and tag.get('src'):
                asset_url = urljoin(url, tag['src'])
                local_path = download_asset(asset_url, asset_folder)
                tag['src'] = local_path

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('CREATE TABLE IF NOT EXISTS pages (url TEXT, content TEXT)')
        c.execute('INSERT INTO pages (url, content) VALUES (?, ?)', (url, str(soup)))
        conn.commit()
        conn.close()
        logging.info("Website content saved to database.")
    except Exception as e:
        logging.error(f"Failed to fetch and save page {url}: {e}")

def create_flask_app(db_path, asset_folder='static'):
    app = Flask(__name__, static_folder=asset_folder)
    
    @app.route('/')
    def index():
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute('SELECT content FROM pages')
            page_content = c.fetchone()[0]
            conn.close()
            logging.info("Serving page content from database.")
            print(page_content)  # Debug print
            return render_template_string(page_content)
        except Exception as e:
            logging.error(f"Failed to load page content from database: {e}")
            return "Error loading page content"
    
    @app.route('/<path:filename>')
    def static_files(filename):
        try:
            return send_from_directory(asset_folder, filename)
        except Exception as e:
            logging.error(f"Failed to serve static file {filename}: {e}")
            return "Error serving static file"
    
    return app

def main():
    url = input("Enter the URL of the website to clone: ")
    db_path = 'cloned_site.db'
    
    fetch_and_save_page(url, db_path)
    
    app = create_flask_app(db_path)
    app.run(debug=True)

if __name__ == '__main__':
    main()

