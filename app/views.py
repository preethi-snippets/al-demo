from app import app
from flask import render_template,redirect, request, flash,g,session,url_for
import models
from time import time

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/lookup')
def lookup():
    site_name = request.args['site_name']
    start = time()
    r = models.Monthly.query.filter_by(site=site_name).all()
    return render_template('lookup.html', site_name=site_name, time_taken=(str(time() - start) + " s."), result=r)

'''@app.route('/top3')
def top3():
    territory = request.args['territory']
    r = models.get_top_3_by_territory(territory=territory)
    return render_template('index.html')
    '''