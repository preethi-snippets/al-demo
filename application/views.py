from application import application
from flask import render_template,redirect, request, send_from_directory, session, url_for, flash
import models, config
from time import time
import twilio.twiml
from flask_weasyprint import HTML, CSS

from wtforms import Form, BooleanField, StringField, PasswordField, validators, IntegerField, ValidationError
from wtforms.validators import Email, InputRequired
from flask_images import Images

images = Images(application)

def validate_phone(form, field):
    if len(field.data) != 11:
        raise ValidationError('US Phone Number must be 11 digits')
    if field.data[0] != '1':
        raise ValidationError('US Phone Number must start with country code 1')


def validate_territory(form, field):
    if field.data.lower() != 'all':
        raise ValidationError('All is the only available demo territory')

class AddPhoneForm(Form):

    fname = StringField('Full Name', [validators.Length(min=3, max=25)], render_kw={'placeholder':'John Doe'})
    #email = StringField('Email Address',
     #                  validators=[InputRequired("Please enter email address"), Email("Need valid email address")],
      #                  render_kw={'placeholder': 'jdoe@company.com'})
    territory = StringField('Territory', [InputRequired(), validate_territory], render_kw={'placeholder': 'All'})

    phone = StringField('11 digit US Phone Number', [InputRequired(), validate_phone],
                         render_kw={'placeholder': '1XXXXXXXXXX'})



@application.route('/')
def hello_world():
    return render_template('index.html')

@application.route('/addphone', methods=['GET', 'POST'])
def addphone():
    form = AddPhoneForm(request.form)
    #print form.username.data, form.email.data
    if request.method == 'POST' and form.validate():
        models.add_terr_assoc(name=form.fname.data, phone=form.phone.data, territory=form.territory.data)
        flash('Added user ' + form.fname.data + ' with phone ' + form.phone.data)
        return redirect(url_for('addphone'))
    #flash('No Added user')
    return render_template('add_phone.html', form=form)

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

def create_session(from_phone, sites):
    resp = []
    site_dict = {}
    resp.append("Multiple matches: ")
    for (index, site) in enumerate(sites):
        resp.append("%d) %s (%s) " % (index+1, site.site, site.zip))
        site_dict[index+1] = site
    session[from_phone] = site_dict
    print "Session created for " + from_phone
    #print resp
    return resp

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

def generate_report(site, response):

    site_info = models.describe_site_for_twilio(site)
    html = render_template('describe_report.html', r=site_info)
    report_file = site.replace(" ", "_") + '_report.png'
    HTML(string=html).write_png(config.fig_dir + report_file, stylesheets=[CSS(url_for('static', filename='report.css'))],
                                resolution=200)

    # with response.message(site_info['message']) as m:
    #   m.media('/trend_figures/' + report_file)
    response.message(site_info['message'])
    response.message('').append(twilio.twiml.Media('/trend_figures/' + report_file))

    return response

@application.route('/al-twilio', methods=['GET', 'POST'])
def parse_twilio():

    help_message = "Happy to help! I can pull answers to these keywords: "
    invalid_keyword_message = "Sorry, please try one from these: "
    keywords = ['help','top3', 'bottom3', 'describe']
    from_phone = "+15129638448"
    #words=['top3']
    #words = ['d', 'cancer']
    words = ['10']
    #from_phone = request.form.get('From')
    #words = request.form.get('Body').lower().split(' ')
    keyword = words[0]

    lookup_phone = from_phone.lstrip('+')
    response = twilio.twiml.Response()

    if (keyword == 'help' or keyword.startswith('h')):
        response.message(help_message + ' '.join(keywords))

    elif (keyword == 'top3' or keyword.startswith('t')):
        msg_list = []
        msg_list.append("Top 3 for ")
        msg_list.extend(models.get_top3_by_phone(lookup_phone))
        print msg_list
        response = create_msg_chunks(msg_list, response)

    elif (keyword == 'bottom3' or keyword.startswith('b')):
        msg_list = []
        msg_list.append("Bottom 3 for ")
        msg_list.extend(models.get_bottom3_by_phone(lookup_phone))
        print msg_list
        response = create_msg_chunks(msg_list, response)

    elif (keyword == 'describe' or keyword.startswith('d')):
        sites = models.find_site_by_territory(lookup_phone, words[1])
        if (len(sites) == 0):
            response.message("No matches")
        elif (len(sites) == 1):
            response = generate_report(sites[0].site, response)
        else:
            response = create_msg_chunks(create_session(lookup_phone, sites), response)

    elif (1 <= int(keyword) <= 20):
        # retrieve site from phone's session
        site_dict = session[lookup_phone]
        response = generate_report(site_dict[int(keyword)].site, response)
    else:
        response.message(invalid_keyword_message + ' '.join(keywords))

    return (str(response))

def generate_ivr_menu(response):
    menu_msg = "For top 3 accounts, press 1. For bottom 3 accounts, press 2. To hangup, press *"
    with response.gather(numDigits=1, action=url_for('ivr_menu'), method="POST") as g:
        for i in range(3):
                g.say(menu_msg, voice="man", language="en")
                g.pause(length=3)
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
    response.say(welcome_msg, voice="man", language="en")
    response.pause(length=1)
    welcome_msg = "This is Al to help you with insights. "
    response.say(welcome_msg, voice="man", language="en")
    response.pause(length=1)
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
        response.say('Here are the top 3 accounts.', voice="man", language="en")
        response.pause(length=1)
        response.say(" ".join(models.get_top3_by_phone(lookup_phone)),
                     voice="man", language="en")
        return str(response)
    elif (selected_option == '2'):
        response.say('Here are the bottom 3 accounts.', voice="man", language="en")
        response.pause(length=1)
        response.say(" ".join(models.get_bottom3_by_phone(lookup_phone)),
                     voice="man", language="en")
        return str(response)
    elif (selected_option == '*'):
        response.say('Its been a pleasure. Please leave feedback on my performance at info@159solutions.com. Good bye!',
                     voice="man", language="en")
        response.hangup()
        return str(response)
    else:
        error_msg = "Sorry, I do not recognize that option."
        response.say(error_msg, voice="man", language="en")
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