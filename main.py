import PySimpleGUI as sg
import os
from shutil import which
from doi2bib import *
from apppath import *

root = fetch_path()

sg.theme('DarkAmber') # Default1
layout = [[sg.Column([[sg.Image(filename=f'{root}/media/RCRL_small.png')]],justification='center')],
          [sg.Text('Event Details')],
          [sg.Text('Presenter:'),sg.InputText(key='presenter',tooltip="Presenter's name",expand_x=True)],
          [sg.Text('Date:'),sg.CalendarButton('Select',target='date',format=('%A, %d %B %Y')),sg.InputText('',key='date',expand_x=True,tooltip="Date of meeting (format: Day, DD/MM/YYYY)",)],
          [sg.Text('Time:'),sg.Combo(list(range(1,13)),default_value=11,key='time'),
           sg.Combo(['AM','PM'],default_value='AM',key='meridiem')],
          [sg.Text()],
          [sg.Text('Article Details')],
          [sg.Text('DOI:',size=(5,1)),sg.InputText(key='doi',expand_x=True,tooltip="DOI of article"),
           sg.Button('Search',size=(6,1),enable_events=True,key='Search',
                     tooltip="Generate BibTeX using DOI")],
          [sg.Text('BibTeX:',size=(5,1)),sg.Multiline('',key='bibtex',size=(50,8),expand_x=True,tooltip="BibTeX of article (requires title, author, year, journal, and url)"),sg.Button('Clear',size=(6,1),enable_events=True)],
          [sg.Text('or')],
          [sg.Text('Custom Title:'),sg.InputText(key='custom title',expand_x=True,tooltip="Custom title of the poster")],
          [sg.Text('URL:'),sg.InputText(key='url',expand_x=True,tooltip="Related URL")],
          [sg.Text()],
          [sg.Text('Save Location:'),sg.InputText(key='save location',expand_x=True),
           sg.FileSaveAs(file_types=(("PDF File",".pdf"),))],
          [sg.ProgressBar(8,orientation='h',size=(10,20),key='progress',expand_x=True),sg.Text('Idle.',key='progress text')],
          [sg.OK(),sg.Cancel()]]

window = sg.Window('e-Journal Club Poster Generator v1',layout,resizable=True,icon=f'{root}/media/RCRL.ico')

while True:
    event,values = window.read()
    
    if event == sg.WIN_CLOSED or event == 'Cancel':
        break
        
    if event == 'Search':
        # grabbing bibtex using doi
        doigrab = grab(values['doi'])
        if doigrab[0] == 'Success':
            bibtex = doigrab[1]
        else:
            sg.popup('Error: ',doigrab[0])
            
        bibtex = bibtex[:bibtex.find(r'{')+1] + 'main' + bibtex[bibtex.find(r','):]
        bibtex = bibtex.replace('%2F','/')
        window['bibtex'].update(bibtex)
    
    if event == 'Clear':
        window['bibtex'].update('')
    
    if event == 'OK':
        window['progress'].update(0)
        window['progress text'].update('Processing...')
        
        # check if latex installation exists
        if which('lualatex') == None or which('biber') == None:
            window['progress text'].update('Error.')
            sg.popup('Error: ','LaTeX is not installed.')
            continue
        
        # check if fields are empty
        if values['presenter'] == '':
            window['progress text'].update('Error.')
            sg.popup('Error: ','Presenter name not entered.')
            continue
            
        if values['date'] == '':
            window['progress text'].update('Error.')
            sg.popup('Error: ','Date not selected.')
            continue
        
        if values['bibtex'] == '' and values['custom title'] == '' and values['url'] == '':
            window['progress text'].update('Error.')
            sg.popup('Error: ','No article details entered.')
            continue
        
        if values['bibtex'] == '' and values['url'] == '':
            window['progress text'].update('Error.')
            sg.popup('Error: ','No URL entered.')
            continue
            
        if values['bibtex'] == '' and values['custom title'] == '':
            window['progress text'].update('Error.')
            sg.popup('Error: ','No custom title entered.')
            continue
        
        if values['save location'] == '':
            window['progress text'].update('Error.')
            sg.popup('Error: ','No destination specified.')
            continue
            
        window['progress'].update(1)
        
        # split date and day
        date = values['date']
        date = date.split(', ')
        day, date = date[0],date[1]
        window['progress'].update(2)
        
        if values['bibtex'] == '':
            # create tex files for custom title
            with open(f'{root}/latex/input.tex','w',encoding='utf-8') as f:
                f.write(r'\newcommand{\details}{'+f'{day.upper()} | {date.upper()} | {values["time"]} {values["meridiem"].upper()}'+r'}'+'\n')
                f.write(r'\newcommand{\presenter}{'+f'{values["presenter"].upper()}'+r'}'+'\n')
                f.write(r'\newcommand{\articletype}{'+f'{values["custom title"]}'+r'}')

            with open(f'{root}/latex/paper.bib','w',encoding='utf-8') as f:
                f.write('@misc{main,'+'\n\t'+'url={'+f'{values["url"]}'+r'}'+'\n'+r'}')
            
        else:
            # confirming bibtex
            bibtex = values['bibtex']
            
            check = bibtex.split(',\n\t')[0].split('{')[0][1:]
            if check == 'incollection':
                articletype = 5
            else:
                field = [row.split(' =')[0] for row in bibtex.split(',\n\t')[1:]]
                if 'volume' in field:
                    if 'number' in field:
                        articletype = 1
                    else:
                        articletype = 2
                else:
                    if 'number' in field:
                        articletype = 3
                    else:
                        articletype = 4
            
            # check for important fields
            full_field = ['title','author','year','journal','url']
            field_err = []
            for f in full_field:
                if f not in field:
                    field_err.append(f)

            if len(field_err) != 0:
                field_err[0] = field_err[0].capitalize()
                window['progress'].update(0)
                window['progress text'].update('Error.')
                sg.popup('Error: ',f'{", ".join(field_err)} not in bibitem.')
                continue

            # create tex files for articles
            with open(f'{root}/latex/input.tex','w',encoding='utf-8') as f:
                f.write(r'\newcommand{\details}{'+f'{day.upper()} | {date.upper()} | {values["time"]} {values["meridiem"].upper()}'+r'}'+'\n')
                f.write(r'\newcommand{\presenter}{'+f'{values["presenter"].upper()}'+r'}'+'\n')
                f.write(r'\newcommand{\articletype}{'+f'{articletype}'+r'}')
        
            with open(f'{root}/latex/paper.bib','w',encoding='utf-8') as f:
                f.write(bibtex)
            
        window['progress'].update(3)
        
        # save location
        output_loc = values['save location']
        
        # compile latex poster
        current_dir = root
        os.chdir(current_dir+'/latex')
        os.system('lualatex poster.tex')
        window['progress'].update(4)
        
        os.system('biber poster')
        window['progress'].update(5)
        
        os.system('lualatex poster.tex')
        window['progress'].update(6)
        
        os.system('lualatex poster.tex')
        window['progress'].update(7)
        
        os.chdir(current_dir)
        os.system(f'copy "latex\poster.pdf" "{output_loc}"')
        window['progress'].update(8)
        window['progress text'].update('Done!')

window.close()