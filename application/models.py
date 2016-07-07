from flask_sqlalchemy import SQLAlchemy
from application import application
from sqlalchemy.sql.expression import and_
from pandas import read_excel, read_table
import config

db = SQLAlchemy(application)

class Monthly(db.Model):
    __tablename__ = 'monthly_sample'
    index = db.Column('index', db.BigInteger, primary_key=True)
    #rank = db.Column('Rank', db.BigInteger)
    territory = db.Column('territory', db.String)
    site = db.Column('site', db.String)
    #site_id = db.Column('Site ID', db.String)
    #affiliations = db.Column('Affiliated Outlets/Physicians', db.String)
    #mdm_id = db.Column('mdm_id', db.String)
    brand_name = db.Column('brand_name', db.String)
    r6_sales = db.Column('r6_sales', db.Integer)
    r3_growth_value = db.Column('r3_growth_value', db.Integer)
    r6_sales_contrib = db.Column('r6_sales_contrib', db.Float)

def populate_db_from_excel():

    # Drop un-interesting columns
    descriptive_cols = ['Territory', 'Site', 'Brand Name']

    monthly_data_cols = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12',
                         'M13', 'M14', 'M15', 'M16', 'M17', 'M18', 'M19', 'M20', 'M21', 'M22', 'M23', 'M24']

    relevant_cols = descriptive_cols + monthly_data_cols

    df = read_excel(config.excel_file, sheetname=config.sheet_in_excel_file,
                    converters={'Territory':str, 'Site':str, 'Brand Name':str,
                                'M1':int, 'M2':int, 'M3':int, 'M4':int, 'M5':int, 'M6':int, 'M7':int, 'M8':int,
                                'M9':int, 'M10':int, 'M11':int, 'M12':int, 'M13':int, 'M14':int, 'M15':int, 'M16':int,
                                'M17':int, 'M18':int, 'M19':int, 'M20':int, 'M21': int, 'M22': int, 'M23': int, 'M24': int})
    for c in df.columns:
        if c not in relevant_cols:
            df = df.drop(c, axis=1)

    df.rename(columns={'Territory':'territory', 'Site':'site', 'Brand Name':'brand_name'}, inplace=True)

    '''create new columns
        rN_sales: rolling sales over N months
        pN_sales: rolling sales over previous N months
    '''
    df['r1_sales'] = df['M1']
    df['p1_sales'] = df['M2']

    df['r3_sales'] = df['M1'] + df['M2'] + df['M3']
    df['p3_sales'] = df['M4'] + df['M5'] + df['M6']

    df['r6_sales'] = df['M1'] + df['M2'] + df['M3'] + df['M4'] + df['M5'] + df['M6']
    df['p6_sales'] = df['M7'] + df['M8'] + df['M9'] + df['M10'] + df['M11'] + df['M12']

    df['r12_sales'] = df['M1'] + df['M2'] + df['M3'] + df['M4'] + df['M5'] + df['M6'] + df['M7'] + df['M8'] + df['M9'] + df['M10'] + df['M11'] + df['M12']
    df['p12_sales'] = df['M13'] + df['M14'] + df['M15'] + df['M16'] + df['M17'] + df['M18'] + df['M19'] + df['M20'] + df['M21'] + df['M22'] + df['M23'] + df['M24']

    '''
    rN_growth_value: growth amount between current and previous rolling sales
    '''
    df['r3_growth_value'] = df['p3_sales'] - df['r3_sales']
    df['r6_growth_value'] = df['p6_sales'] - df['r6_sales']
    df['r12_growth_value'] = df['p12_sales'] - df['r12_sales']

    # Once crunched, monthly sales data need not be stored in DB
    for c in df.columns:
        if c in monthly_data_cols:
            df = df.drop(c, axis=1)

    print df.head()

    '''sales_contrib: how much the site contributed towards the brand's territory sales
    '''
    # Groupby brand_name, territory, find sum, and create a dictionary from the df for easy lookup
    sum_dict = df[['brand_name', 'territory', 'r6_sales']].groupby(['brand_name', 'territory'], sort=False).sum().to_dict()['r6_sales']

    # create new column by dividing sales by sum for (brand,territory)
    df['r6_sales_contrib'] = df.apply(lambda row: row['r6_sales'] * 100.0 / sum_dict[(row['brand_name'], row['territory'])], axis = 1)

    #print df.head()
    print "Generating database from excel file: ", config.excel_file, "... ",
    df.to_sql(con=db.get_engine(application), name=config.table_name, flavor=config.db_flavor, if_exists='replace')
    print '.'

def populate_db_from_csv():

    # Drop un-interesting columns
    interesting_cols = ['Territory', 'Site', 'MDM ID', 'Brand Name', 'R6 Sales', 'R6 Growth']

    df = read_table(config.tab_csv_file, converters={'Territory':str, 'Site':str, 'MDM ID':str, 'Brand Name':str, 'R6 Sales':float, 'R6 Growth': float})
    for c in df.columns:
        if c not in interesting_cols:
            df = df.drop(c, axis=1)

    new_column_names = ['territory', 'site', 'mdm_id', 'brand_name', 'r6_sales', 'r6_growth']
    df.columns = new_column_names

    print df.head()
    print "Generating database from csv file: ", config.tab_csv_file, "... ",
    df.to_sql(con=db.get_engine(application), name=config.table_name, flavor=config.db_flavor, if_exists='replace')
    print '.'

def create_db():
    db.create_all()
    populate_db_from_excel()

def get_top_3_by_territory(territory, brand_name):
    all_accounts = Monthly.query.filter(and_(Monthly.territory==territory, Monthly.brand_name==brand_name)).order_by(Monthly.r3_growth_value.desc()).limit(3).all()
    return all_accounts

def get_bottom_3_by_territory(territory, brand_name):
    all_accounts = Monthly.query.filter(and_(Monthly.territory==territory, Monthly.brand_name==brand_name)).order_by(Monthly.r3_growth_value.asc()).limit(3).all()
    return all_accounts

def describe_site(site):

    primary_accounts = []
    for brand_name in config.primary_brands:
        primary_accounts.extend(Monthly.query.filter(and_(Monthly.site == site, Monthly.brand_name == brand_name)).all())

    other_accounts = []
    for brand_name in config.other_brands:
        other_accounts.extend(Monthly.query.filter(and_(Monthly.site == site, Monthly.brand_name == brand_name)).all())

    all_accounts = {'primary': primary_accounts, 'other': other_accounts}
    return all_accounts


