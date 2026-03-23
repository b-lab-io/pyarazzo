*** Settings ***
Documentation    Configuration and environment settings for datasource tests

*** Variables ***
# Environment Configuration
${ENV}                        local
${BASE_URL_LOCAL}             http://localhost:8000
${BASE_URL_STAGING}           https://staging-api.example.com
${BASE_URL_PRODUCTION}        https://api.example.com

# Default partition for multi-tenant scenarios
${DEFAULT_PARTITION}          default-partition

# Test data defaults
${DEFAULT_TIMEOUT}            10s
${DEFAULT_RETRY_LIMIT}        3
${DEFAULT_RETRY_INTERVAL}     1s

# Location ID (UUID format)
${TEST_LOCATION_ID}           550e8400-e29b-41d4-a716-446655440000

# Datasource payload templates
${CREATE_DATASOURCE_PAYLOAD}
...    {
...      "lat": 5.9930956844705605,
...      "lon": -172.99270463893933,
...      "disableEstimations": true,
...      "temporalGranularity": "hourly"
...    }

${UPDATE_DATASOURCE_PAYLOAD}
...    {
...      "lat": 5.97,
...      "lon": -172.97,
...      "disableEstimations": false,
...      "temporalGranularity": "hourly"
...    }

# HTTP Status Codes
${STATUS_OK}                  200
${STATUS_CREATED}             201
${STATUS_NO_CONTENT}          204
${STATUS_BAD_REQUEST}         400
${STATUS_UNAUTHORIZED}        401
${STATUS_FORBIDDEN}           403
${STATUS_NOT_FOUND}           404
${STATUS_SERVER_ERROR}        500
