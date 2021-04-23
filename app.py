from flask import Flask, render_template,request, flash, url_for, session,redirect, logging
from data import Articles
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps



app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'


db = SQLAlchemy(app)
class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    username = db.Column(db.String(30))
    password = db.Column(db.String(100))
    register_date = db.Column(db.DateTime, server_default=db.func.now())

    def __init__(self, name, email, username,password):  
      self.name = name  
      self.email = email  
      self.username = username  
      self.password = password

Articles = Articles()


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html',articles = Articles)

@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html',id = id)

class RegisterForm(Form):
    name = StringField('Name', validators=[validators.Length(min=1, max=50)])
    username = StringField('Username', validators=[validators.Length(min=4, max=25)])
    email = StringField('Email', validators=[validators.Length(min=6, max=50)])
    password = PasswordField('Password', 
        validators=[validators.DataRequired(), 
                    validators.EqualTo('confirm',message='Password do not match!')])
    confirm = PasswordField('Confirm Password')

@app.route('/register',methods=['GET','POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        user = Users(name,email,username,password)

        db.session.add(user)
        db.session.commit()
        flash('You are now registered and can login!','success')
        return redirect(url_for('index'))
    return render_template('register.html',form=form)

@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        user = request.form['username']
        pass_candidate = request.form['password']

        
        result = db.session.query(Users).filter(Users.username==user).first()
        if result is not None:
            password = result.password
            if sha256_crypt.verify(pass_candidate,password):
                session['logged_in'] = True
                session['username'] = user
                flash('Password matched, sucessfully login!','success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid Login! Please try again','danger')
                return redirect('/login')

        else:
            flash('NO Luck! Please try again','danger')
            return redirect('/login')
        
    return render_template('login.html')


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unautorized! , Please login','danger')
            return redirect(url_for('login'))
    return wrap

@app.route('/dashboard')
@is_logged_in
def dashboard():
    return render_template('dashboard.html')
    
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out! ','success')
    return redirect(url_for('login'))




if __name__ == '__main__':
    app.secret_key='yash1234'
    app.run()
