from flask_sqlalchemy import SQLAlchemy
from application import application

db = SQLAlchemy(application)

class Monthly(db.Model):
    __tablename__ = 'Monthly_Site_Listing'
    index = db.Column('index', db.BigInteger)
    rank = db.Column('Rank', db.BigInteger)
    territory = db.Column('Territory', db.String)
    site = db.Column('Site', db.String)
    site_id = db.Column('Site ID', db.String)
    affiliations = db.Column('Affiliated Outlets/Physicians', db.String)
    mdm_id = db.Column('MDM ID', db.String, primary_key=True, nullable=False)
    r6_sales = db.Column('R6 Sales', db.String)

'''
def get_top_3_by_territory(territory):
    all_accounts = Monthly.query.filter_by(territory=territory).order_by(Monthly.r6_sales.desc()).limit(3).all()
    for account in all_accounts:
        print account.territory, account.r6_sales

        '''
