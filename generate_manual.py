import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Devanagari and Gujarati fonts
pdfmetrics.registerFont(TTFont('Devanagari', '/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('Gujarati', '/System/Library/Fonts/Supplemental/Gujarati Sangam MN.ttc', subfontIndex=0))

# Page content: title, screenshot path, and instructions in English, Hindi, Gujarati
pages_content = [
    {
        "title": "Dashboard Overview",
        "screenshot": "/Users/codekajugad/Downloads/Vastrenix App UI.pdf",
        "page_num": 1,
        "en": "1. Daily Sales Overview\n2. Track Expenses/Income\n3. View Recent Activity",
        "hi": "1. आज की बिक्री\n2. ख़र्च/आय ट्रैक करें\n3. हाल की गतिविधियाँ",
        "gu": "1. આજનું વેચાણ\n2. ખર્ચ/આવક જુઓ\n3. તાજેતરની પ્રવૃત્તિઓ"
    },
    {
        "title": "Creating a Retail Bill",
        "screenshot": "/Users/codekajugad/Downloads/Vastrenix App UI.pdf",
        "page_num": 2,
        "en": "1. Click 'New Sale'\n2. Scan or search items\n3. Checkout and Collect Payment",
        "hi": "1. 'नया बिल' खोलें\n2. आइटम स्कैन/खोजें\n3. पेमेंट लेकर बिल पूरा करें",
        "gu": "1. 'નવું બિલ' ખોલો\n2. આઇટમ સ્કૅન/શોધો\n3. પેમેન્ટ લઈને બિલ પૂરું કરો"
    }
]

def create_manual(output_filename="Vastrenix_User_Manual.pdf"):
    c = canvas.Canvas(output_filename, pagesize=A4)
    width, height = A4

    for page in pages_content:
        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, f"Vastrenix: {page['title']}")

        # Screenshot Area (placeholder box)
        c.rect(100, 300, width-200, 400, stroke=1, fill=0)
        c.setFont("Helvetica", 12)
        c.drawString(120, 500, "[Placeholder: App Screenshot]")

        # Instructions
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 250, "English:")
        c.setFont("Helvetica", 12)
        text = c.beginText(50, 230)
        for line in page['en'].split('\n'):
            text.textLine(line)
        c.drawText(text)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(300, 250, "Hindi:")
        c.setFont("Devanagari", 12)
        text_hi = c.beginText(300, 230)
        for line in page['hi'].split('\n'):
            text_hi.textLine(line)
        c.drawText(text_hi)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(300, 180, "Gujarati:")
        c.setFont("Gujarati", 12)
        text_gu = c.beginText(300, 160)
        for line in page['gu'].split('\n'):
            text_gu.textLine(line)
        c.drawText(text_gu)

        c.showPage()

    c.save()
    print(f"Generated {output_filename}")

if __name__ == "__main__":
    create_manual()