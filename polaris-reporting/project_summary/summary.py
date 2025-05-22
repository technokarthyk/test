"""
We can generate the summary about the project and also the retrieve the webscraping, document processing and etc.. 
based on the project type we can retrieve the multiple summary information.
"""
import logging
from utils.common_functions import error_response, success_response, get_utc_dates
from utils.database import get_query_data, manage_container
from datetime import datetime, timezone
import copy
import uuid

class Summary:
    def __init__(self, config, error_filepath):
        self.config = config
        self.filepath = error_filepath

    #generate the summary report for specific projecttype or all the projecttype
    def generate_summary(self, **kwargs):
        try:
            data = {}
            summary_template = {}
            summary_template['webscraping'] = {}
            summary_template['webscraping']['execution'] = {}
            summary_template['webscraping']['environmentStatus'] = {}            
            summary_template['webscraping']['totalProjects'] = 0
            summary_template['webscraping']['totalURLs'] = 0
            summary_template['webscraping']['execution']['completed'] = 0
            summary_template['webscraping']['execution']['inprogress'] = 0
            summary_template['webscraping']['execution']['failed'] = 0
            summary_template['webscraping']['totalDatas'] = 0
            summary_template['webscraping']['environmentStatus']['pending'] = 0
            summary_template['webscraping']['environmentStatus']['dev'] = 0
            summary_template['webscraping']['environmentStatus']['qa'] = 0
            summary_template['webscraping']['environmentStatus']['production'] = 0

            ytd = copy.deepcopy(summary_template)
            mtd = copy.deepcopy(summary_template)

            #keyword arguments information get
            clientId = kwargs.get('clientId')
            environment_statuses = ['pending', 'development','qa','production']
            execution_statuses = ['completed', 'failed', 'in progress']

            date_utc = get_utc_dates()

            logging.warning(f'month-start = {date_utc[1]}')

            project_query = f"""SELECT c.projectType, c.clientName FROM c WHERE c.status = '{self.config.get('Active')}'"""
            urls_exec_query = f"""SELECT VALUE COUNT(1) FROM c"""

            if clientId:
                project_query += f""" AND c.clientId = '{clientId}'"""
                urls_exec_query += f""" WHERE c.clientId = '{clientId}'"""

            month_project_data = get_query_data(project_query + f""" AND c.startDate >= '{date_utc[1]}'""", key='projects')
            year_project_data = get_query_data(project_query + f""" AND c.startDate >= '{date_utc[2]}'""", key='projects')


            for year_project in year_project_data:
                if year_project.get('projectType') == 'Web Scraping':
                    ytd['webscraping']['totalProjects'] += 1

            for month_project in month_project_data:
                if month_project.get('projectType') == 'Web Scraping':
                    mtd['webscraping']['totalProjects'] += 1

            for env in environment_statuses:
                logging.warning(f'{env}')

                month_urls_query = urls_exec_query + f" AND LOWER(c.status) = '{env}' AND c._ts >= {int(date_utc[1].timestamp())}"
                year_urls_query = urls_exec_query + f" AND LOWER(c.status) = '{env}' AND c._ts >= {int(date_utc[2].timestamp())}"

                logging.warning(f"month urls query - {month_urls_query}")
                logging.warning(f"year_urls_query - {year_urls_query}")

                month_urls_data = get_query_data(month_urls_query, key='urls')
                year_urls_data = get_query_data(year_urls_query, key='urls')

                if month_urls_data:
                    mtd['webscraping']['environmentStatus'][env] = month_urls_data[0]
                    mtd['webscraping']['totalURLs'] += month_urls_data[0]

                if year_urls_data:
                    ytd['webscraping']['environmentStatus'][env] = year_urls_data[0]
                    ytd['webscraping']['totalURLs'] += year_urls_data[0]

            for execution in execution_statuses:
                month_urls_query = urls_exec_query + f" AND LOWER(c.status) = '{execution}' AND c._ts >= {int(date_utc[1].timestamp())}"
                year_urls_query = urls_exec_query + f" AND LOWER(c.status) = '{execution}' AND c._ts >= {int(date_utc[2].timestamp())}"

                logging.warning(f"month urls query - {month_urls_query}")
                logging.warning(f"year_urls_query - {year_urls_query}")

                month_urls_data = get_query_data(month_urls_query, key='task_exe')
                year_urls_data = get_query_data(year_urls_query, key='task_exe')

                if month_urls_data:
                    mtd['webscraping']['execution'][execution] = month_urls_data[0]

                if year_urls_data:
                    ytd['webscraping']['execution'][execution] = year_urls_data[0]

            data['id'] = str(uuid.uuid4())
            data['analyzerId'] = clientId
            data['clientId'] = clientId
            data['clientName'] = ''
            data['YTD'] = ytd
            data['MTD'] = mtd
            data['createdBy'] = "Admin"
            data['createdDate'] = f"{date_utc[1]}"
            data['updatedBy'] = "Admin"
            data['updatedDate'] = ""
            container = manage_container(key='project_summary', action='create', body=data)
            if container:
                return success_response(response="Summary generated successfully.")
            return error_response(
                    file_path=self.file_path,
                    type=self.config.get('Functional'),
                    code='CLI-FUN-1603'
            )

        except Exception as e:
            logging.error(f"Generate summary error: {e}")
            return error_response(
                file_path=self.filepath,
                type=self.config.get('ExecException'),
                code='exec-except-1000'
                )

    def retrieve_summary(self, **kwargs):
        try:
            clientId = kwargs.get('clientId')
            daterange = kwargs.get('daterange') #YTD, MTD
            data = []
            query = f"SELECT * FROM c"
            if clientId:
                query += f" WHERE c.clientId = '{clientId}'"
            summary_data = get_query_data(query, key="project_summary")
            if not summary_data:
                return error_response(
                    file_path=self.file_path,
                    type=self.config.get('Functional'),
                    code='CLI-FUN-1605'
                )
            for summary in summary_data:
                info = {}
                info['clientId'] = summary.get('clientId')
                info['clientName'] = summary.get('clientName')
                project_type = summary.get(daterange)
                if 'webscraping' in project_type:
                    info['webscraping'] = []
                    info['webscraping'].append({
                        "name": "Execution Status"
                    })
                info['']
        except Exception as e:
            logging.error(f"Generate summary error: {e}")
            return error_response(
                file_path=self.filepath,
                type=self.config.get('ExecException'),
                code='exec-except-1000'
                )
