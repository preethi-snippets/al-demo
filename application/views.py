from application import application
from flask import render_template,redirect, request, send_from_directory, session, url_for, flash
import models, config
from time import time, sleep
import twilio.twiml
from twilio.rest import TwilioRestClient
from flask_weasyprint import HTML, CSS
import re

from wtforms import Form, BooleanField, SubmitField, StringField, PasswordField, validators, IntegerField, ValidationError, TextAreaField
from wtforms.validators import Email, InputRequired
from flask_images import Images

images = Images(application)

client = TwilioRestClient(config.twilio_account_sid, config.twilio_auth_token)

def validate_phone(form, field):
    if len(field.data) != 10:
        raise ValidationError('US Phone Number must be 10 digits')

def validate_territory(form, field):
    if field.data.lower() != 'National level':
        raise ValidationError('National level is the only available demo territory')


class AddPhoneForm(Form):

    fname = StringField('Full Name', [validators.Length(min=3, max=25)], render_kw={'placeholder':'John Doe'})
    #email = StringField('Email Address',
     #                  validators=[InputRequired("Please enter email address"), Email("Need valid email address")],
      #                  render_kw={'placeholder': 'jdoe@company.com'})
    # territory disabled input at this point
    territory = StringField('Territory', default='National level')

    phone = StringField('10 digit US Phone Number', [InputRequired(), validate_phone],
                         render_kw={'placeholder': 'XXXXXXXXXX'})

class PushSmsForm(Form):
    text_msg = TextAreaField('Text to send', default='Hello from Al!')

    phone = StringField('10 digit US Phone Number', [InputRequired(), validate_phone],
                         render_kw={'placeholder': 'XXXXXXXXXX'})

    pushsms = SubmitField(label='Push SMS')
    insight = SubmitField(label='Push Insights')

@application.route('/')
def hello_world():
    return render_template('index.html')

@application.route('/addphone', methods=['GET', 'POST'])
def addphone():
    form = AddPhoneForm(request.form)
    #print form.username.data, form.email.data
    if request.method == 'POST' and form.validate():
        models.add_terr_assoc(name=form.fname.data, phone='1'+form.phone.data, territory='National level')
        flash('Added user ' + form.fname.data + ' with phone ' + form.phone.data)
        return redirect(url_for('addphone'))
    #flash('No Added user')
    return render_template('add_phone.html', form=form)

@application.route('/pushsms', methods=['GET', 'POST'])
def pushsms():
    form = PushSmsForm(request.form)
    if request.method == 'POST' and form.validate():

        if form.insight.data:
            client.messages.create(to='1' + form.phone.data, from_=config.twilio_phone,
                                   body="This is an insight from Al")
            flash('Sent insights to phone ' + '1' + form.phone.data)
        else:
            client.messages.create(to='1'+form.phone.data, from_=config.twilio_phone,
                               body=form.text_msg.data)
            flash('Sent message to phone ' + '1'+form.phone.data)

        return redirect(url_for('pushsms'))
    return render_template('push_sms.html', form=form)

@application.route('/createdb')
def createdb():
    start = time()
    models.create_db()
    return render_template('createdb.html', time_taken=(str(time() - start) + " s."))

@application.route('/lookup')
def lookup():
    site_name = request.args['site_name']
    start = time()
    r = models.Sales.query.filter_by(site=site_name).all()
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

def create_session(from_phone, sites, keyword):
    resp = []
    site_dict = {}
    resp.append("Multiple matches: ")
    for (index, site) in enumerate(sites):
        resp.append("%d) %s (ZIP: %s) " % (index+1, site.site, site.zip))
        site_dict[index+1] = {'keyword': keyword, 'site': site }
    session[from_phone] = site_dict
    print "%s session created for %s" % (keyword, from_phone)
    #print site_dict
    #print resp
    return resp
'''
def create_msg_chunks(msg_list, response):

    cur_len = 0
    num_msgs = 1
    for msg in msg_list:
        if ((cur_len + len(msg)) < 155):
            cur_len += len(msg)
        else:
            num_msgs += 1
            cur_len = len(msg)

    #print num_msgs
    index = 1
    if (num_msgs > 1):
        cur_msg = "%d/%d: " % (index, num_msgs)
    else:
        cur_msg = ''
    for msg in msg_list:
        if ((len(cur_msg) + len(msg)) < 155):
            cur_msg = cur_msg + msg
        else:
            print cur_msg
            response.message(cur_msg)
            index += 1;
            cur_msg = "%d/%d: " % (index, num_msgs)
            cur_msg = cur_msg + msg

    response.message(cur_msg)
    #print response
    return response
'''

def create_send_twilio_msgs(msg_list, fp, tp):

    cur_len = 0
    num_msgs = 1
    for msg in msg_list:
        if ((cur_len + len(msg)) < 153):
            cur_len += len(msg)
        else:
            num_msgs += 1
            cur_len = len(msg)
        #print "num: %d, msg: %s" % (num_msgs, msg)

    # print num_msgs
    index = 1
    if (num_msgs > 1):
        cur_msg = "%d/%d: " % (index, num_msgs)
    else:
        cur_msg = ''
    for msg in msg_list:
        if ((len(cur_msg) + len(msg)) < 160):
            cur_msg = cur_msg + msg
        else:
            #print cur_msg
            client.messages.create(to=tp, from_=fp, body=cur_msg)
            sleep(0.5)
            index += 1;
            cur_msg = "%d/%d: " % (index, num_msgs)
            cur_msg = cur_msg + msg

    client.messages.create(to=tp, from_=fp, body=cur_msg)
    # print response
    #return response

def generate_snapshot(site, fp, tp):

    site_info = models.describe_site_for_twilio(site)
    html = render_template('describe_report.html', r=site_info)
    report_file = site.replace(" ", "_") + '_report.png'
    HTML(string=html).write_png(config.fig_dir + report_file, stylesheets=[CSS(url_for('static', filename='report.css'))],
                                resolution=200)
    #create_send_twilio_msgs(site_info['message'], fp=fp, tp=tp)
    client.messages.create(from_=fp, to=tp, body='', media_url = (config.images_url + report_file))

def generate_description(site, fp, tp):
    site_info = models.describe_site_for_twilio(site)
    create_send_twilio_msgs(site_info['message'], fp=fp, tp=tp)
    client.messages.create(from_=fp, to=tp, body='', media_url=[(config.images_url + site_info['sales_media']),
                                                                 (config.images_url + site_info['growth_media'])])

def generate_activity(site, fp, tp):
    create_send_twilio_msgs(models.site_activity(site), fp=fp, tp=tp)


@application.route('/al-twilio', methods=['GET', 'POST'])
def parse_twilio():

    help_message = "Hello, I am Alfred. I can help you with customized insights specific to your geography."
    invalid_keyword_message = "Sorry, please try one from these... "
    keywords = ['Top3', 'Bottom3', 'Describe < >', 'Snapshot < > ', 'Activity < >',
                'Overall Performance', 'Insights', 'ICPlan', 'ICPerformance']
    #from_phone = "+15129638448"
    #twilio_phone = config.twilio_phone

    #words=['hi']
    #words = ['s', 'cancer']
    #words = 'what are my top'
    from_phone = request.form.get('From')
    twilio_phone = request.form.get('To')
    words = request.form.get('Body').lower()
    keyword = words.split(' ')[0]

    lookup_phone = from_phone.lstrip('+')
    response = twilio.twiml.Response()

    insights_msg = ["Competitive pressure has been increasing in your top accounts. ",
                   "Here are two accounts with growing potential that may be valuable to call on: City Of Hope National Medical Center, Cedars Sinai Health System"]
    icplan_msg = ["Your target payout is $5,000. Your final payout is based on two components.",
              "75% ($3,750) of the payout is based on your attainment (Sales / Goal). 25% is based on relative rank within your division."]
    opp_msg = ["Here are 3 targets with maximum opportunity near 19104: ",
           "1. Hospital Of The University Of Pennsylvania, 2. Fox Chase Cancer Center Outpatient, 3. Thomas Jefferson University Hospital."]
    icperf_msg = ["Your H2'15 PTP is 107%. Mar'16 goal = 8662 and Mar'16 PTP = 90%. You are tracking towards a H1'16 payout of $6,300."]

    if (keyword == 'hi'):
        create_send_twilio_msgs(msg_list=list((help_message, 'Keywords: ', ', '.join(keywords))),
                                fp=twilio_phone, tp=from_phone)
        #response.message(help_message + ', '.join(keywords))
        #print message

    elif (keyword.startswith('t') or re.match(r".*top.*", words)):
        msg_list = []
        msg_list.append("Top 3 for ")
        msg_list.extend(models.get_top3_by_phone(lookup_phone))
        #print msg_list
        #response = create_msg_chunks(msg_list, response)
        create_send_twilio_msgs(msg_list=msg_list,
                                fp=twilio_phone, tp=from_phone)

    elif (keyword.startswith('b') or re.match(r".*bottom.*", words)):
        msg_list = []
        msg_list.append("Bottom 3 for ")
        msg_list.extend(models.get_bottom3_by_phone(lookup_phone))
        #print msg_list
        create_send_twilio_msgs(msg_list=msg_list,
                                fp=twilio_phone, tp=from_phone)

    elif (keyword == 'describe' or keyword.startswith('d')):
        second_word = words.split(' ')[1]
        sites = models.find_site_by_territory(lookup_phone, second_word)
        if (len(sites) == 0):
            create_send_twilio_msgs(list("No matches"),
                                    fp=twilio_phone, tp=from_phone)
        elif (len(sites) == 1):
            generate_description(sites[0].site, fp=twilio_phone, tp=from_phone)
        else:
            create_send_twilio_msgs(create_session(lookup_phone, sites, 'describe'),
                                    fp=twilio_phone, tp=from_phone)


    elif (keyword == 'snapshot' or keyword.startswith('s')):
        second_word = words.split(' ')[1]
        sites = models.find_site_by_territory(lookup_phone, second_word)
        if (len(sites) == 0):
            create_send_twilio_msgs(list("No matches"),
                                    fp=twilio_phone, tp=from_phone)
        elif (len(sites) == 1):
            generate_snapshot(sites[0].site, fp=twilio_phone, tp=from_phone)
        else:
            create_send_twilio_msgs(create_session(lookup_phone, sites, 'snapshot'),
                              fp=twilio_phone, tp=from_phone)

    elif (keyword == 'activity' or keyword.startswith('a')):
        second_word = words.split(' ')[1]
        sites = models.find_site_by_territory(lookup_phone, second_word)
        if (len(sites) == 0):
            create_send_twilio_msgs(list("No matches"),
                                    fp=twilio_phone, tp=from_phone)
        elif (len(sites) == 1):
            generate_activity(sites[0].site, fp=twilio_phone, tp=from_phone)
        else:
            create_send_twilio_msgs(create_session(lookup_phone, sites, 'activity'),
                                    fp=twilio_phone, tp=from_phone)

    elif (keyword == 'overall' or keyword.startswith('ov') or re.match(r".*how am i doing.*", words)):
        create_send_twilio_msgs(models.overall_performance(lookup_phone),
                                           fp=twilio_phone, tp=from_phone)

    elif (keyword == 'insights' or keyword.startswith('in')):
        create_send_twilio_msgs(insights_msg, fp=twilio_phone, tp=from_phone)

    elif (keyword == 'icperformance' or keyword.startswith('icpe')):
        create_send_twilio_msgs(icperf_msg, fp=twilio_phone, tp=from_phone)


    elif (keyword == 'icplan' or keyword.startswith('icpl')):
        create_send_twilio_msgs(icplan_msg,
                                fp=twilio_phone, tp=from_phone)
        client.messages.create(from_=twilio_phone, to=from_phone,
                               body='', media_url=(config.images_url + 'payout-sample.jpg'))

    elif (keyword == 'opportunities' or keyword.startswith('op')):
        create_send_twilio_msgs(opp_msg, fp=twilio_phone, tp=from_phone)

    elif (keyword.isdigit()):
        # retrieve site from phone's session
        site_dict = session[lookup_phone]
        index = int(keyword)
        keyword = site_dict[index]['keyword']
        if (keyword == 'snapshot'):
            generate_snapshot(site_dict[index]['site'].site, fp=twilio_phone, tp=from_phone)
        elif (keyword == 'activity'):
            generate_activity(site_dict[index]['site'].site, fp=twilio_phone, tp=from_phone)
        else:
            generate_description(site_dict[index]['site'].site, fp=twilio_phone, tp=from_phone)
    else:
        create_send_twilio_msgs(msg_list=list((invalid_keyword_message, ', '.join(keywords))),
                                fp=twilio_phone, tp=from_phone)

    return (str(response))

def add_msg_to_rsp(response, msg, pause_len=1):
    response.say(msg, voice="woman", language="en-US")
    response.pause(length=pause_len)
    return response

def generate_ivr_menu(response):
    menu_msg = "For top 3 accounts, press 1. For bottom 3 accounts, press 2. For overall performance, press 3. For insights, press 4. To hangup, press *"
    with response.gather(numDigits=1, action=url_for('ivr_menu'), method="POST") as g:
        for i in range(3):
                g = add_msg_to_rsp(g, menu_msg, pause_len=3)
    return response

@application.route('/al-voice/welcome', methods = ['GET', 'POST'])
def ivr_welcome():
    from_phone = request.form.get('From')
    #from_phone = "+15129638448"
    lookup_phone = from_phone.lstrip('+')
    username = models.lookup_user(lookup_phone)
    response = twilio.twiml.Response()
    welcome_msg = "Welcome " + username
    welcome_msg += "!"
    response = add_msg_to_rsp(response, welcome_msg)
    welcome_msg = "This is Alice to help you with insights. "
    response = add_msg_to_rsp(response, welcome_msg)
    response = generate_ivr_menu(response)
    return str(response)

@application.route('/al-voice/menu', methods = ['POST'])
def ivr_menu():
    from_phone = request.form.get('From')
    #from_phone = "+15129638448"
    lookup_phone = from_phone.lstrip('+')
    selected_option = request.form['Digits']
    #selected_option = '1'
    response = twilio.twiml.Response()
    if (selected_option == '1'):
        response = add_msg_to_rsp(response, 'Here are the top 3 accounts.')
        response = add_msg_to_rsp(response, " ".join(models.get_top3_by_phone(lookup_phone)))
        return str(response)
    elif (selected_option == '2'):
        response = add_msg_to_rsp(response,'Here are the bottom 3 accounts.')
        response = add_msg_to_rsp(response, " ".join(models.get_bottom3_by_phone(lookup_phone)))
        return str(response)
    elif (selected_option == '3'):
        response = add_msg_to_rsp(response, " ".join(models.overall_performance(lookup_phone)))
        return str(response)
    elif (selected_option == '4'):
        response = add_msg_to_rsp(response, " ".join(insights_msg))
        return str(response)
    elif (selected_option == '*'):
        response = add_msg_to_rsp(response,
                                  'Its been a pleasure. Please leave feedback on my performance at info@159solutions.com. Good bye!')
        response.hangup()
        return str(response)
    else:
        error_msg = "Sorry, I do not recognize that option."
        response = add_msg_to_rsp(response, error_msg)
        response = generate_ivr_menu(response)
        return str(response)

@application.route('/session-test', methods = ['GET', 'POST'])
def session_test():
    from_phone = request.args.get("phone")
    index = 3
    site_dict = session[from_phone]
    print "lookup.... " + from_phone, site_dict[index].site
    return (str(site_dict))

@application.after_request
def add_header(response):
    """
    Dont cache any response
    """
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Pragma'] = 'no-cache'
    return response
