import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
st.set_page_config(layout='wide')

df_adlb=pd.read_parquet('adlb_final.parquet')
df_adsl=pd.read_parquet('adsl_final.parquet')
df_adae=pd.read_parquet('adae_final.parquet')

tab1,tab2,tab3=st.tabs(['Subject Level','Laboratory','Adverse Events'])

st.sidebar.header('Dashboard Controls')
selected_treatment=st.sidebar.selectbox('Select Treatment',('Placebo', 'Xanomeline High Dose', 'Xanomeline Low Dose'))

adae_toggle=st.sidebar.checkbox('All',value=True)
## ADSL Dashboard
with tab1:
    age_group=['<65','65-80','>80']
    df_adsl['AGEGR1']=pd.Categorical(df_adsl['AGEGR1'],categories=age_group,ordered=True)
    def create_disposition_donut_plots(data,variable):
        figs = {}
        for group in data['ARM'].unique():
            filtered_data = data[data['ARM'] == group]
            fig = px.pie(filtered_data, names=variable, hole=0.5, 
                        title=f'Disposition Summary in {group} Group') 
            fig.update_traces( hovertemplate=
    '<b>%{label}:</b><br>' +
    'Count: %{value:.3g}<br>' +  
    'Percentage: %{percent:.2%}') 
            figs[group] = fig
        return figs

    def create_distribution_plots(data, parameter):
        figs = {}
        par_dict={'BMIBL':'Body Mass Index','WEIGHTBL':'Weight','HEIGHTBL':'Height'}
        for group in data['ARM'].unique():
            filtered_data = data[data['ARM'] == group]
            fig = px.box(filtered_data, x='SEX', y=parameter, 
                        title=f'{par_dict[parameter]} Distribution by Gender in {group} Group')
            fig.update_layout(yaxis_title=par_dict[parameter])
            figs[group] = fig
        return figs

    def create_subject_count_bar_plot(data):
        figs = {}
        for group in data['ARM'].unique():
            filtered_data = data[data['ARM'] == group]
            subject_count = filtered_data.groupby(by=['AGEGR1','SEX'])['SUBJID'].nunique().reset_index()  
            fig = px.bar(subject_count, x='AGEGR1', y='SUBJID', color='SEX',barmode='group',title=f'Number of Subjects by AGE Group in {group} Group')
            fig.update_layout(xaxis_title='Age Group', yaxis_title='Number of Subjects')
            fig.update_traces(hovertemplate=
    '<b>Age Group:</b> %{x}<br>' +
    '<b>Subject Count:</b> %{y:.3g}<br>')
            figs[group] = fig
        return figs

    st.title("Subject Level Analysis")

    col1, col2 = st.columns(2)

    with col1:
        demographic_option=st.selectbox('Select a Variable to view Demographics',('Race','Ethinicity','Disposition'))
        if demographic_option=='Disposition':
            selected_variable='DCDECOD'
        elif demographic_option=='Ethinicity':
            selected_variable='ETHNIC'
        elif demographic_option=='Race':
            selected_variable='RACE'


    with col2:
        distribution_option=st.selectbox('Select type of Distribution',('BMI','Weight','Height'))
        if distribution_option=='BMI':
            selected_characteristic='BMIBL'
        elif distribution_option=='Weight':
            selected_characteristic='WEIGHTBL'
        elif distribution_option=='Height':
            selected_characteristic='HEIGHTBL'


    disposition_plots = create_disposition_donut_plots(df_adsl,selected_variable)

    col1,col2=st.columns(2)
    with col1:
        st.plotly_chart(disposition_plots[selected_treatment], use_container_width=True)

    distribution_plots = create_distribution_plots(df_adsl, selected_characteristic)

    with col2:
        st.plotly_chart(distribution_plots[selected_treatment], use_container_width=True)

    subject_count_plots = create_subject_count_bar_plot(df_adsl)

    with col1:
        st.plotly_chart(subject_count_plots[selected_treatment], use_container_width=True)

with tab2:
    st.title('Laboratory')

    param_dict={'Hemoglobin (mmol/L)':'HGB', 'Hematocrit':'HCT',
       'Ery. Mean Corpuscular Volume (fL)':'MCV',
       'Ery. Mean Corpuscular Hemoglobin (fmol(Fe))':'MCH',
       'Ery. Mean Corpuscular HGB Concentration (mmol/L)':'MCHC',
       'Leukocytes (GI/L)':'WBC', 'Lymphocytes (GI/L)':'LYM', 'Monocytes (GI/L)':'MONO',
       'Eosinophils (GI/L)':'EOS', 'Basophils (GI/L)':'BASO', 'Platelet (GI/L)':'PLAT',
       'Erythrocytes (TI/L)':'RBC'}
    
    ##Function to create a bar group to compare means of Parameters pre-Post treatment
    def pre_post(data,param):
        par=list(param_dict.keys())[list(param_dict.values()).index(param)]
        data=data.groupby(by=['TRTA','AVISIT','PARAMCD'])['AVAL'].mean().reset_index()
        filtered_data=data.rename(columns={'TRTA':'Treatment','AVISIT':'Analysis Visit','AVAL':'Mean'})
        fig=px.bar(filtered_data[((filtered_data['Analysis Visit']=='Baseline') | (filtered_data['Analysis Visit']=='End of Treatment')) & (filtered_data['PARAMCD']==param)],
                    x='Treatment',y='Mean',color='Analysis Visit',barmode='group',
                    title=f'Pre-Post Treatment per Treatment Group for Parameter {par}',
                    hover_data={'Treatment':True,'Analysis Visit':True,'Mean':':.3g'})
        fig.update_layout(yaxis_title=f'{par}',xaxis_title='Treatment')
        return fig


    ##Function to create a line chart and compare treatments with their means per parameter
    def param_trend(data,param):
        par=list(param_dict.keys())[list(param_dict.values()).index(param)]
        data=data.groupby(by=['TRTA','VISIT','PARAMCD'])['AVAL'].agg([('AVAL','mean'),('ASTD','std')]).reset_index()
        filtered_data=data
        filtered_data = filtered_data.rename(columns={'VISIT': 'Visit','AVAL': 'Mean','TRTA': 'Treatment','ASTD': 'Standard Deviation'})
        fig=px.line(filtered_data[filtered_data['PARAMCD']==param],
                x='Visit',y='Mean',color='Treatment',title=f'Mean {par} Value across VISITS',hover_data={'Visit':True,'Mean':':.3g','Treatment':True,'Standard Deviation':':.3g'})
        fig.update_layout(yaxis_title=f'{par}')
        return fig

        
    ##To create a Box plot to understand the distribution of parameters value per treatment across weeks
    def box_treatment(data,param):
        figs={}
        par=list(param_dict.keys())[list(param_dict.values()).index(param)]
        data=data.rename(columns={'VISIT':'Visit','AVAL':'Value','LBNRIND':'Lab Indicator','USUBJID':'Subject ID'})
        for group in data['TRTA'].unique():
            filtered_data=data[data['TRTA']==group]
            fig=px.box(filtered_data[ (filtered_data['PARAMCD']==param)],
                    x='Visit',y='Value',
                    title=f'Distribution of Paramter {par} for Treatment Group {group}',
                    hover_data={'Visit':True,'Value':':.3g','Lab Indicator':True,'Subject ID':True})
            fig.update_layout(xaxis_title='VISIT',yaxis_title=f'{par}')
            figs[group]=fig
        return figs

    ## To create a line chart with SD for the values of Absolute Change and Percentage Change
    def line_with_range(data,param,abs):
        par=list(param_dict.keys())[list(param_dict.values()).index(param)]
        if abs==2:
            data=data.groupby(by=['TRTA','VISIT','PARAMCD'])['ABSVAL'].agg([('ABSVAL','mean'),('ABSSTD','std')]).reset_index()
            data=data[data['VISIT']!='SCREENING 1']
            filtered_data=data[(data['PARAMCD']==param)]
            filtered_data=filtered_data.rename(columns={'TRTA':'Treatment','VISIT':'Visit','ABSVAL':'Mean','ABSSTD':'Standard Deviation'})
            fig=px.line(filtered_data,x='Visit',y='Mean',color='Treatment',hover_data={'Treatment':True,'Visit':True,'Mean':':.3g','Standard Deviation':':.3g'})
            fig.update_layout(title=f'Absolute Change for {par}',xaxis_title='Visit',yaxis_title='Absolute Change')
            return fig
        elif abs==3: 
            data=data.groupby(by=['TRTA','VISIT','PARAMCD'])['PCTVAL'].agg([('PCTVAL','mean'),('PCTSTD','std')]).reset_index()
            data=data[data['VISIT']!='SCREENING 1']
            filtered_data=data[(data['PARAMCD']==param)]
            filtered_data=filtered_data.rename(columns={'TRTA':'Treatment','VISIT':'Visit','PCTVAL':'Mean','PCTSTD':'Standard Deviation'})
            fig=px.line(filtered_data,x='Visit',y='Mean',color='Treatment',hover_data={'Treatment':True,'Visit':True,'Mean':':.3g','Standard Deviation':':.3g'})
            fig.update_layout(title=f'Percentage Change for {par}',xaxis_title='Visit',yaxis_title='Percent Change')  
            return fig

    ## To create Bar graph to view the counts of the dataset per treatment per parameter and classify them according to their Lab Indicator variables
    def faceted_trend(data,param):
        par=list(param_dict.keys())[list(param_dict.values()).index(param)]
        data=data.groupby(by=['TRTA','AVISIT','PARAMCD','LBNRIND'])['USUBJID'].nunique().reset_index()
        data=data[(data['AVISIT']=='Baseline') | (data['AVISIT']=='End of Treatment')]
        data=data[~data['PARAMCD'].str.contains('_W*')]
        column_mapping={'LBNRIND':'Lab Indicator','AVISIT':'Analysis Visit',
                        'TRTA':'Treatment','PARAMCD':'Parameter','USUBJID':'Count'}
        data=data.rename(columns=column_mapping)
        figs={}
        for group in data['Treatment'].unique():
            filtered_data=data[(data['Treatment']==group) & (data['Parameter']==param)]   
            fig=px.bar(filtered_data,x='Analysis Visit',y='Count',color='Lab Indicator',barmode='group',category_orders={'Lab Indicator':['NORMAL','HIGH','LOW']},text='Count',title=f'Pre-Post Lab Indicators for Parameter {par}')
            fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
            fig.update_traces(textposition='inside',textfont=dict(size=14),insidetextanchor='middle')
            figs[group]=fig
        return figs

    def line_with_sd(data,param,abs):
        data['ABLFL']=data['ABLFL'].fillna('N')
        data=data[data['ABLFL']=='N']
        figs={}
        par=list(param_dict.keys())[list(param_dict.values()).index(param)]
        if abs==2:
            data=data.groupby(by=['TRTA','VISIT','PARAMCD'])['ABSVAL'].agg([('ABSVAL','mean'),('ABSSTD','std')]).reset_index()
            data=data[data['VISIT']!='SCREENING 1']
            data['UPPER']=data['ABSVAL']+data['ABSSTD']
            data['LOWER']=data['ABSVAL']-data['ABSSTD']

            for group in data['TRTA'].unique():
                filtered_data=data[(data['TRTA']==group) & (data['PARAMCD']==param)]
                fig=go.Figure([go.Scatter(name='Mean Absolute Change',x=filtered_data['VISIT'],y=filtered_data['ABSVAL'],mode='lines',line=dict(color='rgb(31, 119, 180)'),showlegend=False,hovertemplate=('<b>Visit:</b> %{x}<br>' +'<b>Absolute Change:</b> %{y:.3g}<br>' +'<b>Standard Deviation:</b> %{customdata[0]:.3g}<br>'),customdata=filtered_data[['ABSSTD']]),
                            go.Scatter(name='Upper limit',x=filtered_data['VISIT'],y=filtered_data['UPPER'],mode='lines',marker=dict(color="#444"),line=dict(width=0),fillcolor='rgba(68, 68, 68, 0.3)',fill='tonexty',showlegend=False,hovertemplate=('<b>Visit:</b> %{x}<br>' +'<b>Upper Limit:</b> %{y:.3g}<br>')),
                go.Scatter(name='Lower limit',x=filtered_data['VISIT'],y=filtered_data['LOWER'],mode='lines',marker=dict(color="#444"),line=dict(width=0),fillcolor='rgba(68, 68, 68, 0.3)',fill='tonexty',showlegend=False,hovertemplate=('<b>Visit:</b> %{x}<br>' +'<b>Lower Limit:</b> %{y:.3g}<br>'))])
                fig.update_layout(title=f'Absolute Change for {par} for Treatment Group {group}',xaxis_title='VISIT',yaxis_title='Absolute Change')
                figs[group]=fig
            return figs
        elif abs==3: 
            data=data.groupby(by=['TRTA','VISIT','PARAMCD'])['PCTVAL'].agg([('PCTVAL','mean'),('PCTSTD','std')]).reset_index()
            data=data[data['VISIT']!='SCREENING 1']
            data['UPPER']=data['PCTVAL']+data['PCTSTD']
            data['LOWER']=data['PCTVAL']-data['PCTSTD']

            for group in data['TRTA'].unique():
                filtered_data=data[(data['TRTA']==group) & (data['PARAMCD']==param)]
                fig=go.Figure([go.Scatter(name='Mean Percent Change',x=filtered_data['VISIT'],y=filtered_data['PCTVAL'],mode='lines',line=dict(color='rgb(31, 119, 180)'),showlegend=False,hovertemplate=('<b>Visit:</b> %{x}<br>' +'<b>Absolute Change:</b> %{y:.3g}<br>' +'<b>Standard Deviation:</b> %{customdata[0]:.3g}<br>'),customdata=filtered_data[['PCTSTD']]),
                            go.Scatter(name='Upper limit',x=filtered_data['VISIT'],y=filtered_data['UPPER'],mode='lines',marker=dict(color="#444"),line=dict(width=0),fillcolor='rgba(68, 68, 68, 0.3)',fill='tonexty',showlegend=False,hovertemplate=('<b>Visit:</b> %{x}<br>' +'<b>Upper Limit:</b> %{y:.3g}<br>')),
                go.Scatter(name='Lower limit',x=filtered_data['VISIT'],y=filtered_data['LOWER'],mode='lines',marker=dict(color="#444"),line=dict(width=0),fillcolor='rgba(68, 68, 68, 0.3)',fill='tonexty',showlegend=False,hovertemplate=('<b>Visit:</b> %{x}<br>' +'<b>Lower Limit:</b> %{y:.3g}<br>'))])
                fig.update_layout(title=f'Percentage Change for {par} for Treatment Group {group}',xaxis_title='VISIT',yaxis_title='Percent Change')
                figs[group]=fig
            return figs
        
    col1,col2=st.columns(2)

    with col2:
        parameter_option=st.selectbox('Select a Parameter to View',('Hemoglobin (mmol/L)', 'Hematocrit',
        'Ery. Mean Corpuscular Volume (fL)',
        'Ery. Mean Corpuscular Hemoglobin (fmol(Fe))',
        'Ery. Mean Corpuscular HGB Concentration (mmol/L)',
        'Leukocytes (GI/L)', 'Lymphocytes (GI/L)', 'Monocytes (GI/L)',
        'Eosinophils (GI/L)', 'Basophils (GI/L)', 'Platelet (GI/L)',
        'Erythrocytes (TI/L)'))


    # with col1:
    #     visit_options=st.toggle('View At End Of Treatment')
    #     if visit_options:
    #         donut_plots=create_baseline_end(df,'End of Treatment',param[parameter_option])
    #     else:
    #         donut_plots=create_baseline_end(df,'Baseline',param[parameter_option])
    #     st.plotly_chart(donut_plots[selected_treatment],use_container_width=True)

    pre_post_plot=pre_post(df_adlb,param_dict[parameter_option])

    
    with col1:

        abs_or_pct=st.selectbox('Select Plot Type:',('Mean Change','Mean Absolute Change','Mean Percent Change'))
        if abs_or_pct=='Mean Change':
            abs=1
        elif abs_or_pct=='Mean Absolute Change':
            abs=2
        else:
            abs=3


    abs_plot=line_with_range(df_adlb,param_dict[parameter_option],abs)

    act_trend=param_trend(df_adlb,param_dict[parameter_option])
  

    col1,col2=st.columns(2)

    with col1:  
        if abs==1:
            st.plotly_chart(act_trend,use_container_width=True)
        elif abs==2:
            st.plotly_chart(abs_plot,use_container_width=True)
        else:
            st.plotly_chart(abs_plot,use_container_width=True)

    with col2:
        if abs==1:
            box_plot=box_treatment(df_adlb,param_dict[parameter_option])
            st.plotly_chart(box_plot[selected_treatment],use_container_width=True)
        elif abs==2:
            plot_with_sd=line_with_sd(df_adlb,param_dict[parameter_option],abs)
            st.plotly_chart(plot_with_sd[selected_treatment],use_container_width=True)
        elif abs==3:
            plot_with_sd=line_with_sd(df_adlb,param_dict[parameter_option],abs)
            st.plotly_chart(plot_with_sd[selected_treatment],use_container_width=True)


    col3,col4=st.columns(2)
    with col3:
        st.plotly_chart(pre_post_plot,use_container_width=True)

    with col4:
        facet_plot=faceted_trend(df_adlb,param_dict[parameter_option])
        st.plotly_chart(facet_plot[selected_treatment],use_container_width=True)

with tab3:
    st.title('Adverse Events')
    # Grouping data as per requirements
    df1 = df_adae.groupby(by=['TRTA', 'AEBODSYS', 'ADURN'])['USUBJID'].count().reset_index()
    df2 = df_adae.groupby(by=['TRTA', 'AEBODSYS'])['USUBJID'].count().reset_index()
    df2.rename(columns={'USUBJID': 'Occurrences'}, inplace=True)
    df3 = df_adae.groupby(by=['TRTA', 'AESHOSP'])['ADURN'].sum().reset_index()
    df3.rename(columns={'ADURN': 'Total_Adverse_Event_Duration'}, inplace=True)
    df4 = df_adae.groupby(by=['TRTA', 'AESEV'])['ADURN'].sum().reset_index()
    df5 = df_adae.groupby(['TRTA', 'AEBODSYS', 'AEOUT'])['USUBJID'].count().reset_index()
    df6 = df_adae.groupby(by=['TRTA', 'AEREL'])['AESEV'].count().reset_index()

    if adae_toggle:
        st.header("Adverse Events Overview for All Treatments")


        st.subheader('AE by Subjects')
        fig1 = px.scatter(df1, x='ADURN', y='AEBODSYS', color='TRTA',
                              labels={'ADURN':'Duration','AEBODSYS':'Body System','TRTA':'Treatment'},
                              height=400, width=800)
        fig1.update_layout(margin=dict(l=0, r=0, b=0, t=40), font=dict(size=12))  # Adjusted layout
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader('Occurrences by Treatment')
        fig2 = px.scatter(df2, x='Occurrences', y='AEBODSYS', color='TRTA',
                              labels={'Occurrences': 'Occurrences', 'AEBODSYS': 'Body System', 'TRTA': 'Treatment'},
                              height=400, width=800)
        fig2.update_layout(margin=dict(l=0, r=0, b=0, t=40), font=dict(size=12))  # Adjusted layout
        st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader('Adverse Events by Body System')
        fig5 = px.scatter(
                df5,
                x='USUBJID',  
                y='AEBODSYS', 
                color='TRTA',
                symbol='AEOUT',  
                labels={'AEBODSYS': 'Body System', 'Count': 'Number of Cases', 'TRTA': 'Treatment','USUBJID':'Subject Count','AEOUT':'Outcome'}, 
                height=600,
                width=800)
        fig5.update_layout(margin=dict(l=0, r=0, b=0, t=40),font=dict(size=12),legend=dict(orientation="h",yanchor="top",y=-0.2,x=0.01))
        st.plotly_chart(fig5,use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            st.subheader('Total Adverse Event Duration by Hospitalization')
            fig3 = px.bar(df3, x='AESHOSP', y='Total_Adverse_Event_Duration', color='TRTA',
                          labels={'AESHOSP': 'Hospitalizaion', 'Total_Adverse_Event_Duration': 'Duration', 'TRTA': 'Treatment'},
                          height=400, width=700)
            fig3.update_layout(margin=dict(l=0, r=0, b=0, t=40), font=dict(size=12))  # Adjusted layout
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            st.subheader('Adverse Event Duration by Severity')
            fig4 = px.sunburst(
                df4,
                path=['TRTA', 'AESEV'],  # Define hierarchy: Treatment -> Severity
                values='ADURN',  # Size of each slice represents duration
                labels={'TRTA': 'Treatment', 'AESEV': 'Severity', 'ADURN': 'Duration'},
                color='TRTA',  # Color by treatment
                height=400,
                width=800)
            st.plotly_chart(fig4, use_container_width=True)
        
        col5,col6 = st.columns(2)
        with col5:
            st.subheader('Severity Causal Relationship')
            fig6 = px.bar(df6, x='AEREL', y='AESEV', color='TRTA',
                          labels={'AEREL': 'Causality', 'AESEV': 'Severity', 'TRTA': 'Treatment'},
                          height=400, width=900,barmode='group')
            fig6.update_layout(margin=dict(l=0, r=0, b=0, t=40), font=dict(size=12))  
            st.plotly_chart(fig6, use_container_width=True) 
    else:
        st.header(f"Adverse Events Overview for {selected_treatment}")


        st.subheader('AE by Subjects')
        df1_filtered = df1[df1['TRTA'] == selected_treatment]
        fig1 = px.scatter(df1_filtered, x='ADURN', y='AEBODSYS', color='TRTA',
                              labels={'ADURN': 'Duration', 'AEBODSYS': 'Body System', 'TRTA': 'Treatment'},
                              height=400, width=900)
        fig1.update_layout(margin=dict(l=200, r=0, b=0, t=40), font=dict(size=8))
        st.plotly_chart(fig1, use_container_width=True)

        st.subheader(f'Occurrences for Treatment Group {selected_treatment}')
        df2_filtered = df2[df2['TRTA'] == selected_treatment]
        fig2 = px.scatter(df2_filtered, x='Occurrences', y='AEBODSYS', color='TRTA',
                              labels={'Occurrences': 'Occurrences', 'AEBODSYS': 'Body System', 'TRTA': 'Treatment'},
                              height=400, width=800)
        fig2.update_layout(margin=dict(l=0, r=0, b=0, t=40), font=dict(size=12))  # Adjusted layout
        st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader('Adverse Events by Body System')
        df5_filtered = df5[df5['TRTA'] == selected_treatment]
        fig5 = px.scatter(
                df5_filtered,
                x='USUBJID',  # Use 'Count' for the x-axis
                y='AEBODSYS',  # Use 'AEBODSYS' for the y-axis
                color='TRTA',
                symbol = 'AEOUT',# Different colors for different treatments
                labels={'AEBODSYS': 'Body System', 'Count': 'Number of Cases', 'TRTA': 'Treatment','USUBJID':'Subject Count','AEOUT':'Outcome'},  # Labels for axes and legend
                height=400,
                width=2000)
        st.plotly_chart(fig5,use_container_width=True)

        col3, col4 = st.columns(2)

        with col3:
            st.subheader('Total Adverse Event Duration by Hospitalization')
            df3_filtered = df3[df3['TRTA'] == selected_treatment]
            fig3 = px.bar(df3_filtered, x='AESHOSP', y='Total_Adverse_Event_Duration', color='TRTA',
                          labels={'AESHOSP': 'Hospitaliztion', 'Total_Adverse_Event_Duration': 'Duration', 'TRTA': 'Treatment'},
                          height=400, width=800  # Increased size
                          )
            fig3.update_layout(margin=dict(l=0, r=0, b=0, t=40), font=dict(size=12))  # Adjusted layout
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            st.subheader('Adverse Event Duration by Severity')
            df4_filtered = df4[df4['TRTA'] == selected_treatment]
            fig4 = px.pie(df4, names='AESEV', values='ADURN', hole=0.35,
                          labels={'AESEV': 'Severity', 'ADURN': 'Duration'},
                          height=400, width=800)  # Increased width
            fig4.update_layout(margin=dict(l=0, r=0, b=0, t=40), font=dict(size=12))  # Adjusted layout
            st.plotly_chart(fig4, use_container_width=True)


        col5,col6 = st.columns(2)    
        with col5:    
            st.subheader('Severity Causal Relationship')
            df6_filtered = df6[df6['TRTA'] == selected_treatment]
            fig6 = px.bar(df6_filtered, y='AESEV', x='AEREL', color='TRTA',
                          labels={'AEREL': 'Causality', 'AESEV': 'Severity', 'TRTA': 'Treatments'},
                          height=400, width=800,barmode='group' # Increased size
                          )
            fig6.update_layout(margin=dict(l=0, r=0, b=0, t=40), font=dict(size=12))  # Adjusted layout
            st.plotly_chart(fig6, use_container_width=True)
