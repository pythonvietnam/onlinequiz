# -*- coding: UTF-8 -*-
from app import mongo
from bson.objectid import ObjectId
from datetime import datetime

def exam_attended(username):
    "Return list of exams"
    assignments = mongo.db.assignments.find({'username': username}, {'exam_link': 1, 'deadline': 1, 'point': 1}).sort("create_date", 1)
    names = []
    for assignment in assignments:
        name = mongo.db.exams.find_one({'link': assignment['exam_link']}, {'name': 1})['name']
        point = u' (Đang thi...)'
        if datetime.now() > assignment['deadline'].replace(tzinfo=None):
            point = ' (' + str(assignment['point']) + ')'
        names.append(name + point)
    return '</br>'.join(names)

    
class Page(object):
    def __init__(self, link, name, catalogues=None):
        self.link = link
        self.name = name
        if catalogues == None:
            self.catalogues = [(link, name)]
        else:
            self.catalogues = catalogues
        
    def context(self):
        return {}


class ViewForm(object):
    def __init__(self, collection, infos, url, link):
        self.collection = collection
        self.infos = infos
        self.url = url
        self.link = link
    
    def __str__(self):                
        title = ''
        for info in self.infos:
            title +=  """<td><b>""" + info[0] + """</b></td>"""
        title += """<td></td>"""
        
        rows = ''
        for doc in self.collection:
            row = ''
            for info in self.infos:
                if len(info) > 2:
                    width = info[2]
                else:
                    width = ''
                    
                if info[1] == 'image':
                    row += """<td width=""" + width + """><div class="imgfill" style="background-image: url('/static/uploads/""" + doc[info[1]] + """');"></div></td>"""
                elif info[1] == 'attended':
                    row += """<td width=""" + width + """>""" + exam_attended(doc['username']) + """</td>"""
                elif info[1] in ['group', 'group_permission']:
                    if doc[info[1]] == None:
                        row += """<td width=""" + width + """></td>"""
                    else:
                        row += """<td width=""" + width + """>""" + unicode(mongo.db.groups.find_one( {'_id': ObjectId(doc[info[1]]) } )['name'] ) + """</td>"""
                elif info[1] == 'quespackage':
                    row += """<td width=""" + width + """>""" + unicode(mongo.db.quespackages.find_one( {'code': doc['quespackage'] } )['name'] ) + """</td>"""
                else:
                    row += """<td width=""" + width + """>""" + unicode(doc[info[1]]) + """</td>"""
            
            row += """<td>
                        <center>
                            <form action='""" + unicode(self.url) + """' method='POST'>
                            <a href='""" + unicode(self.url) + """&edit=""" + str(doc[self.link]) + """'><img border="0" src="/static/pic/edit-icon.png" width="22" height="22"></a>
                                <input type=text name=delete value='""" + str(doc[self.link]) + u"""' hidden>
                                <input type='image' alt='submit' onclick="return confirm('Bạn có chắc chắn muốn xóa?');" src="/static/pic/delete-icon.png" width="22" height="22">
                            </form>
                        </center>
                      </td>"""
            rows += """<tr>""" + row + """</tr>"""

        return  """<table class="pure-table pure-table-bordered">
                        <tr>
                        """ + title + """
                        </tr>
                        """ + rows + """
                    </table>"""

        
class EditForm(object):
    def __init__(self, doc, infos):
        self.doc = doc
        self.infos = infos
    
    def __str__(self):
        rows = ''
        enctype = ''
        for info in self.infos:
            if info[2] == 'readonly':
                row = """<tr>
                             <td><b>""" + unicode(info[0]) + """</b></td>
                             <td>""" + unicode(self.doc[info[1]]) + """</td>
                         </tr>"""
            elif info[2] == 'readonly_direct':
                row = """<tr>
                             <td><b>""" + unicode(info[0]) + """</b></td>
                             <td>""" + unicode(info[1]) + """</td>
                         </tr>"""
            elif info[2] == 'text':
                row = """<tr>
                             <td><b>""" + unicode(info[0]) + """</b></td>
                             <td><input type="text" name='""" + unicode(info[1]) + """' value='""" + unicode(self.doc[info[1]]) + """' size="60" required></td>
                         </tr>"""
            elif info[2] == 'number':
                row = """<tr>
                             <td><b>""" + unicode(info[0]) + """</b></td>
                             <td><input type="number" name='""" + unicode(info[1]) + """' value='""" + unicode(self.doc[info[1]]) + """' min=0 required></td>
                         </tr>"""
            elif info[2] == 'textarea':
                row = """<tr>
                             <td><b>""" + unicode(info[0]) + """</b></td>
                             <td><textarea type="text" name='""" + unicode(info[1]) + """' rows='7' cols='70' required>""" + unicode(self.doc[info[1]]) + """</textarea></td>
                         </tr>"""
            elif info[2] == 'pass':
                row = """<tr>
                             <td><b>""" + unicode(info[0]) + """</b></td>
                             <td><input type="text" name='""" + unicode(info[1]) + u"""' size="30" value='' placeholder='Nếu không thay đổi thì để trống' pattern="[^]{6,}"></td>
                         </tr>"""
            elif info[2] == 'image':
                row = """<tr>
                             <td><b>""" + unicode(info[0]) + """</b></td>
                             <td>
                                <img class="imgfill" style="background-image: url('/static/uploads/""" + self.doc[info[1]] + """');">
                                <input type="file" name='""" + unicode(info[1]) + """'>
                                </td>
                         </tr>"""
                enctype = "enctype=multipart/form-data"
            elif info[2] == 'news':
                row = """<tr>
                             <td><b>""" + unicode(info[0]) + """</b></td>
                             <td width="900px"><textarea type="text" name='""" + unicode(info[1]) + """' class="ckeditor">""" + unicode(self.doc[info[1]]) + """</textarea></td>
                         </tr>
                         <script src="/static/js/ckeditor/ckeditor.js"></script>"""
            else:
                options = ''
                for value in info[2]:
                    if value == self.doc[info[1]]:
                        stt = 'selected'
                    else:
                        stt = ''
                        
                    if info[1] in ['group', 'group_permission']:
                        name = mongo.db.groups.find_one({'_id': ObjectId(value)})['name']
                    else:
                        name = value
                    options += """<option value='""" + value + """'""" + stt + """>""" + name + """</option>"""

                row = """<tr>
                             <td><b>""" + unicode(info[0]) + """</b></td>
                             <td>
                                <select name='""" + unicode(info[1]) + """'>
                                    """ + options + """
                                </select>
                             </td>
                         </tr>"""
            rows += row
                    
        return """<form method="POST" """ + enctype + """ class="pure-form pure-form-aligned">
                    <table class="pure-table pure-table-bordered">
                    
                        """ + rows + """
                        <tr>
                            <td></td>
                            <td>
                                    <input type="submit" name="edit" value="Save" class="pure-button button-success" autofocus>
                                    <input type="button" value="Cancel" class="pure-button button-error" onClick="history.go(-1);">
                            </td>
                        </tr>
                    </table>
                  </form>"""
