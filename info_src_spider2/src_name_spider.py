# -*- coding: utf-8 -*

import requests
from user_agents import agents
from lxml import etree
import random
import re 
import pymysql
from topDomainReg import *
import datetime
import multiprocessing
from settings import *
import os
import time

import sys
reload(sys)
sys.setdefaultencoding('utf8')


class PurseMysql(object):

    def __init__(self):

        self.headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate, br',
        'Accept-Language':'zh-CN,zh;q=0.9',
        'Cache-Control':'max-age=0',
        'Connection':'keep-alive',
        'Host':'www.baidu.com',
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

        self.split_pattern = '_|:|--|\.|,|-|\(|\)|\s+|\||——|\*|\，|\：|;|\；|\——|\－|－'

    
    def clear_domain(self, domain):
        """
        处理域名
        """
        if '/' in domain:
            try:
                domain = re.search('//.*?%s/' % RegexForJudgeDomain, domain).group().replace('/', '')
            except:
                pass
        # 去除域名杂质
        if 'www.' in domain:
            domain = domain.replace('www.', '')
        if 'http://' in domain:
            domain = domain.replace('http:', '')
        if 'https://' in domain:
            domain = domain.replace('https:', '')
        return domain
    
    def parse_top_domain(self, domain):
        """
        顶级域名分类
        """
        for db in doubleTopDomain:
            if db in domain:
                # 生成列表
                domain_lst = re.split('\.', domain)
                # 判断长度
                if len(domain_lst) == 3:
                    return domain_lst
                if len(domain_lst) == 4:
                    return domain_lst[1:]
                elif len(domain_lst) > 4:
                    return domain_lst[2:]
        
        # 生成列表
        domain_lst = re.split('\.', domain)
        # 判断长度
        if len(domain_lst) == 2:
            return domain_lst
        if len(domain_lst) == 3:
            return domain_lst[1:]
        elif len(domain_lst) > 3:
            return domain_lst[2:]

    def request_top_domain(self, top_domain):
        """
        搜索顶级域名中文名称
        """
        top_domain_url = 'http://www.baidu.com/s?ie=utf-8&wd={}'.format(top_domain)
        response = requests.get(top_domain_url, headers=self.headers)
        html = etree.HTML(response.text.replace('<em>', '').replace('</em>', ''))
        return html
    
    def search_baidu(self, domain):
        try:
            headers = {}
            headers['User-Agent'] = random.choice(agents)
            url =  'http://www.baidu.com/s?ie=utf-8&wd={}'.format(domain)
            res = requests.get(url, headers=headers)
            res.encoding = 'utf-8'
            html = etree.HTML(res.text.replace('<em>', '').replace('</em>', ''))
            title = html.xpath('//div[@id=1]/h3/a/text()')[0]
            title = re.split(self.split_pattern, title)[0]
            if html.xpath('//span/font[1]'):
                if '没有找到该URL' in html.xpath('//span/font[1]/text()')[0]:
                    title = '-'
                    return title
            if len(title) >= 10:
                title = title[:10]
        except:
            title = '-'
        return title
    
                
    def get_second_domain(self, domain):
      
        try:
            if 'baidu' in domain:
                title = self.search_baidu(domain)
            else:
                headers = {}
                headers['User-Agent'] = random.choice(agents)
                res = requests.get(domain, headers=headers, timeout=1)
                get_code = res.apparent_encoding
                res.encoding = get_code
                html = etree.HTML(res.text.replace('<em>', '').replace('</em>', ''))
                title = html.xpath('//head/title/text()')[0]
                
        except:
            try:
                title = self.search_baidu(domain)
            except:
                title = '-'

        title = re.split(self.split_pattern, title)[0]

        if '40' in title:
            title = '-'
        elif 'ERROR' in title:
            title = '-'
        elif '提示信息' in title:
            title = '-'
        elif 'bad' in title:
            title = '-'
        elif '页面' in title:
            title = '-'
        elif '该页' in title:
            title = '-'
        elif 'Not' in title:
            title = '-'
        elif 'The' in title:
            title = '-'
        elif '50' in title:
            title = '-'
        elif 'Error' in title:
            title = '-'
        elif '抱歉' in title:
            title = '-'

        title = title.replace('【','').replace('】', '').replace('》','').replace('《','')

        if '——' in title:
            title = title.replace('——', '')

        if len(title) >= 6:
            title = title[:6]
        return title
    

    def syn_table_data(self, nowTime, domain):

        # update syn table
        sql_syn = 'UPDATE t_site_syn SET name = "%s", update_date = "%s", flag_type = 2 WHERE url_pattern = %s' % (title, nowTime, domain)
                


    def update_title_to_mysql(self, element):
        # 修改时间
        nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # trans
        domain = element[0].decode()
        # 获取域名中文
        top_title = self.get_top_domain(domain)
        sec_title = self.get_second_domain(domain)
        title = '%s.%s' % (top_title, sec_title)
        # 去掉书名号
        if title != None:
            title = title.replace('"', '').replace("'", "")
        

        if '-.-' in title:
            try:
                self.cursor = self.db.cursor()
                select_update = 'select remark from t_site_base where id = %s' % (element[1])
                self.cursor.execute(select_update)
                remark = self.cursor.fetchone()[0]
                # 组成sql语句
                sql_update = 'UPDATE t_site_base SET name = "%s", update_date = "%s" WHERE id = %s' % (remark, nowTime, element[1])
                # 执行sql
                self.cursor.execute(sql_update)
                print '[Process-%s]:%s' % (os.getpid(), remark)
                # 确认事务
                self.db.commit()
            except Exception as e:
                print e
            try:
                self.syn_other_table(remark, nowTime, domain)
            except Exception as e:
                print e
        
        elif title == None:
            try:
                self.cursor = self.db.cursor()
                select_update = 'select remark from t_site_base where id = %s' % (element[1])
                self.cursor.execute(select_update)
                remark = self.cursor.fetchone()[0]
                # 组成sql语句
                sql_update = 'UPDATE t_site_base SET name = "%s", update_date = "%s" WHERE id = %s' % (remark, nowTime, element[1])
                # 执行sql
                self.cursor.execute(sql_update)
                print '[Process-%s]:%s' % (os.getpid(), remark)
                # 确认事务
                self.db.commit()
            except Exception as e:
                print e
            try:
                self.syn_other_table(remark, nowTime, domain)
            except Exception as e:
                print e

        elif '-.' in title:
            try:
                self.cursor = self.db.cursor()
                select_update = 'select remark from t_site_base where id = %s' % (element[1])
                self.cursor.execute(select_update)
                remark = self.cursor.fetchone()[0]
                # 组成sql语句
                sql_update = 'UPDATE t_site_base SET name = "%s", update_date = "%s" WHERE id = %s' % (remark, nowTime, element[1])
                # 执行sql
                self.cursor.execute(sql_update)
                print '[Process-%s]:%s' % (os.getpid(), remark)
                # 确认事务
                self.db.commit()
            except Exception as e:
                print e
            try:
                self.syn_other_table(remark, nowTime, domain)
            except Exception as e:
                print e

        elif '百度' in title:
            try:
                self.cursor = self.db.cursor()
                select_update = 'select remark from t_site_base where id = %s' % (element[1])
                self.cursor.execute(select_update)
                remark = self.cursor.fetchone()[0]
                # 组成sql语句
                sql_update = 'UPDATE t_site_base SET name = "%s", update_date = "%s" WHERE id = %s' % (remark, nowTime, element[1])
                # 执行sql
                self.cursor.execute(sql_update)
                print '[Process-%s]:%s' % (os.getpid(), remark)
                # 确认事务
                self.db.commit()
            except Exception as e:
                print e
            try:
                self.syn_other_table(remark, nowTime, domain)
            except Exception as e:
                print e
        else:
            try:
                self.cursor = self.db.cursor()
                # 剔除符号
                title = title.replace('-', '')
                if re.search('.*?\.$', title):
                    title = title.replace('.', '')
                elif re.search('^\.', title):
                    title = title.replace('.', '')
                # 组成sql语句
                sql_update = 'UPDATE t_site_base SET name = "%s", update_date = "%s" WHERE id = %s' % (title, nowTime, element[1])
                # 执行sql
                self.cursor.execute(sql_update)
                print '[Process-%s]:%s' % (os.getpid(), element)
                # 确认事务
                self.db.commit()
            except Exception as e:
                print e
            try:
                self.syn_other_table(title, nowTime, domain)
            except Exception as e:
                print e
    

    def syn_other_table(self, title, nowTime, domain):
        # 同步另一张表
        try:
            self.cursor = self.db.cursor()
            sql_syn = 'UPDATE t_site_syn SET name = "%s", update_date = "%s", flag_type = 2 WHERE url = "%s"' % (title, nowTime, domain)
            self.cursor.execute(sql_syn)
            self.db.commit()
            print 'syn date %s to t_site_syn' % title
        except Exception as e:
            pass
    

    def get_top_domain(self, domain):

        if ('http' or 'https') in domain:
            try:
                url_pattern = re.search('//.*?%s/' % RegexForJudgeDomain, domain).group().replace('/', '')
            except:
                url_pattern = domain 

        else:
            url_pattern = domain
        
        try:
            url = 'http://icp.chinaz.com/{}'.format(url_pattern)
            # 获取备案信息html
            headers = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate',
            'Accept-Language':'zh-CN,zh;q=0.9',
            'Cache-Control':'max-age=0',
            'Connection':'keep-alive',
            'Host':'icp.chinaz.com',
            'Upgrade-Insecure-Requests':'1',
            }
            headers['User-Agent'] = random.choice(agents)
            res = requests.get(url, headers=headers)
            html = etree.HTML(res.text.replace('<em>', '').replace('</em>', ''))
            # 获取详细数据
            if not html.xpath('/html/body/div[2]/div[2]/p/text()'):
                web_name = html.xpath('//*[@id="first"]/li[4]/p/text()')[0]
            else:
                url = 'http://www.icpchaxun.com/beian.aspx?icpType=-1&icpValue={}'.format(url_pattern)
                # 获取备案信息html
                headers = {}
                headers['User-Agent'] = random.choice(agents)
                res = requests.get(url, headers=headers)
                html = etree.HTML(res.text.replace('<em>', '').replace('</em>', ''))
                # 获取详细数据
                web_name = html.xpath('/html/body/div[3]/div[1]/table/tbody/tr/td[5]/span/text()')[0].strip()
        except:
            try:
                headers = {}
                headers['User-Agent'] = random.choice(agents)
                url =  'http://www.baidu.com/s?ie=utf-8&wd={}'.format(url_pattern)
                res = requests.get(url, headers=headers)
                res.encoding = 'utf-8'
                html = etree.HTML(res.text.replace('<em>', '').replace('</em>', ''))
                title = html.xpath('//div[@id=1]/h3/a/text()')[0]
                title = re.split(self.split_pattern, title)[0]
                if html.xpath('//span/font[1]'):
                    if '没有找到该URL' in html.xpath('//span/font[1]/text()')[0]:
                        title = '-'
                        return title

                if '——' in title:
                    title = title.replace('——', '')
                web_name = title.replace('【','').replace('】', '').replace('》','').replace('《','')
            except:
                web_name = '-'
        
        if len(web_name) >= 10:
            web_name = web_name[:6]
        
        return web_name
    
    def requests_backup_website(self, url):

        headers = {
        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding':'gzip, deflate',
        'Accept-Language':'zh-CN,zh;q=0.9',
        'Cache-Control':'max-age=0',
        'Connection':'keep-alive',
        'Host':'whois.chinaz.com',
        'Upgrade-Insecure-Requests':'1',
        'Origin':'http://whois.chinaz.com'
        }
        try:
            headers['User-Agent'] = random.choice(agents)
            res = requests.get(url, headers=headers)
            res.encoding = 'utf-8'
            html = etree.HTML(res.text)
            return html
        except Exception as e:
            print e


    def sync_domian_with_mysql(self):

        try:
            sql_select = 'select url_pattern, id from t_site_base where update_date is Null limit 1'
            self.cursor.execute(sql_select)
            element = self.cursor.fetchone()
            
            # wait
            if element == None:
                print 'refreshing mysql and waiting for new data......'
                self.refresh()
                time.sleep(10)
                return
            
            self.update_title_to_mysql(element)

        except Exception as e:
            print e

    
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
    while True:
        try:
            pm.sync_domian_with_mysql()
        except Exception as e:
            print e
            pm.refresh()
            pm.sync_domian_with_mysql()
            pass
    
    
    