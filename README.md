Depending on the setup of a Field Service Organization's Content Record Management System, various reports sometimes need to be pulled and compiled in order to gather specific insights.  This script compiles the following multiple reports from various CRM systems in order to provide customers a detailed history of their asset:

* Case & Work Order Report (Salesforce)
* Service Contract Report (Salesforce)
* Part Consumption Report (Salesforce)
* Field Service Engineer Timesheet Report (Salesforce)
* Parts Pricing Report (Netsuite)

This script can be modified to provide standard cost of asset's service history given the standard cost per hour of a field service engineer and standard cost of parts.  This information can give Field Service Management insights into profitability of the organization.

Reports should be loaded into the same folder with the following names (.csv file with UTF-8 encoding):

* cases.csv
* contracts.csv
* parts.csv
* timesheets.csv
* part_pricing.csv

Ensure that variables headers in the reports are the same as the script.  The script will produce the tidy output dataframe of 'df.csv' which can then be further analyzed in user's software of choice
