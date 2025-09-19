from tkinter import Tk, Button, Label, Frame
from tkinter.ttk import Progressbar
from tkinter.filedialog import askopenfile
from tkinter.messagebox import showwarning, showerror
from subprocess import run, Popen, PIPE, STDOUT, CalledProcessError
from json import loads
from re import search


########    الثوابت الدوال   ########


BG = '#222244'
itemsBG = "#217AB9"
itemsFG = "white"
ATTRS = {'bg':BG, 'fg':itemsFG}

def getVideo():
    global videoLink
    
    videoLink = askopenfile(mode='r', filetypes=[('ملفات فيديو', '*.mp4 *.mov *.mkv')])
    
    if not videoLink:
        showwarning('تنبيه', 'لم يتم اختيار أي ملف')
        return
    
    elif not videoLink.name.endswith('.mp4'):
        showwarning('تنبيه', '.ربما لا تتم العملية بنجاح لأن صيغة الملف مختلفة\n(.mp4) الرجاء أن يكون الملف المختار بصيغة')
    
    extractAudio()    

def extractAudio():
    global videoLink, audioLink, guidingLabel
    
    try:
        jsonVideoLen = run(['ffprobe',                  # برمجية
                        '-v', 'error',                  # عدم إظهار الملاحظات البرمجية
                        '-show_entries',                # للعرض فقط
                        'format=duration',              # صفة مدة الفيديو
                        '-of', 'json', videoLink.name], # JSON عرض ككائن 
                       stdout=PIPE, stderr=STDOUT)
        
        # وتحديد المدة وتحويلها إلى عدد صحيح JSON التعامل مع كائن 
        videoLen = float(loads(jsonVideoLen.stdout)['format']['duration']) 
        audioLink = f'{videoLink.name.rsplit(".", 1)[0]}.wav'
        
        commandOutput = Popen([
        'ffmpeg', '-i', videoLink.name,
        '-vn',                          # تجاهل الفيديو
        '-acodec', 'pcm_s16le',         # كودك wav قياسي
        '-ar', '44100',                 # 44100hz معدل عينات 
        audioLink,
        '-y'],                            # الكتابة فوق الملف إذا موجود
        stderr=PIPE, text=True)
        
        for line in commandOutput.stderr:

            if "time=" in line:

                finishedDuration = search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
                if finishedDuration:
                    h, m, s = finishedDuration.groups()
                    finishedDuration = int(h) * 3600 + int(m) * 60 + float(s)
                    
                    progress = (finishedDuration / videoLen) * 100
                    print(f"\rProgress: {progress:.2f}%", end="", flush=True)
                    progressbar['value'] = progress

        commandOutput.wait()

        print("\rProgress: 100%\t", flush=True)
        progressbar['value'] = 100

    except CalledProcessError:
        showerror('خطأ', '.حدث خطأ في عملية استخراج الصوت، حاول مجددا')
        return
    
    else:
        guidingLabel = Label(fr, ATTRS, text='تم استخراج الصوت')
        guidingLabel.pack(pady=(30, 10))
        print(audioLink)
        separateAudio()

def separateAudio():
    global videoLink, audioLink, guidingLabel

    outputFolder = 'separated'

    command = [
        'demucs',
        '--two-stems=vocals',
        '-o',
        outputFolder,
        audioLink
    ]

    run(command, shell=True)

    



########    تهيئة الواجهة   ########


app = Tk()
app.title('مزيل الموسيقا')

fr = Frame(app, bg=BG)

app.minsize(250, 200)
app.maxsize(250, 200)

fr.pack(expand=True, fill='both')


########    محتوى الواجهة   ########


# Label(fr, ATTRS,text='!مرحبًا بك في مزيل الموسيقا', font=('Helvatica', 12, 'bold')).pack(pady=(30, 10))

selectingVidBtn = Button(fr, ATTRS, bg=itemsBG, text='اختر', command=getVideo)
selectingVidBtn.pack(ipadx=20, ipady=3, pady=30)

progressbar = Progressbar(fr, orient='horizontal', length=200)
progressbar.pack()

app.mainloop()