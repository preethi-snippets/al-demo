from application import application
from flask import render_template,redirect, request, send_from_directory, session
import models, config
from time import time
import twilio.twiml

@application.route('/')
def hello_world():
    return render_template('index.html')

@application.route('/createdb')
def createdb():
    start = time()
    models.create_db()
    return render_template('createdb.html', time_taken=(str(time() - start) + " s."))

@application.route('/lookup')
def lookup():
    site_name = request.args['site_name']
    start = time()
    r = models.Monthly.query.filter_by(site=site_name).all()
    return render_template('lookup.html', site_name=site_name, time_taken=(str(time() - start) + " s."), result=r)

@application.route('/top3')
def top3():
    territory = request.args.get('territory')
    start = time()
    r = []
    for brand_name in config.primary_brands:
        r.extend(models.get_top_3_by_territory(territory=territory, brand_name=brand_name))
    return render_template('top3.html', territory=territory, time_taken=(str(time() - start) + " s."), result=r)

@application.route('/bottom3')
def bottom3():
    territory = request.args.get('territory')
    start = time()
    r = []
    for brand_name in config.primary_brands:
        r.extend(models.get_bottom_3_by_territory(territory=territory, brand_name=brand_name))
    return render_template('bottom3.html', territory=territory, time_taken=(str(time() - start) + " s."), result=r)

@application.route('/describe')
def describe():
    site = request.args.get('site')
    start = time()
    r = models.describe_site(site)
    return render_template('describe.html', site=site, time_taken=(str(time() - start) + " s."), result=r)

@application.route('/trend_figures/<filename>',methods=['GET'])
def retrieve_trend_image(filename):
    print 'received file: ' + filename
    return send_from_directory(config.fig_dir, filename)

def create_session(from_phone, sites):
    resp = ''
    site_dict = {}
    for (index, site) in enumerate(sites):
        resp = resp + "%d) %s " % (index+1, site.site)
        site_dict[index+1] = site
    session[from_phone] = site_dict
    print "created..... " + from_phone, session[from_phone], site_dict[2].site
    return resp

@application.route('/al-twilio', methods=['GET', 'POST'])
def parse_twilio():

    help_message = "Happy to help! I can pull answers to these keywords: "
    invalid_keyword_message = "Sorry, please try one from these: "
    keywords = ['help','top3', 'bottom3', 'describe']
    from_phone = "+15129638448"
    #words = ['d', 'west']
    words = ['3']
    #from_phone = request.form.get('From')
    #words = request.form.get('Body').lower().split(' ')
    keyword = words[0]

    lookup_phone = from_phone.lstrip('+')
    response = twilio.twiml.Response()

    if (keyword == 'help' or keyword.startswith('h')):
        response.message(help_message + ' '.join(keywords))

    elif (keyword == 'top3' or keyword.startswith('t')):
        response.message("Top 3 for " + models.get_top3_by_phone(lookup_phone))

    elif (keyword == 'bottom3' or keyword.startswith('b')):
        response.message("Bottom 3 for " + models.get_bottom3_by_phone(lookup_phone))

    elif (keyword == 'describe' or keyword.startswith('d')):
        sites = models.find_site_by_territory(from_phone, words[1])
        if (len(sites) == 0):
            response.message("No matches")
        elif (len(sites) == 1):
            site_info = models.describe_site_for_twilio(sites[0].site)
            with response.message(site_info['message']) as m:
                m.media('/trend_figures/' + site_info['media'])
        elif (1 < len(sites) > 5):
            response.message("Multiple matches" + create_session(lookup_phone, sites))

    elif (1 <= int(keyword) <= 20):
        # retrieve site from phone's session
        site_dict = session[lookup_phone]
        site_info = models.describe_site_for_twilio(site_dict[int(keyword)].site)
        with response.message(site_info['message']) as m:
            m.media('/trend_figures/' + site_info['media'])
    else:
        response.message(invalid_keyword_message + ' '.join(keywords))

    return (str(response))

@application.route('/session-test', methods = ['GET', 'POST'])
def session_test():
    from_phone = request.args.get("phone")
    index = 3
    site_dict = session[from_phone]
    print "lookup.... " + from_phone, site_dict[index].site
    return (str(site_dict))
    #return (str(counter))