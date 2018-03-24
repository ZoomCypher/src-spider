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


class PurseMysql(object):
    """
    顶级域名录入备案信息到mysql
    """

    def __init__(self):

        self.headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate',
        'Accept-Language':'zh-CN,zh;q=0.9',
        'Cache-Control':'max-age=0',
        'Connection':'keep-alive',
        'Host':'icp.chinaz.com',
        'Upgrade-Insecure-Requests':'1',
        }

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

    def add_new_varchar(self):
        try:
            sql = 'alter table t_site_base add conn_id varchar(10) '
            self.cursor.execute(sql)
        except:
            pass
    
    def create_backup_table(self):
        try:
            sql = "CREATE TABLE t_site_backup_ip(id INT UNSIGNED NOT NULL PRIMARY KEY AUTO_INCREMENT, url_pattern VARCHAR(100),company_name VARCHAR(100),company_property VARCHAR(10),license_key VARCHAR(100),web_name VARCHAR(100),web_domain VARCHAR(300))"
            self.cursor.execute(sql)
        except:
            pass

    def get_elements(self):
        try:
            sql = 'select url_pattern, id from t_site_base where parent_id = 0 and conn_id is NULL limit 1'
            self.cursor.execute(sql)
            elements = self.cursor.fetchone()
            return elements
        except:
            pass
    
    def requests_backup_website(self, url):
        try:
            self.headers['User-Agent'] = random.choice(agents)
            res = requests.get(url, headers=self.headers)
            html = etree.HTML(res.text.replace('<em>', '').replace('</em>', ''))
            return html
        except:
            pass

    def search_backup_info(self):

        try:
            # 获取一条数据
            elements = self.get_elements()
            if elements == None:
                print 'refreshing mysql and waiting for new data.....'
                self.refresh()
                time.sleep(10)
                return

            url_pattern = elements[0]
            url_id = elements[1]
        except:
            return

        try:
            url = 'http://icp.chinaz.com/{}'.format(url_pattern)
            # 获取备案信息html
            html = self.requests_backup_website(url)
            # 获取详细数据
            if not html.xpath('/html/body/div[2]/div[2]/p/text()'):
                company_name = html.xpath('//*[@id="first"]/li[1]/p/text()')[0]
                company_property = html.xpath('//*[@id="first"]/li[2]/p/strong/text()')[0]
                license_key = html.xpath('//*[@id="first"]/li[3]/p/font/text()')[0]
                web_name = html.xpath('//*[@id="first"]/li[4]/p/text()')[0]
                web_domain = html.xpath('//*[@id="first"]/li[5]/p/text()')[0]
            else:
                url = 'http://www.icpchaxun.com/beian.aspx?icpType=-1&icpValue={}'.format(url_pattern)
                # 获取备案信息html
                headers = {}
                headers['User-Agent'] = random.choice(agents)
                res = requests.get(url, headers=headers)
                html = etree.HTML(res.text.replace('<em>', '').replace('</em>', ''))
                # 获取详细数据
                company_name = html.xpath('/html/body/div[3]/div[1]/table/tbody/tr/td[2]/a/text()')[0].strip()
                company_property = html.xpath('/html/body/div[3]/div[1]/table/tbody/tr/td[3]/text()')[0].strip()
                license_key = html.xpath('/html/body/div[3]/div[1]/table/tbody/tr/td[4]/a/text()')[0].strip()
                web_name = html.xpath('/html/body/div[3]/div[1]/table/tbody/tr/td[5]/span/text()')[0].strip()
                web_domain = html.xpath('/html/body/div[3]/div[1]/table/tbody/tr/td[6]/span/text()')[0].strip()
        except:
            company_name = ''
            company_property = ''
            license_key = ''
            web_name = ''
            web_domain = ''

        try:
            # 插入数据到新表
            self.insert_backinfo_into_table(url_pattern, company_name, company_property, license_key, web_name, web_domain)
            # 获取新表的id
            ref_id = self.get_refid_from_table(url_pattern)
            # 将ref_id写入table
            self.update_refid_into_table(url_id, ref_id)
        except:
            pass

    
    def insert_backinfo_into_table(self, url_pattern, company_name, company_property, license_key, web_name, web_domain):
        try:
            sql = 'insert into t_site_backup_ip(url_pattern, company_name, company_property, license_key, web_name, web_domain) values ("%s","%s","%s","%s","%s","%s")' % (url_pattern, company_name, company_property, license_key, web_name, web_domain)
            self.cursor.execute(sql)
            self.db.commit()
        except:
            pass
    
    def get_refid_from_table(self, url_pattern):
        try:
            sql = 'select id from t_site_backup_ip where url_pattern = "%s"' % url_pattern
            self.cursor.execute(sql)
            ref_id = self.cursor.fetchone()
            return ref_id[0]
        except:
            pass
    
    def update_refid_into_table(self, url_id, ref_id):
        try:
            print 'parent:%s' % ref_id, 'id:%s' % url_id
            sql = 'update t_site_base set conn_id = %s where id = %s' % (ref_id, url_id)
            self.cursor.execute(sql)
            self.db.commit()
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
    

    
if __name__ == '__main__':
    
    pm = PurseMysql()
    pm.add_new_varchar()
    pm.create_backup_table()
    while True:
        try:
            pm.search_backup_info()
            pm.refresh()
        except:
            pm.refresh()
            pm.search_backup_info()
            pass