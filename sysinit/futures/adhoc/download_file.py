import urllib.request

from sysdata.config.production_config import get_production_config

config = get_production_config()

url = config.get_element("download_url")
filename = config.get_element("download_filename")

urllib.request.urlretrieve(url, filename)
print(f"Downloaded {filename}")
