# github_issue_exporter

Export GitHub PR and Issues as CSV


## Usage

```
./pull_requests_and_issues.py [options] <GitHub organization name> <GitHub project name>
```

Where *GitHub organization name* is the name of the organization owning the GitHub repository, and *GitHub project name* is the repository name.

Options:

* --help: Display the help message
* --state: Select which PR/Issues should be exported (open, closed, all - Default: open)
* --sort: Sort order for PR/Issues (created, updated, comments - Default: created)
* --verbose: Output debug messages
* --quiet: no output except errors


## Output

This tool will export the Pull Requests and Issues into two files, in tab-separated CSV format:

* "GitHub organization name"_"GitHub project name"_Issues.csv
* "GitHub organization name"_"GitHub project name"_PR.csv

The following fields are exported:

* ID: The Issue/PR number (this is not the GitHub internal ID)
* Title
* Created: the timestamp when the Issue/PR was created, beautyfied
* URL: the web URL for the Issue/PR
* State: the current state of the Issue/PR
