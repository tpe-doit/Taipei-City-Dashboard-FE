from airflow import DAG
from operators.common_pipeline import CommonDag


def _D080101(**kwargs):
    from proj_city_dashboard.D080101.cdc_visit_case_etl import cdc_visit_case_etl
    
    URL = "https://od.cdc.gov.tw/eic/NHI_AcuteUpperRespiratoryInfections.csv"
    DIEASE_NAME = '急性上呼吸道感染'
    
    cdc_visit_case_etl(URL, DIEASE_NAME, **kwargs)


dag = CommonDag(proj_folder="proj_city_dashboard/v1", dag_folder="D080101")
dag.create_dag(etl_func=_D080101)