import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def save_file(content, path):
    with open(path, 'wb') as f:
        f.write(content)

def download_assets(soup, base_url, asset_tag, attr, folder):
    assets = soup.find_all(asset_tag)
    if not os.path.exists(folder):
        os.makedirs(folder)
    for asset in assets:
        asset_url = urljoin(base_url, asset.get(attr))
        if asset_url.startswith(base_url):
            asset_content = requests.get(asset_url).content
            asset_path = os.path.join(folder, os.path.basename(asset_url))
            save_file(asset_content, asset_path)
            asset[attr] = os.path.join(folder, os.path.basename(asset_url))

def clone_website(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Download CSS
    download_assets(soup, url, 'link', 'href', 'css')

    # Download JS
    download_assets(soup, url, 'script', 'src', 'js')

    # Download Images
    download_assets(soup, url, 'img', 'src', 'images')

    # Save HTML
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(str(soup))

if __name__ == "__main__":
    website_url = "https://www.trainingndt.com/complete-ndt-training/"
    clone_website(website_url)
