# TN Gazette Extractor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FlatGithub](https://img.shields.io/badge/FlatGithub-View%20Data-green?style=flat-square&logo=github)](https://flatgithub.com/srikanthlogic/TNGazette)
[![Open in Gitpod](https://img.shields.io/badge/Open%20in-Gitpod-blue?logo=gitpod)](https://gitpod.io/#https://github.com/srikanthlogic/TNGazette)


TN Gazette Extractor is a Python program that extracts gazette pages results from the [Tamil Nadu Gazette website](https://www.stationeryprinting.tn.gov.in/) and saves them as a CSV file.

Usage
To use TN Gazette Extractor, follow these steps:

Clone or download the repository to your local machine.

Install the required Python packages by running pip install -r requirements.txt in your terminal.

Run the program by 
`python tn_gazette_extractor.py [--archive-mode <archive_mode>]`  
in your terminal.

The program takes the following arguments:

--archive-mode: (optional) the archive mode to use. Valid options are "full" (extract the entire archive) or "current-year" (extract only the current year's archive). Default is current-year

Once the program finishes running, the extracted CSV file will be available in `data`  directory as the program.