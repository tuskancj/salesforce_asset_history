#This script will read in multiple reports from Salesforce and Netsuite 
#to provide a full service history & cost analysis by service contract period
#   View README for more information

import pandas as pd
import numpy as np
import plotnine as plt
import janitor

#set variables
forCustomer = False #change to false if looking at internal costs
hourly_rate = 375 #current organizational hourly rate (USD)
if not forCustomer:
   hourly_rate = 125 #based on $1000/day standard cost to company

#read in and tidy cases & work orders
df_cases = pd.read_csv('cases.csv')
df_cases = janitor.clean_names(df_cases)
df_cases = df_cases.rename(columns={'type':'case_type', 
                                    'work_type_work_type_name':'wo_type', 
                                    'status':'case_status', 
                                    'work_order_number':'wo_number', 
                                    'status_1':'wo_status', 
                                    'account_name_account_name':'account_name', 
                                    'asset_product_product_name':'product_name', 
                                    'asset_serial_number':'serial_number', 
                                    'description':'case_description',
                                    'case_owner_full_name':'case_owner',
                                    'owner_full_name':'wo_owner'})
df_cases = df_cases.astype({'case_number':str, 
                            'wo_number':str})
df_cases[['incident_date']] = df_cases[['incident_date']].apply(pd.to_datetime, format = '%m/%d/%Y', errors = 'coerce')
df_cases.drop_duplicates(inplace=True) #will remove duplicate rows only if exactly the same.  same case, diff WO# remain

#read in and tidy contracts
df_contracts = pd.read_csv('contracts.csv')
df_contracts = janitor.clean_names(df_contracts)
df_contracts = df_contracts.rename(columns={'account_name_account_name':'account_name', 
                                            'asset_serial_number':'serial_number', 
                                            'asset_product_product_name':'product_name', 
                                            'account_name_primary_technician_name':'primary_technician',
                                            'asset_install_date':'install_date'})
df_contracts = df_contracts.astype({'contract_number':str})
df_contracts[['contract_start_date', 'contract_end_date', 'install_date']] = df_contracts[['contract_start_date', 'contract_end_date', 'install_date']].apply(pd.to_datetime, format = '%m/%d/%Y', errors = 'coerce')
df_contracts.drop_duplicates(inplace=True)

#read in and tidy timesheets
df_time = pd.read_csv('timesheets.csv')
df_time = janitor.clean_names(df_time)
df_time = df_time.rename(columns={'work_order_number':'wo_number',
                                  'time_sheet_name':'ts_name',
                                  'name':'ts_entry_name',
                                  'account_account_name':'account_name',
                                  'work_type_work_type_name':'wo_type',
                                  'asset_serial_number':'serial_number',
                                  'owner_full_name':'wo_owner',
                                  'duration_in_hours':'ts_duration_in_hours',
                                  'start_time':'ts_start_time',
                                  'end_time':'ts_end_time',
                                  'created_date':'ts_created_date',
                                  'type':'ts_type'})
df_time = df_time.astype({'wo_number':str})
df_time[['ts_start_time', 'ts_end_time']] = df_time[['ts_start_time', 'ts_end_time']].apply(pd.to_datetime, format = '%m/%d/%Y %I:%M %p', errors = 'coerce')
df_time[['ts_created_date']] = df_time[['ts_created_date']].apply(pd.to_datetime, format = '%m/%d/%Y', errors = 'coerce')
df_time.drop_duplicates(inplace=True)

#read in and tidy part consumption
df_parts = pd.read_csv('parts.csv')
df_parts = janitor.clean_names(df_parts)
df_parts = df_parts.rename(columns = {'work_order_number':'wo_number',
                            'asset_serial_number':'serial_number',
                            'product_item_product_name_product_name':'item_name',
                            'consumed_product_code':'item_number',
                            'account_account_name':'account_name',
                            'owner_full_name':'wo_owner'})
df_parts = df_parts.astype({'wo_number':str})
df_parts[['created_date']] = df_parts[['created_date']].apply(pd.to_datetime, format = '%m/%d/%Y', errors = 'coerce')
# df_parts.drop_duplicates(inplace=True)

#read in and tidy part pricing
df_part_pricing = pd.read_csv('part_pricing.csv')
df_part_pricing = janitor.clean_names(df_part_pricing)
df_part_pricing = df_part_pricing.rename(columns={'item':'item_number', 
                                                  'display_name':'item_desc',
                                                  'unit_price':'sales_price',
                                                  'last_purchase_price':'purchase_price'})
df_part_pricing = df_part_pricing.astype({'item_internal_id':str})
df_part_pricing.drop_duplicates(inplace=True)

#start a master df
df = df_cases.copy()

#gather contract information
for index, row in df_contracts.iterrows():
    if index == 0:
        df['contract_number'] = np.where(
            (df['incident_date'] >= df_contracts['contract_start_date'][index]) &
            (df['incident_date'] <= df_contracts['contract_end_date'][index]), 
            df_contracts['contract_number'][index],
            pd.NA)
        
        df['contract_type'] = np.where(
            (df['incident_date'] >= df_contracts['contract_start_date'][index]) &
            (df['incident_date'] <= df_contracts['contract_end_date'][index]), 
            df_contracts['contract_type'][index],
            'Billable')
    else:
        df['contract_number'] = np.where(
            (df['incident_date'] >= df_contracts['contract_start_date'][index]) &
            (df['incident_date'] <= df_contracts['contract_end_date'][index]), 
            df_contracts['contract_number'][index],
            df['contract_number'])
        
        df['contract_type'] = np.where(
            (df['incident_date'] >= df_contracts['contract_start_date'][index]) &
            (df['incident_date'] <= df_contracts['contract_end_date'][index]), 
            df_contracts['contract_type'][index],
            df['contract_type'])
        
#filter timesheet df and merge total hours with cases df
df_time = df_time[['wo_number', 
                   'ts_entry_name', 
                   'ts_name', 
                   'ts_duration_in_hours', 
                   'ts_start_time', 
                   'ts_end_time',
                   'ts_created_date', 
                   'ts_type']]

df_time = df_time.groupby('wo_number', as_index=False).agg({'ts_duration_in_hours':'sum'})

#ensure time sheet hours is a value, not NA
df_time['ts_duration_in_hours'] = np.where(df_time['ts_duration_in_hours'].isna(), 0, df_time['ts_duration_in_hours'])

#update master df
df = pd.merge(df, df_time, on='wo_number', how='left', validate='m:1')
df['ts_hourly_rate'] = hourly_rate

#ensure no NaN after merge
df['ts_duration_in_hours'] = np.where(df['ts_duration_in_hours'].isna(), 0, df['ts_duration_in_hours'])

#calculate ts total cost
df['ts_total_cost'] = df['ts_duration_in_hours']*df['ts_hourly_rate']

#get the max sales price of each part number (sometimes there are duplicates)
df_part_pricing = df_part_pricing.groupby(['item_number', 'item_desc'], as_index=False).agg({'sales_price':'max', 'purchase_price':'max'})

#merge with serial number parts df and compute total price based on quantity consumed
df_parts = pd.merge(df_parts, df_part_pricing, on='item_number', how='left', validate='m:1')
if forCustomer:
    df_parts['item_total_cost'] = df_parts['quantity_consumed']*df_parts['sales_price']

else:
    df_parts['item_total_cost'] = df_parts['quantity_consumed']*df_parts['purchase_price']

#aggregate total item cost per WO then merge with the master df
df_parts_summary = df_parts.groupby('wo_number', as_index=False).agg({'item_total_cost':'sum'})
df = pd.merge(df, df_parts_summary, on='wo_number', how='left', validate='1:1')

#ensure items total cost is a value, not NA
df['item_total_cost'] = np.where(df['item_total_cost'].isna(), 0, df['item_total_cost'])

#add Work Order total cost column
df['wo_total_cost'] = df['ts_total_cost']+df['item_total_cost']

#write to file
df.to_csv('df.csv')