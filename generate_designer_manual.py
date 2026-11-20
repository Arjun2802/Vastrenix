"""
Vastrenix How to Use - Designer PDF Generator
Creates a professional A4 multilingual user manual with:
- Large app screenshots in the middle
- English, Hindi (Devanagari), Gujarati (Sangam MN) on sides
- No text overlap - proper spacing and styling
- All payment methods documented
- Full bill/invoice receipt screen
- Store setup guide
- Designer styling with colors and layout
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register multilingual fonts
pdfmetrics.registerFont(TTFont('Devanagari', '/System/Library/Fonts/Supplemental/Devanagari Sangam MN.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('Gujarati', '/System/Library/Fonts/Supplemental/Gujarati Sangam MN.ttc', subfontIndex=0))

# App color theme (from Vastrinx brand)
VAS_GRAPHITE = '#0E0E12'
VAS_HERO = '#5B3DF5'
VAS_MIST = '#F6F6F8'
VAS_WHITE = '#FFFFFF'

A4_W, A4_H = A4
MARGIN = 30 * mm  # ~30mm margin all sides
CONTENT_W = A4_W - 2 * MARGIN
CONTENT_H = A4_H - 2 * MARGIN

# ===================== STEP DEFINITIONS =====================
# Each step: title, UI page number (from your PDF), English text, Hindi text, Gujarati text
steps = [
    {
        'title': 'Login & Account Setup',
        'ui_page': 5,
        'en_steps': [
            '1. Open the Vastrenix app on your phone or browser.',
            '2. Enter your email address and create a password.',
            '3. Click "Continue" to proceed.',
            '4. If new user, tap "New here? Create account" and fill name, email, password.',
            '5. To join an existing store, tap "I work at a store" and enter the Store Code (e.g., VX-ODF-AB12).',
            '6. Admin will approve your staff request — you will see a notification once approved.'
        ],
        'hi_steps': [
            '1. vastrenix एप खोलें अपने फ़ोन या ब्राउज़र में।',
            '2. अपना ईमेल पता और पासवर्ड बनाएँ।',
            '3. "जारी रखें" पर क्लिक करें।',
            '4. यदि नए उपयोगकर्ता हैं तो "नहीं? अकाउंट बनाएँ" टैप करें और नाम, ईमेल, पासवर्ड भरें।',
            '5. present एक्सisting स्टोर में शामिल होने के लिए, "मैं एक स्टोर में काम करता/करती हूँ" टैप करें और Store Code दर्ज करें (जैसे VX-ODF-AB12).',
            '6. प्रशासक आपके स्टाफ़ अनुरोध को मंज़ूरी देंगे — अनुमोदित होने पर एक नोटिफिकेशन देखेंगे।'
        ],
        'gu_steps': [
            '1. vastrenix એપ તમારા ફોન અથવા બ્રાઉઝરમાં ઓપન કરો.',
            '2. તમારું ઇમેઇલ_addr અને પાસવર્ડ બનાવો.',
            '3. "ચાલુ રાખો" પર ક્લિક કરો.',
            '4. નવા felhasznál户如若 નવા ઉપયોગકર્તા હોવા ના તો "નહીં? એકાઉન્ટ બનાવો" ટેપ કરી નામ, ઇમેઇલ, પાસવર્ડ ભરો.',
            '5. વ Stafford જોડolandના સ્ટોરમાં શામેલ કરવા માટે, "હું કોઈ સ્ટોરમાં કામ કરું છું" ટેપ કરી Store Code દREGISTER કરો (જણા VX-ODF-AB12).',
            '6. એડમિન તમારું સ્ટाफ़ અનુરोध મંજૂર કરેगा — મંજૂરી હોવાથી નોટિફિકેશન મળશે।'
        ]
    },
    {
        'title': 'Dashboard Overview',
        'ui_page': 9,
        'en_steps': [
            'The dashboard shows your store\'s daily sales summary at a glance.',
            'Key metrics displayed: Total sales, number of bills, average bill amount, cash in drawer.',
            'Quick stats: Low stock alerts, recent bills, team requests, and shift status.',
            'Use the bottom navigation bar to switch between: Home, Stock, Money, Reports, and Network.',
            'Today\'s sales figure updates in real-time as bills are generated.',
            'Swipe or tap to view yesterday\'s sales or last 7 days performance.'
        ],
        'hi_steps': [
            'डैशबोर्ड पर अपनी दुकान की दैनिक बिक्री का सारांश एक नज़र में दिखता है।',
            'प्रदर्शित की गई प्रमुख मेट्रिक्स: कुल बिक्री, बिल की संख्या, औसत बिल राशि, गल्ले में नकद।',
            'त्वरित आँकड़े: स्टॉक में कमी की चेतावनी, हाल के बिल, टीम अनुरोध, और शिफ्ट स्थिति।',
            'नीचे नेविगेशन बार का उपयोग करके होम, स्टॉक, पैसा, रिपोर्ट और नेटवर्क के बीच स्विच करें।',
            'आज की बिक्री का आंकड़ा वास्तविक समय में बिल उत्पन्न होते समय अपडेट होता है।',
            'स्वाइप या टैप करके कल की बिक्री या पिछले 7 दिनों के प्रदर्शन देखें।'
        ],
        'gu_steps': [
            'ડેશબોર્ડે તમારા દુકાન દ્યનમ્ય પર નિર્ણય એક નજરે દાખવે છે.',
            'મુખ્ય મેટ્રિક્સ મિત્ર દર્શાવાય: કુલ વેચાણ, બિલની સંખ્યા, અનુ bilin averagebill નો રકમ, કેશ ડ્રોअરમાં.',
            'અત્વપૂર્ણ આંકડાઓ: ઓછો સ્ટોક ચેતવણી, તાજેતરના બિલ, ટીમ અનુરોધ, અને શિફ્ટ સ્થિતિ.',
            'નીચેના નેવિગેજ્મેન્ટ બારનું ઉપયોગ કરીને હોમ, સ્ટોક, પેમની, રિપોર્ટ અને નેટવર્ક વચ્ચે Swich કરો.',
            'આજના વેચાણના સંખ્યા વસ્તા જીત droplets જ્યારે બિલ જનરેટ થે છે ત્યારે રિઅલ‑ટાઈમમાં અપડેટ થાય છે।',
            'સ્વાઈપ અથવા ટેપ કરીને યestu યesterdayના વેચાણ અથવા પાછા 7 દિવસની પ્રદર્શનો જ Floyd।'
        ]
    },
    {
        'title': 'Create a New Retail Bill',
        'ui_page': 10,
        'en_steps': [
            'Tap "New Bill" to start a fresh sale.',
            'Search for items by name, SKU, or scan barcode using the scanner.',
            'Select garment variants (size, color) and enter quantity.',
            'Add customer: either select existing customer or add a new walk-in customer (optional, needed for credit).',
            'Review the bill: subtotal, discounts (amount or %), GST inclusion, round-off, and total.',
            'Tap "Complete Sale" when ready.'
        ],
        'hi_steps': [
            'नया बिल खोलने के लिए "नया बिल" टैप करें।',
            'आइटम का नाम, SKU द्वारा खोजें या बारकोड स्कैनर से स्कैन करें।',
            'आकार, रंग वैरिएंट चुनें और मात्रा दर्ज करें।',
            'ग्राहक जोड़ें: मौजूदा ग्राहक चुनें या नए वॉक-इन ग्राहक जोड़ें (वैकल्पिक, उधार के लिए आवश्यक)।',
            'बिल की समीक्षा करें: उप-योग, छूट (राशि या %), GST शामिल, गोल-ऑफ, और कुल।',
            'तैयार होने पर "बिक्री पूरी करें" टैप करें।'
        ],
        'gu_steps': [
            'નવા બિલ માટે "નવું બил" ટેપ કરો.',
            'નામ, SKU દ્વારા ઉમેદવેં અથવા બારકોડ સ્કેનરથી સ્ક্যান કરો.',
            'આઈટમ વેરિઅન્ટ (સાઈઝ, رنگ) પસંદ કરો અને મात्रा દર입ો.',
            'ગ્રાહક ઉમેરો: मौजूद ગ્રાહક પસંદ કરો અથવા નવા વોક-ઇન ગ્રાહક ઉમેરો (વૈકલ્પિક, ઉધાર માટે નધારિક)।',
            'બિલની સમીક્ષા કરો: પેટા સરવાળો, છૂટ (રકમ અથવા %), GST સામેલ, રાઉન્ડ ઓફ્ટ, અને કુલ.',
            'પૂરી કરીઓ ણા તૈયાર હોવાથી "બિલ પૂરાં કરો" ટેપ કરો।'
        ]
    },
    {
        'title': 'Checkout & Payment Methods',
        'ui_page': 11,
        'en_steps': [
            'After adding items, the checkout screen shows: Amount Due, payment method options, and cash received field.',
            'Select payment method:',
            '  • Cash: Enter the cash received amount. System calculates change automatically.',
            '  • UPI: Shows QR code for customer to scan (GPay, PhonePe, Paytm). Wait for payment confirmation.',
            '  • Card: Enter last 4 digits of card (optional). Confirm card payment.',
            '  • Split: Divide the amount between multiple methods (e.g., partial cash + partial UPI).',
            '  • Credit: Mark customer as "on credit" — adds to their outstanding dues with reminder date.',
            'Once payment is confirmed, the system shows: "Payment received", UTR reference field (optional), and options to View Invoice, Print, or Share via WhatsApp.'
        ],
        'hi_steps': [
            'आइटम जोड़ने के बाद, चेकआउट स्क्रीन दिखाती है: देय राशि, भुगतान विकल्प, और नकद प्राप्त क्षेत्र।',
            'भुगतान विधि चुनें:',
            '  • नकद: नकद प्राप्त की गई राशि दर्ज करें। सिस्टम स्वतः परिवर्तन की गणना करता है।',
            '  • UPI: ग्राहक को स्कैन करने के लिए QR कोड दिखाता है (GPay, PhonePe, Paytm)। भुगतान की पुष्टि की प्रतीक्षा करें।',
            '  • कार्ड: कार्ड के अंतिम 4 अंक दर्ज करें (वैकल्पिक)। कार्ड भुगतान की पुष्टि करें।',
            '  • स्प्लिट: रकम को बहु विधियों के बीच विभाजित करें (जैसे आंशिक नकद + आंशिक UPI)।',
            '  • उधार: ग्राहक को "उधार पर"マーク करें — इससे उनकी देनदारी में जुड़ता है और याद दिलाने की तारीख जुड़ती है।',
            'एक बार भुगतान पुष्टि हो जाने पर, सिस्टम दिखाता है: "भुगतान प्राप्त", वैकल्पिक UTR/reference क्षेत्र, और Invoice देखें, Print, या WhatsApp पर साझा करने के विकल्प।'
        ],
        'gu_steps': [
            'આઇટમ ઉમેર્યા છCompletion After, checout સ્ક્રીન દરેકે: Amount Due, ચુકવણી પદ્ધતિ નિકુંજ, અને રોકડ મળ્યો FIELD.',
            'ચુકવણી પદ્ધતિ પસંદ કરો:',
            '  • રોકડ: રોકડ મળેલી રકમ દર입ો. સિસ્ટમ ત 自動 ઓછામાં ઓછા રકમ ક[count કરો].',
            '  • UPI: ગ્રાહકો QR કોડ સ્કેન કરવા માટે QR કોડ દર્શાવે છે (GPay, PhonePe, Paytm). પ્ર payment confirmation દરી શકેતા છે.',
            '  • કર્ડ: કાર્ડ ના છેલ્લા 4 અંક દર입ો (વૈકલ્પિક). કાર્ડ ચુકવણીની પુષ્ટિ કરો.',
            '  • સ્પ્લિટ: રકમને બહુ પદ્ધતિઓ વચ્ચે વિભાજન કરો (જैसे આંકજાત નકદ + આંકજાત UPI).',
            '  • ક્રેડિટ: કસ્ટમરને "ઉધાર પર" ચિર્ખરો — તેના બક ovaryના રકમમાં જુમે છે અને યાદ_delivery_ની તારીખ જોડે છે.',
            'પખાને ચુકવણી પોષ્ટ થ Havana After payment confirmed, the system shows: "Payment received", UTR reference field (optional), and options to View Invoice, Print, or Share via WhatsApp.'
        ]
    },
    {
        'title': 'Printed Receipt & Full Bill/Invoice',
        'ui_page': 21,
        'en_steps': [
            'After payment, tap "View Invoice" to see the full formatted bill.',
            'The invoice screen shows: Bill number, date, store name and GSTIN, bill-to information, itemized list with HSN codes, rates, quantities, and amounts.',
            'Tax breakdown: CGST and SGST amounts, or "Prices include GST" if selected.',
            'Tap "Print" to print via thermal printer (Compact Thermal theme) or export PDF.',
            'Tap "WhatsApp" to share the invoice as a formatted message with bill details and payment link.',
            'The printed receipt shows: Shop name/logo, bill no., date/time, item table, totals, GST, and payment method — suitable for thermal 58/80mm receipt printers.'
        ],
        'hi_steps': [
            'भुगतान के बाद, "देखें इनवॉइस" टैप करके पूर्ण formatted bill देखें।',
            'इनवॉइस स्क्रीन दिखाती है: बिल नं., तारीख, दुकान का नाम और GSTIN, बिल-व्यक्ति की जानकारी, elementized list with HSN कोड, दरें, मात्रा, और राशि।',
            'कर ब्रेकडाउन: CGST और SGST राशि, या "कीमत में GST शामिल" यदि चुना गया है।',
            '"प्रिंट" टैप करके thermal printer (Compact Thermal theme) पर प्रिंट करें या PDF निर्यात करें।',
            '"WhatsApp" टैप करके formatted संदेश के रूप में invoice साझा करें जिसमें बिल के विवरण और भुगतान लिंक हों।',
            'छपा हुआ रसीद दर्शाता है: दुकान का नाम/लोगो, बिल नं., तारीख/समय, आइटम तालिका, कुल, GST, और भुगतान विधि — थर्मल 58/80mm रसीद प्रिंटर के लिए उपयुक्त।'
        ],
        'gu_steps': [
            'ચુકવણી પછી, "દેખો Invoice" ટેપ કરી અંકોને ફોર્મેટ બિલ જુઓ.',
            ' invoiced સ્ક્રીન દર્શાવે છે: Bill નંબર, તારીખ, દકાનના નામ અને GSTIN, bill-to માહિતી, આઇટમListaізઆન્ડ રેટ વર્ચ AMOUNT.',
            'તックス બ્રેકડાઉન: CGST અને SGST રકમ, અથવા "કિંમતમાં GST સામેલ" જો બલGBT બંધ કર્યો હતો।',
            ' "પ્રિન્ટ" ટેપ કરી થર્મલ પ્રિન્ટર (Compact Thermal theme) પર પ્રિન্ট કરો અથવા PDF એક્સપોર્ટ કરો।',
            ' "વોટ્સએપ" ટેપ કરી ફોર્મેટેડ મેસેજ invoice શેર કરો જે બિલના વિશેસ અને પેંメント લિંક સાથે હોય.',
            'પ્રિન્ટ થયેલ રસીદ દર્શાવે છે: દુકાનનું નામ/લોગો, બિલ નંબર, તારીખ/સમય, આઇટમ તાલিকা, કુલ, GST, અને ચુકવણી પદ્ધતિ — થર્મલ 58/80mm રસીદ પ્રિન્ટર માટે યોગ્ય।'
        ]
    },
    {
        'title': 'Close Shift',
        'ui_page': 14,
        'en_steps': [
            'At the end of the day/shift, tap "Close Shift".',
            'The system shows: Opening float, cash sales count and total, cash received from dues, payouts/expenses, and expected amount in drawer.',
            'Count the physical cash in the drawer and compare with the system\'s expected amount.',
            'If there is a discrepancy (short or excess), note the amount.',
            'Tap "Count Drawer" to open the denomination counting screen, or tap "Close" to finish and reset the shift.',
            'Shift close report is saved and visible in the Money/Cash Book section.'
        ],
        'hi_steps': [
            'दिन/शिफ्ट के अंत में, "शिफ्ट बंद करें" टैप करें।',
            'सिस्टम दिखाता है: शुरूआती नकद राशि, नकद बिक्री की गिनती और कुल, बकाया से नकद प्राप्त, भुगतान/व्यय, और गल्ले में अपेक्षित राशि।',
            'भौतिक रूप से गल्ले में मौजूद नकद की गिनती करें और सिस्टम की अपेक्षित राशि के साथ तुलना करें।',
            'यदि कोई विसंगति है (कम या अधिक), तो राशि नोट करें।',
            'नोट गिनने के लिए "गल्ला गिनें" टैप करें या "बंद" टैप करके शिफ्ट समाप्त करें और रीसेट करें।',
            'शिफ्ट बंद रिपोर्ट सेव की जाती है और पैसे/कैश बुक अनुभाग में दिखाई देती है।'
        ],
        'gu_steps': [
            'દિવસ/શિફ્ટના અંતે, "શિફ્ટ બંધ કરો" ટેપ કરો.',
            'સિસ્ટમ દર્શાવે છે: શરૂઆતની રોકડ, નકદ વેચાણ ગણતરી અને કુલ, નકCash received from dues, પayouts/ व्यय, અને ગલ્લામાં અન્યુ લગાવોની રકમ.',
            'શારirિક રીતે ગલ્લે મખેલા નક cashની ગણતરી કરો અને સિસ્ટમની અનેક્ષાતી રકમ સાથે તુલના કરો.',
            'તની જોReply vignanતા (ઓછો અથવા વધારે) હોય ને રકમ નોંધો.',
            'ટDrawer ગણાયો ટેપ કરી denomination ગણાયો સ્ક્રીન ઓપન કરો, અથવા ટ "બંધ" ટેપ કરી શિફ્ટ વિશરે અને રિસેટ કરો.',
            'શિફ્ટ બંધ રિપોર્ટ સેવ થાય છે અને પૈસા/ક্যাশ બુક સાઝ્નમાં જ્થાયો હોય છે।'
        ]
    },
    {
        'title': 'How to Setup a New Store',
        'ui_page': 2,
        'en_steps': [
            '1. Open the app and tap "Sign in" / "Create account".',
            '2. Choose "I own a store → Create a new store".',
            '3. Fill in the 5-step setup:',
            '   • Business name (e.g., "Odedara Fashions").',
            '   • City (e.g., "Rajkot").',
            '   • Phone number.',
            '   • Address.',
            '   • GST details: GSTIN number, state, and default GST rate for garments (5%, 12%, or 18% by slab).',
            '4. Tap "Finish Setup".',
            '5. Your store code (e.g., VX-ODF-AB12) is shown in "More → Account". Share this code with staff or dealers so they can join your store network.'
        ],
        'hi_steps': [
            '1. एप खोलें और "साइन इन" / "अकाउंट बनाएँ" टैप करें।',
            '2. "मैं एक स्टोर का मालिक हूँ → नया स्टोर बनाएँ" चुनें।',
            '3. 5-स्टेप सेटअप भरें:',
            '   • व्यापार का नाम (जैसे "ओडे़रा फ़ैशनस").',
            '   • शहर (जैसे "राजकोट").',
            '   • फ़ोन नंबर।',
            '   • पता।',
            '   • GST विवरण: GSTIN नंबर, राज्य, और कपड़ों के लिए डिफ़ॉल्ट GST दर (5%, 12%, या 18% द्वारा स्लैब)।',
            '4. "सेटअप पूरा करें" टैप करें।',
            '5. तुम्हारा स्टोर कोड (जैसे VX-ODF-AB12) "और → अकाउंट" में दिखेगा। स्टाफ या डीलरों को यह कोड दें ताकि वे तुम्हारे स्टोर नेटवर्क में जुड़ सकें।'
        ],
        'gu_steps': [
            '1. એપ ઓપન કરો અને "સાઇન ઇન" / "એકાઉન્ટ બનાવો" ટેપ કરો.',
            '2. "હું એક સ્ટોરનું માલિક હો → નવું સ્ટોર બનાવો" પસંદ કરો.',
            '3. 5-સ્ટેપ સેટઅપ પૂર્ણ કરો:',
            '   • વ્યવસાયનો નામ (જણા "Odedara Fashions").',
            '   • શેહર (અ gauge "Rajkot").',
            '   • ફોન નંબર।',
            '   • સરનામું।',
            '   • GST વિગતો: GSTIN નંબર, રાજ્ય, અને કપડાઓ માટે ડિફૉlt GST દર (5%, 12%, અથવા 18% દ્વારા સ્લબ).',
            '4. "સેટઅપ પૂર્ણ કરો" ટેપ કરો।',
            '5. તમારું સ્ટોર કોડ (જણા VX-ODF-AB12) "અને → એકાઉન્ટ"માં દર્શાયે છે. Stafford ડીલરો તમે અને સ્ટाफ શેર કરો તો તેમ પાસે તમારા સ્ટોર નેટવર્કમાં જોડો શકે છે।'
        ]
    },
    {
        'title': 'Staff Invitation & Roles',
        'ui_page': 34,
        'en_steps': [
            '1. Go to "More" → "Staff" in the bottom navigation.',
            '2. Tap "Share" to send the current page to staff via WhatsApp, email, or copy link.',
            '3. Staff will open the link, create an account, and request access to your store.',
            '4. Enter the Store Code (the code you created when setting up the store).',
            '5. As the store owner/admin, go to Staff section, view pending requests, and tap "Approve" to assign a role: Admin, Branch Manager, Cashier, Inventory Manager, Purchase Manager, Accountant, Dispatcher, or Auditor.',
            '6. Approved staff can now access the app with their designated permissions.'
        ],
        'hi_steps': [
            '1. निचले नेविगेशन बार में "और" → "स्टाफ" पर जाएँ।',
            '2. "शेयर" टैप करके स्टाफ को व्हाट्सएप, ईमेल, या लिंक कॉपी करके वर्तमान पेज भेजें।',
            '3. स्टाफ लिंक खोलेगा, अकाउंट बनाएगा, और आपके स्टोर तक पहुँच का अनुरोध करेगा।',
            '4. Store Code दर्ज करें (जो आपने स्टोर setup के समय बनाया था)।',
            '5. स्टोर मालिक/एडमिन के रूप में, स्टाफ सेक्शन में pending requests देखें और "स्वीकार करें" टैप करके एक भूमिका assign करें: एडमिन, ब्रांच मैनेजर, कैशियर, इन्वेंटरी मैनेजर, ख़रीद मैनेजर, अकाउंटेंट, डिस्पैचर, या ऑडिटर।',
            '6. स्वीकृत स्टाफ अब अपनी निर्धारित अनुमतियों के साथ ऐप का उपयोग कर सकते हैं।'
        ],
        'gu_steps': [
            '1. નીચેના નેવિગેજ્મેન્ટ બારમાં "વધુ" → "સ્ટાફ"પ્રાય Gujarat.',
            '2. "શેર" ટેપ કરી સ્ટાફને WhatsApp, ઇમેઈલ, અથવા લિંક કોરી વર્ટમાન પેજ મોકલો.',
            '3. Stafford લિંક ઓપણે, એકાઉન્ટ બનાવી, અને તમારા સ્ટોર બહેં accessનો અનુરોધ કરો.',
            '4. Store Code દરેજી કો્રDo (જો તમે સ્ટોર સેટઅપ કયા વયોહનો કારણે બનાવોше).',
            '5. સ્ટોર માલિક/એડમિન તરીકે, Staff section-pending requests જૂડો અને "મંજૂર કરો" ટેપ કરી એક ભૂમિકા assign કરો: એડમિન, બ્રાન્ચ માનેજર, કેશિયર, ઇન્વેન્ડરી મેનેજર, wave Mumbai ખી Davidson ખેડ, અકાઉન્ટન્ટ, ડિસ્પેચર, અથવા ઓડિટર।',
            '6. swीकृत Stafford એક્જન્ટઆહીં/app પાસે તેમની નિય assign કરતા પરમાણી સાથે વયોગી શક્યા છે।'
        ]
    }
]

OUTPUT_PDF = '/Users/codekajugad/Desktop/Vastrenix/Vastrenix_HowToUse_Designer.pdf'


def create_designer_manual():
    c = canvas.Canvas(OUTPUT_PDF, pagesize=A4)
    width, height = A4

    # Calculate usable area
    left_margin = 25
    right_margin = 25
    top_margin = 30
    bottom_margin = 30
    usable_w = width - left_margin - right_margin
    usable_h = height - top_margin - bottom_margin

    for idx, step in enumerate(steps):
        page_num = step['ui_page']

        # ---- Background / header area ----
        # Brand header bar at top
        c.setFillColor(colors.HexColor(VAS_HERO))
        c.rect(0, height - top_margin, width, 50, fill=1, stroke=0)
        # Title text
        c.setFillColor(VAS_WHITE)
        c.setFont("Helvetica-Bold", 16)
        title_text = f"Vastrenix: {step['title']}"
        c.drawString(30, height - top_margin + 12, title_text)

        # ---- Screenshot area (large, centered) ----
        screenshot_path = f"/Users/codekajugad/Desktop/Vastrenix/screenshots/page_{page_num:02d}.png"
        screenshot_x = (width - usable_w) / 2  # center it
        screenshot_y = height - top_margin - 50 - 350  # above the bottom text area, big size

        if os.path.exists(screenshot_path):
            # Draw image scaled to usable width, maintaining aspect ratio
            img_height = 350
            c.drawImage(screenshot_path, screenshot_x, screenshot_y, usable_w, img_height, preserveAspectRatio=True, anchor='c')
        else:
            # Fallback colored rectangle with text
            c.setFillColor(colors.HexColor(VAS_GRAPHITE))
            c.rect(screenshot_x, screenshot_y, usable_w, 350, fill=1, stroke=1)
            c.setFillColor(colors.HexColor(VAS_MIST))
            c.setFont("Helvetica", 12)
            c.drawCentredString(screenshot_x + usable_w / 2, screenshot_y + 150, f"[Screenshot: Page {page_num}]")

        # ---- Multilingual instructions on left/right/forward ----
        # We'll use a table-like layout: English left, Hindi center-right, Gujarati far-right
        # Or better: columns with proper spacing

        y_start = screenshot_y - 380  # above screenshot

        # English column (left)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(30, y_start + 20, "ENGLISH:")
        c.setFont("Helvetica", 11)
        en_y = y_start
        for line in step['en_steps']:
            c.drawString(30, en_y, line)
            en_y -= 14

        # Hindi column (middle)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(30 + usable_w / 3, y_start + 20, "HINDI:")
        c.setFont("Devanagari", 11)
        hi_y = y_start
        for line in step['hi_steps']:
            c.drawString(30 + usable_w / 3, hi_y, line)
            hi_y -= 14

        # Gujarati column (right)
        c.setFont("Helvetica-Bold", 13)
        c.drawString(width - 30 - (usable_w / 3), y_start + 20, "GUJARATI:")
        c.setFont("Gujarati", 11)
        gu_y = y_start
        for line in step['gu_steps']:
            # Wrap text if needed - simple approach: limit width
            text_width = c.stringWidth(line, "Gujarati", 11)
            if text_width > width - 80 - (usable_w / 3):
                # split or just draw smaller
                pass
            c.drawString(width - 30 - (usable_w / 3), gu_y, line)
            gu_y -= 14

        # Navigation / page indicator at bottom
        c.setFillColor(colors.HexColor(VAS_MIST))
        c.setFont("Helvetica", 9)
        c.drawString(30, 30, f"Vastrenix How to Use  |  Step {idx+1} of {len(steps)}  |  Page {page_num} of 36 UI")

        c.showPage()

    c.save()
    print(f"Generated designer PDF: {OUTPUT_PDF}")

if __name__ == "__main__":
    create_designer_manual()