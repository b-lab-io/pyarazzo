*** Settings ***
Documentation    Advanced version with parametrized test cases for different scenarios

Library    RequestsLibrary
Library    Collections
Library    String

Resource    keywords.robot

Suite Setup        Initialize Test Suite
Suite Teardown     Teardown Test Suite

*** Variables ***
${BASE_URL}           http://localhost:8000
${X_PARTITION}        default-partition
${LOCATION_ID}        550e8400-e29b-41d4-a716-446655440000


*** Test Cases ***
Create Datasource And Verify Response Structure
    [Documentation]    Verify datasource creation response contains required fields
    [Tags]            create    datasource    validation

    ${response}=    Create And Return Datasource
    
    ${id}=         Get From Dictionary    ${response.json()}    id
    ${data}=       Get From Dictionary    ${response.json()}    data
    
    Should Not Be Empty    ${id}
    Should Be Equal As Numbers    ${response.status_code}    201
    
    Dictionary Should Contain Key    ${data}    lat
    Dictionary Should Contain Key    ${data}    lon

Retrieve Non-Existent Datasource Returns 404
    [Documentation]    Verify that retrieving a non-existent datasource returns 404
    [Tags]            error-handling    datasource

    ${headers}=    Create Dictionary    X-Partition=${X_PARTITION}
    
    ${response}=    GET Request
    ...    datasource_api
    ...    /locations/${LOCATION_ID}/datasources/00000000-0000-0000-0000-000000000000
    ...    headers=${headers}
    ...    expected_status=404
    
    Should Be Equal As Integers    ${response.status_code}    404

Create Update And Retrieve Datasource
    [Documentation]    Multi-step test: Create, update, and retrieve a datasource
    [Tags]            update    datasource    multi-step

    # Create
    ${response}=    Create And Return Datasource
    ${datasource_id}=    Get From Dictionary    ${response.json()}    id
    
    # Verify creation
    ${created_data}=    Get From Dictionary    ${response.json()}    data
    Should Be Equal As Numbers    ${created_data}[disableEstimations]    ${True}
    
    # Update
    ${updated_payload}=    Create Dictionary
    ...    data=${UPDATED_DATASOURCE_PAYLOAD}
    
    ${headers}=    Create Dictionary    X-Partition=${X_PARTITION}
    
    ${response}=    PUT Request
    ...    datasource_api
    ...    /locations/${LOCATION_ID}/datasources/${datasource_id}
    ...    json=${updated_payload}
    ...    headers=${headers}
    
    Should Be Equal As Integers    ${response.status_code}    200
    
    # Retrieve and verify update
    ${response}=    GET Request
    ...    datasource_api
    ...    /locations/${LOCATION_ID}/datasources/${datasource_id}
    ...    headers=${headers}
    
    ${retrieved_data}=    Get From Dictionary    ${response.json()}    data
    Should Be Equal As Numbers    ${retrieved_data}[disableEstimations]    ${False}
    Should Be Equal As Numbers    ${retrieved_data}[lat]    5.97
    Should Be Equal As Numbers    ${retrieved_data}[lon]    -172.97
    
    # Cleanup
    DELETE Request    datasource_api    /locations/${LOCATION_ID}/datasources/${datasource_id}    headers=${headers}

List Datasources
    [Documentation]    Verify listing all datasources returns proper structure
    [Tags]            list    datasource

    ${headers}=    Create Dictionary    X-Partition=${X_PARTITION}
    
    ${response}=    GET Request
    ...    datasource_api
    ...    /locations/${LOCATION_ID}/datasources
    ...    headers=${headers}
    
    Should Be Equal As Integers    ${response.status_code}    200
    
    ${response_data}=    Get From Dictionary    ${response.json()}    data
    Should Be A List    ${response_data}


*** Keywords ***
Initialize Test Suite
    [Documentation]    Setup test environment and create HTTP session
    Create Session    datasource_api    ${BASE_URL}    verify=False

Teardown Test Suite
    [Documentation]    Clean up test resources
    Delete All Sessions

Create And Return Datasource
    [Documentation]    Helper keyword to create a datasource
    ...                Returns the response object for further assertions
    
    ${payload}=    Create Dictionary
    ...    data=${DATASOURCE_PAYLOAD}
    
    ${headers}=    Create Dictionary
    ...    X-Partition=${X_PARTITION}
    
    ${response}=    POST Request
    ...    datasource_api
    ...    /locations/${LOCATION_ID}/datasources
    ...    json=${payload}
    ...    headers=${headers}
    
    [Return]    ${response}
