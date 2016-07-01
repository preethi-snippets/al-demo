import os
application_dir = os.path.dirname(__file__)
database_url = 'postgresql://localhost/test'
csv_file = application_dir + '/../../data/test.csv'
excel_file = application_dir + '/../../data/test.xlsx'
sheet_in_excel_file = 'Sheet1'
table_name = 'monthly_sample'
db_flavor = 'postgres'