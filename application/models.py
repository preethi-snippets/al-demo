from flask_sqlalchemy import SQLAlchemy
from application import application
from sqlalchemy.sql.expression import and_
from pandas import read_excel
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
    mdm_id = db.Column('mdm_id', db.String)
    brand_name = db.Column('brand_name', db.String)
    r6_sales = db.Column('r6_sales', db.Float)
    r6_growth = db.Column('r6_growth', db.Float)

def populate_db_from_excel():

    # Drop un-interesting columns
    interesting_cols = ['Territory', 'Site', 'MDM ID', 'Brand Name', 'R6 Sales', 'R6 Growth']

    df = read_excel(config.excel_file, sheetname=config.sheet_in_excel_file, converters={'Territory':str, 'Site':str, 'MDM ID':str, 'Brand Name':str, 'R6 Sales':float, 'R6 Growth': float})
    for c in df.columns:
        if c not in interesting_cols:
            df = df.drop(c, axis=1)

    new_column_names = ['territory', 'site', 'mdm_id', 'brand_name', 'r6_sales', 'r6_growth']
    df.columns = new_column_names

    print df.head()
    print "Generating database from excel file: ", config.excel_file, "... ",
    df.to_sql(con=db.get_engine(application), name=config.table_name, flavor=config.db_flavor, if_exists='replace')
    print '.'

def create_db():
    db.create_all()
    populate_db_from_excel()

def get_top_3_by_territory(territory, brand_name):
    all_accounts = Monthly.query.filter(and_(Monthly.territory==territory, Monthly.brand_name==brand_name)).order_by(Monthly.r6_growth.desc()).limit(3).all()
    #for account in all_accounts:
     #   print account.territory, account.brand_name, account.r6_growth
    return all_accounts

def get_bottom_3_by_territory(territory, brand_name):
    all_accounts = Monthly.query.filter(and_(Monthly.territory==territory, Monthly.brand_name==brand_name)).order_by(Monthly.r6_growth.asc()).limit(3).all()
    #for account in all_accounts:
     #   print account.territory, account.brand_name, account.r6_growth
    return all_accounts



