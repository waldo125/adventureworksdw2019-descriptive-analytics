from sqlalchemy import create_engine
import pandas as pd
from dotenv import load_dotenv
import os
import numpy as np
import matplotlib.pyplot as plt
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Load enviornment variables in order to connect to SQl Server and read SQL script.  
load_dotenv()
server = os.getenv('server')
database = os.getenv('database')
driver = os.getenv('driver')
sql_file = os.getenv('sql_file')
pdf_file = os.getenv('pdf_file')

# Connect to SQL Server using the environment variables from above.
con = None
connection_string = f"mssql://@{server}/{database}?driver={driver}"
engine = create_engine(connection_string)
con = engine.connect()

# Open and read SQL script from the following directory.
file = f"{sql_file}"
with open(file) as f:
    query_string = f.read()

# Returns a DataFrame corresponding to the result set of the query string.
df = pd.read_sql_query(query_string,con)
con.close()

index = "selling_day"
columns = "year_month"
values = ["year_month_day_revenue","cumulative_year_month_day_revenue"]
chart = df.pivot(index,columns,values)

# The independant variables.
selling_days = list(chart.index)

# The dependant variables.
old_rev = []
new_rev = []
old_cum_rev = []
new_cum_rev = []

for y1,y2,y3,y4 in chart.values:
    old_rev.append(y1)
    new_rev.append(y2)
    old_cum_rev.append(y3)
    new_cum_rev.append(y4)

# The labels used in the visualization.
labels = list(set(df.year_month.to_list()))

# The visualization
fig, (lines,bars) = plt.subplots(figsize=(20,8),nrows=2, ncols=1,sharex=True)

lines.plot(selling_days,old_cum_rev,marker="o",markerfacecolor='black', color='darkorange',label=labels[0])
lines.plot(selling_days,new_cum_rev,marker='o', markerfacecolor='black', color='dodgerblue',label=labels[1])
lines.grid()
lines.set_title("Cumulative Revenue",fontweight="bold")
lines.set_ylabel("Revenue")

width = 0.3
x = np.asarray(list(chart.index))
bars.bar(x - width/2,old_rev,width,color="darkorange",label=labels[0],edgecolor="black")
bars.bar(x + width/2,new_rev,width,color="dodgerblue",label=labels[1],edgecolor="black")
bars.grid()
bars.set_title("Daily Revenue",fontweight="bold")
bars.set_ylabel("Revenue")
bars.set_xlabel("Selling Day")
bars.legend(loc='upper center', bbox_to_anchor=(0.09, -0.08),fancybox=True, shadow=True, ncol=5)


plt.xticks(selling_days)
fig.savefig(f"{pdf_file}")

# Retrieving the selling day, which is used for the year over year comparison. 
comp_day = int(df[df["year_month_day"] == max(df.year_month_day)].selling_day.values)

# Retrieving the new and old dates used in the year over year comparison.
old_date = min(df[df["selling_day"] == comp_day].year_month_day)
new_date = max(df[df["selling_day"] == comp_day].year_month_day)

new_cum_amt = float(df[df["year_month_day"] == new_date].cumulative_year_month_day_revenue.values)
old_cum_amt = float(df[df["year_month_day"] == old_date].cumulative_year_month_day_revenue.values)
new_amt = float(df[df["year_month_day"] == new_date].year_month_day_revenue.values)
old_amt = float(df[df["year_month_day"] == old_date].year_month_day_revenue.values)

# This is a year over year comparison of both cumulative and daily revenue.
a = "{}:\n-Daily revenue of ${} and cumulative revenue of ${}.".format(new_date,new_amt,new_cum_amt)
b = "{}:\n-Daily revenue of ${} and cumulative revenue of ${}.".format(old_date,old_amt,old_cum_amt)

def pdf_to_mail(pdf_file):
    
    session = None
    load_dotenv()
       
    try:
    
        email_sender = os.getenv('email_sender')
        email_sender_password = os.getenv('email_sender_password')
        email_receiver = os.getenv('email_receiver')
        
        session = smtplib.SMTP('smtp.gmail.com',587)
        session.ehlo()
        session.starttls()
        session.login(email_sender,email_sender_password)
        
        email_subject = "Email subject goes here"

        # email body
        email_body = "Hello,\nPlease see my comments below.\n\n{}\n\n{}\n\nThank you".format(a,b)

        msg = MIMEMultipart()
        msg['From'] = email_sender
        msg["To"] = email_receiver
        msg["Subject"] = email_subject
        msg.attach(MIMEText(email_body,"plain"))
        
        pdfname = pdf_file
        binary_pdf = open(pdfname,"rb")

        payload = MIMEBase('application','octet-stream',name=pdfname)
        payload.set_payload((binary_pdf).read())
        encoders.encode_base64(payload)
        payload.add_header("Content-Disposition","attachment", filename=os.path.basename(pdf_file))
        msg.attach(payload)
        
        text = msg.as_string()

        # send email
        session.sendmail(email_sender,email_receiver,text)

    except Exception as e:
        print(e)
        
    finally:
        if session is not None:
            session.quit()
            print("mail sent")

pdf_to_mail(f"{pdf_file}")