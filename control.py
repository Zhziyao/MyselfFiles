#! /usr/bin/env python
import os
import sys
import shutil
import time, datetime 
import smtplib
import string
import subprocess
import threading
from   email.mime.text import MIMEText
configrlogs = []
mailparams  = ['ziyao.zhang@intel.com', 'smtp.intel.com', 'ziyao.zhang', 'intel.com']
mailtowho   = [['ziyao.zhang@intel.com'],
               ['dongpingx.wu@intel.com', 'wudping@gmail.com'],
               ['guangxin.xu@intel.com', 'dongpingx.wu@intel.com'],
               ['jocelyn.li@intel.com', 'guangxin.xu@intel.com', 'dongpingx.wu@intel.com'],
               ['jocelyn.li@intel.com', 'guangxin.xu@intel.com', 'daniel.charles@intel.com', 'ullysses.a.eoff@intel.com', 'zhong.li@intel.com', 'jiankang.yu@intel.com', 'jun.zhao@intel.com', 'focus.luo@intel.com', 'fei.w.wang@intel.com', 'linda.yu@intel.com', 'dongpingx.wu@intel.com']]

libyamiaddrSKL = [['https://github.com/01org/libva.git', ''],
               ['https://github.com/01org/intel-vaapi-driver.git', ''],
               ['https://github.com/01org/cmrt.git', '', 'cmrt'],
               ['https://github.com/01org/intel-hybrid-driver.git', ''],
               ['git://source.ffmpeg.org/ffmpeg.git', ''],
#               ['ssh://hailin@git-amr-3.devtools.intel.com:29418/otc_media-libyami.git', ''],
#               ['ssh://hailin@git-amr-4.devtools.intel.com:29418/otc_media-libyami-utils.git', '']]
               ['https://github.com/01org/libyami.git', 'apache'],
               ['https://github.com/01org/libyami-utils.git', '']]

libyamiparaSKL = [['./autogen.sh', 'VAAPI_PREFIX',   ' '],
               ['./autogen.sh', 'VAAPI_PREFIX',   '--enable-hybrid-codec'],
               ['./autogen.sh', 'VAAPI_PREFIX',   ' '],
               ['./autogen.sh', 'VAAPI_PREFIX',   ' '],
               ['./configure',  'VAAPI_PREFIX',   ' '],
               ['./autogen.sh', 'LIBYAMI_PREFIX', '--enable-vp9dec --enable-vp8enc --enable-jpegenc --enable-h265enc --enable-h265dec --enable-vc1dec --enable-mpeg2dec'],
               ['./autogen.sh', 'LIBYAMI_PREFIX', '--enable-avformat']]

libyamiaddrBRXT = [['https://github.com/01org/libva.git', ''],
               ['https://github.com/01org/intel-vaapi-driver.git', ''],
               ['git://source.ffmpeg.org/ffmpeg.git', ''],
               ['https://github.com/01org/libyami.git', 'apache'],
               ['https://github.com/01org/libyami-utils.git', '']]

libyamiparaBRXT = [['./autogen.sh', 'VAAPI_PREFIX',   ' '],
               ['./autogen.sh', 'VAAPI_PREFIX',   ' '],
               ['./configure',  'VAAPI_PREFIX',   ' '],
               ['./autogen.sh', 'LIBYAMI_PREFIX', '--enable-vp9dec --enable-vp8enc --enable-jpegenc --enable-h265enc --enable-h265dec --enable-vc1dec --enable-mpeg2dec'],
               ['./autogen.sh', 'LIBYAMI_PREFIX', '--enable-avformat']]


logPath = ''
versionLog = ''
rootPath = ''
decodeLog = ''
encodeLog = ''
summaryLog = ''
styleFile = ''
deEncodeResultMatch = True
encodeConformanceList = []

# maybe be need to set the two variables
yamiUtils = 'libyami-utils'
topic = '01org: libyami apache + libyami-utils '
glopens = 0
gfails = 0
tableStart = "<table border=\"1\" cellpadding=\"5\" class=\"table\"> <tr> <th colspan=\"3\">Codec</th><th>Total</th> <th>Pass</th> <th>Passrate</th> </tr>"
tableStartEncode = "<table border=\"1\" cellpadding=\"5\" class=\"table\"> <tr> <th colspan=\"3\">Codec</th><th>Total</th> <th>Pass</th> <th>Passrate</th> </tr>"
tableStartPerformance = "<table border=\"1\" cellpadding=\"5\" class=\"table\"> <tr> <th>Codec</th><th>File</th> <th>Num Of Ways</th> <th>TranscodedFrames</th> <th>FPS</th> </tr>"
tableEnd = "</table>"
tableContent = ''
lastOpens = 0
lastFails = 0
codecs = ['AVC', 'HEVC']

def formatSummary():
    global lastOpens, lastFails, tableContent
    row = "<tr> <td> Summary</td>"
    row += "<td>%d</td>" % (glopens - lastOpens)
    row += "<td>%d</td>" % (glopens - lastOpens - gfails + lastFails)
    passrate = (glopens - lastOpens - gfails + lastFails) / float(glopens - lastOpens) * 100
    row += "<td>%.2f</td></tr>" % passrate
    tableContent += row
    tableContent += "\n"
    lastOpens = glopens
    lastFails = gfails

def formatTR(rows1, rows2, typeinfo, codec):
    global tableContent
    row = "<tr>"
    if rows1 > 1:
        row += "<td rowspan=\"%d\">%s</td>" % (rows1, typeinfo)
    if rows2 >= 1:
        row += "<td rowspan=\"%d\">%s</td>" % (rows2, codec)
    row += "<td>%s</td>" % DecodeResult.folder
    row += "<td>%d</td>" % DecodeResult.opens
    row += "<td>%d</td>" % (DecodeResult.opens - DecodeResult.fails)
    passrate = (DecodeResult.opens - DecodeResult.fails)/float(DecodeResult.opens) * 100
    row += "<td>%.2f</td></tr>" % passrate
    
    global glopens, gfails
    glopens = glopens + DecodeResult.opens
    gfails = gfails + DecodeResult.fails
    tableContent += row
    tableContent += "\n"

def log(filepath, content):
    file = open(filepath, 'a')
    file.write(content + '<br />')
    file.close()
def checkDeEncodeLog():
    all_the_text = ''
    nowValue = datetime.datetime.now()
    delta = datetime.timedelta(days=1)
    lastDay = nowValue - delta
    dateValue = nowValue.strftime('%Y-%m-%d')
    lastDateValue = lastDay.strftime('%Y-%m-%d')
    deEncodeLog = rootPath +'/deEncode_' + dateValue + '.log'
    lastDeEncodeLog = rootPath +'/deEncode_' + lastDateValue + '.log'
    print("summaryLog: " + summaryLog)
    file_object = open(summaryLog)
    all_the_text = file_object.read( )
    file_object.close( )
    decode_encode_result = all_the_text    
    npos = all_the_text.find('<h1>yamitranscode transcode performance test result</h1>')
    print('npos: ' + str(npos))
    if npos != -1:
        decode_encode_result = all_the_text[0:npos]    
    file_object_w = open(deEncodeLog, 'w')
    file_object_w.write(decode_encode_result)
    file_object_w.close( )
    print('lastDeEncodeLog: ' + lastDeEncodeLog + ' deEncodeLog: ' + deEncodeLog)
    result = os.system('diff ' + lastDeEncodeLog + ' ' + deEncodeLog)
    print("result: " + str(result))
    if result != 0:
        print("decode and encode result is not the same as the last!")
        return False
    else:
        return True

def mergeLog():
    os.system('mv  ' + summaryLog  + ' ' + logPath)
    if os.path.exists(decodeLog):
        os.system('cat ' + decodeLog + ' >> ' + logPath)
    if os.path.exists(encodeLog):
        os.system('cat ' + encodeLog  + ' >> ' + logPath)
    os.system('cat ' + versionLog + ' >> ' + logPath);
    # os.system('rm *.tmp')

def pull(dirname, addr):
    pullCmd = 'git pull'
    os.chdir(dirname)
    print(dirname + ' ' + pullCmd)
    state = os.system(pullCmd)
    # try five times pull
    count  = 1
    while state !=0:
        state = os.system(pullCmd)
        count += 1
        if count == 5:
            break
    
    os.chdir(rootPath)
    if state != 0:
        shutil.rmtree(dirname)
        state = clone(addr, '')
        if state != 0:
            return False;
    return state

def clone(addr, branch):
    cloneCmd = ''
    if branch == '':
        cloneCmd = 'git clone ' + addr
    else:  
        cloneCmd = 'git clone -b ' + branch + ' ' + addr
    print(cloneCmd)
    state = os.system(cloneCmd)
    # try five times git clone
    count = 1
    while state !=0:
        state = os.system(cloneCmd)
        count +=1
        if count == 5:
            break

    if state != 0:
        log(logPath, cloneCmd + ' Failed!')
    return state

#git clone
def clone_addr(addrlist, paramlist):
    for addr in addrlist:
        dirname = addr[0][(addr[0].rfind('/')+1):]
        if dirname.find('.') != -1:
            dirname = dirname[0:dirname.find('.')]
        if dirname == 'ffmpeg':
            continue
        if os.path.exists(dirname):
            if pull(dirname, addr[0]) !=0:
                return False
        elif clone(addr[0], addr[1]) != 0:
            # configrlogs.append(cloneCmd[0])
            return False
    return True

def build(dirname, param):
    os.chdir(dirname)
    if dirname == 'libyami-utils':
        if checkFiles('testscripts/unit_test2.sh') == False:
            os.system('ln -s '+ uintTestPath +' ./testscripts/unit_test2.sh')
    buildCmd = param[0] + ' --prefix=' + os.getenv(param[1]) + ' ' +  param[2] + ' && make -j8 && make install'
    print('\n\n' + buildCmd)
    state = os.system(buildCmd)
    count = 1
    while state != 0:
        os.system('git clean -dxf')
        state = os.system(buildCmd)
        count = count + 1
        if count == 5:
            break

    if state == 0:
        process = subprocess.Popen("git log -1 | head -n 1 | awk '{print $2}'", shell=True, stdout=subprocess.PIPE)
        version = process.stdout.read().decode('utf8')
        log(versionLog, dirname + ": " + version + " \r\n<br />")
    else:
        log(logPath, buildCmd + " Failed \r\n<br />")
    os.chdir(rootPath)
    return state

#build
def build_addr(addrlist, paramlist):
    i = 0;
    for addr in addrlist:
        dirname = addr[0][(addr[0].rfind('/')+1):]
        if dirname.find('.') != -1:
            dirname = dirname[0:dirname.find('.')]
        if build(dirname, paramlist[i]) != 0:
            return False
        i = i + 1
    return True

def mail(sendMode):
    content = ""
    content += open(styleFile, 'r').read()
    if os.path.exists(summaryLog):
        content += open(summaryLog, 'r').read()

    if os.path.exists(versionLog):
        content += '<h1>version info</h1><br />'
        content += '=============================================== \r\n<br />'
        file = open(versionLog, 'r')
        content += file.read()
        file.close()
    if os.path.exists(decodeLog):
        content += '<h1>decode failed case</h1><br />'
        content += '=============================================== \r\n<br />'
        logFile = open(decodeLog, 'r')
        content += logFile.read()
        logFile.close()

    if os.path.exists(encodeLog):
        content += '<h1>encode failed case</h1><br />'
        content += '=============================================== \r\n<br />'
        logFile = open(encodeLog, 'r')
        content += logFile.read()
        logFile.close()

    content += "</body></html>"
    toList = mailtowho[sendMode]
    subject = datetime.datetime.now().strftime('%Y-%m-%d') + ' ' + topic + ' daily regression on KBL'
    subject += "[fails: " + str(gfails) + "][opens: " + str(glopens) +"]"
    #if deEncodeResultMatch:
    #    subject += " same as last day"
    #else:
    #    subject += " different from last day"
        
    send_mail(toList, subject, content)

def mailError(sendMode):
    if os.path.exists(logPath):
        logFile = open(logPath, 'r')
        content += logFile.read()
        logFile.close()

    toList = mailtowho[sendMode]
    subject = datetime.datetime.now().strftime('%Y-%m-%d') + ' ' + topic + ' daily regression on SKL'
    subject += "[run error !]"
    send_mail(toList, subject, content)

def send_mail(to_list, sub, content):
    me = 'ziyao'+'<'+mailparams[2]+'@'+mailparams[3]+'>'
    msg = MIMEText(content, _subtype='html', _charset='utf-8')
    if deEncodeResultMatch:
        sub += " same as last day"
    else:
        sub += " different from last day"
        msg['X-MSMail-Priority'] = 'High'
        
    msg['Subject'] = sub
    msg['From'] = me
    msg['To'] = ';'.join(to_list)
    try:
        server = smtplib.SMTP()
        server.connect(mailparams[1])
        server.sendmail(me, to_list, msg.as_string())
        server.close()
        print('\n\nsend email success')
    except Exception, e:
        print str(e)
        print('\n\nsend email fail')
        log(logPath, 'Send email fail!')

def checkFiles(testfiles):
    if not os.path.exists(testfiles):
        print(testfiles + ': media directory is not exists!')
        return False
    return True

def jpegTest(testfiles, jpgfolder):
    if not checkFiles(testfiles):
        return
    summarylogs = ''
    jpgFailedCase = ''
    os.chdir(rootPath)
    testfiles = os.path.abspath(testfiles)    
    os.chdir(yamiUtils + '/testscripts')
    cmd = subprocess.Popen(r"./ssim_test.py " + testfiles, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in cmd.stdout:
        l = line.decode("utf8");
        if "total =" in l.lower():
            arr = l.split(',')
            jpgopens = string.atoi(arr[0].split('=')[-1], 10)
            jpgfails = string.atoi(arr[-1].split('=')[-1], 10)
            DecodeResult.opens += jpgopens 
            DecodeResult.fails += jpgfails
            summarylogs = "opened files:" + str(jpgopens) + ", passed files:" + str(jpgopens - jpgfails) + ", failed files:" + str(jpgfails) + " \r\n<br />"
        else:
            if ' failed' in line:
                fileName = line.split('mediafiles/')[-1]
                jpgFailedCase += fileName +" \r\n<br />"
    DecodeResult.failedCase += summarylogs 
    DecodeResult.failedCase += jpgFailedCase 
    DecodeResult.folder = jpgfolder

def yamiDecodeTest(testfiles, outputdir, savemode, frames = -1):
    if not checkFiles(testfiles):
        return
    testfiles = os.path.abspath(testfiles)    
    os.chdir(yamiUtils + '/testscripts')
    
    testCmd = './unit_test2.sh --decode ' + str(frames) + ' ' + testfiles
    if savemode == 1:
        testCmd += ' 1 ' + outputdir 
    else:
        testCmd += ' 0'

    state = os.system(testCmd)
    if state != 0:
        log(decodeLog, "*****************ERROR***************************")
        log(decodeLog, testfiles)
        log(decodeLog, 'decode did not completed !')
    
    os.chdir(rootPath)
    return state

def yamiEncodeTest(testfiles, outputdir, savemode, codec, fourcc, ipperiod):
    if not checkFiles(testfiles):
        return
    testfiles = os.path.abspath(testfiles)    
    os.chdir(yamiUtils + '/testscripts')

    testCmd = './unit_test2.sh --encode ' + codec + ' ' + fourcc + ' ' + testfiles + ' ' + str(ipperiod)
    if savemode == 1:
        testCmd += ' 1 ' + outputdir
    else:
        testCmd += ' 0'  

    state = os.system(testCmd)
    if state != 0:
        log(encodeLog, "*****************ERROR***************************")
        log(encodeLog, testfiles)
        log(encodeLog, codec + ' encode did not completed !')

    os.chdir(rootPath)
    return state

def yamiDecode(testfiles, outputdir):
    if not checkFiles(testfiles):
        return
    testfiles = os.path.abspath(testfiles)    
    os.chdir(yamiUtils + '/testscripts')
    testCmd = './unit_test2.sh decode ' + testfiles + ' ' + outputdir

    state = os.system(testCmd)
    if state != 0:
        log(decodeLog, "*****************ERROR***************************")
        log(decodeLog, testfiles)
        log(decodeLog, 'decode did not completed !')
    
    os.chdir(rootPath)
    return state

class DecodeResult():
    opens = 0
    fails = 0
    folder = ''
    failedCase = ''

def vc1RCVVerify(refYuvDir, outputdir, folder):
    os.chdir(rootPath)
    testCmd = './vc1_rcv_verify.sh ' + outputdir + ' ' + refYuvDir
    state = os.system(testCmd)
    if state != 0 or os.path.exists('vc1_result.tmp') == False:
        DecodeResult.fails = DecodeResult.opens
        DecodeResult.failedCase = 'verifying the yuv of vc1_rcv failed!'
        return state
    lines = open('vc1_result.tmp', 'r').readlines()
    DecodeResult.folder = folder
    for line in lines:
        if 'opened files' in line:
            arr = line.split(',')
            DecodeResult.opens += string.atoi(arr[0].split(':')[-1], 10)
            DecodeResult.fails += string.atoi(arr[-1].split(':')[-1], 10)
            DecodeResult.failedCase += folder  +"  "+ line + " \r\n<br />"
        if ' fail' in line:
            DecodeResult.failedCase += line +" \r\n<br />"
    return state;

def parseLog(logDir, folder):
    os.chdir(logDir)
    DecodeResult.folder = folder
    lastLogName = os.popen("ls -lrt | awk 'END{print $NF}'").read().rstrip()
    print('lastLogName: ' + lastLogName)
    lines = open(lastLogName).readlines()
    for line in lines:
        if 'opened files' in line:
            arr = line.split(',')
            DecodeResult.opens += string.atoi(arr[0].split(':')[-1], 10)
            DecodeResult.fails += string.atoi(arr[-1].split(':')[-1], 10)
        if ' fail' in line:
            fileName = line.split('mediafiles/')[-1]
            DecodeResult.failedCase += fileName +" \r\n <br />"
    os.remove(lastLogName)
    os.chdir(rootPath)    

def writelogs(typeinfo, codec):
    content = ''
    if DecodeResult.fails != 0:
        content = " \r\n<br />"
        content += "<div>" + codec + ' ' + typeinfo + ' failed case \r\n<br />'
        content += '---------------------------------------------- \r\n<br />'
        content += DecodeResult.failedCase + "</div> \r\n<br />"
        if typeinfo == 'dec':
            log(decodeLog, content)
        else:
            log(encodeLog, content)

    DecodeResult.opens = 0
    DecodeResult.fails = 0
    DecodeResult.folder = ''
    DecodeResult.failedCase = ''
    
class EncodeResultPerformanceTest():
    def __init__(self, codec, filename, decodedframes, waynum_, listfps_ = []):
        self.codec = codec
        self.filename = filename
        self.decodedframes = decodedframes
        self.waynum = waynum_
        self.listfps = listfps_

def parseResultPerformanceTest(inputfile, outputdir, codec, waynum = 0):
    fps = ""
    decodedframes = ""
    filename = inputfile[inputfile.rfind('/')+1:]
    extenssion = filename[filename.rfind('.')+1:]
    bodyname = filename[0:filename.rfind('.')]
    fpslist = []
    for i in range(0, waynum):
        logfilename = bodyname + '_' + str(i) + '.' + extenssion + '.log'
        logfile = outputdir + '/' + logfilename
        lines = open(logfile).readlines()
        for line in lines:
            if 'fps after 5 frames' in line:
                arr = line.split('fps after 5 frames = ')
                fps = arr[1][0:arr[1].rfind('.')]
            if 'encode fail' in line:
        	      fps = 'fail'
        	      fpslist = []
        	      fpslist.append(fps)
        	      break
            if 'frame decoded' in line:
                arr = line.split(' frame decoded')
                decodedframes = arr[0]
        fpslist.append(fps)
    encodeConformanceList.append(EncodeResultPerformanceTest(codec, filename, decodedframes, str(waynum), fpslist)) 

def executeFunc(testCmd):
    state = os.system(testCmd)
    if state != 0:
        print('error ======')

def yamiEncodePerformanceTest(inputfile, outputdir, codec, waynum = 0, save = 0):
    if not checkFiles(inputfile):
        return
    #inputfile = os.path.abspath(inputfile)

    os.chdir(yamiUtils + '/testscripts')

    filename = inputfile[inputfile.rfind('/')+1:]
    extenssion = filename[filename.rfind('.')+1:]
    bodyname = filename[0:filename.rfind('.')]
    cmdThead = [] 
    for i in range(0, waynum):
    	  outputfile = bodyname + '_' + str(i) + '.' + extenssion
    	  testCmd = './unit_test2.sh --encode-performance ' + codec + ' '  + inputfile + ' ' + outputdir + ' ' + outputfile + ' ' + str(save)
    	  cmdThead.append(threading.Thread(target=executeFunc, args=(testCmd,)))
    for t in cmdThead:
        t.start()
    for t in cmdThead:
        t.join() 	 
 
    os.chdir(rootPath)

def getNumOfCodecPerformanceTest(codec):
	  i = 0
	  num = 0
	  rowsNum = len(encodeConformanceList)
	  while (i < rowsNum):
	  	  if(cmp(codec, encodeConformanceList[i].codec) == 0):
	  	  	  num += 1
	  	  i += 1
	  return num

def writeEmailListPerformanceTest():
	  global tableContent
	  lastfilename = ''
	  lastcodec = ''
	  rows = ''
	  fps = 0.0
	  fpsstr = ''
	  waynum_ = 0
	  rowsNum = 0
	  rowsNum = len(encodeConformanceList)
    
	  tableContent += "<h1>yamitranscode transcode performance test result</h1>"
	  tableContent += tableStartPerformance
	  for codec in codecs:
	  	  span = getNumOfCodecPerformanceTest(codec)
	  	  i = 0
	  	  while (i < rowsNum):
	  	  	  if(cmp(encodeConformanceList[i].codec, codec) == 0):
	  	  	  	  rows += "<tr>"
	  	  	  	  if (cmp(lastcodec, codec) != 0):
	  	  	  	  	  rows += "<td rowspan=\"%d\">%s Performance</td>" % (span, codec)
	  	  	  	  	  lastcodec = codec
	  	  	  	  rows += "<td>%s</td>" % encodeConformanceList[i].filename
	  	  	  	  rows += "<td>%s</td>" % encodeConformanceList[i].waynum
	  	  	  	  rows += "<td>%s</td>" % encodeConformanceList[i].decodedframes
	  	  	  	  
	  	  	  	  waynum_ = string.atoi(encodeConformanceList[i].waynum, base=10)
	  	  	  	  fps = 0.0
	  	  	  	  for j in range(waynum_):
	  	  	  	  	  if(cmp(encodeConformanceList[i].listfps[j], 'fail') == 0):
	  	  	  	  	  	  fpsstr = 'fail'
	  	  	  	  	  	  break
	  	  	  	  	  fps += string.atof(encodeConformanceList[i].listfps[j])
	  	  	  	  if(cmp(fpsstr, 'fail') == 0):
	  	  	  	  	  rows += "<td>%s</td>" % fpsstr
	  	  	  	  else:
	  	  	  	  	  fps /= waynum_	  	  
	  	  	  	  	  rows += "<td>%.2f</td>" % fps
	  	  	  	  rows += "</tr>"
	  	  	  i += 1
	  tableContent += rows
	  tableContent += tableEnd

if __name__=='__main__':
    content = ''
    rootPath = os.getcwd()
    logPath = rootPath + '/' + datetime.datetime.now().strftime("%Y-%m-%d") + '.log'
    mediaFilesPath = rootPath + '/medias_for_verify'
    yamiEncodeYuvPath = mediaFilesPath + '/h264_enc_yuv'
    vc1RCVRefYuvDir = mediaFilesPath + '/rcv_ref_yuv'
    uintTestPath = rootPath + '/unit_test2.sh'
    versionLog = rootPath + '/version.tmp'
    decodeLog = rootPath + '/decode.tmp'
    encodeLog = rootPath + '/encode.tmp'
    summaryLog = rootPath +'/summary.tmp'
    styleFile = rootPath + '/style.html'
    isSKL = False
    deEncodeResultMatch = True

    os.system('rm *.tmp')
    if isSKL:
        libyamipara = libyamiparaSKL
        libyamiaddr = libyamiaddrSKL
    else:
        libyamipara = libyamiparaBRXT
        libyamiaddr = libyamiaddrBRXT

    if os.path.exists(logPath):
        os.remove(logPath)

    # if not clone_addr(libyamiaddr, libyamipara):
    #     content = 'libraries update failed'
    #     print('\n\n' + content)
    #     log(logPath, content)
    #     mailError(0)
    #     sys.exit(-1)


    # if not build_addr(libyamiaddr, libyamipara):
    #     content = 'libraries build failed'
    #     print('\n\n' + content)
    #     log(logPath, content)
    #     mailError(0)
    #     sys.exit(-1)

    if not checkFiles(mediaFilesPath):
        os.exit(-1)

    batvideocontent = os.path.abspath(mediaFilesPath)
    decodetestfiles = os.path.join(batvideocontent, 'mediafiles')
    
    testLog = os.path.join(os.path.abspath(yamiUtils), 'testscripts/log')
    yuvSavePath = os.path.join(os.path.abspath(yamiUtils), 'testscripts/decodeYUV')
    
    #Decode Test
    tableContent += "<h1>yamidecode test result</h1>" + tableStart
  
    #h264
    decodeh264files = os.path.join(decodetestfiles, 'AVC')
    yamiDecodeTest(decodeh264files, yuvSavePath, 0)
    parseLog(testLog, 'AVC')
    formatTR(40, 5, "YamiDecoder", "AVC Conformance")
    writelogs('dec', "AVC")
    
    decodeh264files = os.path.join(decodetestfiles, 'AVC_ffmpeg')
    yamiDecodeTest(decodeh264files, yuvSavePath, 0)
    parseLog(testLog, 'AVC_ffmpeg')
    formatTR(0, 0, '', '')
    writelogs('dec', "AVC")

    decodeh264files = os.path.join(decodetestfiles, 'AVC_vpg')
    yamiDecodeTest(decodeh264files, yuvSavePath, 0, 50)
    parseLog(testLog, 'AVC_vpg')
    formatTR(0, 0, '', '')
    writelogs('dec', "AVC")

    #container
    decoderContainer = os.path.join(decodetestfiles, 'AVC_container')
    yamiDecodeTest(decoderContainer, yuvSavePath, 0, 100)
    parseLog(testLog, 'AVC_container')
    formatTR(0, 0, '', '')
    writelogs('dec', 'AVC')

    formatSummary()

    #h265
    decodeH265files = os.path.join(decodetestfiles, 'hevc')

    jvt10files = os.path.join(decodeH265files, "HEVC_10BIT_JVT")
    yamiDecodeTest(jvt10files, yuvSavePath, 0)
    parseLog(testLog, "HEVC_10BIT_JVT")
    formatTR(0, 9, '', 'HEVC Conformance')
    writelogs('dec', "HEVC")

    jvt10files = os.path.join(decodeH265files, "HEVC_10bit_vpg")
    yamiDecodeTest(jvt10files, yuvSavePath, 0)
    parseLog(testLog, "HEVC_10bit_vpg")
    formatTR(0, 0, '', '')
    writelogs('dec', "HEVC")
    
    allegro10files = os.path.join(decodeH265files, "HEVC_Allegro10.0")
    yamiDecodeTest(allegro10files, yuvSavePath, 0)
    parseLog(testLog, "HEVC_Allegro10.0")
    formatTR(0, 0, '', '')
    writelogs('dec', "HEVC")

    jvt10files = os.path.join(decodeH265files, "HEVC_JVT10.0")
    yamiDecodeTest(jvt10files, yuvSavePath, 0)
    parseLog(testLog, "HEVC_JVT10.0")
    formatTR(0, 0, '', '')
    writelogs('dec', "HEVC")

    msftfiles = os.path.join(decodeH265files, "HEVC_MSFT")
    yamiDecodeTest(msftfiles, yuvSavePath, 0)
    parseLog(testLog, "HEVC_MSFT")
    formatTR(0, 0, '', '')
    writelogs('dec', "HEVC")

    bbc10_i = os.path.join(decodeH265files, "HEVC_BBC10.0/i_main")
    yamiDecodeTest(bbc10_i, yuvSavePath, 0)
    parseLog(testLog, "HEVC_BBC10.0")

    bbc10_id = os.path.join(decodeH265files, "HEVC_BBC10.0/id_main")
    yamiDecodeTest(bbc10_id, yuvSavePath, 0)
    parseLog(testLog, "HEVC_BBC10.0")

    bbc10_ip = os.path.join(decodeH265files, "HEVC_BBC10.0/ip_main")
    yamiDecodeTest(bbc10_ip, yuvSavePath, 0)
    parseLog(testLog, "HEVC_BBC10.0")
    formatTR(0, 0, '', '')
    writelogs('dec', "HEVC")

    msftfiles = os.path.join(decodeH265files, "HEVC_ffmpeg")
    yamiDecodeTest(msftfiles, yuvSavePath, 0)
    parseLog(testLog, "HEVC_ffmpeg")
    formatTR(0, 0, '', '')
    writelogs('dec', "HEVC")
    
    #hevc container
    decoderContainer = os.path.join(decodeH265files, 'HEVC_Container')
    yamiDecodeTest(decoderContainer, yuvSavePath, 0, 100)
    parseLog(testLog, 'HEVC_Container')
    formatTR(0, 0, '', '')
    writelogs('dec', 'HEVC')

    formatSummary()

    # VP8
    decodeVp8files1  = os.path.join(decodetestfiles, 'vp8_vpg')
    yamiDecodeTest(decodeVp8files1, yuvSavePath, 0)
    parseLog(testLog, 'vp8_vpg')
    formatTR(0, 5, '', 'VP8 Conformance')
    writelogs('dec', 'VP8')

    decodeVp8files  = os.path.join(decodetestfiles, 'vp8')
    yamiDecodeTest(decodeVp8files, yuvSavePath, 0)
    parseLog(testLog, 'vp8')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP8')
    
    decodeVp8files  = os.path.join(decodetestfiles, 'vp8_alpha_ffmpeg')
    yamiDecodeTest(decodeVp8files, yuvSavePath, 0, 100)
    parseLog(testLog, 'vp8_alpha_ffmpeg')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP8')

    decodeVp8files  = os.path.join(decodetestfiles, 'vp8_ffmpeg')
    yamiDecodeTest(decodeVp8files, yuvSavePath, 0, 100)
    parseLog(testLog, 'vp8_ffmpeg')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP8')

    formatSummary()

    #VP9
    decodeVP9files = os.path.join(decodetestfiles,  'vp9_10bit_argon_profile2_10_extra_streams')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_10bit_argon_profile2_10_extra_streams')
    formatTR(0, 13, '', 'VP9 Conformance')
    writelogs('dec', 'VP9')

    decodeVP9files = os.path.join(decodetestfiles,  'vp9_10bit_argon_profile2_10_streams')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_10bit_argon_profile2_10_streams')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')

    decodeVP9files = os.path.join(decodetestfiles,  'vp9_10bit_basic')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_10bit_basic')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')

    decodeVP9files = os.path.join(decodetestfiles,  'vp9_10bit_SBE_VP9_FC2P2')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_10bit_SBE_VP9_FC2P2')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')

    decodeVP9files = os.path.join(decodetestfiles,  'vp9_10bit_high_Dec_Rev0')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_10bit_high_Dec_Rev0')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')

    decodeVP9files = os.path.join(decodetestfiles,  'vp9_10bit_high_Dec_Rev025')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_10bit_high_Dec_Rev025')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')

    decodeVP9files = os.path.join(decodetestfiles,  'vp9_10bit_high_Dec_Rev05')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_10bit_high_Dec_Rev05')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')

    decodeVP9files = os.path.join(decodetestfiles,  'vp9_10bit_high_Dec_Rev085')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_10bit_high_Dec_Rev085')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')

    decodeVP9files = os.path.join(decodetestfiles,  'vp9_10bit_vpg')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_10bit_vpg')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')
            
    decodeVP9files = os.path.join(decodetestfiles,  'vp9_google')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_google')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')

    decodeVP9files = os.path.join(decodetestfiles,  'vp9_vpg')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0)
    parseLog(testLog, 'vp9_vpg')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')


    decodeVP9files = os.path.join(decodetestfiles,  'vp9-test-vectors_ffmpeg')
    yamiDecodeTest(decodeVP9files, yuvSavePath, 0, 100)
    parseLog(testLog, 'vp9-test-vectors_ffmpeg')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VP9')

    formatSummary()
    
    #MPEG
    decodeMpegfiles = os.path.join(decodetestfiles, 'mpeg2')
    yamiDecodeTest(decodeMpegfiles, yuvSavePath, 0)
    parseLog(testLog, 'mpeg2')
    formatTR(0, 3, '', "MPEG2 Conformance")
    writelogs('dec', 'MPEG2')

    #ffmpg mpeg2 container
    decoderContainer = os.path.join(decodetestfiles, 'mpeg2_ffmpeg_container')
    yamiDecodeTest(decoderContainer, yuvSavePath, 0)
    parseLog(testLog, 'mpeg2_ffmpeg_container')
    formatTR(0, 0, '', '')
    writelogs('dec', 'MPEG2')

    formatSummary()

    #VC1
    decodeVC1files = os.path.join(decodetestfiles, 'VC1_Advance_Profile')
    yamiDecodeTest(decodeVC1files, yuvSavePath, 0)
    parseLog(testLog, 'VC1_Advance_Profile')
    formatTR(0, 4, '', 'VC1 Conformance')
    writelogs('dec', 'VC1')

    decodeVC1files = os.path.join(decodetestfiles, 'VC1_Advance_Profile_ffmpeg')
    yamiDecodeTest(decodeVC1files, yuvSavePath, 0)
    parseLog(testLog, 'VC1_Advance_Profile_ffmpeg')
    formatTR(0, 0, '', '')
    writelogs('dec', 'VC1')

    decodeVC1RCVfiles = os.path.join(decodetestfiles, 'VC1_RCV_Confromance_M_Simple_Profile')
    yamiDecode(decodeVC1RCVfiles, yuvSavePath)
    vc1RCVVerify(vc1RCVRefYuvDir, yuvSavePath, "VC1_RCV_Confromance_M_Simple_Profile")
    formatTR(0, 0, '', '')
    writelogs('dec', 'VC1')

    formatSummary()

    #Jpeg
    decodeJpegfiles = os.path.join(decodetestfiles, 'jpg')
    #jpegTest calls ssim_test.py, needn't parse log file
    jpegTest(decodeJpegfiles, 'jpg')
    formatTR(0, 1, '', "JPEG Conformance")
    #formatTR(2, 1, 'yamidecode', "JPEG Conformance")
    writelogs('dec', 'JPEG')

    tableContent += tableEnd
    log(summaryLog, tableContent)
    tableContent = ''

    #Encode Test
    tableContent += "<h1>yamiencode test result</h1>"
    tableContent += "<h2>The current standard value of psnr is 33</h2>"
    tableContent += tableStartEncode
    
    os.chdir(rootPath)
    #H264
    ipperiod=3
    yamiEncodeTest(yamiEncodeYuvPath, '', 0, 'AVC', 'I420', ipperiod)
    parseLog(testLog, 'AVC')
    formatTR(6, 1, 'YamiEncoder', 'AVC I/P/B frame')
    writelogs('enc', 'AVC')

    ipperiod=0
    yamiEncodeTest(yamiEncodeYuvPath, '', 0, 'AVC', 'I420', ipperiod)
    parseLog(testLog, 'AVC')
    formatTR(0, 1, '', 'AVC I/P frame')
    writelogs('enc', 'AVC')
    
    #H265
    ipperiod=3
    yamiEncodeTest(yamiEncodeYuvPath, '', 0, 'HEVC', 'I420', ipperiod)
    parseLog(testLog, 'HEVC')
    formatTR(0, 1, '', 'HEVC I/P/B frame')
    writelogs('enc', 'HEVC')

    ipperiod=0
    yamiEncodeTest(yamiEncodeYuvPath, '', 0, 'HEVC', 'I420', ipperiod)
    parseLog(testLog, 'HEVC')
    formatTR(0, 1, '', 'HEVC I/P frame')
    writelogs('enc', 'HEVC')
    
    #VP8
    ipperiod=0
    yamiEncodeTest(yamiEncodeYuvPath, '', 0, 'VP8', 'I420', ipperiod=0)
    parseLog(testLog, 'VP8')
    formatTR(0, 1, '', 'VP8')
    writelogs('enc', 'VP8')

    #JPG
    ipperiod=0
    yamiEncodeTest(yamiEncodeYuvPath, '', 0, 'JPEG', 'I420', ipperiod=0)
    parseLog(testLog, 'JPEG')
    formatTR(0, 1, '', 'JPEG')
    writelogs('enc', 'JPEG')

    tableContent += tableEnd
    log(summaryLog, tableContent)
    tableContent = ''

    #TranscodecodePerformance Test
    inputfile = mediaFilesPath + '/performance/2000F-intraperiod32-ipperiod3-CBR-4096Kbps_1920x1080.264'
    outputdir = rootPath + '/' + yamiUtils + '/testscripts' + '/encode_performance_temp'
    save=1
    waynum=1
    yamiEncodePerformanceTest(inputfile, outputdir, codecs[0], waynum, save)
    parseResultPerformanceTest(inputfile, outputdir, codecs[0], waynum)    
    
    inputfile = mediaFilesPath + '/performance/2000F-intraperiod32-ipperiod3-CBR-4096Kbps_1920x1080.264'
    outputdir = rootPath + '/' + yamiUtils + '/testscripts' + '/encode_performance_temp'
    save=1
    waynum=8
    yamiEncodePerformanceTest(inputfile, outputdir, codecs[0], waynum, save)
    parseResultPerformanceTest(inputfile, outputdir, codecs[0], waynum)

    inputfile = mediaFilesPath + '/performance/2000F-intraperiod32-CBR-2048Kbps_1920x1080.265'
    outputdir = rootPath + '/' + yamiUtils + '/testscripts' + '/encode_performance_temp'
    save=1
    waynum=1
    yamiEncodePerformanceTest(inputfile, outputdir, codecs[1], waynum, save)
    parseResultPerformanceTest(inputfile, outputdir, codecs[1], waynum)

    inputfile = mediaFilesPath + '/performance/2000F-intraperiod32-CBR-2048Kbps_1920x1080.265'
    outputdir = rootPath + '/' + yamiUtils + '/testscripts' + '/encode_performance_temp'
    save=1
    waynum=8
    yamiEncodePerformanceTest(inputfile, outputdir, codecs[1], waynum, save)
    parseResultPerformanceTest(inputfile, outputdir, codecs[1], waynum)

    writeEmailListPerformanceTest()
    log(summaryLog, tableContent)
    tableContent = ''

    #send email
    deEncodeResultMatch = checkDeEncodeLog()
    
    if deEncodeResultMatch:
    	mail(0)
    else:
    	mail(0)
    mergeLog()
