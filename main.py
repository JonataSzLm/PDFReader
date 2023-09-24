# -*- coding: utf-8 -*-

from pdfquery import PDFQuery
from lxml import etree
from PIL import Image, ImageDraw, ImageFont

from itertools import groupby
from operator import attrgetter
import json


class Statement:
    def __init__(self, date, memo, value):
        self.date = date
        self.memo = memo
        self.value = value


class ElementPDF:
    def __init__(self, value, x0, x1, y0, y1, w, h):
        self.value = value
        self.x0 = x0
        self.x1 = x1
        self.y0 = y0
        self.y1 = y1
        self.w = w
        self.h = h
        

PDF_PATH = './files/Extrato.pdf'
IMAGE_PATH = './files/Extrato'
XML_PATH = './files/Extrato.xml'
PROFILES_PATH = './files/profiles.json'
HEIGHT = 850


def exportXml():
    try:
        data = pdf.tree
        dataXml = etree.tostring(data, pretty_print=True).decode('utf-8')
        with open(XML_PATH, 'w', encoding='utf-8') as fileXml:
            fileXml.write(dataXml)
            return True
    except:
        return False


def generateImage(elementsList, textEnable=True, lineEnable=False, rectangleEnable=False):
    try:
        width, height = 600, HEIGHT

        image = Image.new('RGB', (width, height), color='white')

        draw = ImageDraw.Draw(image)

        for element in elementsList:
            
            if textEnable:
                draw.text((element.x0, element.y1), text=element.value, fill=(0, 0, 0))

            if lineEnable:
                draw.line((element.x0, element.y1, element.x0, element.y0,), fill=(0, 255, 0), width=1)
                draw.line((element.x1, element.y1, element.x1, element.y0,), fill=(255, 0, 0), width=1)

            if rectangleEnable:
                draw.rectangle([(element.x0, element.y1), (element.x1, element.y0)], outline=(255, 0, 0), width=1)
        


        return image
    
    except Exception as e:
        print(e)
        return None



def groupByY1(elementsList):
    elementsList.sort(key=attrgetter('y1'))
    lines = {key: list(group) for key, group in groupby(elementsList, key=attrgetter('y1'))}
    return lines


def loadProfile(bank):
    try:
        with open(PROFILES_PATH, 'r', encoding='utf-8') as file:
            profiles = json.loads(file.read())

        return profiles['banks'][bank]

    except Exception as e:
        print(e)
        return None


def extractTable(profile, elementsList, indexRow):
    skipNextRow = False

    date = ''
    memo = ''
    credit = ''
    debit = ''
    value = ''
    
    currentRow = [currentCol for currentCol in elementsList.get(indexRow, []) if currentCol.value]
    if len(currentRow) >= profile['minColumns']:
        for col in currentRow:
            if col.x0 >= profile['date']['x0'] and col.x1 <= profile['date']['x1'] and col.value:
                date = col.value

            if col.x0 >= profile['memo']['x0'] and col.x1 <= profile['memo']['x1'] and col.value:
                memo = col.value

            if col.x0 >= profile['credit']['x0'] and col.x1 <= profile['credit']['x1'] and col.value:
                credit = col.value

            if col.x0 >= profile['debit']['x0'] and col.x1 <= profile['debit']['x1'] and col.value:
                debit = col.value
        
    else:

        skipNextRow = True

        elements = sorted(elementsList, key=lambda x: x)
        for iel, element in enumerate(elements):
            if float(element) == float(indexRow):
                

                for i in range(profile['linesInRow']):
                    row = (elementsList[elements[iel + i]])
    
                    for col in row:
                        if col.x0 >= profile['date']['x0'] and col.x1 <= profile['date']['x1'] and col.value:
                            date += col.value

                        if col.x0 >= profile['memo']['x0'] and col.x1 <= profile['memo']['x1'] and col.value:
                            memo += col.value

                        if col.x0 >= profile['credit']['x0'] and col.x1 <= profile['credit']['x1'] and col.value:
                            credit += col.value

                        if col.x0 >= profile['debit']['x0'] and col.x1 <= profile['debit']['x1'] and col.value:
                            debit += col.value

                break

    value = credit if credit else debit
    statement = Statement(date, memo, value)

    return statement, skipNextRow



pdf = PDFQuery(PDF_PATH, laparams={'all_texts': True})
pdf.load()
qtdPages = len([element.text for element in pdf.pq('LTPage')])

# exportXml()
profile = loadProfile('iti')

statements = []

try:
    with open('saida.csv', 'w', encoding='utf-8') as file:
        file.write('Data;Descrição;Valor\n')
        for page in range(qtdPages):
            pdf.load(page)

            elementsList = [ElementPDF(str(element.text), float(element.get('x0', '')), float(element.get('x1', '')), ((-float(element.get('y0', ''))) + HEIGHT), ((-float(element.get('y1', ''))) + HEIGHT), float(element.get('width', '')), float(element.get('height', ''))) for element in pdf.pq('LTTextLineHorizontal')]
            elementsList.extend([ElementPDF(str(element.text), float(element.get('x0', '')), float(element.get('x1', '')), ((-float(element.get('y0', ''))) + HEIGHT), ((-float(element.get('y1', ''))) + HEIGHT), float(element.get('width', '')), float(element.get('height', ''))) for element in pdf.pq('LTTextBoxHorizontal')])

            startTableText = profile['startTable']
            endTableText = profile['endTable']

            startTable = [(-float(el.get('y1', ''))) + HEIGHT for el in pdf.pq(f'LTTextLineHorizontal:contains("{startTableText}")')]
            endTable = [(-float(el.get('y1', ''))) + HEIGHT for el in pdf.pq(f'LTTextLineHorizontal:contains("{endTableText}")')]

            newElementsList = groupByY1(elementsList)
        

            skipLastRow = False
            skipIndex = 0
            for indexYRow, yRow in enumerate(newElementsList):
                if float(yRow) > startTable[0] and float(yRow) < endTable[0]:
                    
                    if not skipLastRow:
                        statement, skipLastRow = extractTable(profile, newElementsList, yRow)
                        statements.append(statement)
                        
                        file.write(f'{statement.date};{statement.memo};{statement.value}\n')


                    if skipLastRow:
                        skipIndex += 1

                    if skipIndex >= profile['linesInRow']:
                        skipLastRow = False
                        skipIndex = 0
                    


except Exception as e:
    print(e)

                # row = newElementsList.get(yRow, [])
                # file.write(f'\nLinha: {yRow}\n')
                # for col in row:
                #     if col.value:
                #         file.write(f'{col.value}\t')

    # image = generateImage(elementsList, rectangleEnable=True)
    # if image:
    #     # image.save(f'{IMAGE_PATH}_pg{page}.png')
    #     image.show()
    #     print(f'Imagem da Pagina {page} foi salva com Sucesso!')
    # else:
    #     print(f'Falha ao tentar salvar a imagem da pagina {page}!')

