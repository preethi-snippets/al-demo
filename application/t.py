from sqlalchemy import create_engine
import pandas as pd
eng=create_engine('postgresql://localhost/test')
df=pd.read_sql_query('select * from monthly_sample',con=eng)
b=df[['brand_name','territory','r6_sales']].groupby(['brand_name','territory'])
i = b.sum()
#i=k.set_index(['brand_name','territory'])
i.to_dict()['r6_sales'][('AVASTIN', '0B331C3-NEW ORLEANS, LA')]
sum_dict=i.to_dict()['r6_sales']

def find_contrib(row):
    return row['r6_sales'] / sum_dict[(row['brand_name'], row['territory'])]

df.apply(find_contrib, axis=1)

df.apply(lamdba row : row['r6_sales']/sum_dict[(row['brand_name'], row['territory'])], axis=1)