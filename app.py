from flask import Flask,render_template,request,redirect,session,flash,url_for
import mysql.connector
from flask_mail import Mail,Message
from itsdangerous import URLSafeTimedSerializer,SignatureExpired
from werkzeug.security import generate_password_hash,check_password_hash
from datetime import timedelta
import os
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import simpleSplit 
from flask import send_file
import io

app=Flask(__name__)
app.secret_key="notessecretkey"
app.permanent_session_lifetime=timedelta(seconds=300)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=587
app.config['MAIL_USE_TLS']=True
app.config['MAIL_USERNAME']='Rahithya@gmail.com'
app.config['MAIL_PASSWORD']='ixgn regn klfz bmqw'

mail=Mail(app)
s=URLSafeTimedSerializer(app.secret_key)

def get_db_connection():
    conn=mysql.connector.connect(
        host="localhost",
        user="root",
        password="Rahithya@123",
        database="notesdb"
    )
    return conn

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('/viewall')
    return redirect('/login')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET','POST'])
def contact():

    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        purpose = request.form['purpose']
        message = request.form['message']

        msg = Message(
            subject=f"New Contact Request: {purpose}",
            sender=email,
            recipients=["rahithya@gmail.com"]
        )

        msg.body = f"""
        Name: {name}
        Email: {email}
        Purpose: {purpose}

        Message:
        {message}
        """

        mail.send(msg)

        reply = Message(
            subject="Thank You for Contacting Us",
            sender="Rahithya@gmail.com",
            recipients=[email]
        )

        reply.body = f"""
                    Hello {name},

                    Thank you for contacting us regarding: {purpose}.
                    We have received your message and will get back to you soon.

                    Your Message:
                    {message}

                    Best Regards,
                    Employee Management System Team
                    """

        mail.send(reply)
        flash("Message sent successfully!", "success")
        return redirect('/contact')
    return render_template("contact.html")


@app.route('/register',methods=['get','post'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        if not username or not email or not password:
            flash("please fill all fields.","danger")
            return redirect('/register')
        hashed_pw=generate_password_hash(password)
        conn=get_db_connection()
        cur=conn.cursor()
        cur.execute("select id from users where username=%s",(username,))
        exists=cur.fetchone()
        if exists:
            cur.close()
            conn.close()
            flash("Username already taken. Choose another.","danger")
            return redirect('/register')
        cur.execute("insert into users(username,email,password) values(%s,%s,%s)",(username,email,hashed_pw))
        conn.commit()
        cur.close()
        conn.close()
        flash("Registered Succefully1 you can login now","success")
        return redirect('/login')
    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        if not username or not password:
            flash("Please enter username and password.","danger")
            return redirect('/login')
        conn=get_db_connection()
        cur=conn.cursor(dictionary=True)
        cur.execute("select * from users where username=%s",(username,))
        user=cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password_hash(user['password'],password):
            session['user_id']=user['id']
            session['username']=user['username']
            flash(f"Welcome, {user['username']}","success")
            return redirect('/viewall')
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.","info")
    return redirect('/login')

@app.route('/addnote',methods=['GET','POST'])
def addnote():
    if 'user_id' not in session:
        flash("please login again","warning")
        return redirect('/login')

    if request.method=='POST':
        title=request.form['title']
        content=request.form['content']
        user_id=session['user_id']
        color=request.form['color']
        if not title or not content:
            flash("Title and content cannot be empty","danger")
            return redirect('/addnote')
        conn=get_db_connection()
        cur=conn.cursor()
        cur.execute("insert into notes(title,content,user_id,color) values(%s,%s,%s,%s)",(title,content,user_id,color))
        conn.commit()
        cur.close()
        conn.close()
        flash("note added successfully.","success")
        return redirect('/viewall')
    return render_template('addnote.html')

@app.route('/viewall')
def viewall():
    if 'user_id' not in session:
        return redirect('/login')
    page = request.args.get('page',1,type=int)
    per_page = 6
    offset = (page-1)*per_page
    conn=get_db_connection()
    cur=conn.cursor(dictionary=True)
    cur.execute("select * from notes where user_id=%s order by pinned desc,created_at desc limit %s offset %s",(session['user_id'],per_page,offset))
    notes=cur.fetchall()
    cur.execute("select count(*) as total from notes where user_id=%s",(session['user_id'],))
    total=cur.fetchone()['total']
    cur.close()
    conn.close()
    total_pages=(total+per_page-1)//per_page
    return render_template('viewnotes.html',notes=notes,page=page,total_pages=total_pages,total_notes=total)

@app.route('/viewnotes/<int:note_id>')
def viewnotes(note_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id=session['user_id']
    conn=get_db_connection()
    cur=conn.cursor(dictionary=True)
    cur.execute("select id,title,content,created_at from notes where id=%s and user_id=%s",(note_id,user_id))
    note=cur.fetchone()
    cur.close()
    conn.close()
    if not note:
        flash("you don't have access to this note.","danger")
        return redirect('/viewall')
    return render_template('singlenote.html',note=note)

@app.route('/updatenote/<int:note_id>',methods=['GET','POST'])
def updatenote(note_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id=session['user_id']
    conn=get_db_connection()
    cur=conn.cursor(dictionary=True)
    cur.execute("select id,title,content from notes where id=%s and user_id=%s",(note_id,user_id))
    note=cur.fetchone()
    if not note:
        cur.close()
        conn.close()
        flash("you do not have access to edit this note.","danger")
        return redirect('/viewall')
    if request.method=='POST':
        title=request.form['title']
        content=request.form['content']
        if not title or not content:
            flash("Title and content cannot fields be empty.","danger")
            return redirect(url_for('updatenote',note_id=note_id))
        cur.execute("update notes set title=%s,content=%s where id=%s and user_id=%s",(title,content,note_id,user_id))
        conn.commit()
        cur.close()
        flash("Note updated successfully.","success")
        return redirect('/viewall')
    cur.close()
    conn.close()
    return render_template('updatenote.html',note=note)

@app.route('/deletenote/<int:note_id>',methods=['POST'])
def deletenote(note_id):
    if 'user_id' not in session:
        return redirect('/login')
    user_id=session['user_id']
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute("delete from notes where id=%s and user_id=%s",(note_id,user_id))
    conn.commit()
    cur.close()
    conn.close()
    flash("note deleted.","info")
    return redirect('/viewall')

@app.route('/pin/<int:note_id>',methods=['POST'])
def pin_note(note_id):
    conn=get_db_connection()
    cur=conn.cursor()
    cur.execute("update notes set pinned = not pinned where id=%s and user_id=%s",(note_id,session['user_id']))
    conn.commit()
    cur.close()
    conn.close()
    return redirect('/viewall')
@app.route('/search')
def search():
    query = request.args.get('q')

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM notes WHERE title LIKE %s OR content LIKE %s",
                ('%' + query + '%', '%' + query + '%'))
    notes = cur.fetchall()

    cur.close()
    conn.close()

    # ✅ ADD THESE
    total_pages = 1
    page = 1

    return render_template("viewnotes.html",
                           notes=notes,
                           total_pages=total_pages,
                           page=page)

@app.route('/profile')
def profile():

    if 'user_id' not in session:
        return redirect('/login')

    conn=get_db_connection()
    cur=conn.cursor(dictionary=True)

    cur.execute("SELECT username,email,profile_image FROM users WHERE id=%s",(session['user_id'],))

    user=cur.fetchone()

    cur.close()
    conn.close()

    return render_template('profile.html',user=user)
import os
from werkzeug.utils import secure_filename

@app.route('/update_profile', methods=['POST'])
def update_profile():

    if 'user_id' not in session:
        return redirect('/login')

    username = request.form['username']
    email = request.form['email']

    image = request.files['profile_image']
    filename = None

    # ✅ FIX: ensure folder exists
    upload_folder = os.path.join('static', 'profile_images')
    os.makedirs(upload_folder, exist_ok=True)

    if image and image.filename != '':
        filename = secure_filename(image.filename)

        upload_path = os.path.join(upload_folder, filename)
        image.save(upload_path)

    conn = get_db_connection()
    cur = conn.cursor()

    if filename:
        cur.execute(
            "UPDATE users SET username=%s, email=%s, profile_image=%s WHERE id=%s",
            (username, email, filename, session['user_id'])
        )
    else:
        cur.execute(
            "UPDATE users SET username=%s, email=%s WHERE id=%s",
            (username, email, session['user_id'])
        )

    conn.commit()
    cur.close()
    conn.close()

    session['username'] = username

    flash("Profile updated successfully", "success")

    return redirect('/profile')
@app.route('/export_pdf')
def export_pdf():

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT title,content,created_at FROM notes WHERE user_id=%s",(session['user_id'],))

    notes = cur.fetchall()

    cur.close()
    conn.close()

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=letter)

    y = 750

    pdf.setFont("Helvetica",12)

    pdf.drawString(200,800,"My Notes Export")

    for note in notes:
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y, f"Title: {note['title']}")
        y -= 20


        pdf.setFont("Helvetica", 10)
        pdf.drawString(50, y, f"Date: {note['created_at']}")
        y -= 20

        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Content:")
        y -= 20

        pdf.setFont("Helvetica", 12)

        max_width = 500
        lines = simpleSplit(note['content'], "Helvetica", 12, max_width)

        for line in lines:
            pdf.drawString(50, y, line)
            y -= 18

            if y < 50:
                pdf.showPage()
                pdf.setFont("Helvetica", 12)
                y = 750

        y -= 20  

    pdf.save()

    buffer.seek(0)

    return send_file(buffer,as_attachment=True,download_name="notes.pdf",mimetype='application/pdf')

@app.route('/export_note/<int:note_id>')
def export_note(note_id):

    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute(
        "SELECT title, content, created_at FROM notes WHERE id=%s AND user_id=%s",
        (note_id, session['user_id'])
    )

    note = cur.fetchone()

    cur.close()
    conn.close()

    if not note:
        flash("Note not found", "danger")
        return redirect('/viewall')

    buffer = io.BytesIO()

    pdf = canvas.Canvas(buffer, pagesize=letter)

    # Title
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, 750, note['title'])

    # Date
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, 730, f"Date: {note['created_at']}")

    # Content
    pdf.setFont("Helvetica", 12)

    y = 700
    max_width=500
    lines = simpleSplit(note['content'],"Helvetica",12,max_width)

    for line in lines:
        pdf.drawString(50, y, line)
        y -= 18

        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 12)
            y = 750

    pdf.save()

    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"{note['title']}.pdf",
        mimetype='application/pdf'
    )

if __name__=='__main__':
    app.run(debug=True)



