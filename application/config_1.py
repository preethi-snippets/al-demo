import os
application_dir = os.path.dirname(__file__)
database_url = 'postgresql://localhost/test'
#database_url = 'postgresql://aldemo:reco!aldemo@aldemo.c6ppf7ztwoya.us-west-2.rds.amazonaws.com:5432/aldemo'
#csv_file = application_dir + '/../../data/test.csv'
#tab_csv_file = application_dir + '/../../data/test_tab_unix.txt'
excel_file = application_dir + '/../data/monthly_test.xlsx'
sales_data_excel_sheet = 'Monthly Site Listing'
terr_assoc_excel_sheet = 'Territory Association'
sales_data_table_name = 'monthly_sample'
terr_assoc_table_name = 'terr_assoc'
db_flavor = 'postgres'
fig_dir = application_dir + '/trend_images/'
#db_flavor = 'mysql'
primary_brands = frozenset(['AVASTIN'])
other_brands = frozenset(['VECTIBIX', 'ERBITUX'])
m1_month_year = "Jan 16"
monthly_data_cols = frozenset(['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12',
                               'M13', 'M14', 'M15', 'M16', 'M17', 'M18', 'M19', 'M20', 'M21', 'M22', 'M23', 'M24'])
months_to_store = frozenset(['M1', 'M2', 'M3', 'M4', 'M5', 'M6'])
# which growth pcts to calculate and include in graphs, depends on how many months of data available
# r3_growth and r6_sales always calculated
rN_growth = frozenset([6,12])
secret_key = 'my secret key'
bubble_scale_factor = 0.75