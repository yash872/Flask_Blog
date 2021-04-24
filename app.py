from flask import Flask, render_template,request, flash, url_for, session,redirect, logging
from flask_sqlalchemy import SQLAlchemy
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps



app = Flask(__name__)
app.debug = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

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

class Articles(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(250))
    author = db.Column(db.String(100))
    body = db.Column(db.String())
    created_date = db.Column(db.DateTime, server_default=db.func.now())

    def __init__(self, title, author, body):  
      self.title = title  
      self.author = author  
      self.body = body  



@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    result = db.session.query(Articles).all()
    if result is not None:
        return render_template('articles.html',articles = result)
    else:
        flash('No Article Found!','success')
        msg = 'No Article Found!'
        return render_template('articles.html',msg=msg)
    

@app.route('/article/<string:id>/')
def article(id):
    result = db.session.query(Articles).filter(Articles.id==id).first()
    return render_template('article.html',article = result)

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
    result = db.session.query(Articles).all()
    if result is not None:
        return render_template('dashboard.html',articles = result)
    else:
        flash('No Article Found!','success')
        msg = 'No Article Found!'
        return render_template('dashboard.html',msg=msg)

class ArticleForm(Form):
    title = StringField('Title', validators=[validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

@app.route('/add_article',methods=['GET','POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
            

        article = Articles(title,session['username'],body)
        db.session.add(article)
        db.session.commit()
        flash('Article has created!','success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html',form=form)

@app.route('/edit_article/<string:id>',methods=['GET','POST'])
@is_logged_in
def edit_article(id):
    result = db.session.query(Articles).filter(Articles.id==id).first()
    form = ArticleForm(request.form)
    form.title.data = result.title
    form.body.data = result.body
    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']
            
        result.title = title
        result.body = body
        db.session.commit()
        flash('Article has updated!','success')
        return redirect(url_for('dashboard'))
        
    return render_template('edit_article.html',form=form)

@app.route('/delete_article/<string:id>')
@is_logged_in
def delete(id):
    delete_article = Articles.query.get_or_404(id)
    try:
        db.session.delete(delete_article)
        db.session.commit()
        flash('Article has deleted!','success')
        return redirect(url_for('dashboard'))
    except:
        flash('Some issue in deleting article!','danger')
        return redirect(url_for('dashboard'))

    
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out! ','success')
    return redirect(url_for('index'))




if __name__ == '__main__':
    app.secret_key='yash1234'
    app.run()
