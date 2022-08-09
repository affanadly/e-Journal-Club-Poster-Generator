import PySimpleGUI as sg
import os
import subprocess
from shutil import which
from doi2bib import *
from apppath import *
from datetime import datetime

sg.theme('DarkAmber')
root = fetch_path()

def fill_check(dictionary):
    empty = []
    for k,v in dictionary.items():
        if values[k] == '':
            empty.append(v)
    if len(empty) == 0:
        return True
    if len(empty) > 2:
        out = ', and '.join([', '.join(empty[:-1]),empty[-1]])
    elif len(empty) == 2:
        out = ' and '.join(empty)
    else:
        out = empty[0]
    sg.popup('Error:',out.capitalize()+'.')
    window['progress'].update(0)
    return False

def gen_filename(name,date):
    name = name.replace(' ','')
    date = date.split(' ')[1:3]
    date = date[0]+date[1][:3]
    return f'{name}_{date}'

def bib_to_dict(bib):
    temp = [i.strip() for i in bib.split(',\n')][1:]
    temp = [i.split('=') for i in temp]
    for i,r in enumerate(temp):
        temp[i] = [temp[i][0],'='.join(temp[i][1:])]
    temp = [[j.strip() for j in i] for i in temp]
    temp.insert(0,bib.split(',\n')[0].strip())
    temp[0] = ['ARTICLETYPE',temp[0].split('{')[0][1:]]
    return dict(temp)

def bib_check(bibtex,check_list=['author','title','year','url']):
    unavail = [item for item in check_list if item not in bibtex.keys()]
    if unavail != []:
        sg.popup('Error:',f'{", ".join(unavail).capitalize()} not present in bibtex')
        window['progress'].update(0)
        return False
    return True

def bib_swapname(bib):
    temp = [i.strip() for i in bib.split(',\n')]
    temp[0] = temp[0].split('{')
    temp[0][1] = '{main'
    temp[0] = ''.join(temp[0])
    return ',\n\t'.join(temp)
    
# logo
logo = [sg.Column([[sg.Image(filename=f'{root}/media/RCRL.png',subsample=4)]],
                 justification='center')]

# event details layout
eventdetails_header = [sg.Text('Event Details')]
presenter_row = [sg.Text('Presenter',size=(8,1)),
                 sg.InputText(key='presenter',tooltip="Presenter's name",
                              expand_x=True)]
date_row = [sg.Text('Date',size=(8,1)),
            sg.InputText(key='date',expand_x=True,
                         tooltip='Date of meeting (format: Day, DD/MM/YYYY)'),
            sg.CalendarButton('Select',size=(6,1),target='date',
                              format=('%A, %d %B %Y'))]
time_row = [sg.Text('Time:',size=(8,1)),
            sg.Combo(list(range(1,13)),default_value=11,key='time'),
            sg.Combo(['AM','PM'],default_value='AM',key='meridiem')]

# article details layout
doi_row = [sg.Text('DOI',size=(6,1)),
           sg.InputText(key='doi',expand_x=True,tooltip='DOI of article'),
           sg.Button('Search',size=(6,1),enable_events=True,key='search',
                     tooltip='Generate BibTeX using DOI')]
bibtex_row = [sg.Text('BibTeX',size=(6,1)),
              sg.Multiline('',key='bibtex',size=(50,8),expand_x=True,
                           tooltip=
            'BibTeX of article (requires title, author, year, journal, and url)'),
              sg.Button('Clear',size=(6,1),enable_events=True,key='clear bibtex')]
preprint_box = [sg.Checkbox('Pre-print',default=False,key='preprint')]

# custom details layout
customtitle_row = [sg.Text('Custom Title',size=(10,1)),
                   sg.InputText(key='custom title',expand_x=True,
                                tooltip='Custom title of the poster')]
url_row = [sg.Text('URL',size=(10,1)),
           sg.InputText(key='url',expand_x=True,tooltip='Related URL')]

customtitlewim_row = [sg.Text('Custom Title',size=(12,1)),
                   sg.InputText(key='custom title im',expand_x=True,
                                tooltip='Custom title of the poster')]
image_row = [sg.Text('Custom Image',size=(12,1)),
             sg.InputText(key='custom image',expand_x=True,
                          tooltip='Custom image for the poster'),
             sg.Button('Load Image',key='load image',size=(10,1))]

# tabs setup layout
article_tab = [sg.Tab('Article Details',[doi_row,bibtex_row,preprint_box],key='article')]
custom_tab = [sg.Tab('Custom Details',[customtitle_row,url_row],key='custom')]
customim_tab = [sg.Tab('Custom Details w/ Image',[customtitlewim_row,image_row],key='customim')]

tab_group = [sg.TabGroup([article_tab,custom_tab,customim_tab],key='selected tab')]

# save location layout
savelocation_row = [sg.Text('Save Location:',size=(10,1)),
                    sg.InputText(key='save location',expand_x=True,
                                 tooltip='Save location for generated poster'),
                    sg.Button('Save As',key='save as',size=(8,1))]

# action and progress bar layout
action_row = [sg.OK(),
              sg.Cancel(),
              sg.Push(),
              sg.ProgressBar(9,orientation='h',size=(25,5),key='progress',expand_x=True),
              sg.Push(),
              sg.Button('About',size=(5,1),enable_events=True,key='about'),
              sg.Button('⚙',enable_events=True,key='settings')]

# main layout
layout = [logo,
          eventdetails_header,
          presenter_row,
          date_row,
          time_row,
          tab_group,
          savelocation_row,
          action_row]

window = sg.Window('e-Journal Club Poster Generator v2',layout,
                   resizable=False,icon=f'{root}/media/RCRL.ico')

# app loop
while True:
    event,values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break
    
    # about button
    if event == 'about':
        about_window = sg.Window('About',layout=[[sg.Text("""
            e-Journal Club Poster Generator v1.1
            GitHub: https://github.com/affanadly/e-Journal-Club-Poster-Generator
            
            Created for the Radio Cosmology Research Laboratory, Universiti Malaya.
            Original design by: Shazwan Radzi
            LaTeX-ed by: Affan Adly
            Python-ed by: Affan Adly
            Tested by: Affan Adly, Abdul Kadir
            
            Contact Affan Adly on GitHub for any issues or suggestions.
            """)],[sg.Button('OK',key='exit about')]])
        while True:
            about_event,about_values = about_window.read()
            if about_event == 'exit about':
                about_window.close()
                break
            if about_event == sg.WIN_CLOSED:
                break
        continue
    
    # save as button
    if event == 'save as':
        if fill_check({
            'presenter' : 'presenter name not entered',
            'date' : 'date not selected'
        }):
            window['save location'].update(sg.tk.filedialog.asksaveasfilename(
                defaultextension='pdf',
                filetypes=(("PDF File", "*.pdf"),),
                initialfile=gen_filename(values['presenter'],values['date']),
                parent=window.TKroot,
                title="Save As"
            ))
            
    # bibtex search
    if event == 'search':
        if values['doi'] != '':
            doigrab = grab(values['doi'].strip())
            if doigrab[0] == 'Success' and doigrab[1][0] != '<':
                bibtex = doigrab[1]
                bibtex = bibtex.replace('%2F','/')
                window['bibtex'].update(bibtex)
            else:
                sg.popup('Error:','DOI not found')
        else:
            sg.popup('Error: DOI is empty')
    
    # clearing bibtex
    if event == 'clear bibtex':
        window['bibtex'].update('')
          
    # advanced settings
    if event == 'settings':
        # layout
        with open(f'{root}/latex/settings.tex','r',encoding='utf-8') as f:
            settings = f.read().split('\n')
            settings[0] = settings[0][25:-1]
            settings[1] = settings[1][26:-1]
            settings[2] = settings[2][26:-1]
            settings[3] = settings[3][26:-1]
            settings[4] = settings[4][27:-1]
            settings[5] = settings[5][27:-1]
        
        settings_window = sg.Window('Settings',layout=[
            [sg.Text('Text under QR code')],
            [sg.InputText(settings[0],size=(50,2),key='qrtxt')],
            [sg.Text('Meeting link')],
            [sg.InputText(settings[1],size=(50,2),key='link')],
            [sg.Text('Text for meeting link')],
            [sg.InputText(settings[2],size=(50,2),key='linktxt')],
            [sg.Text("Contact person's name")],
            [sg.InputText(settings[3],size=(50,2),key='cont')],
            [sg.Text("Contact person's phone number")],
            [sg.InputText(settings[4],size=(50,2),key='contno')],
            [sg.Text("Contact person's email address")],
            [sg.InputText(settings[5],size=(50,2),key='contem')],
            [sg.OK(),sg.Cancel(),sg.Push(),sg.Button('Reset',enable_events=True,key='reset')]])
        while True:
            settings_event,settings_values = settings_window.read()
            if settings_event == 'Cancel':
                settings_window.close()
                break
            if settings_event == sg.WIN_CLOSED:
                break
                
            if settings_event == 'OK':
                for i in range(6):
                    if settings_values[i] == '':
                        sg.popup('Error:','Field(s) cannot be empty')
                        continue
                with open(f'{root}/latex/settings.tex','w',encoding='utf-8') as f:
                    f.write(r'\newcommand{\qrcodetext}{'+f'{settings_values["qrtxt"]}'+r'}'+'\n')
                    f.write(r'\newcommand{\meetinglink}{'+f'{settings_values["link"]}'+r'}'+'\n')
                    f.write(r'\newcommand{\meetingtext}{'+f'{settings_values["linktxt"]}'+r'}'+'\n')
                    f.write(r'\newcommand{\contactname}{'+f'{settings_values["cont"]}'+r'}'+'\n')
                    f.write(r'\newcommand{\contactphone}{'+f'{settings_values["contno"]}'+r'}'+'\n')
                    f.write(r'\newcommand{\contactemail}{'+f'{settings_values["contem"]}'+r'}'+'\n')
                settings_window.close()
                break
                
            if settings_event == 'reset':
                with open(f'{root}/latex/backup.txt','r',encoding='utf-8') as f:
                    backup = f.read().split('\n')
                    settings_window['qrtxt'].update(backup[0])
                    settings_window['link'].update(backup[1])
                    settings_window['linktxt'].update(backup[2])
                    settings_window['cont'].update(backup[3])
                    settings_window['contno'].update(backup[4])
                    settings_window['contem'].update(backup[5])
                    
    # load image for custom poster
    if event == 'load image':
        window['custom image'].update(sg.tk.filedialog.askopenfilename(
                filetypes=(("Images", ["*.jpg","*.jpeg","*.png","*.eps"]),
                           ("All Files (use with caution)","*.*")),
                parent=window.TKroot,
                title="Load Custom Image"
            ))
                    
    # main
    if event == 'OK':
        window['progress'].update(0)
        
        # check if latex installation exists
        if which('lualatex') == None or which('biber') == None:
            sg.popup('Error:','LaTeX is not installed')
            continue
        window['progress'].update(1)
        
        # check for event details
        if not fill_check({
            'presenter' : 'presenter name not entered',
            'date' : 'date not selected',
            'save location' : 'save location not specified'
        }):
            continue
        window['progress'].update(2)
        
        # create input tex file
        with open(f'{root}/latex/details.tex','w',encoding='utf-8') as f:
            f.write(r'\newcommand{\details}{'+f'{values["date"].split(", ")[0].upper()} | {values["date"].split(", ")[1].upper()} | {values["time"]} {values["meridiem"].upper()}'+r'}'+'\n')
            f.write(r'\newcommand{\presenter}{'+f'{values["presenter"].upper()}'+r'}'+'\n')
        
        window['progress'].update(3)
        
        # for usual poster
        if values['selected tab'] == 'article':
            # check if bibtex is empty
            if not fill_check({
                'bibtex' : 'bibtex is empty'
            }):
                continue
            
            bibtex = values['bibtex']
             
            # small issue with Astronomy and Astrophysics journal bibtex
            bibtex = bibtex.replace(r'{\&}amp$\mathsemicolon$',r'\&')
            
            bibtex_d = bib_to_dict(bibtex)
            
            # check fields in bibtex
            if not bib_check(bibtex_d):
                continue
                
            # create title command    
            if bibtex_d['ARTICLETYPE'] == 'article':
                if 'journal' not in bibtex_d.keys():
                    sg.popup('Error:','Journal name not present in bibtex')
                    window['progress'].update(0)
                    continue
                else:
                    if 'volume' in bibtex_d.keys():
                        if 'number' in bibtex_d.keys():
                            title = r'\citefield{main}{title}, \citefield{main}{journaltitle}, \citefield{main}{volume} (\citefield{main}{number}), (\NoHyper\cite{main})'
                        else:
                            title = r'\citefield{main}{title}, \citefield{main}{journaltitle}, \citefield{main}{volume}, (\NoHyper\cite{main})'
                    elif 'number' in bibtex_d.keys():
                        title = r'\citefield{main}{title}, \citefield{main}{journaltitle} (\citefield{main}{number}), (\NoHyper\cite{main})'
                    else: 
                        title = r'\citefield{main}{title}, \citefield{main}{journaltitle}, (\NoHyper\cite{main})'

            elif bibtex_d['ARTICLETYPE'] == 'misc':
                if values['preprint'] == True:
                    if 'publisher' in bibtex_d.keys():
                        title = r'\citefield{main}{title}, \citelist{main}{publisher} (pre-print), (\NoHyper\cite{main})'
                    else:
                        title = r'\citefield{main}{title} (pre-print), (\NoHyper\cite{main})'
                else:
                    if 'publisher' in bibtex_d.keys():
                        title = r'\citefield{main}{title}, \citelist{main}{publisher}, (\NoHyper\cite{main})'
                    else:
                        title = r'\citefield{main}{title}, (\NoHyper\cite{main})'

            elif bibtex_d['ARTICLETYPE'] == 'conference' or bibtex_d['ARTICLETYPE'] == 'inproceedings':
                if 'booktitle' in bibtex_d.keys():
                    if 'pages' in bibtex_d.keys():
                        title = r'\citefield{main}{title}, \citefield{main}{booktitle}, (pp.\citefield{main}{pages}), (\NoHyper\cite{main})'
                    else:
                        title = r'\citefield{main}{title}, \citefield{main}{booktitle}, (\NoHyper\cite{main})'
                else:
                    if 'pages' in bibtex_d.keys():
                        title = r'\citefield{main}{title}, (pp.\citefield{main}{pages}), (\NoHyper\cite{main})'
                    else:
                        title = r'\citefield{main}{title}, (\NoHyper\cite{main})'

            elif bibtex_d['ARTICLETYPE'] == 'inbook':
                if 'chapter' not in bibtex_d.keys():
                    sg.popup('Error:','Chapter title not present in bibtex')
                    window['progress'].update(0)
                    continue
                elif 'pages' not in bibtex_d.keys():
                    sg.popup('Error:','Page number not present in bibtex')
                    window['progress'].update(0)
                    continue
                else:
                    if 'volume' in bibtex_d.keys() and 'series' in bibtex_d.keys():
                        title = r'\citefield{main}{chapter}, In \citefield{main}{title}, volume \citefield{main}{volume} of \citefield{main}{series}, (pp.\citefield{main}{pages}), (\NoHyper\cite{main})'
                    else:
                        title = r'\citefield{main}{chapter}, In \citefield{main}{title}, (pp.\citefield{main}{pages}), (\NoHyper\cite{main})'
            
            # add fulltitle and refurl to details.tex
            with open(f'{root}/latex/details.tex','a',encoding='utf-8') as f:
                f.write(r'\newcommand{\fulltitle}{'+f'{title}'+r'}'+'\n')
                f.write(r'\newcommand{\accompany}{\qr{'+f'{bibtex_d["url"][1:-1]}'+r'}}'+'\n')
            
            # change bibitem name to main and write bibfile ref.bib
            with open(f'{root}/latex/ref.bib','w',encoding='utf-8') as f:
                f.write(bib_swapname(bibtex))
        
            # add bibliography to details.tex
            with open(f'{root}/latex/details.tex','a',encoding='utf-8') as f:
                f.write(r'\addbibresource{ref.bib}')
            
        # for custom poster
        if values['selected tab'] == 'custom':
            # check for custom title and url
            if not fill_check({
                'custom title' : 'custom title is empty',
                'url' : 'url is empty'
            }):
                continue
            
            # add custom title and qr code
            with open(f'{root}/latex/details.tex','a',encoding='utf-8') as f:
                f.write(r'\newcommand{\fulltitle}{'+f'{values["custom title"]}'+r'}'+'\n')
                f.write(r'\newcommand{\accompany}{\qr{'+f'{values["url"]}'+r'}}'+'\n')
                
        # for custom poster with image
        if values['selected tab'] == 'customim':
            # check for custom title and image
            if not fill_check({
                'custom title im' : 'custom title is empty',
                'custom image' : 'custom image is not selected'
            }):
                continue
            
            # copy image to latex folder
            custom_image = values['custom image'].replace('/','\\')
            subprocess.call(f'echo "{custom_image}" '+r'".\latex\media"',shell=True)
            subprocess.call(f'copy "{custom_image}" '+r'".\latex\media"',shell=True)
            custom_image = custom_image.split('\\')[-1]
            
            # add custom title and image
            with open(f'{root}/latex/details.tex','a',encoding='utf-8') as f:
                f.write(r'\newcommand{\fulltitle}{'+f'{values["custom title im"]}'+r'}'+'\n')
                f.write(r'\newcommand{\accompany}{\image{media/'+f'{custom_image}'+r'}}'+'\n')
                
        window['progress'].update(4)
        
        # compile latex poster
        current_dir = root
        os.chdir(current_dir+'/latex')
        subprocess.call('lualatex main.tex',shell=True)
        window['progress'].update(5)
        
        subprocess.call('biber main',shell=True)
        window['progress'].update(6)
        
        subprocess.call('lualatex main.tex',shell=True)
        window['progress'].update(7)
        
        subprocess.call('lualatex main.tex',shell=True)
        window['progress'].update(8)
        
        os.chdir(current_dir)
        save_location = values['save location']
        os.system(f'copy "latex\main.pdf" "{save_location}"')
        window['progress'].update(9)
        
        # deleting custom image
        if values['selected tab'] == 'customim':
            # custom_image = ('./latex/media/'+custom_image).replace('/','\\')
            print(custom_image)
            subprocess.call(r'del ".\latex\media'+'\\'+f'{custom_image}"',shell=True)
            
        # opening poster
        subprocess.call(save_location,shell=True)
        
# cleaning temporary files once program is closed
for file in ['main.aux','main.bbl','main.bcf','main.blg','main.log',
             'main.out','main.pdf','main.run.xml','ref.bib','details.tex']:
    subprocess.call(f'del latex\\{file}',shell=True)
    