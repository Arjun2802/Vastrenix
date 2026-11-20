import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register fonts for Devanagari and Gujarati
pdfmetrics.registerFont(TTFont('Devanagari', '/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('Gujarati', '/System/Library/Fonts/Supplemental/Gujarati Sangam MN.ttc', subfontIndex=0))

# Define steps: each entry has title, screenshot page number, and instructions in 3 languages
steps = [
    {
        'title': 'Login & Store Selection',
        'page_num': 5,
        'en': '1. Enter your email and password.\n2. Click Continue.\n3. If you are a new user, create an account.\n4. Request access to a store via store code.',
        'hi': '1. अपना ईमेल और पासवर्ड दर्ज करें।\n2. कनेक्ट पर क्लिक करें।\n3. यदि आप नए हैं तो खाता बनाएं।\n4. स्टोर कोड से स्टोर का एक्सेस अनुरोध करें।',
        'gu': '1. તમારો ઇમેઇલ અને પાસવર્ડ દાખલ કરો.\n2. ચાલુ રાખો પર ક્લિક કરો.\n3. જો તમે નવા છો તો એકાઉન્ટ બનાવો.\n4. સ્ટોર કોડથી સ્ટોરનો ઍક્સેસ માંગો.'
    },
    {
        'title': 'Dashboard Overview',
        'page_num': 9,
        'en': 'View daily sales, expenses, and recent activity.\nUse the navigation menu to access other sections.',
        'hi': 'दैनिक बिक्री, खर्च और हाल की गतिविधि देखें।\nनेविगेशन मेनू का उपयोग करके अन्य सेक्शन पर जाएँ।',
        'gu': 'દૈનિક વેચાણ, ખર્ચ અને તાજેતરની પ્રવૃત્તિ જુઓ.\nનેવિગેશન મેનુનો ઉપયોગ કરીને અન્ય વિભાગોમાં જાઓ।'
    },
    {
        'title': 'Create a New Retail Bill',
        'page_num': 10,
        'en': '1. Tap “New Bill”.\n2. Scan or search items.\n3. Add customer details.\n4. Review totals and apply discounts if needed.',
        'hi': '1. “नया बिल” टैप करें।\n2. आइटम स्कैन या खोजें।\n3. ग्राहक विवरण जोड़ें।\n4. कुल राशि की समीक्षा करें और आवश्यक होने पर छूट लागू करें।',
        'gu': '1. “નવું બિલ” ટેપ કરો.\n2. આઇટમ સ્કૅન અથવા શોધો.\n3. ગ્રાહક વિગતો ઉમેરો.\n4. કુલ રકમની સમીક્ષા કરો અને જરૂરી હોય તો છૂટ લાગુ કરો।'
    },
    {
        'title': 'Checkout & Payment',
        'page_num': 11,
        'en': 'Choose payment method: Cash, UPI, Card, or Credit.\nConfirm the amount and complete the transaction.',
        'hi': 'भुगतान विधि चुनें: नकद, UPI, कार्ड, या क्रेडिट।\nराशि की पुष्टि करें और लेनदेन पूरा करें।',
        'gu': 'ચુકવણી પદ્ધતિ પસંદ કરો: રોકડ, UPI, કાર્ડ, અથવા ક્રેડિટ.\nરકમની પુષ્ટિ કરો અને વ્યવહાર પૂર્ણ કરો।'
    },
    {
        'title': 'Receipt & Invoice',
        'page_num': 12,
        'en': 'View the printed receipt.\nShare the invoice via WhatsApp or email.',
        'hi': 'प्रिंट किया गया रसीद देखें।\nव्हाट्सएप या ईमेल के माध्यम से इनवॉइस साझा करें।',
        'gu': 'પ્રિન્ટ થયેલ રસીદ જુઓ.\nવોટ્સએપ અથવા ઇમેઇલ દ્વારા ઇનવોઇસ શેર કરો।'
    },
    {
        'title': 'Close Shift',
        'page_num': 14,
        'en': 'Review cash drawer totals.\nCount the drawer and record any discrepancies.',
        'hi': 'कैश ड्रॉअर कुल राशि की समीक्षा करें।\nड्रॉअर गिनें और किसी भी विसंगति को दर्ज करें।',
        'gu': 'કેશ ડ્રોઅર કુલ રકમની સમીક્ષા કરો.\nડ્રોઅર ગણો અને કોઈપણ ભિન્નતા નોંધો।'
    },
    {
        'title': 'Settings & Language',
        'page_num': 35,
        'en': 'Change language, billing defaults, and theme.\nSave changes to apply.',
        'hi': 'भाषा, बिलिंग डिफ़ॉल्ट और थीम बदलें।\nपरिवर्तन सहेजें।',
        'gu': 'ભાષા, બિલિંગ ડિફૉલ્ટ અને થીમ બદલો.\nફેરફારો સાચવો।'
    },
    {
        'title': 'Reports & Analytics',
        'page_num': 23,
        'en': 'View sales reports, stock levels, and financial summaries.',
        'hi': 'बिक्री रिपोर्ट, स्टॉक स्तर और वित्तीय सारांश देखें।',
        'gu': 'વિક્રી રિપોર્ટ, સ્ટોક સ્તર અને નાણાકીય સારાંશ જુઓ।'
    },
    {
        'title': 'Staff Invitation',
        'page_num': 34,
        'en': 'Invite staff via Share menu.\nStaff can request access and await approval.',
        'hi': 'शेयर मेनू के माध्यम से स्टाफ को आमंत्रित करें।\nस्टाफ पहुँच का अनुरोध कर सकता है और अनुमोदन की प्रतीक्षा कर सकता है।',
        'gu': 'શેર મેનૂ મારફતે સ્ટાફને આમંત્રિત કરો.\nસ્ટાફ ઍક્સેસ માંગ કરી શકે છે અને મંજૂરીની રાહ જોઇ શકે છે।'
    }
]

OUTPUT_PDF = '/Users/codekajugad/Desktop/Vastrenix/Vastrenix_HowToUse.pdf'


def create_manual():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
    width, height = A4

    for step in steps:
        # Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, f"Vastrenix: {step['title']}")

        # Screenshot placeholder
        screenshot_path = f"/Users/codekajugad/Desktop/Vastrenix/screenshots/page_{step['page_num']:02d}.png"
        if os.path.exists(screenshot_path):
            c.drawImage(screenshot_path, 100, 250, width-200, 400, preserveAspectRatio=True, anchor='c')
        else:
            c.rect(100, 250, width-200, 400, stroke=1, fill=0)
            c.setFont("Helvetica", 12)
            c.drawString(120, 450, "[Screenshot missing]")

        # Instructions
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, 200, "English:")
        c.setFont("Helvetica", 12)
        text = c.beginText(50, 180)
        for line in step['en'].split('\n'):
            text.textLine(line)
        c.drawText(text)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(300, 200, "Hindi:")
        c.setFont("Devanagari", 12)
        text_hi = c.beginText(300, 180)
        for line in step['hi'].split('\n'):
            text_hi.textLine(line)
        c.drawText(text_hi)

        c.setFont("Helvetica-Bold", 14)
        c.drawString(300, 130, "Gujarati:")
        c.setFont("Gujarati", 12)
        text_gu = c.beginText(300, 110)
        for line in step['gu'].split('\n'):
            text_gu.textLine(line)
        c.drawText(text_gu)

        c.showPage()

    c.save()
    print(f"Generated {OUTPUT_PDF}")

if __name__ == "__main__":
    create_manual()
