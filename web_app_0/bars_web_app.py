import os
from flask import Flask, render_template, request
import pickle
from collections import Counter
import pandas as pd
import numpy as np
import re
from sklearn.ensemble import RandomForestRegressor
import math

app = Flask(__name__)

states = ['California', 'Colorado', 'Florida', 'District of Columbia']

counties = ['Boulder', 'Denver', 'Jefferson']

def retr_model_info():
    with open('model_and_cols.pkl', 'rb') as f:
        county_info_df = pickle.load(f)
        model = pickle.load(f)
        cols = pickle.load(f)
    return(county_info_df, model, cols)

def index_finder(county, state, df):
    if len(state) == 2:
        the_state = state.upper()
        state_df = df[df['state_code'] == the_state]
    else:
        the_state = state.lower().title()
        state_df = df[df['state_name'] == the_state]
    county_list = list(state_df['county_name'])
    for elem in county_list:
        m = re.search(county, elem, re.IGNORECASE)
        if m:
            req_county = elem
            break
    index = state_df.index[state_df['county_name'] == req_county].tolist()[0]
    return(index, req_county)

# the calculation of err_down and err_up are modified code obtained from http://blog.datadive.net/prediction-intervals-for-random-forests/
def predict_bars(idx, county_info_df, model, cols, percentile=95):
    X = np.asarray(county_info_df.iloc[idx][cols]).reshape(1,-1)
    y = county_info_df.iloc[idx]['bars']
    y_pred = model.predict(X)
    preds = []
    for pred in model.estimators_:
        preds.append(pred.predict(X)[0])
    err_down = (np.percentile(preds, (100 - percentile) / 2. ))
    err_up = (np.percentile(preds, 100 - (100 - percentile) / 2.))
    return(min(0,int(y_pred)), max(0,math.ceil(err_down)), math.floor(err_up), int(y))


@app.route('/', methods=['GET'])
def index():
    page = "Should I open a bar?"
    return '''Enter the state and the county you are interested in:
        <form action="/advice" method='POST' >
            <input type="text1" name="user_input" />
            <input type="text2" name="user_input2" />
            <input type="submit" />
        </form>
        '''
    return('Landing page with and explanation of the page')

@app.route('/advice', methods=['GET', 'POST'])
def word_counter():
    text1 = str(request.form['user_input'])
    text2 = str(request.form['user_input2'])
    idx, req_county = index_finder(text2, text1, county_info_df)
    pred, low_numb, high_numb, actual = predict_bars(idx, county_info_df, model, cols)
    page = 'There are {2} bars in {0} (2015 numbers).<br><br>Our model indicates that the market there can support between {3} and {4} bars.'
    return page.format(req_county, pred, actual, low_numb, high_numb)
# def submit():
#     '''Interactive page where people enter the state and county and get the advice about bars'''
#     return render_template('form/submit.html')

@app.route('/rank_and_map', methods=['GET', 'POST'])
def predict():
    '''Page showing the rankings of best and worst counties and a map'''
    data = str(request.form['article_body'])
    pred = str(model.predict([data])[0])
    return render_template('form/predict.html', article=data, predicted=pred)

if __name__ == '__main__':
    county_info_df, model, cols = retr_model_info()
    app.run(host='0.0.0.0', port=5000, debug=True)
