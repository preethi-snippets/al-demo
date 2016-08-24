from flask_sqlalchemy import SQLAlchemy
from application import application
from sqlalchemy.sql.expression import and_
from pandas import read_excel, read_table, Series, DataFrame, concat, MultiIndex, to_numeric, read_sql
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

class Sales(db.Model):
    __tablename__ = config.sales_data_table_name
    id = db.Column('id', db.BigInteger, primary_key=True, autoincrement=True)
    #rank = db.Column('Rank', db.BigInteger)
    territory = db.Column('territory', db.String)
    site = db.Column('site', db.String)
    site_id = db.Column('site_id', db.String, nullable=False)
    #affiliations = db.Column('Affiliated Outlets/Physicians', db.String)
    #mdm_id = db.Column('mdm_id', db.String)
    address = db.Column('address', db.String)
    city = db.Column('city', db.String)
    state = db.Column('state', db.String)
    zip = db.Column('zip', db.String)
    brand_name = db.Column('brand_name', db.String)

    M1 = db.Column('M1', db.Integer)
    M2 = db.Column('M2', db.Integer)
    M3 = db.Column('M3', db.Integer)
    M4 = db.Column('M4', db.Integer)
    M5 = db.Column('M5', db.Integer)
    M6 = db.Column('M6', db.Integer)

    r3_sales = db.Column('r3_sales', db.Integer)
    p3_sales = db.Column('p3_sales', db.Integer)
    r6_sales = db.Column('r6_sales', db.Integer)
    r6_sales_contrib = db.Column('r6_sales_contrib', db.Float)
    r3_growth_value = db.Column('r3_growth_value', db.Integer)
    r3_growth_pct = db.Column('r3_growth_pct', db.Float)

    if 6 in config.rN_growth:
        r6_growth_pct = db.Column('r6_growth_pct', db.Float)

    if 12 in config.rN_growth:
        r12_growth_pct = db.Column('r12_growth_pct', db.Float)

class Activity(db.Model):
    __tablename__ = config.activity_data_table_name
    id = db.Column('id', db.BigInteger, primary_key=True, autoincrement=True)
    #rank = db.Column('Rank', db.BigInteger)
    site = db.Column('site', db.String)
    site_id = db.Column('site_id', db.String, nullable=False)
    calls = db.Column('calls', db.Integer)
    samples = db.Column('samples', db.Integer)
    copay_cards = db.Column('copay_cards', db.Integer)
    speaker_attendees = db.Column('speaker_attendees', db.Integer)
    total_activity = db.Column('total_activity', db.Integer)
    activity_category = db.Column('activity_category', db.String)


class TerrAssoc(db.Model):
    __tablename__ = config.terr_assoc_table_name
     #index = db.Column('index', db.BigInteger, primary_key=True)
    name = db.Column('name', db.String, nullable=False)
    phone = db.Column('phone', db.String, primary_key=True)
    territory = db.Column('territory', db.String, nullable=False)

    def __init__(self, name, phone, territory):
        self.name = name
        self.phone = phone
        self.territory = territory

def add_terr_assoc(name, phone, territory):
    terr_assoc = TerrAssoc(name, phone, territory)
    db.session.add(terr_assoc)
    db.session.commit()

def create_kvsession_store():
    metadata = MetaData(bind=db.get_engine(application))
    #metadata.reflect()
    store = SQLAlchemyStore(db.get_engine(application), metadata, 'kvstore')
    store.table.create(checkfirst=True)
    KVSessionExtension(store, application)

def create_sales_table(df):

    '''df contains the site and Sales sales data
    '''

    '''sales_contrib: how much the site contributed towards the brand's territory sales based on rolling 6 months sales
     '''

    df['r6_sales'] = df['M1'] + df['M2'] + df['M3'] + df['M4'] + df['M5'] + df['M6']

    # Groupby brand_name, territory, find sum, and create a dictionary from the df for easy lookup
    sum_dict = \
        df[['brand_name', 'territory', 'r6_sales']].groupby(['brand_name', 'territory'], sort=False).sum().to_dict()[
            'r6_sales']

    # create new column by dividing sales by sum for (brand,territory)
    df['r6_sales_contrib'] = df.apply(
        lambda row: row['r6_sales'] * 100.0 / sum_dict[(row['brand_name'], row['territory'])], axis=1)
    '''create new columns
        rN_sales: rolling sales over N months
        pN_sales: rolling sales over previous N months
    '''


    df['r3_sales'] = df['M1'] + df['M2'] + df['M3']
    df['p3_sales'] = df['M4'] + df['M5'] + df['M6']
    df['r3_growth_value'] = df['r3_sales'] - df['p3_sales']
    df['r3_growth_pct'] = df['r3_growth_value'] * 100.0 / df['p3_sales'].replace({0: nan})

    if 6 in config.rN_growth:
        df['p6_sales'] = df['M7'] + df['M8'] + df['M9'] + df['M10'] + df['M11'] + df['M12']
        df['r6_growth_value'] = df['r6_sales'] - df['p6_sales']
        df['r6_growth_pct'] = df['r6_growth_value'] * 100.0 / df['p6_sales'].replace({0: nan})
        df = df.drop(['p6_sales'], axis=1)

    if 12 in config.rN_growth:
        df['r12_sales'] = df['M1'] + df['M2'] + df['M3'] + df['M4'] + df['M5'] + df['M6'] + df['M7'] + df['M8'] + df[
            'M9'] + df['M10'] + df['M11'] + df['M12']
        df['p12_sales'] = df['M13'] + df['M14'] + df['M15'] + df['M16'] + df['M17'] + df['M18'] + df['M19'] + df[
            'M20'] + df['M21'] + df['M22'] + df['M23'] + df['M24']
        df['r12_growth_value'] = df['r12_sales'] - df['p12_sales']
        df['r12_growth_pct'] = df['r12_growth_value'] * 100.0 / df['p12_sales'].replace({0: nan})
        df = df.drop(['r12_sales', 'p12_sales'], axis=1)

    # Once crunched, sales data need not be stored in DB
    months_to_discard = list(config.monthly_data_cols - config.months_to_store)
    print months_to_discard
    for c in df.columns:
        if c in months_to_discard:
            df = df.drop(c, axis=1)

    print df.head()
    engine = db.get_engine(application)
    print "Creating table ", config.sales_data_table_name, "... ",
    db.metadata.drop_all(engine, tables=[Sales.__table__])
    db.metadata.create_all(engine, tables=[Sales.__table__])
    df.to_sql(con=engine, name=config.sales_data_table_name, flavor=config.db_flavor,
              if_exists='append', index=False)
    print '.'
    #db.metadata.reflect()

def create_activity_table(df):
    engine = db.get_engine(application)
    print "Creating table ", config.activity_data_table_name, "... ",
    db.metadata.drop_all(engine, tables=[Activity.__table__])
    db.metadata.create_all(engine, tables=[Activity.__table__])
    df.to_sql(con=engine, name=config.activity_data_table_name, flavor=config.db_flavor,
              if_exists='append', index=False)
    print '.'

def create_terr_assoc_table():
    print "Reading data from excel sheet: ", config.terr_assoc_excel_sheet, "... "
    df = read_excel(config.excel_file, sheetname=config.terr_assoc_excel_sheet,
                    converters={'Name': str, 'Phone': str, 'Territory': str})

    df.rename(columns={'Name': 'name', 'Phone': 'phone', 'Territory': 'territory'}, inplace=True)

    #print df.head()

    engine = db.get_engine(application)
    print "Creating table ", config.terr_assoc_table_name, "... ",
    db.metadata.drop_all(engine, tables=[TerrAssoc.__table__])
    db.metadata.create_all(engine, tables=[TerrAssoc.__table__])
    df.to_sql(con=engine, name=config.terr_assoc_table_name, flavor=config.db_flavor,
              if_exists='append', index=False)
    print '.'
    #db.metadata.reflect()


def read_excel_format_1():

    # Read excel sheet and create dataframe of required format
    # excel sheet format similar to monthly site listing

    # Descriptive columns to pick from the DB
    descriptive_cols = frozenset(['Territory', 'Site', 'Site ID', 'Brand Name',
                                  'Address', 'City', 'State', 'Zip'])

    print "Reading data from excel sheet: ", config.sales_data_excel_sheet, "... "

    df = read_excel(config.excel_file, sheetname=config.sales_data_excel_sheet,
                    converters={'Territory':str, 'Site':str, 'Site ID':str, 'Brand Name':str,
                                'Address': str, 'City': str, 'State': str, 'Zip': str,
                                'M1':int, 'M2':int, 'M3':int, 'M4':int, 'M5':int, 'M6':int, 'M7':int, 'M8':int,
                                'M9':int, 'M10':int, 'M11':int, 'M12':int, 'M13':int, 'M14':int, 'M15':int, 'M16':int,
                                'M17':int, 'M18':int, 'M19':int, 'M20':int, 'M21': int, 'M22': int, 'M23': int, 'M24': int})

    #print df.head

    relevant_cols = descriptive_cols.union(config.monthly_data_cols)

    for c in df.columns:
        if c not in relevant_cols:
            df = df.drop(c, axis=1)

    df.rename(columns={'Territory':'territory', 'Site':'site', 'Site ID': 'site_id', 'Brand Name':'brand_name',
                       'Address':'address', 'City':'city', 'State':'state', 'Zip':'zip'}, inplace=True)

    return df

def read_excel_format_2():

    # Read excel sheet and create dataframe of required format
    # excel sheet format similar to demo data with two level columns

    print "Reading data from excel sheet: ", config.sales_data_excel_sheet, "... "

    df = read_excel(config.excel_file, sheetname=config.sales_data_excel_sheet, header=None)
    df.columns = MultiIndex.from_arrays((df.iloc[0:2].fillna(method='ffill', axis=1))[:2].values,
                                           names=['level0', 'level1'])
    df.drop(df.index[[0, 1]], inplace=True)
    df.columns = [' '.join(col).strip() for col in df.columns.values]

    df_list = []
    for brand in (config.primary_brands.union(config.other_brands)):
        df_new = (df[['Site Site', 'Site Site ID', 'Site Territory', 'Site Address',
                      'Site City', 'Site State', 'Site Zip',
                      '%s M1' % brand, '%s M2' % brand, '%s M3' % brand,
                      '%s M4' % brand, '%s M5' % brand, '%s M6' % brand]])
        df_new['brand_name'] = df_new['Site Site'].apply(lambda x: brand)
        #df_new['brand_name'] = Series([brand for x in range(len(df_new.index))], index=df_new.index)


        df_new.rename(columns={'Site Site': 'site',
                               'Site Site ID': 'site_id',
                               'Site Territory': 'territory',
                               'Site Address': 'address',
                               'Site City': 'city',
                               'Site State': 'state',
                               'Site Zip': 'zip',
                              '%s M1' % brand: 'M1',
                               '%s M2' % brand: 'M2',
                               '%s M3' % brand: 'M3',
                                '%s M4' % brand: 'M4',
                                '%s M5' % brand: 'M5',
                               '%s M6' % brand: 'M6'}, inplace=True)

        df_list.append(df_new)

    df_sales = concat(df_list)

    # change data type to numeric for sales data
    for col in ['M1', 'M2', 'M3', 'M4', 'M5', 'M6']:
        df_sales[col] = to_numeric(df_sales[col]).round()

    #print df_sales.head(n=5)

    #print df.head(n=5)
    # create "Activity" data from corresponding columns
    df_activity = df[['Site Site', 'Site Site ID', 'Activity Calls', 'Activity Samples',
                      'Activity Copay cards', 'Activity Speaker attendees']]

    df_activity.rename(columns={'Site Site': 'site',
                                'Site Site ID': 'site_id',
                                'Activity Calls': 'calls',
                                'Activity Samples': 'samples',
                                'Activity Copay cards': 'copay_cards',
                                'Activity Speaker attendees': 'speaker_attendees'}, inplace=True)

    # change relevant columns to numeric data type
    for col in ['calls', 'samples', 'copay_cards', 'speaker_attendees']:
        df_activity[col] = to_numeric(df_activity[col]).round()

    # create category
    df_activity['total_activity'] = df_activity['calls'] + df_activity['samples'] \
                                    + df_activity['copay_cards'] + df_activity['speaker_attendees']

    def find_cat(value):
        cat = ''
        if value <= 150:
            cat = 'Low'
        elif value > 200:
            cat = 'High'
        else:
            cat = 'Medium'
        return cat


    df_activity['activity_category'] = df_activity['total_activity'].apply(find_cat)

    #print df_activity.head(n=5)

    return {'sales': df_sales, 'activity': df_activity}


def create_and_populate_tables():

    if (config.excel_data_format == '1'):
        df = read_excel_format_1()
        create_sales_table(df)
    elif (config.excel_data_format == '2'):
        df_dict = read_excel_format_2()
        create_sales_table(df_dict['sales'])
        create_activity_table(df_dict['activity'])

    create_terr_assoc_table()

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
    create_and_populate_tables()

def get_top_3_by_territory(territory, brand_name):
    all_accounts = Sales.query.filter(and_(Sales.territory==territory, Sales.brand_name==brand_name)).order_by(Sales.r3_growth_value.desc()).limit(3).all()
    print all_accounts
    return all_accounts

def get_bottom_3_by_territory(territory, brand_name):
    all_accounts = Sales.query.filter(and_(Sales.territory==territory, Sales.brand_name==brand_name)).order_by(Sales.r3_growth_value.asc()).limit(3).all()
    return all_accounts

def describe_site(site):

    primary_accounts = []
    plot_dict = {}
    index_lst = range(1,7)

    # Retrieve primary brands
    for brand_name in config.primary_brands:
        accounts = Sales.query.filter(and_(Sales.site == site, Sales.brand_name == brand_name)).all()
        primary_accounts.extend(accounts)
        plot_dict[brand_name] = Series([accounts[0].M1, accounts[0].M2, accounts[0].M3,
                                        accounts[0].M4, accounts[0].M5, accounts[0].M6],
                                       index=index_lst)

    # Retrieve other brands
    other_accounts = []
    for brand_name in config.other_brands:
        accounts = Sales.query.filter(and_(Sales.site == site, Sales.brand_name == brand_name)).all()
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

def lookup_user(phone):
    user = TerrAssoc.query.filter(TerrAssoc.phone == phone).first()
    return user.name

def lookup_terr(phone):
    account = TerrAssoc.query.filter(TerrAssoc.phone == phone).first()
    #for account in account_list:
     #   print account.phone, account.territory
    if account:
        return account.territory
    else:
        return None

def none_float(input):
    if input is None:
        return "NA"
    else:
        return "%.1f%%" % (input)

def get_top3_by_phone(phone):
    territory = lookup_terr(phone)
    response = []
    for brand_name in config.primary_brands:
        all_accounts = Sales.query.filter(
            and_(Sales.territory == territory, Sales.brand_name == brand_name)).order_by(
            Sales.r3_growth_value.desc()).limit(3).all()
        response.append("%s : " % brand_name.title())
        for index, account in enumerate(all_accounts):
            rsp = " %d. %s (growth: %s units)" % (index+1, account.site, account.r3_growth_value)
            #rsp = rsp + none_float(account.r3_growth_pct) + ")"
            response.append(rsp)
    return response

def get_bottom3_by_phone(phone):

    territory = lookup_terr(phone)
    response = []
    for brand_name in config.primary_brands:
        all_accounts = Sales.query.filter(
            and_(Sales.territory == territory, Sales.brand_name == brand_name)).order_by(
            Sales.r3_growth_value.asc()).limit(3).all()
        response.append("%s : " % brand_name.title())
        for index, account in enumerate(all_accounts):
            rsp = " %d. %s (growth: %s units) " % (index + 1, account.site, account.r3_growth_value)
            #rsp = rsp + none_float(account.r3_growth_pct) + ")"
            response.append(rsp)
    return response

def find_site_by_territory(phone, site_input):
    territory = lookup_terr(phone)
    sites = []

    for brand_name in config.primary_brands:
        accounts = Sales.query.filter(and_(Sales.territory == territory, Sales.brand_name == brand_name, Sales.site.ilike('%'+site_input+'%'))).distinct(Sales.site_id).all()
        sites.extend(accounts)

    # maybe store these sites in a session?
    #for site in sites:
     #   print site.site, site.site_id, site.brand_name
    return sites

def generate_sales_trend_plot(site, plot_dict, sales_index):
    # Generate sales trend plot for all brands
    #print plot_dict
    plt.style.use('ggplot')
    DataFrame(plot_dict).plot(marker='.', figsize=(3, 2.5), fontsize=1)
    plt.grid(True)
    plt.ylim(ymin=0)
    plt.xlim(xmin=0, xmax=7)
    month_labels = [datetime.datetime.strftime((datetime.datetime.strptime(config.m1_month_year, "%b %y") +
                                                relativedelta(months=-(i - 1))), "%b %y") for i in sales_index]
    month_labels.reverse()
    # print month_labels
    plt.xticks(sales_index, month_labels, fontsize=6.5)
    plt.yticks(fontsize=6.5)
    plt.title("Sales Trends", fontsize=8)
    plt.legend(prop={'size': 6})
    plt.tick_params(length=0)
    sales_trend_filename = site.replace(" ", "_") + '_sales_trend.png'
    # print filename
    plt.savefig(config.fig_dir + '/' + sales_trend_filename)
    return sales_trend_filename

def generate_growth_trend_plot(site, r_growth_pct):
    # Generate growth trend chart for all brands
    df = DataFrame(r_growth_pct).fillna(0)
    #print df
    #print df.index
    #print list(df.index)
    plt.style.use('ggplot')
    df.plot.bar(figsize=(3, 2.5))
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
    return growth_trend_filename

def describe_site_for_twilio(site):
    #print site
    plot_dict = {}
    bubble_plot = {}
    r_growth_pct = {}
    sales_index = range(1, 7)
    bubble_index = ['R3 Growth', 'R3 Growth Pct', 'R6 Sales']
    date = config.m1_month_year.title()
    sms_resp = []
    sms_resp.append("Details for %s (%s):" % (site, date))

    #setattr(db.get_engine(application), 'echo', True)
    all_brands = list(config.primary_brands)
    all_brands.extend(list(config.other_brands))
    for brand_name in all_brands:
        #print str(Sales.query.filter(and_(Sales.site == site, Sales.brand_name == brand_name)))
        #accounts = Sales.query.filter(and_(Sales.site == site, Sales.brand_name == brand_name)).all()
        account = Sales.query.filter(and_(Sales.site == site, Sales.brand_name == brand_name)).first()

        #print "retrieving for brand = ", brand_name, accounts, accounts.brand_name
        if account:
            sms = " %s sales " % (brand_name) + \
                    "grew by " + none_float(account.r3_growth_pct) + \
                    " and contributes " + none_float(account.r6_sales_contrib) + \
                    " to the territory. "
            sms_resp.append(sms)
            plot_dict[brand_name] = Series([account.M6, account.M5, account.M4,
                                        account.M3, account.M2, account.M1],
                                       index=sales_index)

            r_growth_pct[brand_name] = Series([account.r3_growth_pct], index=['R3'])
            if 6 in config.rN_growth:
                r_growth_pct[brand_name] = r_growth_pct[brand_name].append(Series([account.r6_growth_pct], index=['R6']))
            if 12 in config.rN_growth:
                r_growth_pct[brand_name] = r_growth_pct[brand_name].append(Series([account.r12_growth_pct], index=['R12']))

            bubble_plot[brand_name] = Series([account.r3_growth_value, account.r3_growth_pct, account.r6_sales],
                                             index=bubble_index)
            #print accounts.__dict__
            db.session.expire(account)

    #print sms_resp
    sales_trend_filename = generate_sales_trend_plot(site, plot_dict, sales_index)
    growth_trend_filename = generate_growth_trend_plot(site, r_growth_pct)

    # Generate bubble chart for all brands
    df = DataFrame(bubble_plot).T.fillna(0)
    # print df
    # print df.index
    # print list(df.index)
    plt.style.use('ggplot')
    df.plot.scatter(x='R3 Growth', y='R3 Growth Pct', s=df['R6 Sales'] * config.bubble_scale_factor, figsize=(6, 2.5), alpha=0.5)
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

    return {'message': sms_resp,
            'site': site,
            'site_address': account.address,
            'date': date,
            'site_city': account.city,
            'site_state': account.state,
            'site_zip': account.zip,
            'media': sales_trend_filename,
            'sales_media': sales_trend_filename,
            'growth_media': growth_trend_filename,
            'bubble_media': bubble_chart_filename}

def overall_performance(phone):
    territory = lookup_terr(phone)
    response = []

    if (territory):
        response.append("Overall performance at " + territory + ": ")
        for brand_name in (config.primary_brands):
            all_sites = read_sql((Sales.query.filter(
                and_(Sales.territory == territory, Sales.brand_name == brand_name))).statement,
                                 db.get_engine(application))

            #print all_sites.head(n=5)

            r3_total = all_sites['r3_sales'].sum()
            p3_total = all_sites['p3_sales'].sum()
            r3_growth = p3_total - r3_total
            if p3_total:
                r3_growth_pct = r3_growth * 100.0 / p3_total
            else:
                r3_growth_pct = None

            rsp = "Rolling 3 month sales and growth for %s are " % (brand_name)
            rsp = rsp + "%d " % (r3_total)
            rsp = rsp + " and " + none_float(r3_growth_pct) + ". "
            response.append(rsp)

            top3_sites = Sales.query.filter(and_(Sales.territory == territory, Sales.brand_name == brand_name)).order_by(Sales.r3_sales.desc()).limit(3).all()

            rsp = "Highest contributors: "
            for (index, item) in enumerate(top3_sites):
                rsp = rsp + "%d) %s " % (index+1, top3_sites[index].site)
            response.append(rsp)

            for item in top3_sites:
                rsp = " %s" % (item.site)
                rsp = rsp + " grew by " + none_float(item.r3_growth_pct)
                rsp = rsp + " and contributes " + none_float(item.r6_sales_contrib) + " to " + territory
                response.append(rsp)
    else:
        response.append(" No territory found for phone")

    return response

def site_activity(site):
    activity = Activity.query.filter(Activity.site == site).first()
    #print activity

    sms_resp = []
    sms_resp.append("%s has had %s activity over the last 3 months." % (site, activity.activity_category))
    sms_resp.append("The account received %d calls, %d samples, %d copay cards and %d speaker attendees in the last 3 months."
                    % (activity.calls, activity.samples, activity.copay_cards, activity.speaker_attendees))

    #print sms_resp
    return sms_resp





