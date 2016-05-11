# -*- coding: UTF-8 -*-
from app import mongo
from flask import session

def verify_login(username, password, level=['Thí sinh']):
    """ Kiểm tra login """
    return mongo.db.users.find({'username': username, 
                                'password': password, 
                                'level': {'$in': level},
                                'status': 'Hoạt động'}).count() == 1

def is_banned(username):
    return mongo.db.users.find_one({'username': username, 'status': 'Khóa'}) != None

def get_user(username):
    """ Lấy thông tin tài khoản """
    return mongo.db.users.find_one({'username': username})
    
def check_profile_form(profile_form):
    """ Kiểm tra profile form, nếu thiếu bất cứ mục nào sẽ trả về False """
    return not (profile_form['fullname'] == '' or 
                profile_form['email'] == '' or
                profile_form['work'] == '' or 
                profile_form['regency'] == '')
    
def update_profile(username, request_form):
    if mongo.db.users.find_one({'username': username}, {'password': 1})['password'] != request_form['password']:
        return u"Bạn nhập sai mật khẩu hiện tại!"
    elif (request_form['new_password'] != '' and 
          len(request_form['new_password']) < 6):
        return u"Mật khẩu mới phải có ít nhất 6 kí tự!"
    elif (request_form['new_password'] != '' and 
          request_form['new_password'] != request_form['confirm_password']):
        return u"Mật khẩu mới không trùng khớp!"
    elif not check_profile_form(request_form):
        return u"Vui lòng điền đầy đủ thông tin các mục!"
    elif '@' not in request_form['email']:
        return u"Bạn nhập email chưa đúng, vui lòng nhập lại!"
    else:
        if request_form['new_password'] != '':
            mongo.db.users.update({'username': username}, { '$set' : {'fullname': request_form['fullname'], 
                                                                      'email': request_form['email'], 
                                                                      'work': request_form['work'], 
                                                                      'regency': request_form['regency'], 
                                                                      'password': request_form['new_password']} })
        else:
            mongo.db.users.update({'username': username}, { '$set' : {'fullname': request_form['fullname'], 
                                                                      'email': request_form['email'], 
                                                                      'work': request_form['work'], 
                                                                      'regency': request_form['regency']} })
        session['fullname'] = request_form['fullname']
        return u"Cập nhật thành công!"