# -*- coding: utf-8 -*
import sys
reload(sys)
sys.setdefaultencoding('utf8')
import requests
from user_agents import agents
from lxml import etree
import random
import re 
from topDomainReg import *
import pymysql
from settings import *
import time


class ParseParentId(object):
    """
    分组
    """

    def __init__(self):

        self.db = pymysql.connect(
                    host=HOST, 
                    user=USER,
                    password=PASSWORD,
                    db=DB,
                    port=PORT,
                    use_unicode=True, 
                    charset="utf8"
        )
        self.cursor = self.db.cursor()
    
    def get_parent_id(self):

        # 获取第二条数据
        try:
            sql = 'select id, parent_id from t_site_base WHERE conn_id is NULL LIMIT 1'
            self.cursor.execute(sql)
            elements = self.cursor.fetchone()

            if elements == None:
                self.db = pymysql.connect(
                    host=HOST, 
                    user=USER,
                    password=PASSWORD,
                    db=DB,
                    port=PORT,
                    use_unicode=True, 
                    charset="utf8"
                    )
                self.cursor = self.db.cursor()
                print 'refreshing mysql and waiting new domain.....'
                time.sleep(10)
                return 
                
            uid = elements[0]
            parent2id = elements[1]

            if parent2id == 0:
                pass
            else:
                # 获取上一条数据
                sql = 'select conn_id from t_site_base where id = %s' % parent2id
                self.cursor.execute(sql)
                element = self.cursor.fetchone()
                ref_id = element[0]
                
                # 更新第二条数据
                sql = 'update t_site_base set conn_id = %s where id = %s' % (ref_id, uid)
                print 'conn:%s' % ref_id, 'id:%s' % uid
                self.cursor.execute(sql)
                self.db.commit()
        except Exception as e:
            print e
            pass

    
    def get_first_id(self):

        try:
            sql = 'select id, parent_id from t_site_base where id' 
            self.cursor.execute(sql)
            element = self.cursor.fetchone()
            return element[0]
        except:
            pass
    
    def check_valid(self, start_id):
        try:
            sql = 'select conn_id from t_site_base where id = %s' % start_id
            self.cursor.execute(sql)
            element = self.cursor.fetchone()
            return element
        except:
            pass
    
    def refresh(self):
        self.db = pymysql.connect(
                    host=HOST, 
                    user=USER,
                    password=PASSWORD,
                    db=DB,
                    port=PORT,
                    use_unicode=True, 
                    charset="utf8"
        )
        self.cursor = self.db.cursor()
    
    def get_element(self):
        sql = 'select'


if __name__ == '__main__':

    ppi = ParseParentId()

    while True:
        try:
            ppi.get_parent_id()
        except Exception as e:
            print e
            ppi.refresh()
            ppi.get_parent_id()
            pass
