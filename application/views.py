from application import application
from flask import render_template,redirect, request, flash,g,session,url_for
import models
from time import time

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
    brand_name = request.args.get('brand')
    start = time()
    r = models.get_top_3_by_territory(territory=territory, brand_name=brand_name)
    return render_template('top3.html', territory=territory, brand=brand_name, time_taken=(str(time() - start) + " s."), result=r)

@application.route('/bottom3')
def bottom3():
    territory = request.args.get('territory')
    brand_name = request.args.get('brand')
    start = time()
    r = models.get_bottom_3_by_territory(territory=territory, brand_name=brand_name)
    return render_template('bottom3.html', territory=territory, brand=brand_name, time_taken=(str(time() - start) + " s."), result=r)
