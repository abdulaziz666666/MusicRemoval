# 1.1
# soundfile, ffprobe, ffmpeg, demucs يتطلب تشغيل البرنامج ما يلي: بايثون 3.9.0 والمكتبات 
# لا يتطلب البرنامج أي اتصال بالانترنت بعد تحميل متطلباته

'''
:(الظاهرة) الأخطاء الحالية
-   (تم الإصلاح) ظهور شريط التحميل قبل اختيار المقطع
-   (تم الإصلاح) عدم اختفاء شريط التحميل بعدما تظهر رسالة نجاح العملية
-   (تم الإصلاح) عدم اختفاء عناصر الواجهة عند اختيار مقطع آخر بعد المقطع الأول
-   لا يمكن إظهار موقع المقطع المعدل  

:الأخطاء بعد التجارب
-   عند اختيار مقطع آخر، لا تتم إعادة ضبط شريط التحميل
    كذلك تظهر ،guidingLabel ويظهر ملصق نصي جديد بدلا عن
    (تم الإصلاح) الأزرار الخاصة بعرض المقطع أو موقعه

:ملاحظات
-   سأبقي الأخطاء التي تم إصلاحها في حال ظهرت بسبب حالة استثنائية

-   للتدقيق في debugMode يمكنك في السطر 179 تفعيل وضع التصحيح 
    .الملفات المتعلقة بعمليات البرنامج من استخراج الصوت وفصل الموسيقا

-   على مجلد مسمى باسم الملف الصوتي، بداخله htdemucs يحتوي مجلد
    تحتوي على الأصوات البشرية والأصوات vocal.mp3, novocal.mp3 ملفات
    .غير البشرية
'''

from tkinter import Tk, Button, Label, Frame
from tkinter.ttk import Progressbar
from tkinter.filedialog import askopenfile
from tkinter.messagebox import showwarning, showerror
from subprocess import run, Popen, PIPE, CalledProcessError
from os import chdir, remove
from shutil import rmtree



########    الثوابت والدوال   ########

BG = '#222244'
itemsBG = "#217AB9"
itemsFG = "white"
LABEL_ATTRS = {'bg':BG, 'fg':itemsFG}
BTN_ATTRS = {'bg':itemsBG, 'fg':itemsFG}
BTN_PACK_ATTRS = {'ipadx':20, 'ipady':3, 'pady':30}

def getVideo():
    global inputVideo
    
    inputVideo = askopenfile(mode='r', filetypes=[('ملفات فيديو', '*.mp4 *.mov *.mkv')])

    if not inputVideo:
        showwarning('تنبيه', 'لم يتم اختيار أي ملف')
        return
    
    elif not inputVideo.name.endswith('.mp4'):
        showwarning('تنبيه', '.ربما لا تتم العملية بنجاح لأن صيغة الملف مختلفة\n(.mp4) الرجاء أن يكون الملف المختار بصيغة')
    
    extractAudio()    

def extractAudio():
    global SOURCE_LINK, inputVideo, inputAudioFullName, progressbar, progress, guidingLabel, openLinkBtn, openOutputVideoBtn
    
    SOURCE_LINK = inputVideo.name.rsplit("/", 1)[0]
    inputAudioFullName = inputVideo.name.rsplit(sep='.', maxsplit=1)[0] + '.wav'

    try:
        if guidingLabel and openLinkBtn and openOutputVideoBtn: # في حال وجودهم

            interfaceItems = (guidingLabel, openLinkBtn, openOutputVideoBtn)
            for _ in interfaceItems:
                _.destroy()
    
    except NameError: # في حال كان أول استخدام
        pass 

    extractingAudioCommand = [
        'ffmpeg', '-i', inputVideo.name,
        '-vn',                          # تجاهل الفيديو
        '-acodec', 'pcm_s16le',         # كودك wav قياسي
        '-ar', '44100',                 # 44100hz معدل عينات 
        inputAudioFullName,
        '-y'                            # الكتابة فوق الملف إذا موجود
    ]

    progressbar = Progressbar(fr, orient='horizontal', length=200)
    progressbar.pack(padx=20, pady=(0, 5))
    
    guidingLabel = Label(fr, LABEL_ATTRS, text='..جاري استخراج الصوت')
    guidingLabel.pack(pady=(0, 10))

    try:
        run(extractingAudioCommand, shell=True)

        guidingLabel.config(text='..جاري استخراج الصوت')
        app.update()

    except CalledProcessError:
        showerror('خطأ', '.حدث خطأ في عملية استخراج الصوت، حاول مجددا')
    
    else:
        separateAudio()

def separateAudio():
    global SOURCE_LINK, inputVideo, inputAudioFullName, outputFolder, guidingLabel, progressbar, progress

    guidingLabel.config(text='0%\n..جاري فصل الموسيقا')
    
    # أمر فصل الصوت إلى أصوات بشرية وأصوات غير بشرية
    separationCommand = [
        'demucs',
        '--mp3',
        '-o',
        SOURCE_LINK, # بافتراض أن ملف الصوت في نفس مسار ملف الفيديو
        '--two-stems=vocals',
        inputAudioFullName
    ]

    try:
        # إلا إنه لم يستمر كذلك shell=True كان يعمل بدون 
        # يمكنك إزالتها للتدقيق في مخرجاتها، مع أنه قد لا يعمل
        commandOutput = Popen(separationCommand, stderr=PIPE, text=True, shell=True) 
        
        for line in commandOutput.stderr:

            if '%' in line:
                
                progressEnd = line.find('%')
                progress = int(line[:progressEnd])
                guidingLabel.config(text=f'{progress}%\n..جاري فصل الموسيقا')
                progressbar['value'] = progress

                app.update()

        commandOutput.wait()
    
    except CalledProcessError:
        showerror('خطأ', '.حدث خطأ في عملية فصل الموسيقا، حاول مجددا')

    else:
        outputFolder = SOURCE_LINK + '/htdemucs/'
        audioFolderName = inputAudioFullName.rsplit(sep='/', maxsplit=1)[1].removesuffix('.wav')
        outputFolder += audioFolderName

        # print('SOURCE_LINK:\n', SOURCE_LINK)
        # print('inputVideo.name:\n', inputVideo.name)
        # print('inputAudioFullName:\n',inputAudioFullName)
        # print('outputFolder:\n', outputFolder)
        
        mergeVideoAndAudio()

def mergeVideoAndAudio():
    global inputVideo, inputAudioFullName, guidingLabel, progressbar, progress, outputFolder, outputVideo, openLinkBtn, openOutputVideoBtn
    
    outputVideo = inputVideo.name.rsplit(sep='.', maxsplit=1)[0] + '(بلا موسيقا).mp4' # output.mp4 -> output(بلا موسيقا).mp4
    outputAudio = outputFolder + '/vocals.mp3'

    mergingCommand = [
        'ffmpeg',
        '-i', inputVideo.name,
        '-i', outputAudio,
        '-map', '0:v:0',   # الفيديو من الملف الأول
        '-map', '1:a:0',   # الصوت من الملف الثاني
        '-c:v', 'copy',
        '-c:a', 'aac',
        outputVideo,
        '-y'
    ]

    try:
        run(mergingCommand, shell=True)
        outputVideoName = outputVideo.rsplit(sep='/', maxsplit=1)[1]
        guidingLabel.config(text=f'!تمت إزالة الموسيقا بنجاح\n\nاسم المقطع الجديد هو\n{outputVideoName}\nتم حفظه في مجلد المقطع الأصلي')

    except CalledProcessError:
        showerror('خطأ', '.حدث خطأ في عملية دمج الصوت والفيديو، حاول مجددا')
    
    else:
        openLinkBtn = Button(fr, BTN_ATTRS, text='فتح موقع المقطع', command=openLink)
        openLinkBtn.pack(BTN_PACK_ATTRS, pady=(20, 10))

        openOutputVideoBtn = Button(fr, BTN_ATTRS, text='فتح المقطع', command=openOutputVideo)
        openOutputVideoBtn.pack(BTN_PACK_ATTRS, pady=(0, 10))

        progressbar.destroy()
        
        debugMode = False
        if not debugMode:
            # في موقع المقطع الأصلي htdemucs يتم حذف ملف الصوت المستخرج من الفيديو الأصلي ومجلد فصل الموسيقا
            remove(inputAudioFullName)
            rmtree(SOURCE_LINK + '/htdemucs/')


def openLink():
    global SOURCE_LINK

    chdir(SOURCE_LINK)
    run('start .', shell=True) # هذا الأمر لا يعمل ويجب تغييره

def openOutputVideo():
    global outputVideo
    run(outputVideo, shell=True)



########    تهيئة الواجهة   ########

app = Tk()
app.title('مزيل الموسيقا')
app.iconbitmap('شعار مزيل الموسيقا.ico')

fr = Frame(app, bg=BG)
fr.pack(expand=True, fill='both', ipadx=5)

Label(fr, LABEL_ATTRS, text='قم باختيار المقطع لعزل الموسيقا عنه').pack(padx=30, pady=(20, 0))

selectingVidBtn = Button(fr, BTN_ATTRS, text='اختر', command=getVideo)
selectingVidBtn.pack(BTN_PACK_ATTRS)

app.mainloop()
