from flask_sqlalchemy import SQLAlchemy
from application import application
from sqlalchemy.sql.expression import and_
from pandas import read_excel, read_table, Series, DataFrame
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.ticker import FormatStrFormatter
import datetime
from dateutil.relativedelta import relativedelta
from numpy import nan
import config
from flask_kvsession import KVSessionExtension
from simplekv.db.sql import SQLAlchemyStore
from sqlalchemy import MetaData

db = SQLAlchemy(application)

class Monthly(db.Model):
    __tablename__ = config.monthly_data_table_name
    index = db.Column('index', db.BigInteger, primary_key=True)
    #rank = db.Column('Rank', db.BigInteger)
    territory = db.Column('territory', db.String)
    site = db.Column('site', db.String)
    site_id = db.Column('site_id', db.String)
    #affiliations = db.Column('Affiliated Outlets/Physicians', db.String)
    #mdm_id = db.Column('mdm_id', db.String)
    address = db.Column('address', db.String)
    city = db.Column('city', db.String)
    state = db.Column('state', db.String)
    zip = db.Column('zip', db.String)
    brand_name = db.Column('brand_name', db.String)

    r6_sales = db.Column('r6_sales', db.Integer)
    r6_sales_contrib = db.Column('r6_sales_contrib', db.Float)
    r3_growth_value = db.Column('r3_growth_value', db.Integer)

    r3_growth_pct = db.Column('r3_growth_pct', db.Float)
    r6_growth_pct = db.Column('r6_growth_pct', db.Float)
    r12_growth_pct = db.Column('r12_growth_pct', db.Float)

    M1 = db.Column('M1', db.Integer)
    M2 = db.Column('M2', db.Integer)
    M3 = db.Column('M3', db.Integer)
    M4 = db.Column('M4', db.Integer)
    M5 = db.Column('M5', db.Integer)
    M6 = db.Column('M6', db.Integer)

class TerrAssoc(db.Model):
    __tablename__ = config.terr_assoc_table_name
    #index = db.Column('index', db.BigInteger, primary_key=True)
    phone = db.Column('phone', db.BigInteger, primary_key=True)
    territory = db.Column('territory', db.String)

def create_kvsession_store():
    metadata = MetaData(bind=db.get_engine(application))
    store = SQLAlchemyStore(db.get_engine(application), metadata, 'kvstore')
    #print "Not creating kvstore table...."
    store.table.create(checkfirst=True)
    KVSessionExtension(store, application)

def populate_db_from_excel():

    # Descriptive columns to pick from the DB
    descriptive_cols = frozenset(['Territory', 'Site', 'Site ID', 'Brand Name',
                                  'Address', 'City', 'State', 'Zip'])

    monthly_data_cols = frozenset(['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12',
                         'M13', 'M14', 'M15', 'M16', 'M17', 'M18', 'M19', 'M20', 'M21', 'M22', 'M23', 'M24'])

    df = read_excel(config.excel_file, sheetname=config.monthly_data_excel_sheet,
                    converters={'Territory':str, 'Site':str, 'Site ID':str, 'Brand Name':str,
                                'Address': str, 'City': str, 'State': str, 'Zip': str,
                                'M1':int, 'M2':int, 'M3':int, 'M4':int, 'M5':int, 'M6':int, 'M7':int, 'M8':int,
                                'M9':int, 'M10':int, 'M11':int, 'M12':int, 'M13':int, 'M14':int, 'M15':int, 'M16':int,
                                'M17':int, 'M18':int, 'M19':int, 'M20':int, 'M21': int, 'M22': int, 'M23': int, 'M24': int})

    print df.head

    relevant_cols = descriptive_cols.union(monthly_data_cols)

    for c in df.columns:
        if c not in relevant_cols:
            df = df.drop(c, axis=1)

    df.rename(columns={'Territory':'territory', 'Site':'site', 'Site ID': 'site_id', 'Brand Name':'brand_name',
                       'Address':'address', 'City':'city', 'State':'state', 'Zip':'zip'}, inplace=True)

    '''create new columns
        rN_sales: rolling sales over N months
        pN_sales: rolling sales over previous N months
    '''

    if 3 in config.rN_growth:
        df['r3_sales'] = df['M1'] + df['M2'] + df['M3']
        df['p3_sales'] = df['M4'] + df['M5'] + df['M6']
        df['r3_growth_value'] = df['r3_sales'] - df['p3_sales']
        df['r3_growth_pct'] = df['r3_growth_value'] * 100.0 / df['p3_sales'].replace({0: nan})
        df = df.drop(['r3_sales', 'p3_sales'], axis=1)

    if 6 in config.rN_growth:
        df['r6_sales'] = df['M1'] + df['M2'] + df['M3'] + df['M4'] + df['M5'] + df['M6']
        df['p6_sales'] = df['M7'] + df['M8'] + df['M9'] + df['M10'] + df['M11'] + df['M12']
        df['r6_growth_value'] = df['r6_sales'] - df['p6_sales']
        df['r6_growth_pct'] = df['r6_growth_value'] * 100.0 / df['p6_sales'].replace({0: nan})

    if 12 in config.rN_growth:
        df['r12_sales'] = df['M1'] + df['M2'] + df['M3'] + df['M4'] + df['M5'] + df['M6'] + df['M7'] + df['M8'] + df['M9'] + df['M10'] + df['M11'] + df['M12']
        df['p12_sales'] = df['M13'] + df['M14'] + df['M15'] + df['M16'] + df['M17'] + df['M18'] + df['M19'] + df['M20'] + df['M21'] + df['M22'] + df['M23'] + df['M24']
        df['r12_growth_value'] = df['r12_sales'] - df['p12_sales']
        df['r12_growth_pct'] = df['r12_growth_value'] * 100.0 / df['p12_sales'].replace({0: nan})
        df = df.drop(['r12_sales', 'p12_sales'], axis=1)

    # Once crunched, monthly sales data need not be stored in DB
    months_to_discard = list(set(monthly_data_cols) - config.months_to_store)
    print months_to_discard
    for c in df.columns:
        if c in months_to_discard:
          df = df.drop(c, axis=1)

    '''sales_contrib: how much the site contributed towards the brand's territory sales
    '''
    # Groupby brand_name, territory, find sum, and create a dictionary from the df for easy lookup
    sum_dict = df[['brand_name', 'territory', 'r6_sales']].groupby(['brand_name', 'territory'], sort=False).sum().to_dict()['r6_sales']

    # create new column by dividing sales by sum for (brand,territory)
    df['r6_sales_contrib'] = df.apply(lambda row: row['r6_sales'] * 100.0 / sum_dict[(row['brand_name'], row['territory'])], axis = 1)

    print df.head()
    print "Generating database from excel sheet: ", config.monthly_data_excel_sheet, "... ",
    df.to_sql(con=db.get_engine(application), name=config.monthly_data_table_name, flavor=config.db_flavor, if_exists='replace')
    print '.'

    df = read_excel(config.excel_file, sheetname=config.terr_assoc_excel_sheet,
                    converters={'Phone': int, 'Territory': str})

    df.rename(columns={'Phone': 'phone', 'Territory': 'territory'}, inplace=True)

    print df.head()
    print "Generating database from excel sheet: ", config.terr_assoc_excel_sheet, "... ",
    df.to_sql(con=db.get_engine(application), name=config.terr_assoc_table_name, flavor=config.db_flavor, if_exists='replace')
    print '.'

'''
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
    '''

def create_db():
    db.create_all()
    populate_db_from_excel()

def get_top_3_by_territory(territory, brand_name):
    all_accounts = Monthly.query.filter(and_(Monthly.territory==territory, Monthly.brand_name==brand_name)).order_by(Monthly.r3_growth_value.desc()).limit(3).all()
    print all_accounts
    return all_accounts

def get_bottom_3_by_territory(territory, brand_name):
    all_accounts = Monthly.query.filter(and_(Monthly.territory==territory, Monthly.brand_name==brand_name)).order_by(Monthly.r3_growth_value.asc()).limit(3).all()
    return all_accounts

def describe_site(site):

    primary_accounts = []
    plot_dict = {}
    index_lst = range(1,7)

    # Retrieve primary brands
    for brand_name in config.primary_brands:
        accounts = Monthly.query.filter(and_(Monthly.site == site, Monthly.brand_name == brand_name)).all()
        primary_accounts.extend(accounts)
        plot_dict[brand_name] = Series([accounts[0].M1, accounts[0].M2, accounts[0].M3,
                                        accounts[0].M4, accounts[0].M5, accounts[0].M6],
                                       index=index_lst)

    # Retrieve other brands
    other_accounts = []
    for brand_name in config.other_brands:
        accounts = Monthly.query.filter(and_(Monthly.site == site, Monthly.brand_name == brand_name)).all()
        other_accounts.extend(accounts)
        plot_dict[brand_name] = Series([accounts[0].M1, accounts[0].M2, accounts[0].M3,
                                        accounts[0].M4, accounts[0].M5, accounts[0].M6],
                                       index=index_lst)

    # Generate trend plot for all brands
    DataFrame(plot_dict).plot(marker='.')
    plt.grid()
    plt.ylabel('Number of Vials')
    plt.ylim(ymin=0)
    plt.xlim(xmin=0, xmax=7)
    month_labels = [datetime.datetime.strftime((datetime.datetime.strptime(config.m1_month_year, "%b %y") +
                                                        relativedelta(months=-(i-1))), "%b %y") for i in index_lst]
    # print month_labels
    plt.xticks(index_lst, month_labels)
    plt.title("Trends for " + site)
    filename = site.replace(" ", "_") + '.png'
    #print filename
    plt.savefig(config.fig_dir + '/' + filename)

    # Create return info
    #print config.m1_month_year, config.m1_month_year.title()
    return {'primary': primary_accounts, 'other': other_accounts,
                    'latest_date': config.m1_month_year.title(),
                    'trend_file': filename}

def lookup_terr(phone):
    account_list = TerrAssoc.query.filter(TerrAssoc.phone == phone).limit(1).all()
    #for account in account_list:
     #   print account.phone, account.territory
    return account_list

def get_top3_by_phone(phone):
    territory = lookup_terr(phone)[0].territory

    response = ""
    for brand_name in config.primary_brands:
        all_accounts = Monthly.query.filter(and_(Monthly.territory == territory, Monthly.brand_name == brand_name)).order_by(Monthly.r3_growth_value.desc()).limit(3).all()
        response = response + "%s :" % brand_name
        for index, account in enumerate(all_accounts):
            response = response + " %d) %s (growth %s)" % (index+1, account.site, account.r3_growth_value)

    return response

def get_bottom3_by_phone(phone):
    territory = lookup_terr(phone)[0].territory

    response = ""
    for brand_name in config.primary_brands:
        all_accounts = Monthly.query.filter(and_(Monthly.territory == territory, Monthly.brand_name == brand_name)).order_by(Monthly.r3_growth_value.asc()).limit(3).all()
        response = response + "%s :" % brand_name
        for index, account in enumerate(all_accounts):
            response = response + " %d) %s (growth %.1f)" % (index+1, account.site, account.r3_growth_value)

    return response

def find_site_by_territory(phone, site_input):
    territory = lookup_terr(phone)[0].territory
    sites = []

    for brand_name in config.primary_brands:
        accounts = Monthly.query.filter(and_(Monthly.territory == territory, Monthly.brand_name == brand_name, Monthly.site.ilike('%'+site_input+'%'))).distinct(Monthly.site_id).all()
        sites.extend(accounts)

    # maybe store these sites in a session?
    for site in sites:
        print site.site, site.site_id, site.brand_name
    return sites

def none_float(input):
    if input is None:
        return "NA"
    else:
        return "%.1f%%" % (input)

'''
def describe_one_site_twilio(site):
    plot_dict = {}
    index_lst = range(1, 7)
    sms_resp_str = ""
    date = config.m1_month_year.title()

    for brand_name in config.primary_brands:
        sms_resp_str = sms_resp_str + \
                       "%s: " % (brand_name) + \
                       " terr contrib: " + none_float(account.r6_sales_contrib) + \
                       ", growth: " + none_float(account.r3_growth_pct) + \
                       " (%s) " % (date)
        plot_dict[brand_name] = Series([account.M1, account.M2, account.M3,
                                    account.M4, account.M5, account.M6],
                                   index=index_lst)

    for brand_name in config.other_brands:
        sms_resp_str = sms_resp_str + \
                       "%s: " % (brand_name) + \
                       " terr contrib: " + none_float(account.r6_sales_contrib) + \
                       ", growth: " + none_float(account.r3_growth_pct) + \
                       " (%s) " % (date)
        plot_dict[brand_name] = Series([account.M1, account.M2, account.M3,
                                    account.M4, account.M5, account.M6],
                                   index=index_lst)
        '''

def describe_site_for_twilio(site):
    print site
    plot_dict = {}
    bubble_plot = {}
    r_growth_pct = {}
    index_lst = range(1, 7)
    sales_index = ['R3', 'R6', 'R12']
    bubble_index = ['R3 Growth', 'R3 Growth Pct', 'R6 Sales']
    sms_resp_str = ""
    date = config.m1_month_year.title()

    # Retrieve primary brands
    for brand_name in config.primary_brands:
        accounts = Monthly.query.filter(and_(Monthly.site == site, Monthly.brand_name == brand_name)).all()
        if len(accounts):
            account = accounts[0]
            sms_resp_str = sms_resp_str + \
                       "%s: " % (brand_name) + \
                        " terr contrib: " + none_float(account.r6_sales_contrib) + \
                        ", growth: " + none_float(account.r3_growth_pct) + \
                        " (%s) " % (date)
            plot_dict[brand_name] = Series([account.M1, account.M2, account.M3,
                                        account.M4, account.M5, account.M6],
                                       index=index_lst)
            r_growth_pct[brand_name] = Series([account.r3_growth_pct, account.r6_growth_pct, account.r12_growth_pct],
                                         index=sales_index)
            bubble_plot[brand_name] = Series([account.r3_growth_value, account.r3_growth_pct, account.r6_sales],
                                             index=bubble_index)

    # Retrieve other brands
    for brand_name in config.other_brands:
        accounts = Monthly.query.filter(and_(Monthly.site == site, Monthly.brand_name == brand_name)).all()
        if len(accounts):
            account = accounts[0]
            sms_resp_str = sms_resp_str + \
                           "%s: " % (brand_name) + \
                           " terr contrib: " + none_float(account.r6_sales_contrib) + \
                           ", growth: " + none_float(account.r3_growth_pct) + \
                           " (%s) " % (date)
            plot_dict[brand_name] = Series([account.M1, account.M2, account.M3,
                                            account.M4, account.M5, account.M6],
                                           index=index_lst)
            r_growth_pct[brand_name] = Series([account.r3_growth_pct, account.r6_growth_pct, account.r12_growth_pct],
                                              index=sales_index)
            bubble_plot[brand_name] = Series([account.r3_growth_value, account.r3_growth_pct, account.r6_sales],
                                             index=bubble_index)

    # Generate sales trend plot for all brands
    plt.style.use('ggplot')
    DataFrame(plot_dict).plot(marker='.', figsize=(3.5, 3), fontsize=1)
    plt.grid(True)
    #plt.ylabel('Number of Vials', fontsize=6)
    plt.ylim(ymin=0)
    plt.xlim(xmin=0, xmax=7)
    month_labels = [datetime.datetime.strftime((datetime.datetime.strptime(config.m1_month_year, "%b %y") +
                                                relativedelta(months=-(i - 1))), "%b %y") for i in index_lst]
    # print month_labels
    plt.xticks(index_lst, month_labels, fontsize=6.5)
    plt.yticks(fontsize=6.5)
    plt.title("Sales Trends", fontsize=8)
    plt.legend(prop={'size':6})
    plt.tick_params(length=0)
    #fig = plt.figure(figsize=[3, 5], dpi=200)
    sales_trend_filename = site.replace(" ", "_") + '_sales_trend.png'
    # print filename
    plt.savefig(config.fig_dir + '/' + sales_trend_filename)

    # Generate growth trend chart for all brands
    df = DataFrame(r_growth_pct).fillna(0)
    #print df
    #print df.index
    #print list(df.index)
    plt.style.use('ggplot')
    df.plot.bar(figsize=(3.5, 3))
    plt.grid(True)
    plt.xticks(fontsize=6.5,rotation='horizontal')
    plt.yticks(fontsize=6.5)
    plt.gca().get_yaxis().set_major_formatter(FormatStrFormatter('%d%%'))
    plt.tick_params(length=0)
    plt.title('Growth Trends', fontsize=8)
    plt.legend(prop={'size': 6})
    growth_trend_filename = site.replace(" ", "_") + '_growth_trend.png'
    # print filename
    plt.savefig(config.fig_dir + '/' + growth_trend_filename)

    # Generate bubble chart for all brands
    df = DataFrame(bubble_plot).T.fillna(0)
    # print df
    # print df.index
    # print list(df.index)
    plt.style.use('ggplot')
    df.plot.scatter(x='R3 Growth', y='R3 Growth Pct', s=df['R6 Sales'] * 0.5, figsize=(6.5, 2.5), alpha=0.5)
    plt.grid(True)
    plt.ylabel('R3 Growth Pct', fontsize=6.5)
    plt.xlabel('R3 Growth Value', fontsize=6.5)
    plt.xticks(fontsize=6.5)
    plt.yticks(fontsize=6.5)
    plt.gca().get_yaxis().set_major_formatter(FormatStrFormatter('%d%%'))
    plt.tick_params(length=0)
    # biggest_bubble = df['R6 Sales'].max()/2
    # print biggest_bubble
    # plt.ylim(ymin=(df['R3 Growth Pct'].min() - biggest_bubble), ymax=df['R3 Growth Pct'].max() + biggest_bubble)
    # plt.xlim(xmin=(df['R3 Growth'].min() - biggest_bubble), xmax=df['R3 Growth'].max() + biggest_bubble)
    plt.title('Relative Growth vs. Absolute Growth', fontsize=8)
    for i, txt in enumerate(list(df.index)):
        # print i, df['R3 Growth'][i], df['R3 Growth Pct'][i], txt
        plt.text(df['R3 Growth'][i], df['R3 Growth Pct'][i], txt, fontsize=5, horizontalalignment='center')

    bubble_chart_filename = site.replace(" ", "_") + '_bubble.png'
    # print filename
    plt.savefig(config.fig_dir + '/' + bubble_chart_filename)

    return {'message': sms_resp_str,
            'site': site,
            'site_address': account.address,
            'date': config.m1_month_year.title(),
            'site_city': account.city,
            'site_state': account.state,
            'site_zip': account.zip,
            'media': sales_trend_filename,
            'sales_media': sales_trend_filename,
            'growth_media': growth_trend_filename,
            'bubble_media': bubble_chart_filename}







