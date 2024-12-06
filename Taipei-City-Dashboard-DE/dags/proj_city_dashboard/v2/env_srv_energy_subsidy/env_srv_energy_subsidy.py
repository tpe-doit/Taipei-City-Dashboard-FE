from airflow import DAG
from operators.common_pipeline import CommonDag
import pandas as pd
from sqlalchemy import create_engine
from utils.extract_stage import get_data_taipei_api
from utils.load_stage import (
    save_geodataframe_to_postgresql,
    update_lasttime_in_data_to_dataset_info,
)

from datetime import datetime
from utils.transform_address import (
    clean_data,
    get_addr_xy_parallel,
    main_process,
    save_data,
)
from utils.transform_geometry import add_point_wkbgeometry_column_to_df
from utils.transform_time import convert_str_to_time_format


dag_id = "env_srv_energy_subsidy"


def _transfer(**kwargs):


    ##############
    ## get config
    ##############
    ready_data_db_uri = kwargs.get("ready_data_db_uri")
    data_path = kwargs.get("data_path")
    dag_infos = kwargs.get("dag_infos")
    dag_id = dag_infos.get("dag_id")
    load_behavior = dag_infos.get("load_behavior")
    default_table = dag_infos.get("ready_data_default_table")
    history_table = dag_infos.get("ready_data_history_table")
    RID = "01370301-b843-4b60-ae8c-6a8789880bfe"
    FROM_CRS = 4326
    GEOMETRY_TYPE = "Point"

    ##############
    ## Extract
    ##############
    raw_list = get_data_taipei_api(RID)
    raw_data = pd.DataFrame(raw_list)
    # raw_data["data_time"] = raw_data["_importdate"].iloc[0]["date"]
    
    raw_data["etl_dtm"] = datetime.now()
    print(raw_data)

    ##############
    ## Transform
    ##############
    data = raw_data.copy()
    # rename
    data = data.rename(
        columns={
            "年度": "data_year",
            "核撥件數": "num_of_approval",
            "累積核撥件數": "acc_num_of_approval",
            "補助金額": "subsidy_amt",
            "累計補助金額": "acc_subsidy_amt",
            "節電量": "enegry_saving_amt",
            "累積節電量": "acc_enegry_saving_amt",
        }
    )

    # # standardize time
    # data["etl_dtm"] = convert_str_to_time_format(data["etl_dtm"])
    # # geocoding
    # addr = data["address"]
    # addr_cleaned = clean_data(addr)
    # standard_addr_list = main_process(addr_cleaned)
    # result, output = save_data(addr, addr_cleaned, standard_addr_list)
    # data["address"] = output
    # unique_addr = pd.Series(output.unique())
    # x, y = get_addr_xy_parallel(unique_addr)
    # temp = pd.DataFrame({"lng": x, "lat": y, "address": unique_addr})
    # data = pd.merge(data, temp, on="address", how="left")
    # # add town
    # town_pattern = "(中正|大同|中山|松山|大安|萬華|信義|士林|北投|內湖|南港|文山)區"
    # data["town"] = data["address"].str.extract(town_pattern, expand=False) + "區"
    # data.loc[data["town"] == "區", "town"] = ""
    # # define columns
    # data["lng"] = pd.to_numeric(data["lng"], errors="coerce")
    # data["lat"] = pd.to_numeric(data["lat"], errors="coerce")
    # # geometry
    # gdata = add_point_wkbgeometry_column_to_df(
    #     data, data["lng"], data["lat"], from_crs=FROM_CRS
    # )


    # select columns
    ready_data = gdata[
        [
            "data_time",
            "town",
            "address",
            "area",
            "person_capacity",
            "is_accessible",
            "lng",
            "lat",
            "wkb_geometry",
        ]
    ]

    # Load
    engine = create_engine(ready_data_db_uri)
    save_dataframe_to_postgresql(
        engine,
        gdata=ready_data,
        load_behavior=load_behavior,
        default_table=default_table,
        history_table=history_table,
        # geometry_type=GEOMETRY_TYPE,
    )


    # lasttime_in_data = data["data_time"].max()
    # update_lasttime_in_data_to_dataset_info(engine, dag_id, lasttime_in_data)


dag = CommonDag(proj_folder="proj_city_dashboard/v2", dag_folder= dag_id)
dag.create_dag(etl_func=_transfer)