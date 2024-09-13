import streamlit as st
import pandas as pd
import altair as alt
import io
import toml

scoutId2name = {
    'D0370AFB-8526-4AB6-8443-855A8C4FA66C': 'Business Contraction',
    'B78772F2-79E4-4EE9-A216-06FB510DA56C': 'Business Expansion',
    '3F2D6A22-A150-4294-81E7-641B31CDBEA3': 'Corruption / Fraud',
    '3247A303-9928-4E68-8C75-A94896674ADC': 'Cybersecurity',
    '6E0DD46D-2E3E-4295-BCA8-BDEFC38CDDA0': 'Financial Distress',
    'BD5122ED-0062-4F69-A05A-3FEBF2214B66': 'Fund Raising',
    'C340B8BB-B4EE-4C6F-8A5C-64042BF2BB84': 'Initial Public Offering',
    'DA319688-26CE-4AF3-B3A3-36AACF56D6FC': 'Layoffs',
    'ADEAC249-160D-409B-8B3C-D1C34764CEAD': 'Management Changes',
    '5B4848D9-4EF3-427A-8D39-214FFC68F0B9': 'Mergers & Acquisitions',
    '11E43097-A519-4B37-B206-141C290A65C0': 'Monetary Policy',
    '381971A8-ABFF-4579-A085-440754109976': 'Partnerships and Collaborations',
    'A0291382-9FE1-4A53-B4CB-0ADA081BDECC': 'Product Development',
    'B975FB00-3A7B-4EC4-9CA0-F1CB87D27F8A': 'Severe Business Disruption',
    '17DD67DF-14C9-4429-8621-2B864805B542': 'Suits and Litigation (new)' ,
    '3D46B8DF-F362-4AFA-A008-876CC103A0E9': 'ESG Investing',
    'B29A4CDE-D3C8-47C7-B131-8093298E2F8C': 'Money Laundering',
    '0BF7608C-1345-4709-BDD7-F9801EC1CA3D': 'Regulatory Actions',
    'ED499931-5D59-4AC1-B5C2-C327E4C086DD': 'Supply Shortages',
}

scoutname2Id = {v:k for k,v in scoutId2name.items()}

# buffer to use for excel writer
buffer = io.BytesIO()

st.set_page_config(
    page_title="Key Developments",
    layout="wide",
    initial_sidebar_state="expanded")


@st.cache_data
def convert_to_csv(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv(index=False).encode('utf-8')

def plot_timeline(df):
    # Assuming 'df' is your DataFrame with a 'keyDevEventTypeName' column
    # 1. Count the occurrences of each keyDevEventTypeName
    topic_counts = df['keyDevEventTypeName'].value_counts().reset_index()
    topic_counts.columns = ['keyDevEventTypeName', 'count']

    # 2. Merge the occurrence count with the original DataFrame
    merged_df = pd.merge(df, topic_counts, on='keyDevEventTypeName')

    # 3. Sort the merged DataFrame based on the count (descending) and the keyDevEventTypeName
    df = merged_df.sort_values(by=['count'], ascending=[False])

    # top_n = st.number_input('Enter the number of top topics:', min_value=1, value=10, step=1)
    top_n = 10

    # 2. Sort by count and take the top 10
    top_10_topics = list(topic_counts['keyDevEventTypeName'])[:top_n]

    # 3. Filter the original DataFrame to keep only rows with the top 10 topics
    df = df[df['keyDevEventTypeName'].isin(top_10_topics)]

    df['cluster_first_date'] = pd.to_datetime(df['cluster_first_date'], format='mixed')

    height = 600
    # Display the bar chart
    company_name = df['companyName'][0]
    # st.title(company_name)
    with col3:
        st.header("ScoutAI Counts")
        st.altair_chart(alt.Chart(topic_counts).mark_bar().encode(
                        y=alt.X('keyDevEventTypeName', sort='-x',  title="Day of week"),
                        x=alt.Y('count', title="count"),
                        color=alt.Color('count'),
                    ).properties(height=height), use_container_width=True)
        # height = st.number_input("Chart Height", min_value=100, value=600)

    # Create the Altair chart
    timeline_chart = alt.Chart(df).mark_circle().encode(
        x=alt.X("cluster_first_date:T",  axis=alt.Axis(title="Date", format="%d-%m-%Y")),
        y=alt.Y("keyDevEventTypeName:N", sort=alt.EncodingSortField(field='count', op='count', order='descending'), axis=alt.Axis(title="Scout AI")),
        color=alt.Color("keyDevEventTypeName:N", sort=alt.EncodingSortField(field='count', op='count', order='descending'), title="Scout AI"),
        # legend=alt.Legend(title="Scout AI", sort=alt.EncodingSortField(field='count', op='count', order='descending')),
        tooltip=["headline", "cluster_first_date", "situation"],
        size=alt.value(200),
    ).properties(title="Timeline", height=height)

    # Display the chart in Streamlit
    with col2:
        st.title(f"{company_name} Key Developments")
        st.altair_chart(timeline_chart, use_container_width=True)

col2, col3 = st.columns([4, 1])


with st.sidebar:

    uploaded_file = st.file_uploader("Upload past keydev results")
    if uploaded_file:
        #read csv
        print(uploaded_file)
        if '.csv' in uploaded_file.name:
            df=pd.read_csv(uploaded_file)
        else:
            df=pd.read_excel(uploaded_file, sheet_name=0)
            print(df)

        for key in ["cluster_first_date", "companyName", "keyDevEventTypeName", "headline", "situation"]:
            try:
                assert key in df.columns
            except AssertionError:
                print(f"{key} was not found in the excel or csv, please make sure it exists/rename")
                st.warning(f"{key} was not found in the excel or csv, please make sure it exists/rename")
                break
        else:
            # Input fields
            company_counts = {}
            for company in df['companyName']:
                if company not in company_counts:
                    company_counts[company] = 0
                company_counts[company] += 1
            sorted_companies = sorted(company_counts.items(), key=lambda item: item[1], reverse=True)
            scout_ai_list_company_name = st.selectbox(
                            'Companies',
                            [c for c,_ in sorted_companies],
                            )

            df = df[df['companyName'].isin([scout_ai_list_company_name])]


            plot_timeline(df)
    else:
        with open(".streamlit/secrets.toml", "r") as f:
            loaded = toml.load(f, _dict=dict)
        output_df = pd.DataFrame(loaded)
        plot_timeline(output_df)