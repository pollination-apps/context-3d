# coding=utf-8
import streamlit as st

def generate_element(text, color):
    return '''
    <span style="
        height: 16px;
        width: 16px;
        background-color: rgb{0};
        border-radius: 50%;
        display: inline-block;
        ">
    </span><span style="margin: 0px 10px 5px 5px;">{1}</span>
    '''.format(tuple(color.tolist()), text).replace('\n', '')

def generate_legend(legend_data: dict):
    html_leg = ''
    for k, v in legend_data.items():
        html_leg += generate_element(k, v)
    
    legend = """
        </head>
        <body>
        <div style="text-align:left">
        <h3>Legend</h3>
        {}
        </div>
        </body>
        """.format(html_leg)
    
    st.markdown(legend, unsafe_allow_html=True)