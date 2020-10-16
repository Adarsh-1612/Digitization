# -*- coding: utf-8 -*-
"""
Created on Mon Sep  7 11:29:49 2020

@author: hp
"""

import tabula
import pandas as pd
import numpy as np
from datetime import datetime as dt

# function to merge the Description column
def concat_desc( df, start_row):

    for j in range(start_row, len(df)):

        prev_row=j-1

        while j<len(df) and pd.isna(df['Balance'][j]):

            df['Description'][prev_row]=str(df['Description'][prev_row])+" "+str(df['Description'][j])

            j+=1

    df.dropna(subset=['Balance'],inplace=True)
    df.reset_index(drop=True,inplace=True)
    return df

def old_format(tables,master_table2):
    for i in range(len(tables)):

        df_copy=tables[i].copy()

        #identifying start of trasaction inside datframe

        header_row=-1
        for j in range(len(df_copy)):
            if type(df_copy.iloc[j,0])==str and df_copy.iloc[j,0]=='Date':
                      header_row=j
                      date_col=0
                      df_copy=df_copy.rename(columns={df_copy.keys()[0]: 'Date'})
                      break
                    

        #if dataframe is valid; identifying the columns and renaming them

        if header_row!=-1:

            for k in range(len(df_copy.columns)):

                if type(df_copy.iloc[header_row,k])==str and df_copy.iloc[header_row,k]=='Balance':

                    df_copy=df_copy.rename(columns={df_copy.keys()[k]: 'Balance'})

                if type(df_copy.iloc[header_row,k])==str and df_copy.iloc[header_row,k].startswith('Description'):

                    df_copy=df_copy.rename(columns={df_copy.keys()[k]: 'Description'})

                if type(df_copy.iloc[header_row,k])==str and df_copy.iloc[header_row,k].find('Deposit')!=-1:

                    df_copy=df_copy.rename(columns={df_copy.keys()[k]: 'Deposit'})

                if type(df_copy.iloc[header_row,k])==str and df_copy.iloc[header_row,k].startswith('Withdrawal'):

                    df_copy=df_copy.rename(columns={df_copy.keys()[k]: 'Withdrawal'})
            if len(df_copy.columns)==5 or len(df_copy.columns)==6:
                    #removing dates from descriptions
                    for j in range(len(df_copy)):
                        if not pd.isna(df_copy['Date'][j]):
                          df_copy['Description'][j]=df_copy['Description'][j][10:]

            #to handle one exception in pdf - 5-unlocked table[1]

            if len(df_copy.columns)==9:
                  df_copy['Balance']=df_copy.iloc[1:,8]
                  df_copy.drop([df_copy.columns[-1]],inplace=True,axis=1)

            df_copy=concat_desc(df_copy,header_row+2)

                #dropping the extra columns and framing the final df
            if len(df_copy.columns)>7:
                  df_copy.dropna(axis=1,how='all',inplace=True)

            if len(df_copy.columns)==7:
                  df_copy.drop(df_copy.columns.difference(['Date','Balance','Description','Deposit','Withdrawal']),axis=1, inplace=True)

                #adding dates to trasactions of same day
                #here the number columns will either be 6 or 7
            df_copy['Date']=df_copy[['Date']].fillna(method='pad')
            master_table2=pd.concat([master_table2,df_copy[1:]])

    return master_table2

def new_format(path,passcode,master_table):
    tables = tabula.read_pdf(path,stream=True,password=passcode,area=[207,27,688,569],pages='all',columns=[71,113,328,371,437,507])
    for i in range(len(tables)) :
       df_copy=tables[i].copy()
       if df_copy.columns[0] != 'Date':
          df_copy.loc[max(df_copy.index)+1,:] = None
          df_copy = df_copy.shift(1,axis=0)
          df_copy.iloc[0] = df_copy.columns
          if len(df_copy.columns) == 7:
              df_copy.columns = ['Date', 'Value Date', 'Description', 'Cheque','Deposit','Withdrawal','Balance']
       df_copy=concat_desc(df_copy,1)

       #dropping the extra columns and framing the final df
       if len(df_copy.columns)==7:
            df_copy.drop(df_copy.columns.difference(['Date','Balance','Description','Deposit','Withdrawal']),axis=1, inplace=True)

        #adding dates to trasactions of same day
        #here the number columns will either be 6 or 7
       df_copy['Date']=df_copy[['Date']].fillna(method='pad')
       master_table=pd.concat([master_table,df_copy[1:]])
    return master_table


def standard_chartered_digitization(pdf_path,out_path):

    file_name=pdf_path.split('/')[-1][:-4]
    master_table2=pd.DataFrame()
    passcode=''

    try:
        #if file is encrypted but with empty password
        tables = tabula.read_pdf(pdf_path,pages='all',stream=True,password=passcode)
    except:
        passcode=input("Enter the Password:")
        tables = tabula.read_pdf(pdf_path,pages='all',stream=True,password=passcode)


    if len(tables)==0:

        print("This is an image-based statement, hence, cannot be digitized here")

        return

    #to oversee the warning to concatenate descriptions/narrations

    pd.options.mode.chained_assignment = None
    check_df=tables[0].copy()
    for a in range(len(check_df)):
        same=0
        if type(check_df.iloc[a,0])==str and check_df.iloc[a,0].find('Date   Value Description')!=-1:
            same =-1
            master_table2=new_format(pdf_path,passcode,master_table2)
            break
    if same==0:
            same=-2
            master_table2=old_format(tables,master_table2)


    master_table2=master_table2[master_table2['Description']!="BALANCE FORWARD"]
    master_table2.reset_index(inplace=True,drop=True)  
    if (not(master_table2.iloc[-1,2]!=master_table2.iloc[-1,2]) and not(master_table2.iloc[-1,3]!=master_table2.iloc[-1,3])):
        master_table2=master_table2.iloc[:-1]


    
    if (same==-2):
        account_name=tables[0].iloc[1,tables[0][tables[0].columns[1]].first_valid_index()]
        for i in range(len(tables[0])):
            for j in range(len(tables[0].columns)):
                if tables[0].iloc[i,j]=="ACCOUNT NO. :":
                    account_no="'{}'".format(tables[0].iloc[i,j+1])
                    break
                
    if same==-1:
        account_info = tabula.read_pdf(pdf_path,stream=True, password=passcode, area=[51,27,207,568], pages='1', pandas_options={'header': None},columns=[315,404])
        account_detail= account_info[0].copy()
        for x in range(len(account_detail)):
           if type(account_detail.iloc[x,1])==str and account_detail.iloc[x,1]=='ACCOUNT NO:':
             account_no=account_detail.iloc[x,2]
             account_name= account_detail.iloc[0,0]
           if type(account_detail.iloc[x,1])==str and account_detail.iloc[x,1]=='STATEMENT DATE :':
             statement_date=account_detail.iloc[x,2]
             year=account_detail.iloc[x,2][7:12]
             master_table2['Date']=master_table2['Date'].apply(lambda x:'{} {}'.format(x,year))
             
             
    master_table2['Account Name'] = account_name
    master_table2['Account Number'] = account_no
    master_table2.rename(columns={'Date':'Txn Date','Withdrawal':'Debit','Deposit':'Credit'}, inplace=True)
    master_table2 = master_table2[['Txn Date', 'Description', 'Debit', 'Credit', 'Balance', 'Account Name','Account Number']]
    master_table2['Txn Date'] = [dt.strftime(pd.to_datetime(x,dayfirst=True),"%d-%m-%Y") for x in master_table2['Txn Date']]
    last_trans_date = master_table2['Txn Date'].iat[-1]

    #conversion into csv
    master_table2.to_csv("{}/{}_{}_{}.csv".format(out_path,file_name, account_no, last_trans_date),index=False)

try:
    standard_chartered_digitization(r"C:/Users/hp/Downloads/STANDARD CHARTERED (1-1-20 TO 21-8-20  GDM psd 52206029027.pdf",r"C:/Users/hp/Downloads") 
except:
    print("\nThis statement cannot be digitized.\n")
