# -*- coding: UTF-8 -*-
from app import app, mongo
from flask import request, render_template, session, url_for, redirect, flash, g
from functions import *
from bson.objectid import ObjectId
from md5 import md5
from datetime import datetime
from os import path, mkdir
from cpviews import *
from functools import wraps
    
def is_making(deadline):
    return deadline.replace(tzinfo=None) >= datetime.now()

def seconds_to_time(seconds):
    return u'%d phút %d giây' % divmod(seconds, 60)
    
def exam_link_to_name(exam_link):
    return mongo.db.exams.find_one({'link': exam_link}, {'name': 1})['name']
    
def exam_link_to_mode(exam_link):
    return mongo.db.exams.find_one({'link': exam_link}, {'mode': 1})['mode']
    
def username_to_fullname(username):
    return mongo.db.users.find_one({'username': username}, {'fullname': 1})['fullname']
    
def assignment_in_exam(username, exam_link):
    assignment = mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link}, {'deadline': 1})
    if assignment and assignment['deadline'].replace(tzinfo=None) < datetime.now():
        return "completed"
    elif assignment and assignment['deadline'].replace(tzinfo=None) >= datetime.now():
        return "testing"
    else:
        return None
        
def check_ticked(answers):
    for a in answers:
        if True in a:
            return True
    return False
        
def ticked(username, exam_link):
    assignment = mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link}, {'asm_of_user': 1})['asm_of_user']
    count = 0
    for ques in assignment:
        if check_ticked(ques[1]):
            count += 1
    return count
    
def logging(content):
    logpath = app.config['LOGS_FILE'] + str(datetime.now())[:10]
    if not path.exists(logpath):
        mkdir(logpath)
    fin = open(logpath + '/' + session['manager'] + '.txt', 'a')
    fin.write('\n' + request.remote_addr + ' -- ' + str(datetime.now()) + ' -- ' + content.encode('utf-8'))
    fin.close()
	
@app.route('/tin-tuc')
@app.route('/')
def news():
    session.permanent = True
    if 'id' in request.args:
        try:
            news = mongo.db.news.find_one({"_id": ObjectId(request.args.get("id", "")), "status": {'$ne': 'Chưa duyệt'}})
            other_news = mongo.db.news.find({"_id": {"$lt": ObjectId(request.args.get("id", ""))}, "status": {'$ne': 'Chưa duyệt'}}, 
                                            {'name': 1}).sort('_id', -1).limit(5)
            return render_template('news.html', news=news, 
                                                other_news=other_news)
        except:
            return redirect(url_for('news'))
    
    all_news = mongo.db.news.find({"status": {'$ne': 'Chưa duyệt'}}, 
								  {'name': 1, 'summary': 1, 'image': 1}).sort('_id', -1).limit(15)
    
    return render_template('news.html', news=all_news)

@app.route('/du-thi')
def exam():
    session.permanent = True
    if 'username' in session:
        now = datetime.now()
        have_official = mongo.db.exams.find({'mode': 'Chính thức', 
                                             'status': 'Hiện', 
                                             'deadline': {'$gte': now}, 
                                             'start_date': {'$lte': now}}).count()
        return render_template('exam.html', exams=get_all_exams(), 
                                            now=now, 
                                            have_official=have_official, 
                                            assignment_in_exam=assignment_in_exam)
    else:
        error = u"Vui lòng đăng nhập để có thể xem mục này!"
        return render_template('login.html', page='exam', error=error)

@app.route('/du-thi/<exam_link>', methods=['GET','POST'])
def exam_process(exam_link):
    session.permanent = True
    try:
        if ('username' in session and 
            not check_profile_form(mongo.db.users.find_one({'username':  session['username']})) and 
            not is_banned(session['username'])):
            flash(u"Vui lòng điền đầy đủ thông tin cá nhân trước khi vào thi!")
            return redirect(url_for('profile'))
        
        """ 
        Kiểm tra nếu có login, kì thi có tồn tại, đang dùng phương thức POST thì qua bước 1
        nếu có login, kì thi có tồn tại và dùng phương thức GET thì qua bước 2 là show ra thông tin kì thi
        các trường hợp còn lại bị đầy về trang /du-thi danh sách các kì thi
        """
    
        if (request.method == 'POST') and ('username' in session) and (exam_link in get_all_exam_links()):
            username = session['username']
            exam = get_exam(exam_link)
            assignment = mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link},
                                                       {'deadline': 1, 'submitted': 1})

            """
            Có 2 trường hợp để được vào thi là:
            Đã có bài thi và bài thi vẫn còn thời hạn
            hoặc Chưa có bài thi nhưng thời hạn kì thi vẫn còn
            """
            if (assignment and is_making(assignment['deadline'])) or (assignment==None and is_making(exam['deadline'])):
                while assignment==None:
                    # Nếu chưa có bài làm thì tạo mới và lấy thông tin bài thi để show
                    create_assignment(username, exam_link)
                    assignment = mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link},
                                                               {'deadline': 1, 'submitted': 1})
                
                # Thời gian còn lại của bài thi (đơn vị là giây)
                duration = int((assignment['deadline'].replace(tzinfo=None) - datetime.now()).total_seconds())
                
                if request.form['doexam']==u'Tiếp tục' or request.form['doexam']==u'Bắt đầu':
                    asm_of_user = get_asm_of_user(username, exam_link)
                    
                elif request.form['doexam']==u'Nộp bài' or request.form['doexam']==u'Cập nhật':
                    update_assignment(username, exam_link, request.form) #Khi ấn nộp bài 1. Cập nhật bài làm
                    asm_of_user = get_asm_of_user(username, exam_link) #2. Sau đó lại lấy dữ liệu bài làm -> hiển thị ra, người dùng có thể nộp lại cho đến khi hết giờ
                    grading(username, exam_link)  #3. Chấm điểm (mỗi lần nộp bài sẽ tiến hành cập nhật lại điểm)
                    assignment = mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link}, {'submitted': 1}) #4. Lấy lại số lần submit
                
                # Trường hợp cố gắng gửi biểu mẫu post ko hợp lệ
                else:
                    return "Bạn đang cố gắng hack vào hệ thống?"

                # Truyền biến submitted với mục đich để xác địch thông tin đã nộp bài chưa
                return render_template('exam_process2.html', duration=duration, 
                                                             submitted=assignment['submitted'], 
                                                             asm_of_user=asm_of_user, 
                                                             exam=exam, 
                                                             completed_time=seconds_to_time(mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link}, {'completed_time': 1})['completed_time']), 
                                                             ticked=ticked(username, exam_link),
                                                             check_ticked=check_ticked)
            else:
                return redirect(url_for('exam_process', exam_link=exam_link))
                
        # Nếu GET 1 kì thi tồn tại: check login và kiểm tra sự tồn tại của kì thi sau đó show thông tin của kì thi và trạng thái của người dùng
        elif ('username' in session) and (exam_link in get_all_exam_links()) and not is_banned(session['username']):
            username = session['username']
            now = datetime.now()
            exam = get_exam(exam_link)
            assignment = mongo.db.assignments.find_one({'username': username, 'exam_link': exam_link},
                                                       {'deadline': 1, 'point': 1})
            
            if request.args.get('m','') != '' and assignment and not is_making(assignment['deadline']):
                result_on = (mongo.db.general.find_one({'catalog': 'result'})['result_on'] == u"Có" or exam['mode'] == u'Thi thử')
                return render_template('exam_process1.html', exam=exam, 
                                                             assignment=get_assignment(username, exam_link), 
                                                             result_on=result_on, 
                                                             now=now, 
                                                             is_making=is_making, 
                                                             check_ticked=check_ticked, 
                                                             seconds_to_time=seconds_to_time)
            
            
            return render_template('exam_process1.html', exam=exam, 
                                                         assignment=assignment, 
                                                         is_making=is_making, 
                                                         now=now, 
                                                         seconds_to_time=seconds_to_time)
        
        # Nếu cố tình GET hoặc POST 1 kì thi ko có hoặc chưa đăng nhập sẽ bị chuyển về danh sách exam /du-thi
        else:
            return redirect(url_for('exam'))
    except:
        return redirect(url_for('logout'))

@app.route('/ca-nhan', methods=['GET','POST'])
def profile():
    session.permanent = True
    try:
        if 'username' in session and not is_banned(session['username']):
            username = session['username']
            notify = None
            if request.method == 'POST':
                notify = update_profile(username, request.form)
            
            # Lấy thông tin user và các bài thi của user đó
            user = get_user(username)
            assignments = mongo.db.assignments.find({'username': username, 'deadline': {'$lt': datetime.now()}},
                                                    {'exam_link': 1, 'point': 1, 'completed_time': 1}).sort('create_date', -1)
            return render_template('profile.html', notify=notify, 
                                                   user=user, 
                                                   assignments=assignments, 
                                                   seconds_to_time=seconds_to_time, 
                                                   exam_link_to_name=exam_link_to_name,
                                                   exam_link_to_mode=exam_link_to_mode)
        elif 'username' in session and is_banned(session['username']):
            return redirect(url_for('logout'))
        else:
            error = u"Vui lòng đăng nhập để có thể xem mục này!"
            return render_template('login.html', page='profile', error=error)
    except:
        return redirect(url_for('logout'))
    
@app.route('/dang-nhap', methods=['GET','POST'])
def login(error = None):
    if 'username' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        page = request.form['page']

        username = request.form['username']
        password = request.form['password']
		
        if verify_login(username, password):
            session.permanent = True
            session['username'] = username
            session['fullname'] = mongo.db.users.find_one({'username': username}, {'fullname': 1})['fullname']
            return redirect(url_for(page))
        else:
            error = u"Bạn nhập sai tài khoản hoặc mật khẩu!"

    elif request.method == 'GET':
        page = 'profile'
    
    return render_template('login.html', error=error, page=page)

@app.route('/dang-xuat')
def logout():
    session.pop('username', None)
    session.pop('fullname', None)
    return redirect(url_for('news'))

    
############ Trang quản trị ############

@app.route('/admin')
def admin():
    if 'manager' in session:
        return redirect(url_for('cpanel', link='home'))
    else:
        return render_template('admin/login.html')
        
@app.route('/mlogin', methods=['GET','POST'])
def mlogin(error = None):
    if 'manager' in session:
        return redirect(url_for('admin'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if verify_login(username, password, ["Quản trị Hệ thống"]):
            session.permanent = True
            session['manager'] = username
            session['level'] = mongo.db.users.find_one({'username': username}, {'level': 1})['level']
            return redirect(url_for('admin'))
        else:
            error = u"Bạn đã nhập sai tài khoản hoặc mật khẩu!"

    return render_template('admin/login.html', error=error)

@app.route('/mlogout')
def mlogout():
    session.pop('manager', None)
    session.pop('level', None)
    return redirect(url_for('admin'))
    
    
class Cpanel(object):
    def __init__(self, app, pages):
        self.app = app
        self.pages = pages
        self.run()
    
    def run(self):
        @self.app.route('/admin/<link>', methods=['GET','POST'])
        def cpanel(link):
            session.permanent = True
            if 'manager' in session and session['level'] == u'Quản trị Hệ thống':
                for page in self.pages:
                    if link == page.link:
                        result = page.context()
                        if result['notify'] != '':
                            logging(result['notify'])
                        return render_template('admin/' + page.link + '.html', pages=self.pages, page=page, **result)
            else:
                return redirect(url_for('mlogout'))
                
    
class BlankHomePage(Page):
    def __init__(self):
        self.link = 'home'
        self.name = u'Home'
        self.catalogues = [('home', u'Home')]
    
    def context(self):
        cata = request.args.get('c', '')
        result = {'notify': ''}
        if cata == 'home':
            result['show'] = u"Hệ thống quản trị"
            return result
        else:
            result['show'] = u"Hệ thống quản trị"
            return result
        

def change_password(username, request_form):
    if request_form['password'] != mongo.db.users.find_one({"username": username})['password']:
        return u"Error Change Password: Bạn nhập sai mật khẩu hiện tại"
    elif request_form['new_password'] != request_form['confirm_password']:
        return u"Error Change Password: Mật khẩu xác nhận chưa khớp"
    elif request_form['new_password'] >= 6:
        mongo.db.users.update({"username": username}, {'$set': {"password": request_form['new_password']} })
        return u"Mật khẩu đã được thay đổi"
    else:
        return u"Error Change Password: Nhập sai biểu mẫu"

class ChangePasswordPage(Page):
    def context(self):
        notify = ''
        if request.method == 'POST':
            notify = change_password(session['manager'], request.form)
        return {'notify': notify}

        
admin_mode = [HomePage(),
              NewsPage(),
              UserPage(),
              ExamPage(), 
              QuestionPage(), 
              AssignmentPage(),
              ChangePasswordPage('changepassword', u'Đổi mật khẩu')]

cp = Cpanel(app, admin_mode)