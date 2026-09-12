import os
from opensearchpy import OpenSearch
from dotenv import load_dotenv

load_dotenv()

OPENSEARCH_URL = os.getenv("OPENSEARCH_URL", "https://opensearch:9200")
OPENSEARCH_PASSWORD = os.getenv("OPENSEARCH_INITIAL_ADMIN_PASSWORD", "admin")

client = OpenSearch(
    hosts=[OPENSEARCH_URL],
    http_compress=True,
    http_auth=('admin', OPENSEARCH_PASSWORD),
    use_ssl=OPENSEARCH_URL.startswith("https"),
    verify_certs=False,
    ssl_assert_hostname=False,
    ssl_show_warn=False
)

def get_db():
    return client
