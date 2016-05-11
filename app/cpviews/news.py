# -*- coding: UTF-8 -*-
from flask import request, session
from app import app, mongo, images
from model import *
from datetime import datetime
from bson.objectid import ObjectId
from os import remove

def insert_news(request_form, filename, username):
    news = {'name': request_form['name'], 
            'summary': request_form['summary'], 
            'content': request_form['content'], 
            'create_date': datetime.now(),
            'image': filename,
            'creator': username,
            'status': 'Chưa duyệt'}
    mongo.db.news.insert(news)
    return "Created News: " + unicode(request_form['name'])
    
def update_news(id, request_form, filename, editor):
    name = mongo.db.news.find_one({"_id": ObjectId(id)}, {'name': 1})['name']
    if request_form['name'] != '':
        mongo.db.news.update({"_id": ObjectId(id)},
                       {'$set': 
                            {'name': request_form['name'],
                             'image': filename,
                             'summary': request_form['summary'],
                             'content': request_form['content'],
                             'status': request_form['status']}
                        })
        return "Edited News: " + unicode(name) + ' --> ' + unicode(request_form['name'])
    else:
        return "Error Edit News: " + unicode(name) + u' -- Không được để trống tiêu đề'

def remove_news(id):
    name = mongo.db.news.find_one({'_id': ObjectId(id)}, {'name': 1})['name']
    mongo.db.news.remove({'_id': ObjectId(id)})
    return "Removed News: " + unicode(name)
        

class NewsPage():
    def __init__(self):
        self.link = 'news'
        self.name = u'Tin tức'
        self.catalogues = [('view', u'Danh sách tin'), 
                           ('create', u'Tạo tin mới'),
                           ('upload', u'Tải ảnh')]
    def context(self):
        cata = request.args.get('c', '')
        result = {'notify': ''}
        if cata == 'view':
            if 'edit' in request.args:
                id = request.args.get('edit')
                if request.method == 'POST' and request.form['edit'] == 'Save':
                    if request.files.get('image').filename != '':
                        remove(app.config['UPLOADED_IMAGES_DEST'] + mongo.db.news.find_one({'_id': ObjectId(id)})['image'])
                        filename = images.save(request.files.get('image'), 'news')
                    else:
                        filename = mongo.db.news.find_one({'_id': ObjectId(id)})['image']

                    result['notify'] = update_news(id, request.form, filename, session['manager'] + ' - ' + str(datetime.now()))
                result['show'] = EditForm(mongo.db.news.find_one( { '_id': ObjectId(id) } ), 
                                          [(u'Tiêu đề', 'name', 'text'), 
                                           (u'Ảnh minh họa', 'image', 'image'), 
                                           (u'Tóm tắt', 'summary', 'textarea'),
                                           (u'Nội dung', 'content', 'news'), 
                                           (u'Trạng thái', 'status', [u'Đã duyệt', u'Chưa duyệt']), 
                                           (u'Ngày đăng', 'create_date', 'readonly'), 
                                           (u'Người đăng', 'creator', 'readonly')])
                return result
            elif request.method == 'POST' and 'delete' in request.form:
                remove(app.config['UPLOADED_IMAGES_DEST'] + mongo.db.news.find_one({'_id': ObjectId(request.form['delete'])})['image'])
                result['notify'] = remove_news(request.form['delete'])
            collection = mongo.db.news.find().sort("_id", -1)
            result['show'] = ViewForm(collection, 
                                      [(u'Tiêu đề', 'name'), 
                                       (u'Ảnh minh họa', 'image'), 
                                       (u'Tóm tắt', 'summary'), 
                                       (u'Ngày đăng', 'create_date'), 
                                       (u'Trạng thái', 'status')], 
                                      request.url,
                                      '_id')
            return result
        elif cata == 'create':
            if request.method == 'POST' and 'image' in request.files:
                filename = images.save(request.files.get('image'), 'news')
                result['notify'] = insert_news(request.form, filename, session['manager'])
            return result
        elif cata == 'upload':
            if request.method == 'POST' and 'image' in request.files:
                filename = images.save(request.files.get('image'), 'images')
                mongo.db.images.insert({'filename': filename, 'created_date': datetime.now()})
                result['notify'] = 'Uploaded Image ' + filename
            elif 'delete' in request.args:
                mongo.db.images.remove({'filename': request.args.get('delete', '')})
                remove(app.config['UPLOADED_IMAGES_DEST'] + request.args.get('delete', ''))
                result['notify'] = 'Removed Image ' + request.args.get('delete', '')

            result['files'] = mongo.db.images.find().sort("_id", -1).limit(20)
            return result
        else:
            return result