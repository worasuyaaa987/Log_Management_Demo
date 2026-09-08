import os
from opensearchpy import OpenSearch
from dotenv import load_dotenv

load_dotenv()

OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "http://opensearch:9200")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD", "StrongPassword123!")

# Connect via HTTPS if pointing to the default docker image
host_url = OPENSEARCH_HOST
if "opensearch:9200" in host_url and not host_url.startswith("https"):
    host_url = host_url.replace("http://", "https://")

client = OpenSearch(
    hosts=[host_url],
    http_compress=True,
    http_auth=('admin', OPENSEARCH_PASSWORD),
    use_ssl=True,
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False
)

def get_db():
    return client
