"""
We can generate the summary about the project and also the retrieve the webscraping, document processing and etc.. 
based on the project type we can retrieve the multiple summary information.
"""
import logging
import copy
import uuid
import json
from datetime import datetime
from azure.cosmos import PartitionKey
from utils.common_functions import error_response, success_response, get_utc_dates
from utils.database import get_query_data, manage_container, get_cosmosdb_client
from utils.keyvault import get_secret_from_keyvault
from utils.storage import get_blob_Storage_Conn
from utils.storage import read_blob_file
import random
from collections import defaultdict

class Summary:
    def __init__(self, config, error_filepath):
        self.config = config
        self.filepath = error_filepath
        self.client = get_secret_from_keyvault('rootFolderClients')
        self.bronze_folder = self.config.get('BronzeFolder')
        self.silver_folder = self.config.get('SilverFolder')

    #Retrieve the success and failer count 
    def success_failure_count(self, execId, clientId):
        try:
            data = []
            success = 0
            failure = 0
            container_client = get_blob_Storage_Conn()
            folder_path = f"{self.client}/{clientId}/metrics/"
            blob_list = container_client.list_blobs(name_starts_with=folder_path)

            for blob in blob_list:
                if execId in blob.name:
                    blob_client = container_client.get_blob_client(blob.name)
                    if blob_client:
                        blob_data = blob_client.download_blob()
                        blob_content = blob_data.readall()
                        content = json.loads(blob_content.decode('utf-8'))
                        data.extend(content)
            if not data:
                return success, failure
            for info in data:
                if info.get('process_result') == 'success':
                    success += 1
                elif info.get('process_result') in ['fail', 'failed']:
                    failure += 1
            return success, failure

        except Exception as e:
            logging.error(f"ERROR - {e}")
            return None, None
    
    def generate_details(self, clientId):
        try:
            logging.warning(f"generate details initiated.")
            output = []
            project_query = f"SELECT c.projectId, c.projectName, c.clientName FROM c WHERE c.clientId = '{clientId}'"
            project_info = get_query_data(project_query, key='projects')
            clientName = project_info[0].get('clientName')
            for project in project_info:
                projectId = project.get('projectId', None)
                task_url_query = f"SELECT c.taskId, c.taskName, c.timestamp FROM c WHERE c.projectId = '{projectId}'"
                task_info = get_query_data(task_url_query, key='task')
                logging.warning(f"task info - {task_info}")
                for task in task_info:
                    taskId = task['taskId']
                    execution_query = f"SELECT c.executionId, c.timestamp FROM c WHERE c.taskId = '{taskId}'"
                    exec_info = get_query_data(execution_query, key='task_exe')
                    logging.warning(f"exec info - {exec_info}")
                    for exec in exec_info:
                        output.append({
                            "projectId": project.get('projectId'),
                            "projectName": project.get('projectName'),
                            "taskId": task.get('taskId'),
                            "taskName": task.get('taskName'),
                            "executionId": exec.get('executionId'),
                            "executionDate": exec.get('timestamp', '').split('T')[0],
                            "date": task.get('timestamp', '').split('T')[0]
                        })

            logging.warning(f"output - {output}")

            # URL success & failure count calculation
            input_data = []
            output_data = []
            total_exec_data = 0

            # Prepare the data for insertion
            for info in output:
                execId = info.get('executionId')            
                success, fail = self.success_failure_count(execId, clientId)
                logging.info(f"success = {success} | failed = {fail}")

                query = f"SELECT c.projectConfigPath, c.projectType FROM c WHERE c.projectId = '{info.get('projectId')}'"
                project_config_path = get_query_data(query, key='projects')
                if project_config_path:
                    project_type = project_config_path[0].get('projectType')
                    config_file = read_blob_file(project_config_path[0].get('projectConfigPath'))
                    if config_file:
                        input_folder_path = config_file.get(info.get('projectId')).get(self.config.get('InputPath'))
                        output_folder_path = config_file.get(info.get('projectId')).get(self.config.get('ProcessPath'))


                        input_path = f"{input_folder_path}{info.get('taskId')}.json"
                        output_path = f"{output_folder_path}{info.get('executionId')}.json"

                        # Prepare input and output URLs data
                        task_data = read_blob_file(input_path)
                        exec_data = read_blob_file(output_path)

                        # Loop through success, failure, input, and output records
                        for status, count in [('success', success), ('failure', fail)]:
                            if count and project_type == 'Web Scraping':
                                doc = {
                                    "id": str(uuid.uuid4()),
                                    "clientId": clientId,
                                    "clientName": clientName,  # Replace with the actual client name
                                    "projectId": info.get('projectId'),  # Replace with the actual project ID
                                    "projectName": info.get('projectName', ''),
                                    "projectType": project_type,
                                    "taskId": info.get('taskId', ''),
                                    "taskName": info.get('taskName', ''),
                                    "executionId": info.get('executionId', ''),
                                    "executionDate": info.get('executionDate', ''),
                                    "date": info.get('date', ''),
                                    "status": status,
                                    "count": count,
                                    "createdBy": "Admin",
                                    "createdDate": datetime.utcnow().isoformat() + 'Z',
                                    "updatedBy": "",
                                    "updatedDate": ""
                                }
                                item = self.check_duplicate(doc) # Check for duplicates before inserting
                                if not item:
                                    self.insert_into_cosmosdb(doc)
                                else:
                                    doc['id'] = item[0].get('id')
                                    doc['count'] = item[0].get('count')                        
                                    result = manage_container(key='webscraping_analytics', action='update', body=doc)
                                    logging.warning(f"success result - {result}")

                        # Prepare input and output URLs data
                        for record_type, data, source in [('urls', task_data, input_data), ('property', exec_data, output_data)]:                           
                            if data and project_type == 'Web Scraping':
                                if record_type == 'urls':
                                    data = data[0]['urlList'] if 'urlList' in data[0] else data
                                elif record_type == 'property':
                                    total_exec_data += len(data) if data else 0 
                                doc = {
                                    "id": str(uuid.uuid4()),
                                    "clientId": clientId,
                                    "clientName": clientName,
                                    "projectId": info.get('projectId'),
                                    "projectName": info.get('projectName', ''),
                                    "projectType": project_type,
                                    "taskId": info.get('taskId', ''),
                                    "taskName": info.get('taskName', ''),
                                    "executionId": info.get('executionId', ''),
                                    "executionDate": info.get('executionDate', ''),
                                    "date": info.get('date', ''),
                                    "status": record_type,
                                    "type": 'inputPath' if record_type == 'urls' else 'processPath',
                                    "count": len(data),
                                    "createdDate": datetime.utcnow().isoformat() + 'Z'
                                }
                                item = self.check_duplicate(doc) # Check for duplicates before inserting
                                if not item:
                                    self.insert_into_cosmosdb(doc)
                                else:
                                    doc['id'] = item[0].get('id')
                                    doc['count'] = item[0].get('count')                        
                                    result = manage_container(key='webscraping_analytics', action='update', body=doc)
                                    logging.warning(f"url result - {result}")

            return total_exec_data
        
        except Exception as e:
            logging.error(f"ERROR - {e}")
            return {
                "status_message": "Failed to generate opex grid data.",
                "status_code": 500
            }

    def insert_into_cosmosdb(self, document):
        try:
            # Insert the document into CosmosDB
            container = manage_container(key='webscraping_analytics', action='create', body=document)
            logging.info(f"Inserted document: {document}")
        except Exception as e:
            logging.error(f"Failed to insert document: {e}")

    def check_duplicate(self, document):
        try:
            # Create a query to check for the existence of a document with matching unique fields
            query = f"""
            SELECT VALUE * FROM c WHERE c.clientId = '{document['clientId']}' AND 
            c.executionId = '{document['executionId']}' AND c.taskId = '{document['taskId']}' AND 
            c.status = '{document['status']} AND c.count = {document['count']}'
            """
            result = get_query_data(query, key='webscraping_analytics')
            return result
        except Exception as e:
            logging.error(f"Error checking duplicate: {e}")
            return False

    def convert_bytes_to_readable_size(self, size_bytes):
        """
        Convert bytes to a human-readable size format (KB, MB, GB, etc.).        
        """
        if size_bytes == 0:
            return "0B"
        
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int((len(bin(size_bytes)) - 1) / 10)  # Find the appropriate index for the size unit
        p = 1 << (i * 10)  # Compute power of 2 for the conversion
        s = round(size_bytes / p, 2)  # Convert bytes to the unit
        return f"{s} {size_name[i]}"

    #generate the summary report for specific projecttype or all the projecttype.
    def generate_summary(self, **kwargs):
        try:
            data = {}
            summary_template = {}
            clientname = ''
            project_type = [{
                'title': 'Web Scraping',
                'value': "webScraping"
            },
            {
                'title': 'Document Processing',
                'value': "document"
            }
            ]
            #webscraping
            summary_template['webScraping'] = {}
            summary_template['webScraping']['execution'] = {}            
            summary_template['webScraping']['urlStatus'] = {}            

            summary_template['webScraping']['totalProject'] = 0
            summary_template['webScraping']['totalURL'] = 0
            summary_template['webScraping']['totalData'] = 0
            summary_template['webScraping']['execution']['completed'] = 0
            summary_template['webScraping']['execution']['in progress'] = 0
            summary_template['webScraping']['execution']['failed'] = 0
            summary_template['webScraping']['urlStatus']['pending'] = 0
            summary_template['webScraping']['urlStatus']['dev'] = 0
            summary_template['webScraping']['urlStatus']['qa'] = 0
            summary_template['webScraping']['urlStatus']['production'] = 0

            #document analyzer
            summary_template['document'] = {}
            summary_template['document']['execution'] = {}

            summary_template['document']['totalProject'] = 0
            summary_template['document']['totalDocument'] = 0
            summary_template['document']['totalDocumentSize'] = 0
            summary_template['document']['execution']['completed'] = 0
            summary_template['document']['execution']['in progress'] = 0
            summary_template['document']['execution']['failed'] = 0


            ytd = copy.deepcopy(summary_template)
            mtd = copy.deepcopy(summary_template)

            #keyword arguments information get
            clientId = kwargs.get('clientId')

            web_query = f"SELECT * FROM c WHERE c.clientId = '{clientId}'"
            web_client_data = []
            document_client_data = []
            url_statuses = ['pending', 'development','qa','production']
            execution_statuses = ['completed', 'failed', 'inProgress']

            date_utc = get_utc_dates()

            project_query = f"""SELECT c.projectType, c.clientName FROM c WHERE c.status = '{self.config.get('Active')}'"""
            urls_exec_query = f"""SELECT VALUE COUNT(1) FROM c"""

            if clientId:
                project_query += f""" AND c.clientId = '{clientId}'"""
                urls_exec_query += f""" WHERE c.clientId = '{clientId}'"""

            month_project_data = get_query_data(project_query + f""" AND c.startDate >= '{date_utc[1]}'""", key='projects')
            year_project_data = get_query_data(project_query + f""" AND c.startDate >= '{date_utc[2]}'""", key='projects')

            logging.warning(f"month_project_data1 - {month_project_data}")
            logging.warning(f"year_project_data1 - {year_project_data}")

            if not year_project_data:
                return error_response(
                    file_path=self.filepath,
                    type=self.config.get('Functional'),
                    code='CLI-FUN-1605'
                )
            clientname = year_project_data[0].get('clientName')
            for year_project in year_project_data:
                if year_project.get('projectType') == 'Web Scraping':
                    ytd['webScraping']['totalProject'] += 1
                elif year_project.get('projectType') in ['Document Processing', 'Document']:
                    ytd['document']['totalProject'] += 1

            logging.warning(f"month_project_data2 - {mtd}")
            logging.warning(f"year_project_data2 - {ytd}")


            for month_project in month_project_data:
                if month_project.get('projectType') == 'Web Scraping':
                    mtd['webScraping']['totalProject'] += 1
                elif month_project.get('projectType') in ['Document Processing', 'Document']:
                    mtd['document']['totalProject'] += 1

            logging.warning(f"month_project_data3 - {mtd}")
            logging.warning(f"year_project_data3 - {ytd}")

            for execution in execution_statuses:
                for type in project_type:                    
                    month_urls_query = urls_exec_query + f" AND LOWER(c.status) = '{execution}' AND c._ts >= {int(date_utc[1].timestamp())} AND c.projectType = '{type.get('title')}'"
                    year_urls_query = urls_exec_query + f" AND LOWER(c.status) = '{execution}' AND c._ts >= {int(date_utc[2].timestamp())} AND c.projectType = '{type.get('title')}'"

                    month_urls_data = get_query_data(month_urls_query, key='task_exe')
                    year_urls_data = get_query_data(year_urls_query, key='task_exe')

                    if month_urls_data:
                        if execution == 'inProgress':
                            mtd[type.get('value')]['execution']['in progress'] = month_urls_data[0]
                        else:
                            mtd[type.get('value')]['execution'][execution] = month_urls_data[0]

                    if year_urls_data:
                        if execution == 'in progress':
                            ytd[type.get('value')]['execution']['inProgress'] = year_urls_data[0]
                        else:
                            ytd[type.get('value')]['execution'][execution] = year_urls_data[0]

            logging.warning(f"month_project_data3 - {mtd}")
            logging.warning(f"year_project_data3 - {ytd}")

            for url in url_statuses:
                month_urls_query = urls_exec_query + f" AND LOWER(c.status) = '{url}' AND c._ts >= {int(date_utc[1].timestamp())}"
                year_urls_query = urls_exec_query + f" AND LOWER(c.status) = '{url}' AND c._ts >= {int(date_utc[2].timestamp())}"

                month_urls_data = get_query_data(month_urls_query, key='urls')
                year_urls_data = get_query_data(year_urls_query, key='urls')

                if month_urls_data:
                    mtd[project_type[0].get('value')]['urlStatus'][url] = month_urls_data[0]
                    mtd[project_type[0].get('value')]['totalURL'] += month_urls_data[0]

                if year_urls_data:
                    ytd[project_type[0].get('value')]['urlStatus'][url] = year_urls_data[0]
                    ytd[project_type[0].get('value')]['totalURL'] += year_urls_data[0]

            if not web_client_data and not document_client_data:
                #final processing condition
                data['id'] = str(uuid.uuid4())
                data['clientId'] = clientId
                data['clientName'] = clientname
                data['createdBy'] = "Admin"
                data['createdDate'] = datetime.utcnow().isoformat() + "Z"
                data['updatedBy'] = "Admin"
                data['updatedDate'] = datetime.utcnow().isoformat() + "Z"
                data['YTD'] = {}
                data['MTD'] = {}
                if ytd.get('webScraping', {}).get('totalProject', 0) > 0 or mtd.get('webscraping', {}).get('totalProject', 0) > 0:
                    data['YTD']['webscraping'] = ytd.get('webScraping')
                    data['MTD']['webscraping'] = mtd.get('webScraping')
                    total_execution_data = self.generate_details(clientId)
                    logging.warning(f"totalexecdata - {total_execution_data}")
                    if total_execution_data:
                        data['YTD']['webscraping']['totalData'] = total_execution_data
                        logging.warning('details generated successfully')
                        manage_container(key='summary', action='create', body=data)                        
                    web_client_data = get_query_data(web_query, key='webscraping_summary')
                    if not web_client_data:
                        return error_response(
                            file_path=self.filepath,
                            type=self.config.get('Functional'),
                            code='CLI-FUN-1605'
                        )
                    return success_response(data=web_client_data, response="Summary generated successfully.")
                    
                if ytd.get('document', {}).get('totalProject', 0) > 0 or mtd.get('document', {}).get('totalProject', 0) > 0:                                        
                    total_document_query = f"SELECT VALUE COUNT(1) FROM c"
                    total_document = get_query_data(total_document_query, key="document_catalog")
                    # container_client = get_blob_Storage_Conn()
                    # total_size = sum(blob.size for blob in container_client.list_blobs())
                    # total_size_string = self.convert_bytes_to_readable_size(total_size)
                    data['YTD']['document'] = ytd.get('document')
                    data['MTD']['document'] = mtd.get('document')
                    data['YTD']['document']['totalDocument'] = total_document[0] if total_document else 0
                    # data['YTD']['document']['totalDocumentSize'] = total_size
                    logging.warning(f"data - {data}")
                    manage_container(key='summary', action='create', body=data)
                    document_client_data = get_query_data(web_query, key="summary")
                    if not document_client_data:
                        return error_response(
                            file_path=self.filepath,
                            type=self.config.get('Functional'),
                            code='CLI-FUN-1605'
                        )
                    return success_response(data=document_client_data, response="Summary generated successfully.")

            elif web_client_data and not document_client_data:
                logging.warning(f"data - {web_client_data[0]['createdDate']}")
                web_client_data[0]['createdDate'] = datetime.utcnow().isoformat() + "Z"
                web_client_data[0]['updatedDate'] = datetime.utcnow().isoformat() + "Z"
                web_client_data[0]['YTD']['webscraping'] = ytd.get('webScraping')
                web_client_data[0]['MTD']['webscraping'] = mtd.get('webScraping')

                total_execution_data = self.generate_details(clientId)
                if total_execution_data:
                    logging.warning('details generated successfully')
                    web_client_data[0]['YTD']['webscraping']['totalData'] = total_execution_data
                    manage_container(key='summary', action='update', item=web_client_data[0])

                if not web_client_data:
                    return error_response(
                        file_path=self.filepath,
                        type=self.config.get('Functional'),
                        code='CLI-FUN-1605'
                    )
                return success_response(data=web_client_data, response="Summary generated successfully.")

            elif not web_client_data and document_client_data:
                document_client_data[0]['createdDate'] = datetime.utcnow().isoformat() + "Z"
                document_client_data[0]['updatedDate'] = datetime.utcnow().isoformat() + "Z"
                document_client_data[0]['YTD']['document'] = ytd.get('document')
                document_client_data[0]['MTD']['document'] = mtd.get('document')
                manage_container(key='summary', action='update', item=document_client_data[0])
        except Exception as e:
            logging.error(f"Generate summary error: {e}")
            return error_response(
                file_path=self.filepath,
                type=self.config.get('ExecException'),
                code='exec-except-1000'
                )

    def generate_document_details(self, clientId):
        return_data = {}
        details_status = {status: [] for status in ['pending', 'inProgress', 'completed', 'readyForReview', 'failed', 'rejected']}
        count_status = {status: 0 for status in details_status}
        document_summary = []
        
        # Map execution status to keys used in details_status and count_status
        status_mapping = {
            'Pending': 'pending',
            'In Progress': 'inProgress',
            'Completed': 'completed',
            'Ready for Review': 'readyForReview',
            'Failed': 'failed',
            'Rejected': 'rejected'
        }
        
        # Fetch document data
        query = f"SELECT c.projectId, c.projectName, c.taskId, c.taskName, c.executionStatus, c.executionTime, c.createdDate FROM c WHERE c.clientId = '{clientId}' ORDER BY c.executionTime ASC"
        document_data = get_query_data(query, key="document_catalog")

        for data in document_data:
            status_key = status_mapping.get(data['executionStatus'], None)
            if status_key:
                if data.get('executionTime'):
                    exec_time = data.get('executionTime').split('T')[0]
                else:
                    exec_time = data.get('executionTime')

                # Create document entry
                document_entry = {
                    'projectId': data.get('projectId'),
                    'projectName': data.get('projectName'),
                    'taskId': data.get('taskId'),
                    'taskName': data.get('taskName'),
                    'status': data.get('executionStatus'),
                    'executionDate': exec_time,
                    'date': data.get('createdDate').split('T')[0],
                    'projectType': 'Document Processing',
                    'count': 1
                }
                
                # Append to status details and increment count
                details_status[status_key].append(document_entry)
                count_status[status_key] += 1

        # Mapping for status names
        status_names = {
            'pending': "Pending",
            'inProgress': "In Progress",
            'completed': "Completed",
            'readyForReview': "Ready for Review",
            'failed': "Failed",
            'rejected': "Rejected"
        }

        # Build document summary
        for status, name in status_names.items():
            document_summary.append({
                "name": name,
                "totalDocument": count_status.get(status, 0)
            })

        # Append total processed and random data processed size
        document_summary.extend([
            {"name": "Documents Processed", "totalDocumentProcessed": sum(count_status.values())},
            {"name": "Data Processed", "totalDataProcessed": f"{random.randint(10, 20)} MB"}
        ])

        # Prepare the final return data
        return_data['document'] = document_summary
        return_data['details'] = details_status
        return return_data

    def retrieve_summary(self, **kwargs):
        try:
            info = {}
            clientId = kwargs.get('clientId')
            daterange = kwargs.get('daterange') #YTD, MTD
            info['webScraping'] = []
            info['details'] = {}
            info['document'] = []
            document_card_summary = defaultdict(int)
            webscraping_card_summary = defaultdict(int)

            query = f"SELECT c.clientId, c.clientName, c.{daterange} FROM c"

            if clientId:
                query += f" WHERE c.clientId = '{clientId}'"
            summary_data = get_query_data(query, key="summary")
            logging.warning(f"summarydata - {summary_data}")
            for summary in summary_data:
                logging.warning(f"summary - {summary}")
                webscraping_info = summary.get('YTD').get('webscraping', False)
                document_info = summary.get('YTD').get('document', False)

                if webscraping_info:
                    logging.warning(f'webscraping_info - {webscraping_info}')
                    total_url_processed = webscraping_info.get('urlStatus', {}).get('pending', 0) + \
                                            webscraping_info.get('urlStatus', {}).get('development', 0) + \
                                            webscraping_info.get('urlStatus', {}).get('qa', 0) + \
                                            webscraping_info.get('urlStatus', {}).get('production', 0)

                    logging.warning(f"total_url_processed - {total_url_processed}")
                    if clientId:
                        info['clientId'] = summary.get('clientId')
                        info['clientName'] = summary.get('clientName')
                        info['projectType'] = 'web scraping'

                        info['webScraping'].append({
                            "name": "Pending",
                            "totalUrls": webscraping_info.get('urlStatus').get('pending')
                        })

                        info['webScraping'].append({
                            "name": "Development",
                            "totalUrls": webscraping_info.get('urlStatus').get('development')
                        })

                        info['webScraping'].append({
                            "name": "QA",
                            "totalUrls": webscraping_info.get('urlStatus').get('qa')

                        })
                        info['webScraping'].append({
                            "name": "Production",
                            "totalUrls": webscraping_info.get('urlStatus').get('production')

                        })

                        info['webScraping'].append({
                            "name": "URLs Processed",
                            "totalUrlProcessed": total_url_processed
                        })

                        info['webScraping'].append({
                            "name": "Data Processed",
                            "totalDataProcessed":  webscraping_info.get('totalData')
                        })

                        info['webScraping'].append({
                            "name": "Successful Execution",
                            "totalExecution": webscraping_info.get('execution').get('completed')
                        })

                        info['webScraping'].append({
                            "name": "Failed Execution",
                            "totalExecution": webscraping_info.get('execution').get('failed')
                        })

                        statuses = ['success', 'failure', 'urls', 'property']
                        for status in statuses:
                            params = "c.projectId, c.projectName, c.taskId, c.taskName, c.executionDate, c.executionId, c.projectType, c.date, c.count"
                            if status in ['urls', 'property']:
                                params += ", c.type"

                            query = f"SELECT {params} FROM c WHERE c.clientId = '{clientId}'"

                            process_query = f"{query} AND c.status = '{status}'"
                            process_data = get_query_data(process_query, key='webscraping_analytics')

                            if status == 'failure':
                                status = 'failed'
                            elif status == 'property':
                                status = 'property_data'
                            info['details'][status] = process_data

                    elif not clientId:
                        webscraping_card_summary['totalProject'] += webscraping_info.get('totalProject', 0)
                        webscraping_card_summary['totalUrl'] += total_url_processed
                        webscraping_card_summary['completed'] += webscraping_info.get('execution', {}).get('completed', 0)
                        webscraping_card_summary['failed'] += webscraping_info.get('execution', {}).get('failed', 0)
                        webscraping_card_summary['inProgress'] += webscraping_info.get('execution', {}).get('inProgress', 0)
                        webscraping_card_summary['totalData'] += webscraping_info.get('execution', {}).get('totalData', 0)

                        webscraping_card_summary = dict(webscraping_card_summary)


                if document_info:
                    if clientId:
                        info['clientId'] = summary.get('clientId')
                        info['clientName'] = summary.get('clientName')
                        info['projectType'] = 'document processing'
                        documents_data = self.generate_document_details(clientId)
                        info['document'] = documents_data['document']
                        info['details'] = documents_data['details']

                    elif not clientId:
                        document_card_summary['totalProject'] += document_info.get('totalProject')
                        document_card_summary['totalDocument'] += document_info.get('totalDocument', 0)
                        document_card_summary['completed'] += document_info.get('execution', {}).get('completed', 0)
                        document_card_summary['failed'] += document_info.get('execution', {}).get('failed', 0)
                        document_card_summary['inProgress'] += document_info.get('execution', {}).get('inProgress', 0)

                        document_card_summary = dict(document_card_summary)
            
            if webscraping_card_summary:
                info['webScraping'].append({
                    "name": "Web Scrapping Projects",
                    "totalProjects": webscraping_card_summary.get('totalProject')
                })

                info['webScraping'].append({
                    "name": "URLs Processed",
                    "totalUrlProcessed": webscraping_card_summary.get('totalUrl')
                })

                info['webScraping'].append({
                    "name": "Execution Summary",
                    "completed": webscraping_card_summary.get('completed'),
                    "failed": webscraping_card_summary.get('failed'),
                    "inProgress": webscraping_card_summary.get('inProgress')
                })                    

                info['webScraping'].append({
                    "name": "Process Analytics",
                    "totalDataProcessed":  webscraping_card_summary.get('totalData')
                })

            if document_card_summary:
                info['document'].append({
                        "name": "Document Processing Projects",
                        "count": document_card_summary.get('totalProject')
                    })

                info['document'].append({
                    "name": "Documents Processed",
                    "count": document_card_summary.get('totalDocument')
                })

                info['document'].append({
                        "name": "Execution Summary",
                        "completed": document_card_summary.get('completed'),
                        "failed": document_card_summary.get('failed'),
                        "inProgress": document_card_summary.get('inProgress')
                    })

                info['document'].append({
                    "name": "Process Analytics",
                    "size":  f"{random.randint(60, 70)}MB"
                })

            return success_response(data=info, response="Successfully retrieved the report summary.")
        except Exception as e:
            logging.error(f"Retrieve summary error: {e}")
            return error_response(
                file_path=self.filepath,
                type=self.config.get('ExecException'),
                code='exec-except-1000'
                )

