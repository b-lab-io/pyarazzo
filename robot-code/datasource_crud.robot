*** Settings ***
Documentation    E2E Testing Workflow for Datasource CRUD Operations
...              Tests the create, read, update, and delete operations
...              for datasources in the electricitymap-proxy service

Library    RequestsLibrary
Library    Collections
Library    String

Resource    keywords.robot

Suite Setup        Initialize Test Suite
Suite Teardown     Teardown Test Suite

*** Variables ***
${BASE_URL}           http://localhost:8000
${CONTENT_TYPE}       application/json
${X_PARTITION}        default-partition
${LOCATION_ID}        550e8400-e29b-41d4-a716-446655440000
${DATASOURCE_ID}      ${EMPTY}


*** Test Cases ***
Test Datasource CRUD Workflow
    [Documentation]    Verify complete CRUD workflow for datasources
    [Tags]            crud    workflow    datasource

    Create Datasource And Store ID
    Verify Created Datasource Exists
    Verify Datasource In All List
    Update Datasource Details
    Delete Datasource


*** Keywords ***
Initialize Test Suite
    [Documentation]    Setup test environment and create HTTP session
    Create Session    datasource_api    ${BASE_URL}    verify=False

Teardown Test Suite
    [Documentation]    Clean up test resources
    Delete All Sessions

Create Datasource And Store ID
    [Documentation]    Step 1: Create a new datasource
    ...                Expects HTTP 201 response
    ...                Captures datasource ID from response

    ${payload}=    Create Dictionary
    ...    data=${DATASOURCE_PAYLOAD}
    
    ${headers}=    Create Dictionary
    ...    X-Partition=${X_PARTITION}
    
    ${response}=    POST Request
    ...    datasource_api
    ...    /locations/${LOCATION_ID}/datasources
    ...    json=${payload}
    ...    headers=${headers}
    
    Should Be Equal As Integers    ${response.status_code}    201    
    ...    msg=Failed to create datasource. Status: ${response.status_code}
    
    ${response_data}=    Get From Dictionary    ${response.json()}    id
    Set Suite Variable    ${DATASOURCE_ID}    ${response_data}
    
    Log    Created datasource with ID: ${DATASOURCE_ID}

Verify Created Datasource Exists
    [Documentation]    Step 2: Retrieve the created datasource
    ...                Expects HTTP 200 response

    ${headers}=    Create Dictionary
    ...    X-Partition=${X_PARTITION}
    
    ${response}=    GET Request
    ...    datasource_api
    ...    /locations/${LOCATION_ID}/datasources/${DATASOURCE_ID}
    ...    headers=${headers}
    
    Should Be Equal As Integers    ${response.status_code}    200
    ...    msg=Failed to retrieve datasource. Status: ${response.status_code}
    
    ${response_data}=    Get From Dictionary    ${response.json()}    id
    Should Be Equal    ${response_data}    ${DATASOURCE_ID}
    
    Log    Datasource verified: ${DATASOURCE_ID}

Verify Datasource In All List
    [Documentation]    Step 3: List all datasources for the location
    ...                Expects HTTP 200 response

    ${headers}=    Create Dictionary
    ...    X-Partition=${X_PARTITION}
    
    ${response}=    GET Request
    ...    datasource_api
    ...    /locations/${LOCATION_ID}/datasources
    ...    headers=${headers}
    
    Should Be Equal As Integers    ${response.status_code}    200
    ...    msg=Failed to list datasources. Status: ${response.status_code}
    
    ${datasources}=    Get From Dictionary    ${response.json()}    data
    Should Not Be Empty    ${datasources}
    
    Log    Found ${len(datasources)} datasources

Update Datasource Details
    [Documentation]    Step 4: Update the created datasource
    ...                Expects HTTP 200 response

    ${updated_payload}=    Create Dictionary
    ...    data=${UPDATED_DATASOURCE_PAYLOAD}
    
    ${headers}=    Create Dictionary
    ...    X-Partition=${X_PARTITION}
    
    ${response}=    PUT Request
    ...    datasource_api
    ...    /locations/${LOCATION_ID}/datasources/${DATASOURCE_ID}
    ...    json=${updated_payload}
    ...    headers=${headers}
    
    Should Be Equal As Integers    ${response.status_code}    200
    ...    msg=Failed to update datasource. Status: ${response.status_code}
    
    Log    Updated datasource: ${DATASOURCE_ID}

Delete Datasource
    [Documentation]    Step 5: Delete the created datasource
    ...                Expects HTTP 204 response (No Content)

    ${headers}=    Create Dictionary
    ...    X-Partition=${X_PARTITION}
    
    ${response}=    DELETE Request
    ...    datasource_api
    ...    /locations/${LOCATION_ID}/datasources/${DATASOURCE_ID}
    ...    headers=${headers}
    
    Should Be Equal As Integers    ${response.status_code}    204
    ...    msg=Failed to delete datasource. Status: ${response.status_code}
    
    Log    Deleted datasource: ${DATASOURCE_ID}
