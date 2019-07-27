#coding:utf-8
from bs4 import BeautifulSoup
import requests
import json
import re
import os
import getpass

main_url ="https://www.pixiv.net"
log_in_url ='https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
post_url ='https://accounts.pixiv.net/api/login?lang=zh'

headers ={
    "User-Agent": 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.96 Safari/537.36',
    'Referer': ''
}
dat ={
    'pixiv_id':'',
    'password':'',
    'post_key':'',
    'source':'pc',
    'return_to':'https://www.pixiv.net/'
}
# params ={
#     'lang': 'en',
#     'source': 'pc',
#     'view_type': 'page',
#     'ref': 'wwwtop_accounts_index'
# }

usr =['']*20
pwd =['']*20
global mark
mark =False

ssion =requests.session()
ssion.headers =headers

def account_choise():
    global mark,usr,pwd
    cnt =int(0)
    print("Choose your account: ")
    with open('manage.txt','r+') as f:
        while True:
            st =f.readline()
            if not st:
                break
            cnt+=1
            usr[cnt] =re.search('.*_@_',st).group()[:-3]
            pwd[cnt] =re.search('_@_.*',st).group()[3:]
            print('['+str(cnt)+']: '+usr[cnt])
    print('['+str(cnt+1)+']: add another account')
    print('['+str(cnt+2)+']: reset account')
    chs =int(input("Please Enter[1-"+str(cnt+2)+']: '))
    if chs<=cnt:
        dat['pixiv_id']=usr[chs]
        dat['password']=pwd[chs]
        return
    elif chs==cnt+1:
        mark =True
        dat['pixiv_id']=input("pixiv_id: ")
        dat['password']=getpass.getpass('password: ')
    elif chs==cnt+2:
        with open('manage.txt','w+') as f:
            f.truncate()
        print('Done!')
        exit(0)

def get_key():
    res = ssion.get(log_in_url, timeout =5)
    pattern = re.compile(r'name="post_key" value="(.*?)">')
    dat['post_key'] = pattern.findall(res.text)[0]
    print("---------Present key---------- : "+dat['post_key'])

def change_url(str):
    pat = re.compile('https://i.pximg.net/(.*)/img/')
    b = pat.sub('https://i.pximg.net/img-original/img/',str)
    pat =re.compile('_master1200.jpg')
    return pat.sub('.png',b)

def get_pid(ur):
    return re.search('/[0-9]*_',ur).group()[1:-1]

def down_rank(kd):
    ss=''
    if kd==1:
        ss='daily'
    elif kd==2:
        ss='weekly'
    elif kd==3:
        ss='monthly'
    else:
        print("ERROR!")
        return

    os.chdir(os.path.join(os.getcwd(), 'photos'))
    cnt =int(1)

    for pag in (1,5):
        cont =ssion.get(main_url+'/ranking.php?mode='+ss+'&content=illust&p='+str(pag))
        doc =str(cont.content, "utf-8")
        soup =BeautifulSoup(doc, "lxml")

        for tmp in soup.find_all('section',class_='ranking-item'):
            refe =main_url+tmp.find(class_='ranking-image-item').find('a').get('href')
            url =tmp.find(class_='_layout-thumbnail').find('img').get('data-src')
            tags =tmp.find('img').get('data-tags')
            print("---------------------pic "+str(cnt)+ " ---------------------\n" + "Tags: \n" +tags)

            url =change_url(url)
            print(url)

            headers['Referer'] =refe
            pic_name =get_pid(url)+'.jpg'
            source =ssion.get(url, headers =headers)
            
            if str(source.status_code)=='404':
                url =url[:-3]+'jpg'
                source =ssion.get(url, headers =headers)
            if str(source.status_code)=='200':
                with open(pic_name, "wb") as f:
                    f.write(source.content)
                print(".......DONE!!!\n")
                cnt+=1
            else :
                print("#########Failed！")

def down_likes():
    os.chdir(os.path.join(os.getcwd(), 'photos'))

    like_url='https://www.pixiv.net/bookmark.php'

    cnt =int(0)
    mk =False
    pg =int(input("amount: "))
    print((pg/20)+1)
    for i in (1,(pg/20)+2):
        r =ssion.get(like_url+'?pg='+str(i), headers =headers, timeout =(3,7))
        doc =str(r.content, 'utf-8')
        sp =BeautifulSoup(doc, 'lxml')

        for tmp in sp.find_all("li", class_="image-item"):
            if int(cnt)==int(pg):
                mk =True
                break
            refer =main_url +"/"+tmp.find('a').get('href')
            targ =tmp.find("div", class_="_layout-thumbnail").find("img").get("data-src")
            targ =change_url(targ)

            headers['Referer']=refer
            pic_name =get_pid(targ)+'.jpg'
            print("PID: "+refer)
            source =ssion.get(targ, headers =headers, timeout =(3,7))

            if str(source.status_code) != '200':
                targ =targ[:-3]+'jpg'
                source =ssion.get(targ, headers =headers, timeout =(3,7))
            if str(source.status_code) == '200':
                with open(pic_name, 'wb') as f:
                    f.write(source.content)
                    cnt+=1
                    print (cnt)
                print(".......DONE!!!\n")
            else :
                print("#########Failed！")
        if mk:
            return
    return

# ---------------------------------main--------------------------------------

if __name__ == "__main__":
	account_choise()
	get_key()

	ret =ssion.post(post_url, data =dat)
	print(ret.json())
	jsn =re.search("\"body\": {\".*\"",json.dumps(ret.json())).group()[10]
	if jsn != 's':
		print("ERROR!")
		e=input("Press any key")
		exit(0)
	elif mark == True:
		with open('manage.txt','a+') as f:
			f.write(dat['pixiv_id']+'_@_'+dat['password']+'\n')
			print('\nLogin Successfully!')
	else:
		print('\nLogin Successfully!')
	print("\n------------------------------------\n")

	print("[1]: daily rank\n[2]: weekly rank\n[3]: monthly rank\n[4]: your likes")
	kind =int(input("Please Enter[1-4]: "))
	if kind ==4:
		down_likes()
		print("<<<<<END>>>>>")
	else:
		down_rank(kind)
		print("<<<<<END>>>>>")

	ed =input()
