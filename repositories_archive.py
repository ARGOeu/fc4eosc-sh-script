#!/usr/bin/env python3
import datetime
import argparse
import sys
import logging
import requests

# establish basic logging
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='[%(asctime)s] %(levelname)s %(message)s')


class ArchivalRequestStatus:
    def __init__(self,
                 status_code=None,
                 request_id=None,
                 url=None,
                 service_type=None,
                 save_request_status=None,
                 save_task_status=None,
                 save_request_date=None
                 ):
        self.status_code = status_code
        self.request_id = request_id
        self.url = url
        self.service_type = service_type
        self.save_request_status = save_request_status
        self.save_task_status = save_task_status
        self.save_request_date = save_request_date

    @staticmethod
    def from_response(url, service_type, response, list_format=True):
        """
        Constructs an archival response from a json response
        :param str url: the repository url
        :param str service_type: the service type of the url
        :param requests.models.Response response: the requests' response
        :param boolean list_format: whether the response contains list of statuses(from get)
        :return: ArchivalRequestStatus
        """
        if response.status_code != 200:
            text_status = response.json().get("reason")
            if text_status is None:
                text_status = response.text
            return ArchivalRequestStatus(status_code=response.status_code,
                                         save_request_status=text_status,
                                         url=url,
                                         service_type=service_type
                                         )
        response_body = {}
        if list_format:
            response_body = response.json()[0]
        else:
            response_body = response.json()

        return ArchivalRequestStatus(
            status_code=response.status_code,
            request_id=response_body.get("id"),
            url=url,
            service_type=service_type,
            save_request_status=response_body.get("save_request_status"),
            save_task_status=response_body.get("save_task_status"),
            save_request_date=response_body.get("save_request_date")
        )


class Repository:
    sh_host = "https://archive.softwareheritage.org"
    archival_url = sh_host + "/api/1/origin/save/{0}/url/{1}/"
    visit_url = sh_host + "/api/1/origin/{0}/visit/latest/"

    def __init__(self, url, service_type):
        self.url = url
        self.service_type = service_type

    def visit(self):
        """
        Utilises the GET @ /api/1/origin/{0}/visit/latest/ to check the existence of a repository.
        :return: the status code of the request or -1 in the case of an exception
        """
        u = self.visit_url.format(self.url)
        logging.info(f"[visit]: Visiting {self.url} . . .")
        try:
            response = requests.get(url=u, allow_redirects=True)
            logging.info(f"[visit]: Visited {self.url} and got {response.text}")
            return response.status_code
        except Exception as e:
            logging.error(f"[visit]: Visited {self.url} and got exception {str(e)}")
            return -1

    def archive(self):
        """
         Utilises the POST @ /api/1/origin/save/{0}/url/{1}/ route in order to begin the archival process for
        the respective url
        :return: ArchivalRequestStatus containing the needed fields to produce the final report entry
        """
        u = self.archival_url.format(self.service_type, self.url)
        logging.info(f"[archive]: Archiving {self.url}({self.service_type}) . . .")
        try:
            response = requests.post(url=u, allow_redirects=True)
            logging.info(f"[archive]: Archived {self.url} and got {response.text}")
            return ArchivalRequestStatus.from_response(
                url=self.url,
                service_type=self.service_type,
                response=response,
                list_format=False)
        except Exception as e:
            logging.error(f"[archive]: Error for {self.url}({self.service_type}) - {str(e)}")
            return ArchivalRequestStatus(save_request_status=str(e), url=self.url, service_type=self.service_type)

    def get_status(self):
        """
         Utilises the GET @ /api/1/origin/save/{0}/url/{1}/ route in order to retrieve the status of the
        respective url
        :return: ArchivalRequestStatus containing the needed fields to produce the final report entry
        """
        u = self.archival_url.format(self.service_type, self.url)

        logging.info(f"[get_status]: Retrieving info for {self.url}({self.service_type}) . . .")
        try:
            response = requests.get(url=u, allow_redirects=True)
            logging.info(f"[get_status]: {self.url} and got {response.text}")
            return ArchivalRequestStatus.from_response(
                url=self.url,
                service_type=self.service_type,
                response=response,
                list_format=True)
        except Exception as e:
            logging.error(f"[get_status]: Error for {self.url}({self.service_type}) - {str(e)}")
            return ArchivalRequestStatus(save_request_status=str(e), url=self.url, service_type=self.service_type)


def read_repositories(filepath):
    repositories = []

    repositories_file = open(filepath, "r")
    for line in repositories_file.readlines():
        service_type = line.strip().split(',')[0]
        repository_url = line.strip().split(',')[1]
        logging.debug(f"Reading line for ({service_type}) repository {repository_url} . . .")
        repositories.append(Repository(repository_url, service_type))
    repositories_file.close()
    logging.debug(f"Read {len(repositories)} repositories.")
    return repositories


def main(args):
    report_file_name = f"{args.report}-{str(datetime.datetime.utcnow().isoformat(timespec='seconds'))}"
    report = open(report_file_name, 'w')
    report.truncate(0)

    for repo in read_repositories(args.repos):
        code = repo.visit()
        if code == 200:
            get_status_response = repo.get_status()
            if get_status_response.status_code != 200:
                logging.error(f"[get_status]: Non successful status for {get_status_response.url}"
                              f"({get_status_response.service_type}) - {get_status_response.save_request_status}")
            report.write("{},{},{},{},{},{}\n".format(get_status_response.request_id,
                                                      get_status_response.url,
                                                      get_status_response.service_type,
                                                      get_status_response.save_request_status,
                                                      get_status_response.save_task_status,
                                                      get_status_response.save_request_date
                                                      )
                         )
        else:
            archive_response = repo.archive()
            if archive_response.status_code != 200:
                logging.error(f"[archive]: Non successful archive for {archive_response.url}"
                              f"({archive_response.service_type}) - {archive_response.save_request_status}")
            report.write("{},{},{},{},{},{}\n".format(archive_response.request_id,
                                                      archive_response.url,
                                                      archive_response.service_type,
                                                      archive_response.save_request_status,
                                                      archive_response.save_task_status,
                                                      archive_response.save_request_date
                                                      )
                         )
    report.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Software heritage script to  '
                                                 'check archived services.')
    parser.add_argument("--repos", "-in", dest="repos", help="Repositories file path location",
                        default="repositories.txt")
    parser.add_argument("--report", "-out", dest='report', help="Report file path location", default="results.txt")
    args = parser.parse_args()

    main(args)
