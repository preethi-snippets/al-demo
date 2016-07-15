from application import application
from flask import render_template,redirect, request, send_from_directory
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

@application.route('/al-twilio', methods=['GET', 'POST'])
def parse_twilio():

    help_message = "Happy to help! I can pull answers to these keywords: "
    invalid_keyword_message = "Sorry, please try one from these: "
    keywords = ['help','top3', 'bottom3', 'describe']
    #from_phone = "+15129638448"
    #words = ['d', 'bishop']

    from_phone = request.form.get('From')
    words = request.form.get('Body').lower().split(' ')
    keyword = words[0]

    response = twilio.twiml.Response()

    if (keyword == 'help' or keyword.startswith('h')):
        response.message(help_message + ' '.join(keywords))

    elif (keyword == 'top3' or keyword.startswith('t')):
        response.message("Top 3 for " + models.get_top3_by_phone(from_phone.lstrip('+')))

    elif (keyword == 'bottom3' or keyword.startswith('b')):
        response.message("Bottom 3 for " + models.get_bottom3_by_phone(from_phone.lstrip('+')))

    elif (keyword == 'describe' or keyword.startswith('d')):
        sites = models.find_site_by_territory(from_phone, words[1])
        if len(sites):
            site_info = models.describe_site_for_twilio(sites[0].site)
            with response.message(site_info['message']) as m:
                m.media('/trend_figures/' + site_info['media'])
        else:
            response.message("No matches")
    else:
        response.message(invalid_keyword_message + ' '.join(keywords))

    return (str(response))