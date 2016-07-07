import os
application_dir = os.path.dirname(__file__)
#database_url = 'postgresql://localhost/test'
database_url = 'postgresql://aldemo:reco!aldemo@aldemo.c6ppf7ztwoya.us-west-2.rds.amazonaws.com:5432/aldemo'
csv_file = application_dir + '/../../data/test.csv'
tab_csv_file = application_dir + '/../../data/test_tab_unix.txt'
excel_file = application_dir + '/../../data/monthly_test.xlsx'
sheet_in_excel_file = 'Monthly Site Listing'
table_name = 'monthly_sample'
db_flavor = 'postgres'
#db_flavor = 'mysql'
primary_brands = ['AVASTIN']
other_brands = ['VECTIBIX', 'ERBITUX']