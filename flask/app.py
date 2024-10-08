from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_migrate import Migrate
from wtforms import SelectField, StringField, SubmitField, PasswordField, EmailField, IntegerField, FileField, BooleanField, ValidationError
from flask_wtf.file import FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.validators import DataRequired, Email, EqualTo, Length
import datetime
from datetime import timedelta
import mysql.connector
import os

from sqlalchemy import create_engine

from sqlalchemy.orm import relationship

import pandas as pd
import numpy as np

app = Flask(__name__)

# Secret key
app.config['SECRET_KEY'] = 'key'

# MySQL Database Connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://erpcrm:Erpcrmpass1!@erpcrmdb.cfg0ok8iismy.us-west-1.rds.amazonaws.com:3306/erpcrmdb' 

# Uploads folder
app.config['UPLOAD_FOLDER'] = 'static/files'

# Standard engine
# engine = create_engine('mysql+pymysql://erpcrm:Erpcrmpass1!@aws-erp.cxugcosgcicf.us-east-2.rds.amazonaws.com:3306/erpcrmdb')

# Sets session timeout duration
app.permanent_session_lifetime = timedelta(minutes=30) 

# Initialize database
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mydb = mysql.connector.connect(
    host = 'erpcrmdb.cfg0ok8iismy.us-west-1.rds.amazonaws.com',
    user = 'erpcrm', 
    passwd = 'Erpcrmpass1!', 
    database = 'erpcrmdb' 
)
    
##############################################################################

# Models

# Accounts model
class Accounts(db.Model):
    __tablename__ = 'Accounts'
    AccountID = db.Column(db.Integer, primary_key=True)
    CompanyName = db.Column(db.String(100), nullable=False)
    CompanyRevenue = db.Column(db.Integer, nullable=False)
    EmployeeHeadCount = db.Column(db.Integer, nullable=False)
    CompanyIndustry = db.Column(db.String(100))
    CompanySpecialties = db.Column(db.Text)
    CompanyType = db.Column(db.String(50))
    Country = db.Column(db.String(50), nullable=False)
    City = db.Column(db.String(50))
    Timezone = db.Column(db.String(50))

#Leads Model
class Leads(db.Model):
    __tablename__ = 'Leads'
    LeadID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    AccountID = db.Column((db.Integer),db.ForeignKey('Accounts.AccountID')) #Later
    Position = db.Column(db.String(75))
    FirstName = db.Column(db.String(50))
    LastName = db.Column(db.String(50))
    Email = db.Column(db.String(50))
    CompanyName = db.Column(db.String(100))
    # DateCreated = db.Column(db.Date, default=datetime.datetime.now(datetime.timezone.utc))
    # DateModified = db.Column(db.Date, default=datetime.datetime.now(datetime.timezone.utc))


    
# Clients model
class Clients(db.Model):
    __tablename__ = 'Clients'
    ClientID = db.Column(db.Integer, primary_key=True)
    Subscriber = db.Column(db.String(50), nullable=False, unique=True)
    License = db.Column(db.String(20), nullable=False, unique=True)
    ValidFrom = db.Column(db.Date, default=datetime.datetime.now(datetime.timezone.utc))
    ValidTo = db.Column(db.Date)
    
# Opportunities model    
class Opportunities(db.Model):
    __tablename__ = 'Opportunities'
    OpportunityID = db.Column(db.Integer, primary_key=True)
    AccountID = db.Column(db.Integer)
    LeadID = db.Column(db.Integer)
    ClientID = db.Column(db.Integer)
    Opportunity = db.Column(db.Text)
    Value = db.Column(db.String(255))
    Stage = db.Column(db.String(100))
    CreationDate = db.Column(db.Date, default=datetime.datetime.now(datetime.timezone.utc))
    CloseDate = db.Column(db.Date)

# Users model
class Users(db.Model):
    __tablename__ = 'Users'
    UserID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Email = db.Column(db.String(50), unique=True, nullable=False)
    PasswordHash = db.Column(db.String(128), nullable=False)
    License = db.Column(db.String(20), nullable=False)
    Subscriber = db.Column(db.String(50), nullable=False)
    ValidFrom = db.Column(db.Date, default=datetime.datetime.now(datetime.timezone.utc))
    ValidTo = db.Column(db.Date)
    
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute.')
    
    @password.setter
    def password(self, password):
        self.PasswordHash = generate_password_hash(password)
        
    def verify_password(self, password):
        return check_password_hash(self.PasswordHash, password)  
    
##############################################################################  
 
# Forms
    
# Account form
class AccountForm(FlaskForm):
    company_name = StringField('Company Name:*', validators=[DataRequired()])
    company_revenue = IntegerField('Revenue:*', validators=[DataRequired()])
    employee_head_count = IntegerField('Head Count:*', validators=[DataRequired()])
    company_specialties = StringField('Company Specialties:')
    company_industry = StringField('Company Industry:')
    company_type = StringField('Company Type:')
    country = StringField('Country:*', validators=[DataRequired()])
    city = StringField('City:')
    timezone = StringField('Timezone:')
    submit = SubmitField('Submit')
    
    # email = EmailField('Email:', validators=[DataRequired(), Email()])

#Leads form (InProgress) 7/31
class LeadForm(FlaskForm):
    Company_Name = SelectField('Company Name:', choices= ['Edison', 'Honda', '  '])
    FirstName = StringField('First Name:', validators=[DataRequired()])
    LastName = StringField('Last Name:')
    Title = StringField('Title')
    submit = SubmitField('Submit')


# User form
class UserForm(FlaskForm):
    email = EmailField('Email:', validators=[DataRequired(), Email()])
    license = StringField('License Key:', validators=[DataRequired(),
                                            Length(min=20, max=20, 
                                                    message='License key must be\
                                                20 characters.')])
    password = PasswordField('Password:', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password:', validators=[DataRequired(), EqualTo('password', message='Passwords do not match.')])
    submit = SubmitField('Submit')
    
# Opportunities form
class OpportunityForm(FlaskForm):
    opportunity = StringField('Opportunity:', validators=[DataRequired()])
    value = StringField('Value:', validators=[DataRequired()])
    stage = StringField('Stage:', validators=[DataRequired()])
    submit = SubmitField('Submit')

# File form
class FileForm(FlaskForm):
    file = FileField('File', validators=[FileRequired()])
    submit = SubmitField('Submit')
 
# Password form
class PasswordForm(FlaskForm):
    hashed_password = StringField('Hashed Password:', validators=[DataRequired()])
    password = StringField('Password:', validators=[DataRequired()])
    submit = SubmitField('Submit')
    
    
    
##############################################################################

# Clear opportunities
@app.route('/clear_opportunities/')
def clear_opportunities():
    Opportunities.query.delete()
    db.session.commit()
    
    flash('Opportunities list cleared.')
    return redirect(url_for('accounts_list'))
    

##############################################################################

#leads 7/31
@app.route('/new_leads/', methods=['GET', 'POST'])
def new_leads():

        form = LeadForm()
        choices = None #new will update
        Company_Name = None #new will update
        FirstName = None
        LastName = None
        Title = None
        ###sumbit logic here 
        if form.validate_on_submit():
            FirstName = form.FirstName.data
            LastName = form.LastName.data
            Title = form.Title.data
            flash('Leads added successfully.')
        #db.session.add(form)
        #db.session.commit()
        return render_template('new_leads.html', Company_Name = choices, FirstName = FirstName, LastName = LastName, Title = Title, form=form)
        
@app.route('/leads_import', methods=['GET', 'POST'])
def leads_import():
    form = FileForm()
    filename = None
    if form.validate_on_submit():
        file = form.file.data #first it grabs the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)        
        df = pd.read_csv('static/files/{filename}'.format(filename=filename))
        df = df.where(pd.notnull(df), None) #change to df.replace
    
        flash('File Uploaded successfully.')

        df = df.rename(columns={df.columns[0]:'CompanyName',df.columns[1]: 'Position', df.columns[2]: 'FirstName', df.columns[3]: 'LastName', df.columns[4]: 'Email'})

        #** 8/19  Should create a column function that  auto generates. links company in accounts and retrievs its AccountID and auto increments.

        AccountID = db.Column(db.Integer, db.ForeignKey('accounts.AccountID'), nullable=False)

        '''# Check if the company already exists in the accounts table
        company_name = dct.get('CompanyName')
        account = Accounts.query.filter_by(CompanyName=company_name).first()

        if account is None:
             # Company not found, create new account
            new_account = Accounts(CompanyName=company_name)
            db.session.add(new_account)
            db.session.commit()  # Commit to generate AccountID
            account = new_account  # Now use the newly created account

            # Set the AccountID in the lead data
        dct['AccountID'] = account.AccountID
        
            '''


        for index, row in df.iterrows():
            dct = row.to_dict()
            lead = Leads(**dct)
            db.session.add(lead)
            
       #pd.merge(Accounts, left_on=['CompanyName', 'AccountID'], right_on=['ComapnyName','AccountID'])
        #pd.merge(Leads, Accounts, on='AccountID', how='inner')
            
        db.session.commit()


    return render_template('leads_import.html', form=form)

@app.route('/leads_list', methods = ['GET', 'POST'])
def leads_list():
    db.session.rollback()
    try:
        leads = Leads.query.order_by(Leads.LeadID.desc())
        return render_template('leads_list.html', leads=leads)
    except:
        # flash('Error loading database, please try again.')
        return redirect(url_for('leads_list'))

#############################################################################



# New opportunity
@app.route('/new_opportunity/', methods=['GET', 'POST'])
def new_opportunity():
    form = OpportunityForm()
    
    if form.validate_on_submit():
        opportunity = Opportunities(Opportunity=form.opportunity.data,
                                    Value=form.value.data,
                                    Stage=form.stage.data)
        db.session.add(opportunity)
        db.session.commit()
        
        flash('Opportunity added successfully.')
        return redirect(url_for('opportunities_list'))
    
    
    return render_template('new_opportunity.html', form=form)

# Opportunities list
@app.route('/opportunities_list')
def opportunities_list():
    db.session.rollback()
    try:
        opportunities = Opportunities.query.order_by(Opportunities.OpportunityID.desc())
        return render_template('opportunities_list.html', opportunities=opportunities)
    except:
        # flash('Error loading database, please try again.')
        return redirect(url_for('opportunities_list'))



# New user
@app.route('/new_user/', methods=['GET', 'POST'])
def new_user():
    user = None
    license = None
    form = UserForm()
    # Method == Post
    if form.validate_on_submit():
        user = Users.query.filter_by(Email=form.email.data).first()
        license = Clients.query.filter_by(License=form.license.data).first()
        # User does not exist
        if user is None:
            # Valid license key 
            if license:
                # Hash password
                hashed_password = generate_password_hash(form.password.data, 'scrypt')
                new_user = Users(Email=form.email.data,
                                PasswordHash=hashed_password,
                                License=form.license.data,
                                Subscriber=license.Subscriber,
                                ValidTo='00-00-0000')
                    
                db.session.add(new_user)
                db.session.commit()
                flash('User added successfully.', 'success')
                return redirect(url_for('new_user'))
        
            else:
                flash('Invalid license key.', 'error')
                return redirect(url_for('new_user'))
            
        else:
            flash('User already exists.')
            return redirect(url_for('new_user'))
    for fieldName, errorMessages in form.errors.items():
        for err in errorMessages:
            flash(err, 'error')    
    return render_template('new_user.html', form=form)

@app.route('/password/', methods=['GET', 'POST'])
def password():
    hashed_password = None
    password = None
    passed = None
    submit = False
    form = PasswordForm()
    
    if form.validate_on_submit():
        hashed_password = form.hashed_password.data
        password = form.password.data
        passed = check_password_hash(hashed_password, password)
        submit = True

    return render_template('password.html', form=form, passed=passed,
                           password=password, hashed_password=hashed_password,
                           submit=submit)


# Account import
@app.route('/accounts_import/', methods=['GET', 'POST'])
def accounts_import():
    form = FileForm()
    filename = None
    if form.validate_on_submit():        
        file = form.file.data
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            if filename.split('.')[-1] != 'csv':
                flash('Import failed. Please upload a .csv file.')
                return redirect(url_for('accounts_import'))
            
            while os.path.exists(filepath):
                filename = filename.split('.')[0] + ' copy.csv'
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    
            file.save(filepath)
            
            df = pd.read_csv('static/files/{filename}'.format(filename=filename))
            df = df.where(pd.notnull(df), None)
            
            id = Accounts.query.order_by(Accounts.AccountID.desc()).first()
    
            if id is None:
                id = 1000
            else:
                id = id.AccountID + 10
    
            # Grab max id
            # ids = pd.read_sql("SELECT AccountID FROM Accounts", con=engine)

            # if ids['AccountID'].empty:
            #     id = 1000
            # else:
            #     id = ids['AccountID'].max() + 10
            
            for index, row in df.iterrows():
                dct = row.to_dict()
                dct.update({'AccountID': id})
                id += 10
                account = Accounts(**dct)
                db.session.add(account)
                
            db.session.commit()
            flash('Import successful.')
            return redirect(url_for('accounts_list'))    
                
        except:
            db.session.rollback()
            flash('Import failed. Please ensure .csv file is ordered as \
                follows: Company Name, Company Revenue, Employee Head Count, \
                Company Industry, Company Specialties, Company Type, Country, \
                City, Timezone.')
            return redirect(url_for('accounts_import'))
        
    return render_template('accounts_import.html', form=form)
    
@app.route('/clear_accounts/')
def clear_accounts():
    Accounts.query.delete()
    db.session.commit()
    
    flash('Accounts list cleared.')
    return redirect(url_for('accounts_list'))

# Accounts list    
@app.route('/accounts_list/')
def accounts_list():
    db.session.rollback()
    try:
        accounts = Accounts.query.order_by(Accounts.AccountID.desc())
        return render_template('accounts_list.html', accounts=accounts)
    except:
        # flash('Error loading database, please try again.')
        return redirect(url_for('accounts_list'))


# Update record
@app.route('/update_account/<int:id>', methods=['GET', 'POST'])
def update_account(id):
    form = AccountForm()
    account = Accounts.query.get_or_404(id)
    if form.validate_on_submit():

        account.CompanyName = request.form['company_name']
        account.CompanyRevenue = request.form['company_revenue']
        account.EmployeeHeadCount = request.form['employee_head_count']
        account.CompanySpecialties = request.form['company_specialties']
        account.CompanyType = request.form['company_type']
        account.Country = request.form['country']
        account.City = request.form['city']
        account.Timezone = request.form['timezone']
        
        try:
            db.session.commit()
            flash('User updated successfully.')
            return redirect(url_for('accounts_list'))
        except:
            flash('User update failed.')
            return render_template('update_account.html', form=form, account=account)
        
    return render_template('update_account.html', form=form, account=account, id=id)        
            
            
# Delete record
@app.route('/delete_account/<int:id>')
def delete_account(id):
    account = Accounts.query.get_or_404(id)
    try:
        db.session.delete(account)
        db.session.commit()
        flash('Account deleted successfully.')
        return redirect(url_for('accounts_list'))
    
    except:
        flash('Error deleting account.')
        return redirect(url_for('accounts_list'))
        
 

    
# Export records
# @app.route('/accounts_list/export/')
# def accounts_export():
#      ...



# New account
@app.route('/account_new/', methods=['GET', 'POST'])
def new_account():

    try:
    
        id = Accounts.query.order_by(Accounts.AccountID.desc()).first()
        
        if id is None:
            id = 1000
        else:
            id = id.AccountID + 10
        
        # ids = pd.read_sql("SELECT AccountID FROM Accounts", con=engine)
        
        # if ids['AccountID'].empty:
        #     next_id = 1000
        # else:
        #     next_id = (ids['AccountID'].max()) + 10
        
        form = AccountForm()
        if form.validate_on_submit():
            account = Accounts(AccountID=id,
                            CompanyName=form.company_name.data, 
                            CompanyRevenue=form.company_revenue.data, 
                            EmployeeHeadCount=form.employee_head_count.data,
                            CompanySpecialties=form.company_specialties.data, 
                            CompanyIndustry=form.company_industry.data,
                            CompanyType = form.company_type.data, 
                            Country=form.country.data, City=form.city.data, 
                            Timezone=form.timezone.data)
            db.session.add(account)
            db.session.commit()
            
            flash('Account added successfully.')
            return redirect(url_for('accounts_list'))
        
    except:
        return redirect('new_account')
           
    return render_template('new_account.html', form=form)








# Invalid URL
@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('index'))


# # Internal Server Error
# @app.errorhandler(500)
# def server_error(e):
#     return render_template('.html'), 500
        






@app.route('/')
def index():
    if 'user' in session:
        usr = session['user']
        return render_template('index.html', user=usr)
    else:
        return redirect(url_for('login'))


@app.route('/login/', methods=['POST', 'GET'])
def login():
    if request.method == 'POST': 
        session.permanent = True
        user = request.form['nm']
        password = request.form['pass']
        session['user'] = user
        session['pass'] = password
        
        flash('Login successful.', 'info')
        return redirect(url_for('index'))
    else:
        if 'user' in session:
            return redirect(url_for('index'))
        return render_template('login.html')

@app.route('/logout/')
def logout():
    session.pop('user', None)
    
    session.pop('email', None) # Test
    flash('Successfully logged out.', "info")
    return redirect(url_for('login'))


@app.route('/user/')
def user():
    if 'user' in session:
        user = session['user']
        password = session['pass']
        return render_template('user.html', user=user, password=password)
    else:
        return redirect(url_for('login'))


@app.route('/base/')
def base():
    return render_template('base.html')




# TODO
@app.route('/accounts/')
def accounts():
        return render_template('accounts.html')


@app.route('/leads/')
def leads():
    return render_template('leads.html')

@app.route('/opportunities/')
def opportunities():
    return render_template('opportunities.html')

@app.route('/sales/')
def sales():
    return render_template('sales.html')

@app.route('/marketing/')
def marketing():
    return render_template('marketing.html')

@app.route('/service/')
def service():
    return render_template('service.html')

@app.route('/analytics/')
def analytics():
    return render_template('analytics.html')

@app.route('/help/')
def help():
    return render_template('help.html')

@app.route('/home')
def home():
    return render_template('home.html')

if __name__ == "__main__":
    app.run(debug=True)
    
