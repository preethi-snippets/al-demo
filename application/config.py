import os
application_dir = os.path.dirname(__file__)
database_url = 'postgresql://localhost/test'
#database_url = 'postgresql://aldemo:reco!aldemo@aldemo.c6ppf7ztwoya.us-west-2.rds.amazonaws.com:5432/aldemo'
#csv_file = application_dir + '/../../data/test.csv'
#tab_csv_file = application_dir + '/../../data/test_tab_unix.txt'
excel_file = application_dir + '/../data/Data for Textvantage demo v2.xlsx'
excel_data_format = '2'
sales_data_excel_sheet = 'Sales Data'
terr_assoc_excel_sheet = 'Territory Association'
sales_data_table_name = 'demo_sales_data'
terr_assoc_table_name = 'demo_terr_assoc'
activity_data_table_name = 'demo_activity_data'
db_flavor = 'postgres'
fig_dir = application_dir + '/trend_images/'
#db_flavor = 'mysql'
primary_brands = frozenset(['Protovix'])
other_brands = frozenset(['Compvix'])
monthly_data_cols = frozenset(['M1', 'M2', 'M3', 'M4', 'M5', 'M6'])
months_to_store = frozenset(['M1', 'M2', 'M3', 'M4', 'M5', 'M6'])
m1_month_year = "Feb 16"
# which growth percents to calculate and include in graphs,
#   depends on how many months of data available
#   r3_growth and r6_sales always calculated
rN_growth = frozenset([])
secret_key = 'my secret key'
bubble_scale_factor = 0.05
images_url='localhost:5000/trend_figures/'