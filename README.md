# fc4eosc-sh-script
FAIRCORE4EOSC - Software heritage script to archive core components

# Description

The script reads a list of repositories sources alongside with their type(git,svn.etc)
and attempts to archive each single one of them through the software heritage api.

The execution follows the steps of:
- Use the [visit](https://archive.softwareheritage.org/api/1/origin/visit/latest/doc/) api call to determine if the repository
  is already archived.
- Use the [save](https://archive.softwareheritage.org/api/1/origin/save/doc/) api call to either get the status of an archived repository
  or begin the process of archival for a missing one.
- The script will then produce a report containing the following information
  for each repository(some fields may not be present for all repos).
    - request id
    - repository url
    - repository type
    - save request status
    - save task status
    - save date

# Run

The script accepts two arguments:
- `--repos, -in` The file containing the repositories urls.
- `--report, -out` The destination file to save the result(will append the utc timestamp).

```shell
$ ./repositories_archive.py --repos repositories-example.txt --report-example-report
```

