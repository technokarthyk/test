# Project Summary

## GET

#### Generate summary
Generate the project summary information based on projectType it contains the project count, URL processed, Execution summary, Process Analytics.

Endpoint - https://polarisdev.azure-api.net/reporting/v1/summary/generate/:clientId

Route params

    clientId - b09d2604-9165-401a-b10d-6534f02c1256

Response
    
##### Webscraping

        {
        "data": {
            "id": "1f7a6b31-e8a4-4c79-9574-b848cb6167c6",
            "clientId": "b09d2604-9165-401a-b10d-6534f02c1256",
            "clientName": "RentalBeast",
            "createdBy": "Admin",
            "createdDate": "2024-08-01 00:00:00+00:00",
            "updatedBy": "Admin",
            "updatedDate": "2024-08-01 00:00:00+00:00",
            "YTD": {
                "execution": {
                    "completed": 19,
                    "in progress": 0,
                    "failed": 2,
                    "inProgress": 8
                },
                "urlStatus": {
                    "pending": 0,
                    "dev": 0,
                    "qa": 1126,
                    "production": 28,
                    "development": 13
                },
                "totalProject": 3,
                "totalURL": 1167,
                "totalData": 0
            },
            "MTD": {
                "execution": {
                    "completed": 5,
                    "in progress": 0,
                    "failed": 0,
                    "inProgress": 7
                },
                "urlStatus": {
                    "pending": 0,
                    "dev": 0,
                    "qa": 0,
                    "production": 0,
                    "development": 1
                },
                "totalProject": 1,
                "totalURL": 1,
                "totalData": 0
            }
        },
        "error": [],
        "response": "Summary generated successfully.",
        "status": "ok"
    }

##### Document

    {
        "data": {
            "id": "f9c29653-c4eb-45a2-ab86-a97f202d7434",
            "clientId": "dbab0c21-cc43-4419-b2ee-84ef9ff44d3f",
            "clientName": "Star Alliance",
            "createdBy": "Admin",
            "createdDate": "2024-08-01 00:00:00+00:00",
            "updatedBy": "Admin",
            "updatedDate": "2024-08-01 00:00:00+00:00",
            "YTD": {
                "execution": {
                    "completed": 3,
                    "in progress": 0,
                    "failed": 0,
                    "inProgress": 7
                },
                "totalProject": 5,
                "totalDocument": 0,
                "totalDocumentSize": 0
            },
            "MTD": {
                "execution": {
                    "completed": 3,
                    "in progress": 0,
                    "failed": 0,
                    "inProgress": 7
                },
                "totalProject": 1,
                "totalDocument": 0,
                "totalDocumentSize": 0
            }
        },
        "error": [],
        "response": "Summary generated successfully.",
        "status": "ok"
    }

#### Retrieve summary info
Retrieves the project summary infomation based on the projectType or using queryparams to retrieves the information.

Endpoint - https://polarisdev.azure-api.net/reporting/v1/summary/retrieve/all

Params

    daterange - YTD, MTD

Response

    {
        "data": {
            "webScraping": [
                {
                    "name": "Web Scrapping Project",
                    "totalProjects": 3
                },
                {
                    "name": "Execution Summary",
                    "completed": 19,
                    "failed": 2,
                    "inProgress": 0
                },
                {
                    "name": "URLs Processed",
                    "totalUrlProcessed": 1167
                },
                {
                    "name": "Process Analytics",
                    "totalDataProcessed": 0
                }
            ]
        },
        "error": [],
        "response": "Successfully retrieved the report summary.",
        "status": "ok"
    }

#### Retrieve summary info for specific client
Retrieve the specific client summary report information.
using projectType, clientId and daterange.

Endpoint - https://polarisdev.azure-api.net/reporting/v1/summary/retrieve/client/:clientId

##### Webscraping
Route params

    clientId - b09d2604-9165-401a-b10d-6534f02c1256
    
Params

    daterange - YTD, MTD

Response

    {
        "data": {
            "webScraping": [
                {
                    "name": "Pending",
                    "totalUrls": 0
                },
                {
                    "name": "Development",
                    "totalUrls": 13
                },
                {
                    "name": "QA",
                    "totalUrls": 1126
                },
                {
                    "name": "Production",
                    "totalUrls": 28
                },
                {
                    "name": "URLs Processed",
                    "totalUrlProcessed": 1167
                },
                {
                    "name": "Data Processed",
                    "totalDataProcessed": 0
                },
                {
                    "name": "Successful Execution",
                    "totalExecution": 19
                },
                {
                    "name": "Failed Execution",
                    "totalExecution": 2
                }
            ],
            "clientId": "b09d2604-9165-401a-b10d-6534f02c1256",
            "clientName": "RentalBeast"
        },
        "error": [],
        "response": "Successfully retrieved the report summary.",
        "status": "ok"
    }

##### document
Route params

    clientId - b09d2604-9165-401a-b10d-6534f02c1256
    
Params

    daterange - YTD, MTD

Response

    {
        "data": {
            "webScraping": [],
            "document": [
                {
                    "name": "Total Projects",
                    "count": 5
                },
                {
                    "name": "Task Status",
                    "completed": 3,
                    "failed": 0,
                    "inProgress": 7
                },
                {
                    "name": "Total Documents",
                    "count": 0
                },
                {
                    "name": "Total Document Size",
                    "size": 0
                }
            ],
            "clientId": "dbab0c21-cc43-4419-b2ee-84ef9ff44d3f",
            "clientName": "Star Alliance"
        },
        "error": [],
        "response": "Successfully retrieved the report summary.",
        "status": "ok"
    }