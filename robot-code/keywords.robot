*** Settings ***
Documentation    Shared keywords and test data for datasource API tests

Library    Collections
Library    BuiltIn


*** Variables ***
${DATASOURCE_PAYLOAD}
...    {
...      "lat": 5.9930956844705605,
...      "lon": -172.99270463893933,
...      "disableEstimations": true,
...      "temporalGranularity": "hourly"
...    }

${UPDATED_DATASOURCE_PAYLOAD}
...    {
...      "lat": 5.97,
...      "lon": -172.97,
...      "disableEstimations": false,
...      "temporalGranularity": "hourly"
...    }
