---
source: "original_fallback"
type: "extraordinary"
year: "2020"
pdf_url: "https://web.archive.org/web/20220712091135/http://www.stationeryprinting.tn.gov.in/extraordinary/2020/309_Ex_III_1a.pdf"
Issue No: "309"
Issue Date: "2020-07-31"
Gazette Number: "Part III-Section 1a"
Category: "General Statutory Rules, Notifications, Orders, Regulations, etc., issued by Secretariat Departments"
Department: "COMMERCIAL TAXES AND REGISTRATION DEPARTMENT - NOTIFICATION UNDER THE TAMIL NADU GOODS AND SERVICES TAX RULES, 201"
---

TAMIL  NADU
GOVERNMENT GAZETTE
EXTRAORDINARY 
PUBLISHED  BY  AUTHORITY
 
© 
[Regd. No. TN/CCN/467/2012-14.
 GOVERNMENT  OF  TAMIL  NADU 
[R. Dis. No. 197/2009. 
 
 
 
2020 
[Price:  Rs.  11.20 Paise. 
No. 309] 
CHENNAI, FRIDAY, JULY 31, 2020  
 
 
 
 
 
Aadi 16, Saarvari, Thiruvalluvar Aandu-2051
III-1(a) Ex. (309)                                                                          [ 1 ]
Part III—Section  1(a)
General Statutory Rules, Notifications, Orders, Regulations, etc.,
issued by Secretariat Departments.
NOTIFICATIONS  BY  GOVERNMENT
COMMERCIAL TAXES AND REGISTRATION DEPARTMENT
NOTIFICATION UNDER THE TAMIL NADU GOODS AND SERVICES TAX RULES, 2017.
[G.O. Ms. No.120, Commercial Taxes and Registration (B1), 31st July 2020, Aadi 16, Saarvari, 
Thiruvalluvar Aandu-2051.]
No. SRO A/26(a-1)/2020.
In exercise of the powers conferred by section 164 of the Tamil Nadu Goods and Services Tax Act, 2017 
(Tamil Nadu Act 19 of 2017), the Governor of Tamil Nadu, on the recommendations of the Council, hereby 
makes the following rules further to amend the Tamil Nadu Goods and Services Tax Rules, 2017, namely:- 
1.  (1) These rules may be called the Tamil Nadu Goods and Services Tax (Ninth Amendment) Rules, 
2020.
      (2) They shall come into force on the date of their publication in the Oﬃ  cial Gazette.
2.   In the Tamil Nadu Goods and Services Tax Rules, 2017, for FORM GST INV-01, the following form 
shall be substituted, namely:-
“FORM GST INV – 1 
(See Rule 48)
Format/Schema for e-Invoice
Note 1:Cardinality means whether reporting of the item(s) is mandatory or optional as explained below:
0..1: It means that  reporting of item  is optional and when  reported, the same cannot be repeated.
1..1: It means that reporting  of item is mandatory but cannot be repeated.
1..n: It means that reporting  of item is mandatory and can be repeated more than once.
0..n: It means that  reporting of item is optional but can be repeated more than once if reported. For  
     example, previous invoice reference is optional but if required one can mention many previous invoice 
references.


2 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
Note 2:  Field speciﬁ cation Number (Max length: m, n) indicates ‘m’ places before decimal point and ‘n’ places after 
decimal point. For example, Number (Max length: 3,3) will have the format 999.999
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample Value 
of the ﬁ eld
Explanatory 
Notes
1.
Basic 
Details 
1..1 
Mandatory  
Header for 
Basic Details
 1.0
Version 
1..1 
Version 
Number 
Mandatory  
String 
(Max. 
Length:6)
1.1
This is 
version of 
the e-invoice 
schema. It 
will be used 
to keep track 
of version 
of Invoice 
speciﬁ cation. 
1.1 
IRN 
1..1 
Invoice 
Reference   
Number 
Mandatory 
String 
(Length:64)
a5c12dca
80e
7433
217…..
ba
4013
750f
2046f
229
This will be 
a unique 
reference 
number for the 
invoice. 
However, 
the supplier 
will not be 
populating this 
ﬁ eld. 
The 
registration 
request may 
not have this 
ﬁ eld populated. 
The Invoice 
Registration 
Portal (IRP) 
will generate 
this IRN and 
respond to the 
registration 
request. 
e-invoice is 
valid only 
when it has 
the IRN. 
Hence, this 
is marked as 
mandatory 
ﬁ eld.


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
3
1.2 
Supply_
Type_
Code
1..1 
Code for 
Supply Type
Mandatory 
Enumerated 
List 
B2B/B2C/
SEZWP/
SEZWOP/EXP
WP/EXPWOP/
DEXP  
This will be 
the code to 
identify type of 
supply. 
B2B: Business 
to Business
B2C: Business 
to Consumer
SEZWP: To 
SEZ with 
Payment
SEZWOP: To 
SEZ without 
Payment
EXPWP: 
Export with 
Payment
EXPWOP: 
Export without 
Payment
DEXP: 
Deemed 
Export 
1.3 
Document_
Type_
Code
1..1 
Code 
for Document 
Type
Mandatory 
Enumerated 
List
INV / CRN / 
DBN 
Type of 
Document: 
INV for 
Invoice,   
CRN for Credit 
Note,
DBN for Debit 
note.  
1.4 
Document_Num
1..1 
Document 
Number 
Mandatory 
String 
(Max 
Length:16) 
Sa/1/2019 
This is as per 
relevant rule in 
CGST/SGST/
UTGST Rules. 
1.5 
Document_Date
1..1 
DocumentDate 
Mandatory 
String 
(DD/MM/YYYY) 
21/07/2019 
The date on 
which the 
Invoice was 
issued. Format 
“DD/MM/
YYYY” 
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


4 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
1.6 
Additional_
Currency_Code
0..1 
Additional 
Currency 
Code 
Optional
Enumerated 
List 
USD, EUR
The ﬁ eld is 
for reporting 
additional 
currency, if 
any, in which 
all invoice 
amounts can 
be given, 
along with 
INR.  
One such 
additional 
currency may 
be used in the 
invoice, as per 
list published 
under ISO 
4217 standard. 
List published 
and updated 
from time 
to time at 
https://www.
icegate.gov.
in/Webappl/
CUR_ENQ
1.7 
Reverse_
Charge
0..1 
Reverse 
Charge 
Optional
String 
(Length:1)
Y
Whether the 
tax liability 
payable is 
under Reverse 
Charge.
1.8
IGST_
Applicability_
despite_
Supplier_and_
Recipient_
located_in_
same_ State/
UT
0..1
IGST 
Applicability 
despite 
Supplier and 
Recipient 
located in 
same State/UT
Optional 
String (Length: 
1) 
N
To report the 
scenarios 
where the 
supply is 
chargeable to 
IGST despite 
the fact that 
the Supplier 
and Recipient 
are located 
within  same 
State/UT 
2. 
Document_
Period
0..1 
Optional 
Header for 
Document 
Period
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
5
2.1 
Document_
Period_Start 
_Date 
1..1 
Document 
Period Start 
Date 
Mandatory
String
(DD/MM/YYYY) 
21/07/2019 
This is the 
start date of 
the document 
period 
(delivery/
invoice period).
(This ﬁ eld is 
mandatory 
only if this 
section is 
selected)
2.2 
Document_
Period_End_ 
Date 
1..1 
Document 
Period End 
Date 
Mandatory 
String
(DD/MM/YYYY)
21/07/2019 
This is the 
end date of 
the document 
period 
(delivery/
invoice period). 
(This ﬁ eld is 
mandatory 
only if this 
section is 
selected)
3.
Preceding 
Document 
/ Contract  
Reference
0..1 
Optional 
Header for 
Preceding 
Document 
/ Contract  
Reference
3.1 
Preceding 
Document 
Reference
0..n
  Optional
Sub-header 
for Preceding 
Document 
Reference
3.1.1 
Preceding_
Document_ 
Number
1..1
Preceding 
Document 
Number
Mandatory
String (Max 
length:16) 
Sa/1/2019 
This is the 
reference 
of original 
document/
invoice to 
be provided 
optionally in 
the case of 
debit or credit 
notes. 
Credit/Debit 
notes, against 
invoices 
can also be 
referred here. 
(This ﬁ eld is 
mandatory only 
if this section is 
selected)
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


6 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
3.1.2 
Preceding_
Document_ 
Date
1..1
Date of 
Preceding 
Document
Mandatory
String
(DD/MM/YYYY)
21/07/2019
Date of 
preceding 
document/
invoice. 
(This ﬁ eld is 
mandatory only 
if this section is 
selected)
3.1.3  
Other_ 
Reference
0..1 
Other 
Reference
Optional
String 
(Maxlength:20)
KOL01
This ﬁ eld is 
to provide 
any additional 
reference e.g. 
speciﬁ c branch, 
their user ID, 
their employee 
ID, sales centre 
reference etc.
3.2
Receipt / 
Contract 
References
0..n
Optional
Sub-header 
for Receipt 
/ Contract 
References
3.2.1 
Receipt_Advice_
Reference
0..1 
Receipt Advice 
Reference
Optional 
String (Max 
length:20) 
CREDIT30 
This reference 
is kept for 
user to provide 
number of 
their receipt 
advice to their 
customer, 
in lieu of 
advance.
3.2.2
Receipt_Advice 
_Date
0..1
Date of 
Receipt Advice
Optional
String
(DD/MM/YYYY)
21/07/2019
Date of issue 
of receipt 
advice for 
advance.
3.2.3
Tender_or_Lot_
Reference
0..1 
Tender or Lot 
Reference 
Optional 
String 
(Max length:20) 
TENDER JAN
2020 
This reference 
is kept for 
mentioning 
number or 
details of Lot 
or Tender, if 
supplies are 
made under 
such Lot or 
tender. 
3.2.4
Contract_
Reference
0..1 
Contract 
Reference
Optional 
String 
(Max length:20) 
CONT
23072019 
This reference 
is kept for 
mentioning 
contract 
number, if 
supplies are 
made under 
any speciﬁ c 
Contract 
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
7
3.2.5 
External_
Reference
0..1 
External 
Reference 
Optional 
String 
(Maxlength:20) 
EXT23222 
An additional 
ﬁ eld for 
provision of 
any additional/
external 
reference 
number for the 
supply.
3.2.6 
Project_
Reference
0..1 
Project 
Reference 
Optional 
String 
(Maxlength:20) 
PJTCODE01 
This reference 
is kept for 
mentioning 
project 
number, if 
supplies are 
made under 
any speciﬁ c 
project 
3.2.7 
PO _Ref_Num
0..1 
PO Reference 
Number 
Optional 
String (Max
length:16) 
Vendor 
PO /1 
This is the 
reference 
number of 
Purchase 
Order
3.2.8 
PO_Ref_Date
0..1 
PO Reference 
Date 
Optional 
String
(DD/MM/YYYY) 
21/07/2019 
This is the 
date of 
Purchase 
Order.
4. 
Supplier 
Information 
1..1 
Mandatory
Header for 
Supplier 
Information
4.1 
Supplier_Legal_
Name
1..1
Supplier Legal 
Name 
Mandatory 
String (Max. 
length:100)
XYZ Ltd.
Legal Name, 
as appearing 
in PAN of the 
Supplier 
4.2 
Supplier_
Trade_ Name 
0..1 
Trade Name 
of Supplier 
Optional 
String (Max  
length:100) 
ABC Traders
A name by 
which the 
Supplier is 
known, i.e. 
Business 
Name, other 
than legal 
name
4.3 
Supplier_
GSTIN
1..1 
GSTIN of 
Supplier 
Mandatory 
String 
(Length:15)
29AADFV
7589C1ZX 
GSTIN of the 
Supplier 
4.4 
Supplier_
Address1 
1..1 
Supplier 
Address 1 
Mandatory 
String (Max 
length:100) 
# 1-23-120, 
Flat No. 3, 
Nalanda 
Apartments, 
MG Road, 
Vasanth Nagar
Address 1 of 
the Supplier
(Building/Flat 
no., Road/
Street, Locality 
etc.)
4.5 
Supplier_
Address2 
0..1 
Supplier 
Address 2 
Optional 
String (Max 
length:100) 
# 1-23-120, 
Flat No. 3, 
Nalanda 
Apartments, 
MG Road, 
Vasanth Nagar
Address 2 of 
the Supplier 
(Building/Flat 
no., Road/
Street, Locality 
etc.), if any
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


8 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
4.6 
Supplier_Place
1..1 
Supplier Place 
Mandatory 
String (Max 
length:50) 
Bangalore 
Location of the 
Supplier (City/
Town/Village)
4.7 
Supplier_State_
Code
1..1 
Supplier State 
Code 
Mandatory 
Enumerated 
List
29
State Code of 
the Supplier 
as per GST 
System
List published 
and updated 
from time 
to time at 
https://www.
icegate.gov.
in/Webappl/
STATE_ENQ
4.8 
Supplier_
Pincode
1..1 
Supplier PIN 
Code 
Mandatory 
Number 
(Length: 6) 
560087 
PIN Code of 
the Supplier 
Locality
4.9 
Supplier_Phone
0..1 
Supplier 
Phone 
Optional 
String (Max 
length:12) 
9999999999 
Contact 
number of the 
Supplier 
4.10 
Supplier_Email
0..1 
Supplier e-mail Optional 
String (Max 
length:100) 
supplier@abc.
com
e-mail ID of 
the Supplier,as 
per REGEX 
(Regular 
Expressions) 
pattern
5. 
Recipient
Information 
1..1 
Mandatory 
Header for 
Recipient 
Information 
5.1 
Recipient_
Legal_Name
1..1 
Recipient 
Legal Name 
Mandatory 
String (Max. 
length:100) 
PQR Pvt. Ltd. 
It will be 
legal name of 
recipient, as 
per PAN. 
5.2 
Recipient_
Trade_Name
0..1 
RecipientTrade 
Name
Optional 
String (Max
 length:100) 
Adarsha 
It will be 
trade name 
of recipient, if 
available.
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
9
5.3 
Recipient_
GSTIN
1..1 
GSTIN of 
Recipient
Mandatory 
String 
(Length:15) 
29ABCCR
1832C1ZX, 
URP 
GSTIN of the 
Recipient, if 
available. 
URP: In case 
of exports or 
if supplies 
are made to 
unregistered 
persons
5.4 
Place_Of_
Supply_State_ 
Code
1..1 
Place of 
Supply 
(State Code)
Mandatory 
Enumerated 
List
29, 96
Code/State 
Code of Place 
of Supply 
as per GST 
System. 
List published 
and updated 
from time 
to time at 
https://www.
icegate.gov.
in/Webappl/
STATE_ENQ
5.5 
Recipient_
Address1 
1..1 
Recipient 
Address 1 
Mandatory 
String (Max
 length:100) 
# 1-23-120, 
Flat No. 3, 
Nalanda 
Apartments, 
MG Road, 
Vasanth Nagar
Address 1 of 
the Recipient
(Building/Flat 
no., Road/
Street, Locality 
etc.)
5.6 
Recipient_
Address2 
0..1 
Recipient 
Address 2 
Optional 
String (Max
 length:100) 
# 1-23-120, 
Flat No. 3, 
Nalanda 
Apartments, 
MG Road, 
Vasanth Nagar
Address 2, 
if any, of the 
Recipient
(Building/Flat 
no., Road/
Street, Locality 
etc.), if any
5.7
Recipient_Place
1..1
Recipient 
Place
Mandatory
String (Max
 length:100)
Mysore
Location of the 
Recipient
(City/Town/
Village)
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


10 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
5.8 
Recipient_
State_Code
1..1 
Recipient 
State Code
Mandatory
Enumerated 
List
29
Code/State 
Code of the 
Recipient.
List published 
and updated 
from time 
to time at 
https://www.
icegate.gov.
in/Webappl/
STATE_ENQ
5.9 
Recipient_
Pincode
0..1 
Recipient PIN 
Code 
Optional 
Number 
(Length: 6) 
560002 
PIN code of 
the Recipient 
locality.
In case 
of export, 
Pincode 
need not be 
mentioned.
5.10
Country_Code_
of_Export
0..1
Country Code 
of Export
Optional
Enumerated 
List
AN
Code of 
country of 
export as per 
ISO 3166-
1 alpha-2 
/ Indian 
Customs EDI 
system.
List published 
and updated 
from time 
to time at 
https://www.
icegate.gov.
in/Webappl/
COUNTRY_
ENQ
5.11
Recipient_
Phone
0..1 
Recipient 
Phone  
Optional 
String 
(Maxlength:12) 
0802223323 
Contact 
number of the 
Recipient
5.12
Recipient_
email_ID
0..1 
Recipient 
e-mail ID 
Optional 
String (Max
length:100) 
billing@xyz.
com
e-mail ID of 
the Recipient, 
as per REGEX 
(Regular 
Expressions) 
pattern
6.
Payee 
Information 
0..1 
Optional 
Header 
for Payee 
Information  
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
11
6.1  
Payee_Name
0..1 
Payee Name 
Optional
String 
(Maxlength:100) 
Ramesh K
Name of the 
person to 
whom payment 
is to be made 
6.2 
Payee_Bank_
Account_
Number
0..1 
Payee Bank 
Account 
Number 
Optional
String (Max
length:18) 
386850
1747262
Bank Account 
Number of 
Payee 
6.3 
Mode_of_
Payment
0..1 
Mode of 
Payment 
Optional
String (Max
length:18) 
Direct Transfer
Mode of 
Payment:Cash/
Credit/Direct 
Transfer etc.
6.4
Bank _Branch_
Code
0..1 
Bank 
Branch Code 
Optional
String (Max
length:11) 
SBIN
9876543
Indian 
Financial 
System Code 
(IFSC) of 
Payee’s Bank 
Branch
6.5 
Payment_Terms
0..1 
Payment 
Terms 
Optional 
String (Max
length:100) 
Text
Terms of 
Payment, if 
any, with the 
Recipient can 
be provided. 
6.6
Payment_
Instruction
0..1 
Payment 
Instruction 
Optional 
String (Max
 length:100) 
Text
Instruction, if 
any, regarding 
payment can 
be provided 
6.7  
Credit_
Transfer_Terms
0..1 
Credit Transfer 
Terms
Optional 
String (Max
length:100) 
Text  
Terms to 
specify credit 
transfer 
payments. 
6.8 
Direct_Debit_
Terms
0..1 
Direct Debit 
Terms
Optional 
String (Max 
length:100) 
Text
Terms, if any, 
to specify a 
direct debit. 
6.9 
Credit_Days
0..1 
Credit Days 
Optional 
Numeric (Max 
length:4) 
30
Number of 
days within 
which payment 
is due.  
7.
Delivery_
Information
0..1 
Optional
Header for 
Delivery 
Information
7.1
Ship_To_Details
0..1
Ship To 
Details
Optional
Refer  A 1.0
Details of 
location to 
which the 
supply has to 
be delivered.
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


12 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
7.2 
Dispatch_
From_Details
0..1 
Dispatch
From Details 
Optional
Refer  A 1.1
Details of 
location from 
where Supply 
has to be 
dispatched.
8.
Invoice Item 
Details 
1..n
Mandatory
Header for 
Invoice Item 
Details
8.1 
Item_List
1..n
Item List
Mandatory 
Refer  A 1.2
Provides 
information 
about the 
goods and 
services being 
invoiced.
9. 
Document Total
1..1 
Mandatory
Header for 
Document 
Total Details
9.1  
Document 
Total_Details
1..1 
Document
Total Details 
Mandatory 
Refer  A 1.3
Details of 
document 
total including 
taxes.
10.
Extra 
Information 
0..1 
Optional
Header 
for Extra 
Information
10.1  
Tax_Scheme
1..1 
Tax Scheme
Mandatory 
 
String 
(Max 
length: 10) 
GST  
To specify 
the tax/levy 
applicable – 
GST (This 
ﬁ eld is 
mandatory 
only if this 
section is 
selected)
10.2 
Remarks 
0..1 
Remarks
Optional 
String 
(Max 
length: 100) 
New batch 
Items 
submitted 
A textual note 
that gives 
unstructured 
information 
that is 
relevant to 
the Invoice as 
a whole e.g. 
reasons for 
any correction 
or assignment 
note in case 
the invoice 
has been 
factored etc.
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
13
10.3
Port_Code
0..1
Port Code
Optional
Enumerated 
List
Alpha numeric
In case of 
export/supply 
to SEZ, port 
code can be 
mentioned 
as per Indian 
Customs 
EDI System 
(ICES), if 
applicable 
and available 
at the time 
of reporting 
e-invoice.
Lists published 
and updated 
from time to 
time at below 
URLs:
EDI Port 
Codes:
https://www.
icegate.gov.
in/Webappl/
LOCATION_
ENQ
Non-EDI Port 
Codes:
https://www.
icegate.gov.
in/Webappl/
nonlocation_
det_all.jsp
10.4
Shipping_Bill_
Number
0..1
Shipping Bill 
Number
Optional
String (Max 
length: 20)
Alpha numeric
In case of 
export/supply 
to SEZ, 
shipping bill 
number as 
per Indian 
Customs 
EDI System 
(ICES), can 
be mentioned, 
if applicable 
and available 
at the time 
of reporting 
e-invoice.
10.5
Shipping_Bill_
Date
0..1
Shipping Bill 
Date
Optional
String
(DD/MM/ 
YYYY) 
03/12/2020
Date of 
Shipping Bill 
as per Indian 
Customs EDI 
System (ICES)
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


14 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
10.6
Export_Duty_
Amount
0..1
Export Duty 
Amount
Optional
Number 
(Max Length: 
12,2)
1200000.50
Amount of 
Export Duty 
in INR, if any, 
applicable 
(in case of 
invoices for 
export)
10.7
Supplier_Can_
Opt_Refund
0..1
Supplier Can 
Opt Refund
Optional 
String 
(Length: 1)
Y / N
In case of 
deemed 
export 
supplies, this 
ﬁ eld is for 
mentioning 
whether 
supplier can 
exercise 
the option 
of claiming 
refund or not.
10.8
ECOM_GSTIN 
0..1 
e-Commerce 
Operator’s 
GSTIN 
Optional 
String 
(Length: 15) 
29ABCCR
1832C1CX
GSTIN of 
e-commerce 
operator, if 
supply is 
made through 
him/her.
11.
Additional_
Supporting_
Documents
0..n
Optional   
Header for 
Additional 
Supporting 
Documents
11.1  
Additional_
Supporting_
Documents_
URL
0..1 
Additional 
Supporting 
Documents 
URL
Optional 
String 
(Max length: 
100) 
http://www.xyz.
com/abc
This is to 
enter URL 
reference of 
additional 
supporting 
documents, if 
any.  
11.2  
Additional_
Supporting 
_Documents_
base64
0..1 
Additional
Supporting 
Document 
in base64
Optional 
String 
(Max length: 
1000) 
Base 64 
encoded 
Document 
This is to add 
any additional 
document in 
PDF/Microsoft 
Word in 
Base64 
encoded 
format.
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
15
11.3
Additional_
Information
0..1
Additional 
Information
Optional
String 
(Max length: 
1000)
Free text, 
remarks, 
identiﬁ ers, etc.
Any additional 
information, 
names, 
values, data 
etc. that is 
speciﬁ c for 
the Supplier-
Recipient 
transaction 
e.g. CIN, 
trade-speciﬁ c 
information, 
Drug Licence 
Reg. No., 
FOB/CIF etc.
12.
E-way Bill 
Details 
0..1 
Optional 
Header for 
e-way Bill 
Details
12.1  
Transporter_ID
0..1 
Transporter 
ID
Optional 
String (Length: 
15)
29AADFV
7589C1ZO 
Registration 
/ Enrolment 
Number of the 
transporter 
(This ﬁ eld 
is required 
if Part-A of 
E-waybill 
has to be 
generated)
12.2  
Trans_Mode
0..1 
Mode of 
Transportation 
Optional
Enumerated 
List
1/2/3/4
Option to be 
provided based 
on mode 
of transport 
available on 
e-Way Bill 
Portal
1 for Road;
2 for Rail;
3 for Air;
4 for Ship 
(This ﬁ eld 
is required 
if Part-B of 
e-way bill is 
also to be 
generated)
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


16 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
12.3 
Trans_Distance
1..1 
Distance of 
Transportation 
Mandatory
Number (Max 
length: 4)
200
Distance of 
Transportation
(This ﬁ eld is 
mandatory only 
if this section 
is selected)
12.4  
Transporter_
Name
0..1 
Transporter 
Name 
Optional 
String (Max 
length: 100)
Sphurthi 
Transporters
Name of the 
Transporter
12.5  
Trans_Doc_No.
0..1 
Transport 
Document 
Number 
Optional
String (Max 
length: 15)
As/34/746
Transport 
Document 
Number
(This ﬁ eld is 
mandatory 
if mode of 
Transport is 
Rail or Air or 
Ship)
12.6 
Trans_Doc_
Date
0..1 
Transport 
Document 
Date 
Optional
String(DD/MM/
YYYY) 
21/07/2019 
Date of 
Transport 
document.
(This ﬁ eld is 
mandatory 
if mode of 
Transport is 
Rail or Air or 
Ship)
12.7 
Vehicle_No.
0..1 
Vehicle 
Number 
Optional 
String (Max. 
length: 20) 
KA12KA1234  
or  KA12K1234 
or  KA123456  
or  KAR1234
Vehicle 
Registration 
Number
(This ﬁ eld is 
mandatory 
if mode of 
Transport is 
Road)
12.8
Vehicle_Type
 0..1
Vehicle Type 
Optional
Enumeration 
List 
  O / R
To mention 
nature of 
vehicle:
O: Over-
Dimensional 
Cargo 
R: Regular
(This ﬁ eld is 
mandatory 
if Part-B of 
e-way bill is 
also to be 
generated)
A 1.0         
Ship To Details 
0..1 
Optional
Header for 
Annexure A 
1.0:Ship To 
Details
Schema (Version 1.1)
Sr.
No.
Technical 
name of 
the ﬁ eld
Cardi
nality 
(0..1/ 
1..1/ 
0..n/ 
1..n)
Brief
Description of 
the ﬁ eld
Whether
Mandatory/ 
Optional
Technical
Field 
Speciﬁ cation
Sample 
Value of 
the ﬁ eld
Explanatory 
Notes


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
17
Sr.
No.
Parameter 
Name
Cardin
ality
Description
Whether 
optional or 
mandatory
Field 
Speciﬁ cations 
Sample Value
Explanatory 
Notes
A.1.0.1 
Ship
To Legal
Name
1..1 
Ship To Legal 
Name 
Mandatory 
String 
(Max length: 
100)
ABC-1 Ltd.
Legal Name 
of the entity 
to whom the 
supplies are 
shipped to. 
(This ﬁ eld is 
mandatory 
only if this 
section is 
selected)
A.1.0.2 
ShipTo_Trade_
Name
0..1 
Ship To Trade 
Name 
Optional
String 
(Max length: 
100)
XYZ-1
Trade Name 
of the entity 
to whom the 
supplies are 
shipped to.
A.1.0.3 
ShipTo_GSTIN
0..1 
Ship To 
GSTIN 
Optional
String 
(Length:15) 
36AABCT
2223L1ZF 
GSTIN of the 
entity to whom 
the supplies 
are shipped to.
A.1.0.4 
Ship
To Address1 
1..1 
Ship To  
Address1 
Mandatory 
String (Max 
length: 100) 
Flat No. 2, 
Priya Towers, 
Omega 
Road, 
Srinivasa 
Nagar
Address 1 
of the entity 
to whom the 
supplies are 
shipped to 
(This ﬁ eld is 
mandatory only 
if this section 
is selected)
A.1.0.5 
ShipTo_
Address2 
0..1 
Ship To  
Address2 
Optional 
String (Max 
length: 100) 
Flat No. 2, 
Priya Towers, 
Omega Road, 
Srinivasa 
Nagar
Address 2, 
if any, of the 
entity to whom 
the supplies 
are shipped to
A.1.0.6 
ShipTo_Place
1..1 
Ship To  Place
Mandatory 
String (Max 
length: 100) 
Bangalore 
Place (City/
Town/Village) 
of entity to 
whom the 
supplies are 
shipped to. 
(This ﬁ eld is 
mandatory only 
if this section 
is selected)
A.1.0.7 
ShipTo_Pincode
1..1 
Ship To  
Pincode
Mandatory 
Number(Max 
length: 6) 
560001 
PIN code of 
the location 
to which the 
supplies are 
shipped to. 
(This ﬁ eld is 
mandatory only 
if this section 
is selected)


18 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
A.1.0.8 
Ship_To_State_
Code
1..1 
Ship To State 
Code
Mandatory 
Enumerated 
List 
29
Code/State 
Code (as per 
GST System) 
to which the 
supplies are 
shipped to. 
List published 
and updated 
from time 
to time at 
https://www.
icegate.gov.
in/Webappl/
STATE_ENQ
(This ﬁ eld is 
mandatory only 
if this section 
is selected)
  A 1.1    
Dispatch From 
Details
0..1
Optional
Header for 
Annexure A 
1.1:Dispatch 
From Details
A.1.1.1 
Dispatch
From Name
1..1 
Dispatch 
From Name
Mandatory 
String 
(Max 
length:100)
XYZ-2 
Name of 
the entity 
from which 
goods are 
dispatched. 
(This ﬁ eld is 
mandatory 
only if this 
section is 
selected)
A.1.1.2 
DispatchFrom_
Address1 
1..1 
Dispatch 
From 
Address1 
Mandatory 
String 
(Max 
length: 100) 
Building No. 
4/2, Flat No. 
3, Kakatiya 
Apartments, 
Vasanth Nagar
Address 1 
of the entity 
from which 
goods are 
dispatched. 
(This ﬁ eld is 
mandatory 
only if this 
section is 
selected)
A.1.1.3 
DispatchFrom_
Address2 
0..1 
Dispatch 
From 
Address2 
Optional
String 
(Max 
length: 100) 
Building No. 
4/2, Flat No. 
3, Kakatiya 
Apartments,  
Vasanth Nagar
Address 2 
of the entity 
from which 
goods are 
dispatched. 
Sr.
No.
Parameter 
Name
Cardin
ality
Description
Whether 
optional or 
mandatory
Field 
Speciﬁ cations 
Sample Value
Explanatory 
Notes


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
19
A.1.1.4 
Dispatch 
From_Place
1..1 
Dispatch 
From Place 
Mandatory 
String 
(Max 
length: 100) 
Bangalore 
Place (City/
Town/Village) 
of the entity 
from which 
goods are 
dispatched. 
(This ﬁ eld is 
mandatory 
only if this 
section is 
selected)
A.1.1.5 
Dispatch 
From_State_
Code
1..1 
Dispatch 
From State 
Code
Mandatory 
Enumerated 
List  
29
Code/State 
Code of the 
entity (as per 
GST System), 
from which 
goods are 
dispatched. 
List published 
and updated 
from time 
to time at 
https://www.
icegate.gov.
in/Webappl/
STATE_ENQ
(This ﬁ eld is 
mandatory 
only if this 
section is 
selected)
A.1.1.6 
Dispatch 
From_Pincode
1..1 
Dispatch 
From
Pincode
Mandatory 
Number
(Length: 6)
560087 
Pincode of 
the locality 
of entity 
from where 
goods are 
dispatched. 
(This ﬁ eld is 
mandatory 
only if this 
section is 
selected)
A 1.2  
ItemDetails 
1..n
Mandatory 
Header for 
Annexure 
A 1.2:Item 
Details
Sr.
No.
Parameter 
Name
Cardin
ality
Description
Whether 
optional or 
mandatory
Field 
Speciﬁ cations 
Sample Value
Explanatory 
Notes


20 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
Sr.
No.
Parameter 
Name
Description
Whether 
mandatory 
or optional
Field 
Speciﬁ cations
Sample Value
Explanatory 
Notes 
A.1.2.1 
Sl_No. 
1..1 
Serial 
Number 
Mandatory 
String (Max 
length: 6)  
1,2,3 
Serial number 
of the item
A.1.2.2 
Item_
Description
0..1 
Item 
Description 
Optional 
String (Max 
length: 300)  
Mobile 
Description of 
the item 
A.1.2.3 
Is_Service
1..1 
Service 
Mandatory 
String (Length: 
1)
Y/N 
Specify 
whether supply 
is service or 
not.
A.1.2.4 
HSN_Code
1..1 
HSN Code 
Mandatory
String (Max 
length: 8) 
1122 
To enter 
applicable 
HSN / SAC 
Code of 
Goods / 
Service
A.1.2.5 
Batch Details
0..1 
Optional
Refer A 1.4 
Some 
manufacturers 
may mention 
batch details 
(in Section A 
1.4)
A.1.2.6
Barcode 
0..1 
Barcode 
Optional
String (Max 
length: 30) 
b123 
Barcode, if 
any, of the 
item. 
A.1.2.7 
Quantity 
0..1 
Quantity 
Optional
Number (Max 
length: 10,3)
10 
The quantity 
of items to be 
mentioned in 
the invoice. 
This is 
mandatory 
only in case of 
goods.
A.1.2.8 
Free_Qty
0..1 
Free  Quantity
Optional
Number (Max 
length: 10,3)
99
Quantity of 
item(s), if any, 
given free of 
charge (FOC)
A.1.2.9 
Unit_Of_
Measurement
0..1 
Unit of 
Measurement
Optional
String (Max 
length: 8) 
Box 
The Unit of 
Measurement 
(UOM), if any, 
applicable 
on invoiced 
goods.
A.1.2.10 
Item_Price
1..1 
Item Price 
Mandatory 
Number 
(Max length : 
12,3)
500.5 
Price per unit 
item.


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
21
A.1.2.11
Gross_Amount
1..1 
Gross  
Amount
Mandatory
Number 
(Max length : 
12,2)
5000 
The gross 
price of an 
item (cost 
multiplied 
by quantity 
-rounded oﬀ  
to 2 decimal), 
exclusive of 
taxes.
A.1.2.12 
Item_Discount_
Amount
0..1 
Item Discount 
Amount 
Optional 
Number 
(Max length: 
12,2)
10.25
Discount 
amount, if any, 
for the item.
A.1.2.13
Pre_Tax_Value
0..1
Pre-Tax Value
Optional
Number 
(Max length: 
12,2)
99.00
If pre-tax value 
is diﬀ erent 
from taxable 
value, mention 
the pre-tax 
value and 
taxable values 
separately. 
In some 
cases, the pre-
tax value may 
be diﬀ erent 
from taxable 
value.  
For example, 
where old 
goods are 
exchanged for 
new ones (e.g. 
new phone 
supplied for 
INR 20,000 
along with 
exchange of 
old phone, 
then pre-tax 
value would 
be INR 20,000 
and taxable 
value would be 
INR 24,000, 
assuming 
exchange 
value of old 
phone is 
4,000.  
Another 
example is 
in the case 
of real estate 
where pre-tax 
value may be 
diﬀ erent from 
taxable value.  
Sr.
No.
Parameter 
Name
Cardinality
Description
Whether 
mandatory 
or optional
Field 
Speciﬁ 
cations
Sample Value
Explanatory 
Notes 


22 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
A.1.2.14 
Item_Taxable_
Value
1..1 
Item Taxable 
Value 
Mandatory 
Number
(Max length: 
12,2)   
5000 
This is the 
value on 
which tax is 
computed. 
Value cannot 
be negative. 
A.1.2.15 
GST_Rate
1..1 
GST Rate 
Mandatory 
Number (Max 
length: 3,3)
5 
The GST rate, 
represented 
as percentage 
that applies to 
the invoiced 
item. It will be 
IGST rate or 
sum of CGST 
& SGST 
Rates.
A.1.2.16 
IGST_Amt
0..1 
IGST Amount  
Optional
Number 
(Max Length: 
12,2)
999.45 
Amount 
of IGST 
payable per 
item(rounded 
oﬀ  to 2 
decimals). 
If IGST is 
reported, 
then CGST & 
SGST/UTGST 
will be blank. 
For taxable 
supplies, 
either IGST or 
CGST &SGST/
UTGST should 
be reported.
A.1.2.17
CGST_Amt
0..1 
CGST Amount 
Optional 
Number 
(Max Length: 
12,2)
650.00 
Amount 
of CGST 
payable per 
item(rounded 
oﬀ  to 2 
decimals).
If CGST is 
reported, then 
SGST/UTGST 
has to be 
reported and 
IGST will be 
blank. 
A.1.2.18
SGST_UTGST 
Amt 
0..1 
SGST/UTGST 
Amount 
Optional  
Number (Max 
length: 12,2)
650.00 
Amount of 
SGST/UTGST 
payable per 
item(rounded 
oﬀ  to 2 
decimals).
If SGST/
UTGST is 
reported, then 
CGST must be 
reported and 
IGST will be 
blank.
Sr.
No.
Parameter 
Name
Cardinality
Description
Whether 
mandatory 
or optional
Field 
Speciﬁ 
cations
Sample Value
Explanatory 
Notes 


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
23
A1.2.19
Comp_Cess_
Rate_Ad_
valorem
0..1
Compensation 
Cess Rate, 
Ad_Valorem
Optional
Number 
(Max 
length:3,3)
2.5%
Ad 
valoremRate 
of GST 
Compensation 
Cess, 
applicable, if 
any
A1.2.20
Comp_Cess_
Amt_ Ad_
Valorem
0..1
Compensation 
Cess Amount, 
Ad Valorem 
Optional
Number 
(Max length: 
12,2)
56.00
GST 
Compensation 
Cess amount, 
ad valorem 
(rounded oﬀ  
to 2 decimals) 
(based on 
value of the 
item)
A1.2.21
Comp_Cess_
Amt_Non_Ad_
Valorem
0..1
Compensation 
Cess Amount, 
Non ad 
valorem 
Optional
Number 
(Max 
length:12,2)
23.00
GST 
Compensation 
Cess amount, 
computed 
on the basis 
other than 
value of item 
(i.e. speciﬁ c 
cess amount 
computed 
based on 
quantity, 
number etc.)
A1.2.22
State_Cess_
Rate_ad_
valorem
0..1
State Cess 
Rate, Ad 
Valorem
Optional
Number 
(Max length: 
3,3)
1.5 %
Ad valorem 
Rate of State/
UT Cess, 
applicable, if 
any
A1.2.23
State_Cess_
Amt_Ad_
Valorem
0..1
State Cess 
Amount, ad 
valorem 
Optional
Number 
(Max 
length: 12,2)
43.00
State/UT 
Cess amount, 
ad valorem 
(based on 
value of the 
item)
A1.2.24
State_Cess_
Amt_Non_Ad_
Valorem
0..1
State Cess 
Amount, 
nonad valorem
Optional
Number
(Max 
length: 12,2)
12.00
State/UT 
Cess amount, 
computed 
on the basis 
other than 
value of item 
(i.e. speciﬁ c 
cess amount 
computed 
based on 
quantity, 
number etc.)
Sr.
No.
Parameter 
Name
Cardinality
Description
Whether 
mandatory 
or optional
Field 
Speciﬁ 
cations
Sample Value
Explanatory 
Notes 


24 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
A.1.2.25
Other_
Charges_Item_
Level
0..1 
Other Charges 
(item level)
Optional 
Number 
(Max length: 
12,2)
874.95
Any other 
charges 
applicable at 
item level. 
These may 
not be part of 
taxable value, 
e.g. in case 
of pure agent 
reimbursement. 
A.1.2.26
Purchase_
Order_Line_
Reference
0..1 
Purchase 
Order Line 
Reference
Optional
String (Max 
length: 50) 
746/ABC/01
Reference 
of Purchase 
Order Line 
A.1.2.27
Item_Total_Amt
1..1 
Item Total 
Amount
Mandatory 
Number  
(Max length: 
12,2)
5000 
The item total 
value that 
includes all 
taxes, cesses, 
as well as 
other charges. 
However, this 
value excludes 
discount, if 
any. 
A.1.2.28
Origin_
Country_Code
0..1 
Code of 
Country of 
Origin 
Optional 
Enumerated 
List
  DZ
This is to 
specify country 
of origin of 
the item, e.g. 
mobile phone 
sold in India 
could be 
manufactured 
in other 
country; 
Code of 
country of 
export as per 
ISO 3166-
1 alpha-2 
/ Indian 
Customs EDI 
system (ICES).
List published 
and updated 
from time 
to time at 
https://www.
icegate.gov.
in/Webappl/
COUNTRY_
ENQ
Sr.
No.
Parameter 
Name
Cardinality
Description
Whether 
mandatory 
or optional
Field 
Speciﬁ 
cations
Sample Value
Explanatory 
Notes 


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
25
A.1.2.29
Unique_Serial_
Number
0..1 
Unique Serial 
Number   
Optional
String 
(Max 
length: 20)
553
Serial 
number, in 
case of each 
item having 
a unique 
number.
A.1.2.30
Product_
Attribute_
Details
0..n
Optional 
Refer  A 1.5
Attribute 
details of 
product
A 1.3          Document Total 
Details 
  1..1
  
Mandatory
Header for 
Annexure A 
1.3:Document 
Total Details 
A.1.3.1 
Taxable_Value_
Total
1..1
Total Taxable 
Value 
Mandatory
Number
 (Max length: 
14,2)
768439.35
This is the 
sum of the 
taxable values 
of all the 
items in the 
document.  
A.1.3.2 
IGST_Amt_
Total
0..1 
Total IGST 
Amount
Optional
Number (Max 
length : 14,2)
265.50
Total IGST 
amount for the 
invoice.
Appropriate 
taxes based 
on rule will be 
applicable. 
For example, 
either of CGST 
& SGST/
UTGST or 
IGST will be 
mandatory. 
As this is 
conditional 
mandatory, it 
is marked as 
‘optional’
A.1.3.3
CGST_Am_
Total
0..1 
Total CGST 
Amount
Optional
Number 
(Max length: 
14,2)
  65.45
Total CGST 
amount for the 
invoice.
Appropriate 
taxes based 
on rule will be 
applicable. 
For example, 
either of 
CGST & 
SGST/UTGST 
or IGST will 
be mandatory. 
As this is 
conditional 
mandatory, it 
is marked as 
‘optional’
Sr.
No.
Parameter 
Name
Cardinality
Description
Whether 
mandatory 
or optional
Field 
Speciﬁ 
cations
Sample Value
Explanatory 
Notes 


26 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
A.1.3.4 
SGST_
UTGST_Amt_
Total
0..1 
Total SGST/
UTGST 
Amount
Optional
Number 
(Max length : 
14,2)
  65.45
Total SGST/
UTGST 
amount for the 
invoice.
Appropriate 
taxes based 
on rule will 
be applicable. 
For example, 
either of 
CGST & 
SGST/UTGST 
or IGST will 
be mandatory. 
As it is 
conditional 
mandatory, it 
is marked as 
‘optional’
A.1.3.5 
Comp_Cess_
Amt_Total
0..1 
Total 
Compensation 
Cess Amount 
Optional
Number 
(Max length : 
14,2)
24.95
Total GST 
Compensation 
Cess amount 
for the invoice 
(ad valorem 
as well 
as non-ad 
valorem)
A.1.3.6
State_Cess_
Amt_Total
0..1 
Total State 
Cess Amount 
Optional
Number 
(Max length : 
14,2)
5.45
Total State 
cess amount 
for the invoice 
(ad valorem 
as well 
as non-ad 
valorem)
A.1.3.7
Discount_Amt_
Invoice_Level
0..1
Invoice Level 
Discount 
Amount
Optional
Number 
(Max length: 
14,2)
100.00
This is 
Discount 
Amount, if 
any, applicable 
on total 
invoice value
A.1.3.8
Other_
Charges_
Invoice_Level
0..1
Other Charges 
(Invoice Level)
Optional 
Number
(Max length: 
14,2)
200.00
This is Other 
charges, 
if any,  
applicable on 
total invoice 
value
A.1.3.9
Round_Oﬀ _
Amount
0..1 
Round Oﬀ  
Amount 
Optional
 Number
(Max length: 
2,2)
31.21
This is round 
oﬀ  amount of 
total invoice 
value  
A.1.3.10
Total_Invoice_
Value_INR
1..1 
Total Invoice 
Value in INR 
Mandatory 
Number 
(Max length: 
14,2)
745249678.50
The total value 
of invoice 
including 
taxes/GST and 
rounded to 
two decimals 
maximum.
Sr.
No.
Parameter 
Name
Cardinality
Description
Whether 
mandatory 
or optional
Field 
Speciﬁ 
cations
Sample Value
Explanatory 
Notes 


 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY 
27
A.1.3.11
Total_Invoice_
Value_FCNR
0..1
Total Invoice 
Value in 
FCNR
Optional
Number 
(Max length: 
14,2)
$5729.65
The total value 
of invoice in 
Additional 
Currency
A.1.3.12 
Paid_Amount
0..1 
Paid Amount 
Optional 
Number
(Max 
length:14,2)
8463.50
The amount, if 
any, which has 
been paid in 
advance. 
It must be 
rounded to 
maximum 2 
decimals. 
A.1.3.13
Amount_Due_ 
0..1 
Amount Due 
Optional 
Number (Max 
length:14,2)
98789.50
The 
outstanding 
amount due 
for payment. 
It must be 
rounded to 
maximum 2 
decimals. 
A 1.4          
Batch Details 
0..1 
Optional
Header for 
Annexure 
A 1.4:Batch 
Details
A.1.4.1
Batch_Number
1..1 
Batch Number 
Mandatory 
String 
(Max Length: 
20) 
673927
Certain set of 
manufacturers 
may mention 
batch number 
details. 
(This ﬁ eld is 
mandatory 
only if this 
section is 
selected)
A.1.4.2
Batch_Expiry_ 
Date 
0..1 
Batch Expiry 
Date 
Optional  
String
(DD/MM/YYYY) 
21/11/2019
Expiry Date 
of the Batch, 
if any 
A.1.4.3
Warranty_Date
0..1 
Warranty Date 
Optional 
String
(DD/MM/YYYY)
21/11/2019
Warranty date 
for the Item, if 
any.
A 1.5          
Attribute 
Details of Item
0..n
Optional
Header for 
Annexure A 
1.5:Attribute 
Details of Item
A.1.5.1
Attribute_Name
0..1
Attribute Name
Optional 
String 
(Max Length: 
100) 
Colour
Attribute Name 
of the item.
A.1.5.2
Attribute_Value
0..1 
Attribute Value
Optional 
String
(Max Length: 
100) 
Red, green, etc.
Attribute Value 
of item.”.
  
Sr.
No.
Parameter 
Name
Cardinality
Description
Whether 
mandatory 
or optional
Field 
Speciﬁ 
cations
Sample Value
Explanatory 
Notes 


28 
TAMIL  NADU  GOVERNMENT  GAZETTE  EXTRAORDINARY
 
PRINTED AND PUBLISHED BY THE COMMISSIONER OF STATIONERY AND PRINTING, CHENNAI 
ON BEHALF OF THE GOVERNMENT OF TAMIL NADU
NOTIFICATION UNDER THE TAMIL NADU GOODS AND SERVICES TAX RULES, 2017
ERRATUM TO NOTIFICATION.
[G.O. Ms. No.122, Commercial Taxes and Registration (B1), 31st July 2020, Aadi 16, Saarvari, 
Thiruvalluvar Aandu-2051.]
No. SRO A/26(a-2)/2020.
The following erratum is issued to the Commercial Taxes and Registration Department Notiﬁ cation No.SROA-17(b)/2020, 
published at page 4 in Part III-Section I(a) of the Tamil Nadu Government Gazette, Extraordinary dated the 13th April, 2020, 
namely:- 
Eකකඉගඝඕ.
In the said Notiﬁ cation, at page 4,-
(a) in lines 3 and 6, for ''Central Goods and Services Tax Rules, 2017'', read ”Tamil Nadu Goods and Services Tax Rules, 
2017’’; and
(b) in line 4, for ”Central Goods and Services Tax (Fourth Amendment) Rules, 2020”, read ”Tamil Nadu Goods and Services 
Tax (Fourth Amendment) Rules, 2020’’.
Dr. BEELA RAJESH,
 Secretary to Government.
