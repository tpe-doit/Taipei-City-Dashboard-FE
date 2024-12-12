from airflow import DAG
from operators.common_pipeline import CommonDag
from datetime import datetime,timedelta,timezone
import pandas as pd
import requests
from settings.global_config import PROXIES
from sqlalchemy import create_engine
from utils.get_time import get_tpe_now_time_str
from utils.load_stage import (
    save_dataframe_to_postgresql,
    update_lasttime_in_data_to_dataset_info,
)
from utils.auth_cht import CHTAuth
from airflow.models import Variable
import logging

def _cht_g4(**kwargs):
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    now_time = datetime.now(timezone(timedelta(seconds=28800)))  # Taiwan timezone
    cht = CHTAuth()
    access_token = cht.get_token(now_time)
    url = Variable.get("G2_G4_API_URL")
    print(url)
    headers = {
        'Content-Type': 'application/json'
        }   

    playload = {
        "token": access_token,
        "split": "1",
        "api_id": "33"
    }
    resp = requests.post(url, headers=headers, data=playload, proxies=PROXIES,verify=False)
    print(resp.text)
    if resp.status_code != 200:
        raise ValueError(f"Request failed! status: {resp.status_code}")

    res = resp.json()
    if res['status'] == 1:
        raw_data = pd.DataFrame(res["data"])
        raw_data['time'] = res['time']
        raw_data['data_time'] = get_tpe_now_time_str()
        raw_data['status'] = res['status']
        raw_data['api_id'] =res['api_id']
        raw_data['msg'] = res['msg']
    else:
        print(res)

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        data=raw_data,
        load_behavior=load_behavior,
        default_table=default_table,
    )
    update_lasttime_in_data_to_dataset_info(
            engine, dag_id, raw_data["data_time"].max()
        )

dag = CommonDag(proj_folder="proj_city_dashboard", dag_folder="cht_g4")
dag.create_dag(etl_func=_cht_g4)



