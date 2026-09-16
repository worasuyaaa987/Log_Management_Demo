#!/bin/bash
# init_retention.sh
# Script to configure 7-day retention policy in OpenSearch via ISM (Index State Management)

OPENSEARCH_URL=${OPENSEARCH_URL:-"https://localhost:9200"}
ADMIN_PASS=${OPENSEARCH_INITIAL_ADMIN_PASSWORD:-"admin"}
AUTH="admin:${ADMIN_PASS}"

echo "Waiting for OpenSearch to be available..."
until curl -k -s -u $AUTH $OPENSEARCH_URL | grep -q '"tagline" : "The OpenSearch Project: https://opensearch.org/"'; do
  sleep 5
done

echo "OpenSearch is up! Creating 7-day Retention Policy..."

curl -k -X PUT "$OPENSEARCH_URL/_plugins/_ism/policies/7-day-retention" -u $AUTH -H 'Content-Type: application/json' -d'
{
  "policy": {
    "description": "Delete logs older than 7 days",
    "default_state": "active",
    "states": [
      {
        "name": "active",
        "actions": [],
        "transitions": [
          {
            "state_name": "delete",
            "conditions": {
              "min_index_age": "7d"
            }
          }
        ]
      },
      {
        "name": "delete",
        "actions": [
          {
            "delete": {}
          }
        ],
        "transitions": []
      }
    ]
  }
}
'

echo -e "\nPolicy created. Now applying to index template for 'logs-*'..."

curl -k -X PUT "$OPENSEARCH_URL/_index_template/logs_template" -u $AUTH -H 'Content-Type: application/json' -d'
{
  "index_patterns": ["logs-*"],
  "template": {
    "settings": {
      "plugins.index_state_management.policy_id": "7-day-retention"
    }
  }
}
'

echo -e "\nRetention setup complete! All new indices matching 'logs-*' will be deleted after 7 days."
