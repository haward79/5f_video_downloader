
from pycurl import Curl
from io import BytesIO
import os
import sys
import subprocess

kMaxVideoName = 100
gVideoId = 0

def formatDirectoryPath(path: str) -> str:

    if path.endswith('/'):
        return path
    else:
        return path + '/'



def readUrl() -> str:
    
    while(True):

        url = input('Please input url: ')

        if url == '':

            return ''

        elif url.startswith('http://') or url.startswith('https://'):

            if url.count('www.porn5f.com/video/') == 1:
                print('Accept url: ' + url)
                return url
            else:
                print('Invalid url format. Please check the web page is a 5f video page.')

        else:
            print('Invalid url format. The url must starts with "http" or "https" .')

        print()



def curlGet(url: str) -> bytes:
    
    # Generate objects.
    data = BytesIO()
    curl = Curl()

    # Setup curl.
    curl.setopt(curl.URL, url)
    curl.setopt(curl.WRITEDATA, data)
    curl.setopt(curl.FOLLOWLOCATION, True)
    curl.setopt(curl.HTTPHEADER, ['User-Agent: curl/7.68.0'])

    # Send curl request.
    curl.perform()
    curl.close()

    return data.getvalue()



def getVideoFor5f(url: str) -> str:
    
    sourceCode = curlGet(url).decode('utf-8')
    mp4StrPos = sourceCode.find('.mp4')

    # ".mp4" is found.
    if mp4StrPos != -1:

        # Fetch video url.
        startPos = sourceCode[0:mp4StrPos].rfind('"')
        endingPos = sourceCode[mp4StrPos:].find('"')

        if startPos != -1 and endingPos != -1:

            videoUrl = sourceCode[startPos+1:mp4StrPos+endingPos]

            print('Video url fetched:', videoUrl)
            return videoUrl

        else:

            print('Video url is found, but failed to fetch.')

    else:

        print('Video url not found in the web page.')

    return ''



def generateVideoName(url: str, directoryPath: str = './') -> str:

    global gVideoId
    id = 0
    videoName = ''
    temp = ''

    sourceCode = curlGet(url).decode('utf-8')

    startPos = sourceCode.find('<title>')
    endingPos = sourceCode.find('</title>', startPos)

    if startPos != -1 and endingPos != -1:
        videoName = sourceCode[startPos+7:endingPos]
        videoName = videoName.replace('  ', '')

        # Truncate &*; .
        while True:

            ampPos = videoName.find('&')
            semiPos = videoName.find(';', ampPos)

            if ampPos == -1 or semiPos == -1:
                break
            else:
                videoName = videoName[0:ampPos] + videoName[semiPos+1:]

        # Truncate & and ;
        videoName = videoName.replace('&', '_')
        videoName = videoName.replace(';', '_')

        # Shorten too long file name.
        if len(videoName) > kMaxVideoName:
            videoName = videoName[0:kMaxVideoName]

    if videoName != '':
        temp = videoName
        
    while True:

        # Check already exists filename and invalid filename.
        if videoName == '' or os.path.isfile(directoryPath+videoName+'.m3u8') or os.path.isfile(directoryPath+videoName+'.mp4'):
            pass
        else:
            break

        if temp != '':
            id += 1
            videoName = temp + ' (' + str(id) + ')'
        else:
            gVideoId += 1
            videoName = str(gVideoId)

    return videoName



def downloadFileFor5f(url: str, directoryPath: str, filename: str) -> bool:

    print('Video name is set to "' + filename + '" .')

    fullPathWithoutExtname = directoryPath + filename

    subprocess.run(['wget', url, '-O', fullPathWithoutExtname+'.m3u8'])

    if os.path.isfile(fullPathWithoutExtname+'.m3u8') and os.stat(fullPathWithoutExtname+'.m3u8').st_size > 0:
        print('Playlist downloaded successfully.', 'Next, start to convert video to mp4.', sep='\n')
        subprocess.run(['ffmpeg', '-protocol_whitelist', 'file,crypto,https,tls,tcp', '-i', fullPathWithoutExtname+'.m3u8', fullPathWithoutExtname+'.mp4'])
    else:
        print('Failed to download video play list or the play list is corrupted.')

        try:
            os.remove(fullPathWithoutExtname+'.m3u8')
        except FileNotFoundError:
            pass

        return False

    if os.path.isfile(fullPathWithoutExtname+'.mp4') and os.stat(fullPathWithoutExtname+'.mp4').st_size > 0:
        os.remove(fullPathWithoutExtname+'.m3u8')
        print('Video converted to mp4.')
        return True
    else:
        print('Failed to convert video to mp4.')

        try:
            os.remove(fullPathWithoutExtname+'.m3u8')
            os.remove(fullPathWithoutExtname+'.mp4')
        except FileNotFoundError:
            pass

        return False



def initialize() -> str:

    directoryPath = './'

    choice = input('Do you want to set custom directory to save downloaded videos? [y/N] ')

    if choice.lower() == 'y':
        directoryPath = formatDirectoryPath(input('Please input directory path: '))

    return directoryPath



"""
    Main.
"""

countUrls = 0
urls = []
directoryPath = initialize()

countSuccess = 0
countFailed = 0
failedUrls = []

print('Please enter urls (one url per line): ')

# Read all urls.
while True:
    
    print('\nurl [' + str(countUrls) + '] > ')
    url = readUrl()

    if url == '':
        break
    else:
        urls.append(url)
        countUrls += 1

print()

# Process each url.
for i in range(countUrls):

    print('== Video download [{}] =='.format(i))
    
    url = urls[i]
    filename = generateVideoName(url, directoryPath)
    videoUrl = getVideoFor5f(url)

    if downloadFileFor5f(videoUrl, directoryPath, filename):
        print('Video download successfully.')
        countSuccess += 1
    else:
        print('Video download failed.')
        countFailed += 1
        failedUrls.append(url)

    print('All temp files cleared!')

# Print overview.
print('\n\nTotal: {} , Succeed: {} , Failed: {}'.format(len(urls), countSuccess, countFailed))

if countFailed > 0:

    print('All failed urls are stored in failed.txt .')

    with open('failed.txt', 'w') as fout:

        for i in failedUrls:
            fout.write(i + '\n')

