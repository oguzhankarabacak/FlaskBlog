from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)
app.secret_key="ybblog"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "ybblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
mysql=MySQL(app)

#Makale Form
class ArticleForm(Form):

    title=StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content=TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])

class RegisterForm(Form):
    
    name=StringField("Name Surname",validators=[validators.Length(min=4,max=25)])
    username=StringField("UserName",validators=[validators.Length(min=5,max=35)])
    email=StringField("Email",validators=[validators.Email(message="Please Enter Valid Email")])
    password=PasswordField("Password",validators=[validators.equal_to("confirm",message="Passwords do not Match")])
    confirm=PasswordField("Confirm Password")

class LoginForm(Form):
    username=StringField("UserName")
    password=PasswordField("Password")
    
@app.route("/")
def index():
    numbers=[{"id" : "Deneme Blog"}
            ]
    return render_template("index.html",numbers = numbers)

@app.route("/register",methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method == "POST" and form.validate():

        name=form.name.data
        username=form.username.data
        email=form.email.data
        password=sha256_crypt.encrypt(form.password.data)

        cursor=mysql.connection.cursor()

        sorgu="Insert into users(name,email,username,password) VALUES(%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password))
        mysql.connection.commit()
        cursor.close()
        flash("Successfully Registered","success")

        return redirect(url_for("login"))    

    else : 
        return render_template ("register.html",form = form)

#Kullanıcı Giriş Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else :
            flash("Bu sayfayı Görüntülemek için giriş yapınız","danger")
            return redirect(url_for("login"))
    
    return decorated_function

@app.route("/about")
def about():

    return render_template("about.html")    

#Makale Güncelleme
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required

def update(id):

    if request.method == "GET":

        cursor=mysql.connection.cursor()

        sorgu="Select * From articles where id=%s and author=%s"
        result=cursor.execute(sorgu,(id,session["username"]))

        if result == 0:
            flash("Böyle bir makale yok veya bu işleme yetkiniz yok","danger")
            return redirect(url_for("index"))

        else : 
            article=cursor.fetchone()
            form=ArticleForm()
            form.title.data=article["title"]
            form.content.data=article["content"]

            return render_template("update.html",form=form)     
    else:
        #Post Request

        form=ArticleForm(request.form)

        newTitle=form.title.data
        newContent=form.content.data
        cursor=mysql.connection.cursor()

        sorgu2="Update articles Set title= %s,content= %s where id=%s"

        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()

        flash("Makale Güncellendi","success")
        return redirect(url_for("dashboard"))


@app.route("/login",methods=["POST","GET"])
def login():
    form=LoginForm(request.form)
    if request.method == "POST":
        username=form.username.data
        password_entered=form.password.data

        cursor=mysql.connection.cursor()

        sorgu="Select * From users where username = %s "
        result = cursor.execute(sorgu,(username,))

        if (result > 0):
            data=cursor.fetchone()
            real_password=data["password"]

            if sha256_crypt.verify(password_entered,real_password):
                flash("Succesfully Login","success")
                session["logged_in"]=True
                session["username"]=username
                return redirect(url_for("index"))
            else:
                flash("Wrong Password")
                return redirect(url_for("login"))    
        else :
            flash("Cannot Be Found Your Username","danger")
            return redirect(url_for("login"))
    return render_template("login.html",form = form)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles where author =  %s "
    result = cursor.execute(sorgu,(session["username"],))
    if result > 0:
        my_articles=cursor.fetchall()
        return render_template("dashboard.html",articles=my_articles)

    else:    
        return render_template("dashboard.html")

@app.route("/addarticle",methods=["GET","POST"])
def addArticle():
    form=ArticleForm(request.form)

    if request.method == "POST" and form.validate():

        title=form.title.data
        content=form.content.data

        cursor=mysql.connection.cursor()

        sorgu="Insert into articles(title,author,content) VALUES(%s,%s,%s)"
        cursor.execute(sorgu,(title,session["username"],content))
        mysql.connection.commit()
        cursor.close()
        flash("Makale Başarıyla Eklendi","success")
        return redirect(url_for("dashboard"))

    

    return render_template("addarticle.html",form=form)


#Makaleleri Gösterme
@app.route("/articles")
def article():
    cursor=mysql.connection.cursor()
    sorgu="Select * From articles"

    result=cursor.execute(sorgu)

    if(result > 0 ):

        articles=cursor.fetchall()
        return render_template("articles.html",articles=articles)

    else : 
        return render_template("articles.html")    


@app.route("/article/<string:id>")
def article_detail(id):

    cursor=mysql.connection.cursor()
    sorgu="Select * From articles where id = %s"
    result=cursor.execute(sorgu,(id,))

    if (result > 0):
        article_detail=cursor.fetchone()

        return render_template("article_detail.html",article=article_detail)

    else :

        return render_template("article_detail.html")    


#Makale Silme
@app.route("/delete/<string:id>")
@login_required
def delete(id):

    cursor=mysql.connection.cursor()
    sorgu="Select * From articles where author=%s and id= %s "
    result=cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2="Delete From articles where id = %s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))

    else :
        flash("Böyle bir makale yok veya Bu işleme yetkiniz yok","danger")
        return redirect(url_for("index"))

@app.route("/search",methods=["POST","GET"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))

    else :
        keyword = request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="Select * from articles where title like '%"+keyword+"%'"
        result=cursor.execute(sorgu)
        if result == 0:
            flash("aranan kelime bulunamadı ","warning")
            return redirect(url_for("article"))
        else :
            articles=cursor.fetchall()
            return render_template("articles.html",articles=articles)    
if __name__ == "__main__":
    app.run(debug=True)
