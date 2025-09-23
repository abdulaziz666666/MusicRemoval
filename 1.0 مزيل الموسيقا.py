# 1.0
# أود في التحديثات القادمة تحسين واجهة البرنامج وتصحيح الأخطاء المحتملة وما إلى ذلك 
# soundfile, ffprobe, ffmpeg, demucs يتطلب بايثون 3.9.0 والمكتبات 

from tkinter import Tk, Button, Label, Frame
from tkinter.ttk import Progressbar
from tkinter.filedialog import askopenfile
from tkinter.messagebox import showwarning, showerror
from subprocess import run, Popen, PIPE, STDOUT, CalledProcessError
from json import loads
from re import search


########    الثوابت والدوال   ########


BG = '#222244'
itemsBG = "#217AB9"
itemsFG = "white"
ATTRS = {'bg':BG, 'fg':itemsFG}
# PROCCESSING_STAGES = {'استخراج الصوت':'تم استخراج الصوت بنجاح', 
#                       'فصل الموسيقا':'تم فصل الموسيقا بنجاح', 
#                       'دمج الصوت والفيديو':'تم دمج الصوت والفيديو بنجاح'
# }

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
    global SOURCE_LINK, inputVideo, inputAudioFullName, progress, guidingLabel
    
    SOURCE_LINK = inputVideo.name.rsplit("/", 1)[0]

    jsonVideoLen = run(['ffprobe',                  # برمجية
                    '-v', 'error',                  # عدم إظهار الملاحظات البرمجية
                    '-show_entries',                # للعرض فقط
                    'format=duration',              # صفة مدة الفيديو
                    '-of', 'json', inputVideo.name], # JSON عرض ككائن 
                    stdout=PIPE, stderr=STDOUT)
    
    # وتحديد المدة وتحويلها إلى عدد صحيح JSON التعامل مع كائن 
    videoLen = float(loads(jsonVideoLen.stdout)['format']['duration']) 
    inputAudioFullName = inputVideo.name.rsplit(sep='.', maxsplit=1)[0] + '.wav'

    extractingAudioCommand = [
        'ffmpeg', '-i', inputVideo.name,
        '-vn',                          # تجاهل الفيديو
        '-acodec', 'pcm_s16le',         # كودك wav قياسي
        '-ar', '44100',                 # 44100hz معدل عينات 
        inputAudioFullName,
        '-y'                            # الكتابة فوق الملف إذا موجود
    ]

    guidingLabel = Label(fr, ATTRS, text='0%\n..جاري استخراج الصوت')
    guidingLabel.pack(pady=(10))
    
    try:
        commandOutput = Popen(extractingAudioCommand, stderr=PIPE, text=True)

        for line in commandOutput.stderr:

            if "time=" in line:

                finishedDuration = search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                if finishedDuration:
                    h, m, s = finishedDuration.groups()
                    finishedDuration = int(h) * 3600 + int(m) * 60 + float(s)

                    progress = ((finishedDuration / videoLen) * 100) / 2
                    progress = round(progress, 1)
                    # print(f"\rProgress: {progress}%", end="", flush=True)
                    
                    progressbar['value'] = progress
                    guidingLabel.config(text=f'{progress}%\n..جاري استخراج الصوت')
                    app.update()

        commandOutput.wait()

    except CalledProcessError:
        showerror('خطأ', '.حدث خطأ في عملية استخراج الصوت، حاول مجددا')
    
    else:
        separateAudio()

def separateAudio():
    global SOURCE_LINK, inputVideo, inputAudioFullName, outputFolder, guidingLabel, progress

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
                progress = 50 + int(line[:progressEnd]) / 2
                progressbar['value'] = progress
                guidingLabel.config(text=f'{progress}%\n..جاري فصل الموسيقا')

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
    global inputVideo, guidingLabel, progress
    
    outputVideo = inputVideo.name.rsplit(sep='.', maxsplit=1)[0] + '(بلا موسيقا).mp4' # output.mp4 -> output(بلا موسيقا).mp4
    outputAudio = outputFolder + '/vocals.mp3'

    print(outputFolder)

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
        commandOutput = Popen(mergingCommand, stderr=PIPE, text=True)

        for line in commandOutput.stderr:
            if '[out#' in line:
                guidingLabel.config(text=f'{progress}%\n!تمت إزالة الموسيقا بنجاح')

    except CalledProcessError:
        showerror('خطأ', '.حدث خطأ في عملية دمج الصوت والفيديو، حاول مجددا')
    
    else:
        run(outputVideo, shell=True)


########    تهيئة الواجهة   ########


app = Tk()
app.title('مزيل الموسيقا')
app.minsize(250, 200)
app.maxsize(250, 200)

fr = Frame(app, bg=BG)
fr.pack(expand=True, fill='both')

selectingVidBtn = Button(fr, ATTRS, bg=itemsBG, text='اختر', command=getVideo)
selectingVidBtn.pack(ipadx=20, ipady=3, pady=30)

progressbar = Progressbar(fr, orient='horizontal', length=200)
progressbar.pack()

app.mainloop()
