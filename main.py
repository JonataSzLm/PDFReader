from pdfquery import PDFQuery
from lxml import etree
from PIL import Image, ImageDraw, ImageFont

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


def exportXml():
    try:
        data = pdf.tree
        dataXml = etree.tostring(data, pretty_print=True).decode('utf-8')
        with open(XML_PATH, 'w', encoding='utf-8') as fileXml:
            fileXml.write(dataXml)
            return True
    except:
        return False


def generateImage(elementsList):
    try:
        width, height = 600, 850

        image = Image.new('RGB', (width, height), color='white')

        draw = ImageDraw.Draw(image)
        
        for element in elementsList:
            draw.text((element.x0, element.y0), text=element.value, fill=(0, 0, 0))

        return image
    
    except Exception as e:
        print(e)
        return None

# exportXml()

pdf = PDFQuery(PDF_PATH, laparams={'all_texts': True})
pdf.load()
qtdPages = len([element.text for element in pdf.pq('LTPage')])


for page in range(qtdPages):
    pdf.load(page)

    elementsList = [ElementPDF(str(element.text).encode('ascii', 'ignore'), float(element.get('x0', '')), float(element.get('x1', '')), float(element.get('y0', '')), float(element.get('y1', '')), float(element.get('width', '')), float(element.get('height', ''))) for element in pdf.pq('LTTextLineHorizontal')]
    elementsList.extend([ElementPDF(str(element.text).encode('ascii', 'ignore'), float(element.get('x0', '')), float(element.get('x1', '')), float(element.get('y0', '')), float(element.get('y1', '')), float(element.get('width', '')), float(element.get('height', ''))) for element in pdf.pq('LTTextBoxHorizontal')])

    image = generateImage(elementsList)
    if image:
        image.save(f'{IMAGE_PATH}_pg{page}.png')
        print(f'Imagem da Pagina {page} foi salva com Sucesso!')
    else:
        print(f'Falha ao tentar salvar a imagem da pagina {page}!')

